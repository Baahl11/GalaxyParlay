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


def job_sync_player_stats():
    """
    Job: Sync player season statistics from API-Football.
    Frequency: Every Sunday at 3 AM UTC (weekly)
    """
    try:
        logger.info("job_sync_player_stats_started")
        from app.routes.jobs import sync_all_player_statistics

        result = sync_all_player_statistics(limit=120)
        logger.info(
            "job_sync_player_stats_complete",
            players_synced=result.get("players_synced", 0),
            teams_processed=result.get("teams_processed", 0),
        )
    except Exception as e:
        logger.error("job_sync_player_stats_error", error=str(e))


def job_sync_referee_stats():
    """
    Job: Sync referee statistics from upcoming fixtures.
    Frequency: Weekly (Sunday 4 AM UTC)
    """
    try:
        logger.info("job_sync_referee_stats_started")
        from app.routes.jobs import sync_referee_statistics

        result = sync_referee_statistics()
        logger.info(
            "job_sync_referee_stats_complete",
            referees_synced=result.get("referees_synced", 0),
            referees_failed=result.get("referees_failed", 0),
        )
    except Exception as e:
        logger.error("job_sync_referee_stats_error", error=str(e))


def job_sync_live_scores():
    """
    Job: Update live fixtures and scores.
    Frequency: Every 5 minutes
    """
    try:
        logger.info("job_sync_live_started")
        from app.routes.jobs import sync_live_scores

        result = sync_live_scores()
        logger.info(
            "job_sync_live_complete",
            updated=result.get("fixtures_updated", 0),
            live_fixtures=result.get("live_fixtures", 0),
        )
    except Exception as e:
        logger.error("job_sync_live_error", error=str(e))


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

    # Job 4: Sync live scores every 5 minutes
    scheduler.add_job(
        job_sync_live_scores,
        trigger=IntervalTrigger(minutes=5),
        id="sync_live_scores",
        name="Sync Live Scores",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Job 5: Sync player statistics weekly (Sunday 3 AM UTC)
    scheduler.add_job(
        job_sync_player_stats,
        trigger=CronTrigger(day_of_week="sun", hour="3", minute="0"),
        id="sync_player_stats",
        name="Sync Player Stats",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Job 6: Sync referee statistics weekly (Sunday 4 AM UTC)
    scheduler.add_job(
        job_sync_referee_stats,
        trigger=CronTrigger(day_of_week="sun", hour="4", minute="0"),
        id="sync_referee_stats",
        name="Sync Referee Stats",
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
