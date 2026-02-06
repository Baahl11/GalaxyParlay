"""
Automatic Background Jobs Scheduler
Ejecuta tareas periódicas para mantener fixtures y predicciones actualizadas.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import get_supabase_client
from app.services.fixture_loader import load_upcoming_fixtures
from app.services.prediction_generator import generate_predictions_batch

logger = structlog.get_logger(__name__)

# Scheduler global
scheduler: Optional[AsyncIOScheduler] = None


async def job_load_fixtures():
    """
    Job: Cargar fixtures de la próxima semana desde API-Football.
    Frecuencia: Cada 12 horas
    """
    try:
        logger.info("job_load_fixtures_started")

        # Cargar fixtures de los próximos 14 días
        result = await load_upcoming_fixtures(days_ahead=14)

        logger.info(
            "job_load_fixtures_completed",
            fixtures_loaded=result.get("new_fixtures", 0),
            fixtures_updated=result.get("updated_fixtures", 0),
            duration_seconds=result.get("duration", 0),
        )

    except Exception as e:
        logger.error("job_load_fixtures_failed", error=str(e), exc_info=True)


async def job_generate_predictions():
    """
    Job: Generar predicciones para fixtures sin predicciones.
    Frecuencia: Cada 6 horas
    """
    try:
        logger.info("job_generate_predictions_started")

        client = get_supabase_client()

        # Obtener fixtures de los próximos 7 días sin predicciones
        today = datetime.now().strftime("%Y-%m-%d")
        week_ahead = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        # Buscar fixtures
        fixtures_result = (
            client.table("fixtures")
            .select("id,league_id,home_team_id,away_team_id,kickoff_time")
            .gte("kickoff_time", f"{today}T00:00:00")
            .lte("kickoff_time", f"{week_ahead}T23:59:59")
            .order("kickoff_time")
            .execute()
        )

        fixture_ids = [f["id"] for f in fixtures_result.data]

        if not fixture_ids:
            logger.info("job_generate_predictions_no_fixtures")
            return

        # Verificar cuáles ya tienen predicciones
        pred_result = (
            client.table("model_predictions")
            .select("fixture_id")
            .in_("fixture_id", fixture_ids)
            .execute()
        )

        fixtures_with_predictions = set(p["fixture_id"] for p in pred_result.data)
        fixtures_to_predict = [
            f for f in fixtures_result.data if f["id"] not in fixtures_with_predictions
        ]

        if not fixtures_to_predict:
            logger.info("job_generate_predictions_all_ready")
            return

        logger.info("job_generate_predictions_processing", total_fixtures=len(fixtures_to_predict))

        # Generar predicciones en lotes
        result = await generate_predictions_batch(fixtures_to_predict)

        logger.info(
            "job_generate_predictions_completed",
            predictions_generated=result.get("success_count", 0),
            predictions_failed=result.get("error_count", 0),
            duration_seconds=result.get("duration", 0),
        )

    except Exception as e:
        logger.error("job_generate_predictions_failed", error=str(e), exc_info=True)


async def job_cleanup_old_predictions():
    """
    Job: Limpiar predicciones de partidos pasados (opcional).
    Frecuencia: Diaria a las 3 AM
    """
    try:
        logger.info("job_cleanup_started")

        client = get_supabase_client()

        # Eliminar predicciones de fixtures de hace más de 30 días
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        # Primero obtener fixture_ids antiguos
        old_fixtures = (
            client.table("fixtures")
            .select("id")
            .lt("kickoff_time", f"{cutoff_date}T00:00:00")
            .execute()
        )

        if old_fixtures.data:
            old_fixture_ids = [f["id"] for f in old_fixtures.data]

            # Eliminar predicciones
            result = (
                client.table("model_predictions")
                .delete()
                .in_("fixture_id", old_fixture_ids)
                .execute()
            )

            logger.info(
                "job_cleanup_completed", predictions_deleted=len(result.data) if result.data else 0
            )
        else:
            logger.info("job_cleanup_nothing_to_clean")

    except Exception as e:
        logger.error("job_cleanup_failed", error=str(e), exc_info=True)


async def job_refresh_stale_predictions():
    """
    Job: Refrescar predicciones generadas hace más de 48 horas para fixtures próximos.
    Frecuencia: Cada 24 horas
    """
    try:
        logger.info("job_refresh_stale_predictions_started")

        client = get_supabase_client()

        # Buscar predicciones antiguas de fixtures futuros
        today = datetime.now()
        stale_cutoff = (today - timedelta(hours=48)).isoformat()
        week_ahead = (today + timedelta(days=7)).strftime("%Y-%m-%d")

        # Obtener fixtures próximos
        fixtures_result = (
            client.table("fixtures")
            .select("id,league_id,home_team_id,away_team_id")
            .gte("kickoff_time", today.isoformat())
            .lte("kickoff_time", f"{week_ahead}T23:59:59")
            .execute()
        )

        fixture_ids = [f["id"] for f in fixtures_result.data]

        if not fixture_ids:
            return

        # Buscar predicciones antiguas
        stale_preds = (
            client.table("model_predictions")
            .select("fixture_id,created_at")
            .in_("fixture_id", fixture_ids)
            .lt("created_at", stale_cutoff)
            .execute()
        )

        if not stale_preds.data:
            logger.info("job_refresh_stale_predictions_none_found")
            return

        stale_fixture_ids = set(p["fixture_id"] for p in stale_preds.data)
        fixtures_to_refresh = [f for f in fixtures_result.data if f["id"] in stale_fixture_ids]

        logger.info(
            "job_refresh_stale_predictions_processing", stale_predictions=len(fixtures_to_refresh)
        )

        # Regenerar predicciones
        result = await generate_predictions_batch(fixtures_to_refresh, force_refresh=True)

        logger.info(
            "job_refresh_stale_predictions_completed",
            predictions_refreshed=result.get("success_count", 0),
            duration_seconds=result.get("duration", 0),
        )

    except Exception as e:
        logger.error("job_refresh_stale_predictions_failed", error=str(e), exc_info=True)


def start_scheduler():
    """Iniciar el scheduler con todos los jobs configurados."""
    global scheduler

    if scheduler is not None:
        logger.warning("scheduler_already_running")
        return

    scheduler = AsyncIOScheduler(timezone="UTC")

    # Job 1: Cargar fixtures cada 12 horas (a las 6 AM y 6 PM UTC)
    scheduler.add_job(
        job_load_fixtures,
        trigger=CronTrigger(hour="6,18", minute="0"),
        id="load_fixtures",
        name="Load Upcoming Fixtures",
        replace_existing=True,
        max_instances=1,
        coalesce=True,  # Si se salta una ejecución, solo ejecutar una vez
    )

    # Job 2: Generar predicciones cada 6 horas
    scheduler.add_job(
        job_generate_predictions,
        trigger=IntervalTrigger(hours=6),
        id="generate_predictions",
        name="Generate Predictions",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Job 3: Limpiar datos antiguos diariamente a las 3 AM UTC
    scheduler.add_job(
        job_cleanup_old_predictions,
        trigger=CronTrigger(hour="3", minute="0"),
        id="cleanup_old_data",
        name="Cleanup Old Predictions",
        replace_existing=True,
        max_instances=1,
    )

    # Job 4: Refrescar predicciones antiguas diariamente a las 12 PM UTC
    scheduler.add_job(
        job_refresh_stale_predictions,
        trigger=CronTrigger(hour="12", minute="0"),
        id="refresh_stale_predictions",
        name="Refresh Stale Predictions",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()

    logger.info(
        "scheduler_started",
        jobs=[
            {"id": job.id, "name": job.name, "next_run": str(job.next_run_time)}
            for job in scheduler.get_jobs()
        ],
    )


def stop_scheduler():
    """Detener el scheduler."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info("scheduler_stopped")


@asynccontextmanager
async def scheduler_lifespan():
    """Context manager para integrar con FastAPI lifespan."""
    start_scheduler()

    # Ejecutar jobs inmediatamente al inicio (opcional)
    logger.info("running_initial_jobs")
    await job_load_fixtures()
    await job_generate_predictions()

    yield

    stop_scheduler()
