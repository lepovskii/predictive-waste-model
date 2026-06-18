from __future__ import annotations

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "predictive_waste_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.prediction_tasks",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    timezone="Asia/Jakarta",
    enable_utc=True,
)