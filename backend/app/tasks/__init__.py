from app.tasks.prediction_tasks import (
    add_numbers,
    celery_health_check,
    predict_wip,
)

__all__ = [
    "add_numbers",
    "celery_health_check",
    "predict_wip",
]