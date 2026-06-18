from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.prediction import PredictRequest


class AdapterPreviewStatus(str, Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"


class AdapterIssueSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AdapterIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: AdapterIssueSeverity
    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1)

    row_number: int | None = Field(default=None, ge=1)
    column_name: str | None = None
    raw_value: str | None = None
    action: str | None = None


class AdapterSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_rows: int = Field(ge=0)
    candidate_rows: int = Field(ge=0)
    accepted_rows: int = Field(ge=0)
    skipped_rows: int = Field(ge=0)

    accepted_days: int = Field(ge=0)
    accepted_profiles: int = Field(ge=0)

    warning_count: int = Field(ge=0)
    error_count: int = Field(ge=0)


class AdapterPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = "adapter-preview-v1"
    source_file_name: str
    detected_format: str

    preview_status: AdapterPreviewStatus
    is_valid_for_prediction: bool

    summary: AdapterSummary

    normalized_payloads: list[PredictRequest] = Field(default_factory=list)

    issues: list[AdapterIssue] = Field(default_factory=list)
    required_columns_missing: list[str] = Field(default_factory=list)
    ignored_columns: list[str] = Field(default_factory=list)