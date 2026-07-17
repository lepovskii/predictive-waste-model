from __future__ import annotations

import json
from pathlib import Path
from datetime import date
import redis
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

from app.core.config import settings, update_active_model_path
from app.services.ml_service import clear_model_cache
from app.schemas.model_manager import (
    AvailableModelsResponse,
    ModelArtifact,
    ModelMetadata,
    SwitchModelRequest,
    SwitchModelResponse,
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
    responses={
        409: {"description": "Production date already exists (Duplicate)"},
        503: {"description": "Celery task dispatch failed"},
    },
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
    responses={
        422: {"description": "Validation Error (e.g., date_from > date_to)"},
    },
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
    sort: str = Query(default="activity_desc", pattern="^(activity_desc|activity_asc|date_desc|date_asc)$"),
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
        sort_order=sort,
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
    responses={
        404: {"description": "Task ID not found"},
    },
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
        model_artifact_id=log.model_artifact_id,
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
        model_artifact_id=log.model_artifact_id,
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

@router.get("/models", response_model=AvailableModelsResponse)
def get_available_models():
    from app.services.ml_service import get_active_artifact_id
    
    base_dir = Path(__file__).resolve().parents[3]
    artifacts_dir = base_dir / "ml_training" / "artifacts"
    
    active_folder_name = get_active_artifact_id()
    
    models = []
    
    if artifacts_dir.exists():
        for folder in artifacts_dir.iterdir():
            if folder.is_dir():
                pipeline_path = folder / "pipeline.pkl"
                metadata_path = folder / "model_metadata.json"
                
                # Jika folder memiliki pkl dan json, kita anggap sebagai artifact yang valid
                if pipeline_path.exists() and metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata_dict = json.load(f)
                            
                        is_active = (folder.name == active_folder_name)
                        
                        models.append(
                            ModelArtifact(
                                artifact_id=folder.name,
                                folder_name=folder.name,
                                is_active=is_active,
                                metadata=ModelMetadata(**metadata_dict)
                            )
                        )
                    except Exception:
                        pass
                        
    return AvailableModelsResponse(
        active_artifact_id=active_folder_name,
        models=models
    )

@router.post("/models/switch", response_model=SwitchModelResponse)
def switch_active_model(payload: SwitchModelRequest):
    base_dir = Path(__file__).resolve().parents[3]
    new_artifact_path = f"ml_training/artifacts/{payload.artifact_id}/pipeline.pkl"
    full_path = base_dir / new_artifact_path
    
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact tidak ditemukan di: {new_artifact_path}"
        )
        
    # Update file .env dan hapus cache ML Service agar refresh
    update_active_model_path(new_artifact_path)
    clear_model_cache()
    
    # Simpan ke Redis agar Celery Worker langsung tahu tanpa restart
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.set("active_model_artifact_id", payload.artifact_id)
    
    return SwitchModelResponse(
        message=f"Model berhasil diganti ke {payload.artifact_id}",
        active_artifact_id=payload.artifact_id
    )
