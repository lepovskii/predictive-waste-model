from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.waste import DailyProductionLog, ProductionLogStatus


@dataclass(frozen=True)
class SweeperResult:
    checked_at: datetime
    timeout_minutes: int
    stale_count: int
    failed_task_ids: list[str]


def get_stale_processing_logs(
    db: Session,
    cutoff_time: datetime,
) -> list[DailyProductionLog]:
    return list(
        db.scalars(
            select(DailyProductionLog)
            .where(DailyProductionLog.status == ProductionLogStatus.PROCESSING)
            .where(DailyProductionLog.updated_at < cutoff_time)
            .order_by(DailyProductionLog.updated_at)
        )
    )


def mark_stale_logs_failed(
    db: Session,
    stale_logs: list[DailyProductionLog],
) -> list[str]:
    failed_task_ids: list[str] = []

    for log in stale_logs:
        log.status = ProductionLogStatus.FAILED

        if log.task_id is not None:
            failed_task_ids.append(log.task_id)

    if stale_logs:
        db.commit()

    return failed_task_ids


def sweep_stale_processing_logs(
    db: Session,
    timeout_minutes: int | None = None,
) -> SweeperResult:
    timeout = timeout_minutes or settings.PROCESSING_TIMEOUT_MINUTES

    checked_at = datetime.now(timezone.utc)
    cutoff_time = checked_at - timedelta(minutes=timeout)

    stale_logs = get_stale_processing_logs(
        db=db,
        cutoff_time=cutoff_time,
    )

    failed_task_ids = mark_stale_logs_failed(
        db=db,
        stale_logs=stale_logs,
    )

    return SweeperResult(
        checked_at=checked_at,
        timeout_minutes=timeout,
        stale_count=len(stale_logs),
        failed_task_ids=failed_task_ids,
    )