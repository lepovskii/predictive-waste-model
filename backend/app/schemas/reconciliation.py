from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.prediction import ProductionLogStatusSchema


NonNegativeDecimal = Annotated[
    Decimal,
    Field(ge=Decimal("0")),
]


class ProfileActualInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    profile_name: str = Field(min_length=1, max_length=120)
    actual_wip_ton: NonNegativeDecimal


class ReconcileItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    production_date: date
    actual_wip_ton: NonNegativeDecimal
    actual_prime_ton: NonNegativeDecimal | None = None

    # Kosong jika laporan hanya menyediakan WIP gabungan harian.
    profiles: list[ProfileActualInput] = Field(
        default_factory=list,
        max_length=20,
    )

    @model_validator(mode="after")
    def validate_profiles(self) -> "ReconcileItemRequest":
        seen_profiles: set[str] = set()

        for profile in self.profiles:
            normalized_name = " ".join(
                profile.profile_name.lower().split()
            )

            if normalized_name in seen_profiles:
                raise ValueError(
                    "Profile duplikat dalam rekonsiliasi: "
                    f"{profile.profile_name}"
                )

            seen_profiles.add(normalized_name)

        if self.profiles:
            profile_total = sum(
                (
                    profile.actual_wip_ton
                    for profile in self.profiles
                ),
                Decimal("0"),
            )

            difference = abs(
                profile_total - self.actual_wip_ton
            )

            if difference > Decimal("0.01"):
                raise ValueError(
                    "Total actual_wip_ton per profile harus sama "
                    "dengan actual_wip_ton harian."
                )

        return self


class ReconcileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ReconcileItemRequest] = Field(
        min_length=1,
        max_length=100,
    )

    @model_validator(mode="after")
    def validate_unique_dates(self) -> "ReconcileRequest":
        seen_dates: set[date] = set()

        for item in self.items:
            if item.production_date in seen_dates:
                raise ValueError(
                    "production_date duplikat dalam request: "
                    f"{item.production_date}"
                )

            seen_dates.add(item.production_date)

        return self


class ReconcileItemResult(str, Enum):
    RECONCILED = "RECONCILED"
    UNCHANGED = "UNCHANGED"
    NOT_FOUND = "NOT_FOUND"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ReconcileItemResponse(BaseModel):
    production_date: date
    result: ReconcileItemResult

    task_id: str | None = None
    status: ProductionLogStatusSchema | None = None

    predicted_wip_ton: Decimal | None = None
    actual_wip_ton: Decimal | None = None
    absolute_error_ton: Decimal | None = None

    needs_retraining: bool = False
    message: str


class ReconcileResponse(BaseModel):
    total_items: int = Field(ge=0)
    reconciled_count: int = Field(ge=0)
    unchanged_count: int = Field(ge=0)
    not_found_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)

    results: list[ReconcileItemResponse]