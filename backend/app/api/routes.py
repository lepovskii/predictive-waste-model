from __future__ import annotations

from datetime import date
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.waste import (
    DailyProductionLog,
    ProductionLogStatus,
)
from app.tasks.prediction_tasks import predict_wip
from app.schemas.prediction import (
    PredictAcceptedResponse,
    PredictRequest,
    PredictionStatusResponse,
    ProfileAcceptedResponse,
    ProfileStatusResponse,
    PredictBatchAcceptedResponse,
    PredictBatchItemResponse,
    PredictBatchItemResult,
    PredictBatchRequest,
    PredictionHistoryItemResponse,
    PredictionHistoryResponse,
)
from app.services.production_service import (
    DuplicateProductionDateError,
    create_prediction_log,
    get_prediction_log_by_task_id,
    mark_prediction_log_failed,
    list_prediction_logs,
)

from app.schemas.reconciliation import (
    ReconcileRequest,
    ReconcileResponse,
)
from app.services.reconciliation_service import (
    reconcile_predictions,
)

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "predictive-waste-api",
    }


@router.post(
    "/predict",
    response_model=PredictAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_prediction(
    payload: PredictRequest,
    db: Session = Depends(get_db),
) -> PredictAcceptedResponse:
    try:
        log = create_prediction_log(db=db, payload=payload)
    except DuplicateProductionDateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Production date already exists. "
                f"production_date={exc.production_date}"
            ),
        ) from exc

    try:
        predict_wip.delay(log.task_id)
    except Exception as exc:
        mark_prediction_log_failed(db=db, log=log)

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction request was stored, but Celery task dispatch failed.",
        ) from exc
    
    return build_predict_accepted_response(log)

@router.post(
    "/predict/batch",
    response_model=PredictBatchAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_prediction_batch(
    payload: PredictBatchRequest,
    db: Session = Depends(get_db),
) -> PredictBatchAcceptedResponse:
    results: list[PredictBatchItemResponse] = []

    accepted_count = 0
    duplicate_count = 0
    failed_count = 0

    for item in payload.items:
        try:
            log = create_prediction_log(db=db, payload=item)
        except DuplicateProductionDateError as exc:
            duplicate_count += 1
            results.append(
                PredictBatchItemResponse(
                    production_date=exc.production_date,
                    result=PredictBatchItemResult.DUPLICATE,
                    message=(
                        "Production date already exists. "
                        f"production_date={exc.production_date}"
                    ),
                )
            )
            continue

        try:
            predict_wip.delay(log.task_id)
        except Exception:
            mark_prediction_log_failed(db=db, log=log)

            failed_count += 1
            results.append(
                PredictBatchItemResponse(
                    production_date=log.production_date,
                    result=PredictBatchItemResult.FAILED,
                    task_id=log.task_id,
                    status=log.status,
                    profile_count=len(log.profile_details),
                    total_output_ton=log.total_output_ton,
                    message=(
                        "Prediction request was stored, "
                        "but Celery task dispatch failed."
                    ),
                )
            )
            continue

        accepted_count += 1
        results.append(
            PredictBatchItemResponse(
                production_date=log.production_date,
                result=PredictBatchItemResult.ACCEPTED,
                task_id=log.task_id,
                status=log.status,
                profile_count=len(log.profile_details),
                total_output_ton=log.total_output_ton,
                message="Prediction request accepted and stored as PROCESSING.",
            )
        )

    return PredictBatchAcceptedResponse(
        total_items=len(payload.items),
        accepted_count=accepted_count,
        duplicate_count=duplicate_count,
        failed_count=failed_count,
        results=results,
    )

@router.get(
    "/predictions",
    response_model=PredictionHistoryResponse,
)
def get_prediction_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: ProductionLogStatus | None = Query(
        default=None,
        alias="status",
    ),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PredictionHistoryResponse:
    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from tidak boleh melebihi date_to.",
        )

    logs, total = list_prediction_logs(
        db=db,
        limit=limit,
        offset=offset,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
    )

    return PredictionHistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            build_prediction_history_item(log)
            for log in logs
        ],
    )

@router.post(
    "/reconcile",
    response_model=ReconcileResponse,
    status_code=status.HTTP_200_OK,
)
def reconcile_prediction_results(
    payload: ReconcileRequest,
    db: Session = Depends(get_db),
) -> ReconcileResponse:
    return reconcile_predictions(
        db=db,
        payload=payload,
    )

@router.get(
    "/status/{task_id}",
    response_model=PredictionStatusResponse,
)
def get_prediction_status(
    task_id: str,
    db: Session = Depends(get_db),
) -> PredictionStatusResponse:
    log = get_prediction_log_by_task_id(db=db, task_id=task_id)

    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    return build_prediction_status_response(log)


def build_predict_accepted_response(
    log: DailyProductionLog,
) -> PredictAcceptedResponse:
    profiles = sorted(log.profile_details, key=lambda detail: detail.detail_seq)

    return PredictAcceptedResponse(
        task_id=log.task_id,
        status=log.status,
        production_date=log.production_date,
        profile_count=len(profiles),
        total_output_ton=log.total_output_ton,
        profiles=[
            ProfileAcceptedResponse(
                detail_seq=detail.detail_seq,
                profile_name=detail.profile_name,
                production_ton=detail.production_ton,
            )
            for detail in profiles
        ],
        message="Prediction request accepted and stored as PROCESSING.",
    )


def build_prediction_status_response(
    log: DailyProductionLog,
) -> PredictionStatusResponse:
    profiles = sorted(log.profile_details, key=lambda detail: detail.detail_seq)

    return PredictionStatusResponse(
        task_id=log.task_id,
        status=log.status,
        production_date=log.production_date,
        total_output_ton=log.total_output_ton,
        estimasi_wip_total=log.estimasi_wip_total,
        estimasi_manual_class_b=log.estimasi_manual_class_b,
        estimasi_manual_reject=log.estimasi_manual_reject,
        estimasi_prime=log.estimasi_prime,
        aktual_wip=log.aktual_wip,
        aktual_prime=log.aktual_prime,
        needs_retraining=log.needs_retraining,
        profiles=[
            ProfileStatusResponse(
                detail_seq=detail.detail_seq,
                profile_name=detail.profile_name,
                production_ton=detail.production_ton,
                predicted_wip_ton=detail.predicted_wip_ton,
                actual_wip_ton=detail.actual_wip_ton,
            )
            for detail in profiles
        ],
        created_at=log.created_at,
        updated_at=log.updated_at,
    )

def build_prediction_history_item(
    log: DailyProductionLog,
) -> PredictionHistoryItemResponse:
    return PredictionHistoryItemResponse(
        task_id=log.task_id,
        status=log.status,
        production_date=log.production_date,
        profile_count=len(log.profile_details),
        total_output_ton=log.total_output_ton,
        estimasi_wip_total=log.estimasi_wip_total,
        estimasi_prime=log.estimasi_prime,
        needs_retraining=log.needs_retraining,
        created_at=log.created_at,
        updated_at=log.updated_at,
    )