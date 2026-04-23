"""
Automatic Background Jobs Scheduler - Production Version
Calls actual service functions directly on schedule.
"""

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
    Job: Load upcoming fixtures from API-Football for next 7 days.
    Frequency: Every 12 hours (6 AM, 6 PM UTC)
    """
    try:
        logger.info("job_load_fixtures_started")
        # Import here to avoid circular import at module level
        from app.routes.jobs import sync_fixtures

        result = sync_fixtures()
        logger.info(
            "job_load_fixtures_complete",
            fixtures_synced=result.get("fixtures_synced", 0),
            leagues_processed=result.get("leagues_processed", 0),
        )
    except Exception as e:
        logger.error("job_load_fixtures_error", error=str(e))


def job_generate_predictions_sync():
    """
    Job: Generate ML predictions for all upcoming NS fixtures.
    Frequency: Every 6 hours
    """
    try:
        logger.info("job_generate_predictions_started")
        from app.routes.jobs import run_predictions

        result = run_predictions()
        logger.info(
            "job_generate_predictions_complete",
            predictions_generated=result.get("predictions_generated", 0),
            fixtures_processed=result.get("fixtures_processed", 0),
        )
    except Exception as e:
        logger.error("job_generate_predictions_error", error=str(e))


def job_sync_results_sync():
    """
    Job: Update results for recently finished fixtures.
    Frequency: Every 3 hours
    """
    try:
        logger.info("job_sync_results_started")
        from app.routes.jobs import sync_results

        result = sync_results()
        logger.info(
            "job_sync_results_complete",
            updated=result.get("fixtures_updated", 0),
            checked=result.get("candidates_checked", 0),
        )
    except Exception as e:
        logger.error("job_sync_results_error", error=str(e))


def start_scheduler():
    """
    Start the scheduler with production jobs.
    """
    global scheduler

    if scheduler is not None:
        logger.warning("scheduler_already_running")
        return

    logger.info("scheduler_starting")

    scheduler = AsyncIOScheduler(timezone="UTC")

    # Job 1: Load fixtures every 12 hours (6 AM, 6 PM UTC)
    scheduler.add_job(
        job_load_fixtures_sync,
        trigger=CronTrigger(hour="6,18", minute="0"),
        id="load_fixtures",
        name="Load Fixtures",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Job 2: Generate predictions every 6 hours
    scheduler.add_job(
        job_generate_predictions_sync,
        trigger=IntervalTrigger(hours=6),
        id="generate_predictions",
        name="Generate Predictions",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Job 3: Sync results every 3 hours
    scheduler.add_job(
        job_sync_results_sync,
        trigger=IntervalTrigger(hours=3),
        id="sync_results",
        name="Sync Results",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
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
