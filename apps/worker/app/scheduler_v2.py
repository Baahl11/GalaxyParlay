"""
Automatic Background Jobs Scheduler - Production Version
Uses direct service calls to existing working endpoints.
"""

import asyncio
from typing import Optional

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = structlog.get_logger(__name__)

# Scheduler global
scheduler: Optional[AsyncIOScheduler] = None


def job_load_fixtures_sync():
    """
    Job: Cargar fixtures manualmente via manual trigger endpoint.
    Frecuencia: Cada 12 horas (6 AM, 6 PM UTC)

    Nota: Este job solo registra el evento. Las fixtures se cargan vía API manual.
    """
    try:
        logger.info(
            "job_load_fixtures_triggered",
            message="Use POST /jobs/trigger-load-fixtures para cargar fixtures manualmente",
        )
    except Exception as e:
        logger.error("job_load_fixtures_error", error=str(e))


def job_generate_predictions_sync():
    """
    Job: Trigger para generar predicciones via endpoint manual.
    Frecuencia: Cada 6 horas

    Nota: Este job solo registra el evento. Las predicciones se generan vía API manual.
    """
    try:
        logger.info(
            "job_generate_predictions_triggered",
            message="Use POST /jobs/trigger-generate-predictions para generar predicciones manualmente",
        )
    except Exception as e:
        logger.error("job_generate_predictions_error", error=str(e))


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

    # Job 1: Recordatorio para cargar fixtures cada 12 horas (6 AM, 6 PM UTC)
    scheduler.add_job(
        job_load_fixtures_sync,
        trigger=CronTrigger(hour="6,18", minute="0"),
        id="load_fixtures_reminder",
        name="Load Fixtures Reminder",
        replace_existing=True,
    )

    # Job 2: Recordatorio para generar predicciones cada 6 horas
    scheduler.add_job(
        job_generate_predictions_sync,
        trigger=IntervalTrigger(hours=6),
        id="generate_predictions_reminder",
        name="Generate Predictions Reminder",
        replace_existing=True,
    )

    scheduler.start()

    jobs = scheduler.get_jobs()
    logger.info(
        "scheduler_started",
        jobs_count=len(jobs),
        jobs=[{"id": j.id, "name": j.name, "next_run": str(j.next_run_time)} for j in jobs],
    )


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
