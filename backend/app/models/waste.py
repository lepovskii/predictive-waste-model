from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductionLogStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    DRAFT = "DRAFT"
    ANOMALY = "ANOMALY"
    FAILED = "FAILED"
    RECONCILED = "RECONCILED"


class DailyProductionLog(Base):
    __tablename__ = "daily_production_logs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    production_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[ProductionLogStatus] = mapped_column(
        Enum(ProductionLogStatus, name="production_log_status"),
        nullable=False,
        server_default=text("'PROCESSING'"),
    )

    task_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    
    model_artifact_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    total_output_ton: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    estimasi_wip_total: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    estimasi_manual_class_b: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        server_default=text("0"),
    )

    estimasi_manual_reject: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        server_default=text("0"),
    )

    estimasi_prime: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    aktual_wip: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    aktual_prime: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    needs_retraining: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    profile_details: Mapped[list["DailyProfileDetail"]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DailyProfileDetail(Base):
    __tablename__ = "daily_profile_details"

    __table_args__ = (
        UniqueConstraint("log_id", "detail_seq", name="uq_daily_profile_log_seq"),
        UniqueConstraint("log_id", "profile_name", name="uq_daily_profile_log_profile"),
        CheckConstraint(
            "lower(profile_name) <> 'shutdown'",
            name="ck_profile_not_shutdown",
        ),
        CheckConstraint(
            "production_ton >= 0",
            name="ck_daily_profile_production_ton_non_negative",
        ),
        CheckConstraint(
            "raw_material_ton >= 0",
            name="ck_daily_profile_raw_material_ton_non_negative",
        ),
        CheckConstraint(
            "predicted_wip_ton IS NULL OR predicted_wip_ton >= 0",
            name="ck_daily_profile_predicted_wip_ton_non_negative",
        ),
        CheckConstraint(
            "actual_wip_ton IS NULL OR actual_wip_ton >= 0",
            name="ck_daily_profile_actual_wip_ton_non_negative",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    log_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("daily_production_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    detail_seq: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    profile_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    raw_material_ton: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    production_ton: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    material_pcs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    production_pcs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_hrs: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    availables_hrs: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    setup_time: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    program_stop_min: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    stand_change: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    production_stop_min: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    mechanic_stop_min: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    electric_stop_min: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    roll_shop_stop_min: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    test_rolling_stop_min: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    trial_rolling_stop_min: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    others_stop_min: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    downtime_total_min: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    rolling_hot_hrs: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    idle_hrs: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    rolling_hrs: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    gas_total_day_nm3: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    kv_20: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    kv_33: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    electricity_total_kwh: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    predicted_wip_ton: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    actual_wip_ton: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    log: Mapped[DailyProductionLog] = relationship(
        back_populates="profile_details",
    )