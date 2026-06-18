from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.adapter import AdapterPreviewResponse
from app.services.csv_adapter_service import build_csv_adapter_preview


router = APIRouter(
    prefix="/adapter",
    tags=["adapter"],
)

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024


@router.post(
    "/preview",
    response_model=AdapterPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def preview_csv_adapter(
    file: UploadFile = File(...),
) -> AdapterPreviewResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is required.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are supported by this adapter.",
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded CSV file is empty.",
        )

    if len(file_content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CSV file is too large. Maximum allowed size is 5 MB.",
        )

    return build_csv_adapter_preview(
        file_content=file_content,
        source_file_name=file.filename,
    )