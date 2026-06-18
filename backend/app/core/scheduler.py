from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.sweeper_service import sweep_stale_processing_logs


logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Jakarta")


def run_sweeper_job() -> None:
    with SessionLocal() as db:
        result = sweep_stale_processing_logs(db)

    if result.stale_count > 0:
        logger.warning(
            "Sweeper marked %s stale PROCESSING logs as FAILED. task_ids=%s",
            result.stale_count,
            result.failed_task_ids,
        )
    else:
        logger.info("Sweeper checked stale PROCESSING logs. No stale logs found.")


def start_scheduler() -> None:
    if not settings.SWEEPER_ENABLED:
        logger.info("Sweeper scheduler is disabled.")
        return

    if scheduler.running:
        logger.info("Sweeper scheduler is already running.")
        return

    scheduler.add_job(
        run_sweeper_job,
        trigger="interval",
        seconds=settings.SWEEPER_INTERVAL_SECONDS,
        id="sweeper_stale_processing_logs",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()

    logger.info(
        "Sweeper scheduler started. interval_seconds=%s timeout_minutes=%s",
        settings.SWEEPER_INTERVAL_SECONDS,
        settings.PROCESSING_TIMEOUT_MINUTES,
    )


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Sweeper scheduler stopped.")