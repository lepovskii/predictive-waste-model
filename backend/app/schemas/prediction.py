from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


NonNegativeDecimal = Annotated[Decimal, Field(ge=Decimal("0"))]
PositiveDecimal = Annotated[Decimal, Field(gt=Decimal("0"))]
PositiveInt = Annotated[int, Field(gt=0)]


class ProductionLogStatusSchema(str, Enum):
    PROCESSING = "PROCESSING"
    DRAFT = "DRAFT"
    ANOMALY = "ANOMALY"
    FAILED = "FAILED"
    RECONCILED = "RECONCILED"


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    profile_name: str = Field(min_length=1, max_length=120)

    raw_material_ton: PositiveDecimal
    production_ton: PositiveDecimal
    material_pcs: PositiveInt
    production_pcs: PositiveInt

    total_hrs: PositiveDecimal
    availables_hrs: PositiveDecimal

    setup_time: NonNegativeDecimal
    program_stop_min: NonNegativeDecimal
    stand_change: NonNegativeDecimal
    production_stop_min: NonNegativeDecimal
    mechanic_stop_min: NonNegativeDecimal
    electric_stop_min: NonNegativeDecimal
    roll_shop_stop_min: NonNegativeDecimal
    test_rolling_stop_min: NonNegativeDecimal
    trial_rolling_stop_min: NonNegativeDecimal
    others_stop_min: NonNegativeDecimal
    downtime_total_min: NonNegativeDecimal

    rolling_hot_hrs: NonNegativeDecimal
    idle_hrs: NonNegativeDecimal
    rolling_hrs: NonNegativeDecimal

    gas_total_day_nm3: NonNegativeDecimal
    kv_20: NonNegativeDecimal
    kv_33: NonNegativeDecimal
    electricity_total_kwh: NonNegativeDecimal

    @field_validator("profile_name")
    @classmethod
    def normalize_profile_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())

        if not normalized:
            raise ValueError("profile_name tidak boleh kosong.")

        if normalized.lower() == "shutdown":
            raise ValueError("profile_name 'Shutdown' tidak boleh dikirim ke endpoint prediksi.")

        return normalized


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    production_date: date
    profiles: list[ProfileInput] = Field(
        min_length=1,
        max_length=20,
    )

    estimasi_manual_class_b: NonNegativeDecimal = Decimal("0")
    estimasi_manual_reject: NonNegativeDecimal = Decimal("0")

    @model_validator(mode="after")
    def validate_unique_profiles(self) -> "PredictRequest":
        seen: set[str] = set()

        for profile in self.profiles:
            key = profile.profile_name.lower()

            if key in seen:
                raise ValueError(
                    f"profile_name duplikat dalam request: {profile.profile_name}"
                )

            seen.add(key)

        return self

class PredictBatchItemResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    FAILED = "FAILED"


class PredictBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PredictRequest] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_unique_production_dates(self) -> "PredictBatchRequest":
        seen: set[date] = set()

        for item in self.items:
            if item.production_date in seen:
                raise ValueError(
                    f"production_date duplikat dalam batch: {item.production_date}"
                )

            seen.add(item.production_date)

        return self


class PredictBatchItemResponse(BaseModel):
    production_date: date
    result: PredictBatchItemResult

    task_id: str | None = None
    status: ProductionLogStatusSchema | None = None
    profile_count: int | None = None
    total_output_ton: Decimal | None = None

    message: str


class PredictBatchAcceptedResponse(BaseModel):
    total_items: int = Field(ge=0)
    accepted_count: int = Field(ge=0)
    duplicate_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)

    results: list[PredictBatchItemResponse]

class ProfileAcceptedResponse(BaseModel):
    detail_seq: int
    profile_name: str
    production_ton: Decimal


class PredictAcceptedResponse(BaseModel):
    task_id: str
    status: ProductionLogStatusSchema
    production_date: date
    profile_count: int
    total_output_ton: Decimal
    profiles: list[ProfileAcceptedResponse]
    message: str


class ProfileStatusResponse(BaseModel):
    detail_seq: int
    profile_name: str
    production_ton: Decimal
    predicted_wip_ton: Decimal | None = None
    actual_wip_ton: Decimal | None = None


class PredictionStatusResponse(BaseModel):
    task_id: str | None
    status: ProductionLogStatusSchema
    production_date: date

    total_output_ton: Decimal
    estimasi_wip_total: Decimal | None = None
    estimasi_manual_class_b: Decimal
    estimasi_manual_reject: Decimal
    estimasi_prime: Decimal | None = None

    aktual_wip: Decimal | None = None
    aktual_prime: Decimal | None = None
    needs_retraining: bool

    profiles: list[ProfileStatusResponse]

    created_at: datetime
    updated_at: datetime

class PredictionHistoryItemResponse(BaseModel):
    task_id: str | None
    status: ProductionLogStatusSchema
    production_date: date

    profile_count: int = Field(ge=0)
    total_output_ton: Decimal
    estimasi_wip_total: Decimal | None = None
    estimasi_prime: Decimal | None = None

    needs_retraining: bool

    created_at: datetime
    updated_at: datetime


class PredictionHistoryResponse(BaseModel):
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)

    items: list[PredictionHistoryItemResponse]