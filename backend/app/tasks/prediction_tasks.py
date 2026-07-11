from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from pathlib import Path
from app.core.config import settings
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.waste import DailyProductionLog, ProductionLogStatus
from app.services.ml_service import predict_profile_wip


@celery_app.task(name="app.tasks.prediction_tasks.celery_health_check")
def celery_health_check() -> str:
    return "celery ok"


@celery_app.task(name="app.tasks.prediction_tasks.add_numbers")
def add_numbers(left: int, right: int) -> int:
    return left + right


@celery_app.task(name="app.tasks.prediction_tasks.predict_wip")
def predict_wip(task_id: str) -> dict:
    with SessionLocal() as db:
        log = db.scalar(
            select(DailyProductionLog)
            .options(selectinload(DailyProductionLog.profile_details))
            .where(DailyProductionLog.task_id == task_id)
        )

        if log is None:
            return {
                "status": "NOT_FOUND",
                "task_id": task_id,
                "message": "Prediction log not found.",
            }

        if log.status != ProductionLogStatus.PROCESSING:
            return {
                "status": "SKIPPED",
                "task_id": task_id,
                "message": f"Log status is {log.status.value}, not PROCESSING.",
            }

        profile_details = sorted(
            log.profile_details,
            key=lambda detail: detail.detail_seq,
        )

        if not profile_details:
            log.status = ProductionLogStatus.FAILED
            db.commit()

            return {
                "status": "FAILED",
                "task_id": task_id,
                "message": "No profile details found.",
            }

        predictions = predict_profile_wip(profile_details)

        total_wip = Decimal("0")

        for detail, prediction in zip(profile_details, predictions, strict=True):
            predicted_wip = Decimal(str(round(prediction, 2)))
            detail.predicted_wip_ton = predicted_wip
            total_wip += predicted_wip

        log.estimasi_wip_total = total_wip

        estimated_prime = (
            log.total_output_ton
            - total_wip
            - log.estimasi_manual_class_b
            - log.estimasi_manual_reject
        )

        log.estimasi_prime = max(estimated_prime, Decimal("0"))

        if total_wip > log.total_output_ton:
            log.status = ProductionLogStatus.ANOMALY
        else:
            log.status = ProductionLogStatus.DRAFT

        active_model_folder = Path(settings.MODEL_ARTIFACT_PATH).parent.name
        log.model_artifact_id = active_model_folder

        db.commit()

        return {
            "status": log.status.value,
            "task_id": task_id,
            "profile_count": len(profile_details),
            "estimasi_wip_total": float(log.estimasi_wip_total),
            "estimasi_prime": float(log.estimasi_prime),
        }