"""
Automatic Background Jobs Scheduler - Simplified
Usa endpoints existentes que YA funcionan en producción.
"""

import asyncio
from typing import Optional

import httpx
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = structlog.get_logger(__name__)

# Scheduler global
scheduler: Optional[AsyncIOScheduler] = None


async def job_load_fixtures():
    """
    Job: Cargar fixtures usando el endpoint existente /jobs/sync-fixtures.
    Frecuencia: Cada 12 horas (6 AM, 6 PM UTC)
    """
    try:
        logger.info("job_load_fixtures_started")

        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:8001/jobs/sync-fixtures", timeout=300.0)

            if response.status_code == 200:
                result = response.json()
                logger.info("job_load_fixtures_completed", result=result)
            else:
                logger.error(
                    "job_load_fixtures_failed", status=response.status_code, text=response.text
                )

    except Exception as e:
        logger.error("job_load_fixtures_error", error=str(e), exc_info=True)


async def job_generate_predictions():
    """
    Job: Generar predicciones usando el endpoint existente /jobs/run-predictions.
    Frecuencia: Cada 6 horas
    """
    try:
        logger.info("job_generate_predictions_started")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/jobs/run-predictions", timeout=600.0  # 10 minutos timeout
            )

            if response.status_code == 200:
                result = response.json()
                logger.info("job_generate_predictions_completed", result=result)
            else:
                logger.error(
                    "job_generate_predictions_failed",
                    status=response.status_code,
                    text=response.text,
                )

    except Exception as e:
        logger.error("job_generate_predictions_error", error=str(e), exc_info=True)


def start_scheduler():
    """
    Inicia el scheduler con los jobs configurados.
    """
    global scheduler

    if scheduler is not None:
        logger.warning("scheduler_already_running")
        return

    logger.info("scheduler_starting")

    scheduler = AsyncIOScheduler(timezone="UTC")

    # Job 1: Cargar fixtures cada 12 horas (6 AM, 6 PM UTC)
    scheduler.add_job(
        job_load_fixtures,
        trigger=CronTrigger(hour="6,18", minute="0"),
        id="load_fixtures",
        name="Load Fixtures",
        replace_existing=True,
    )

    # Job 2: Generar predicciones cada 6 horas
    scheduler.add_job(
        job_generate_predictions,
        trigger=IntervalTrigger(hours=6),
        id="generate_predictions",
        name="Generate Predictions",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("scheduler_started", jobs_count=len(scheduler.get_jobs()))


def stop_scheduler():
    """
    Detiene el scheduler.
    """
    global scheduler

    if scheduler is None:
        logger.warning("scheduler_not_running")
        return

    logger.info("scheduler_stopping")
    scheduler.shutdown()
    scheduler = None
    logger.info("scheduler_stopped")
