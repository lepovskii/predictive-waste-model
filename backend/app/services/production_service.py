from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.waste import (
    DailyProductionLog,
    DailyProfileDetail,
    ProductionLogStatus,
)
from app.schemas.prediction import PredictRequest


class DuplicateProductionDateError(Exception):
    def __init__(self, production_date):
        self.production_date = production_date
        super().__init__(f"Production date already exists: {production_date}")


def calculate_total_output_ton(payload: PredictRequest) -> Decimal:
    return sum(
        (profile.production_ton for profile in payload.profiles),
        Decimal("0"),
    )


def build_profile_detail(
    log: DailyProductionLog,
    detail_seq: int,
    profile,
) -> DailyProfileDetail:
    return DailyProfileDetail(
        log=log,
        detail_seq=detail_seq,
        profile_name=profile.profile_name,
        raw_material_ton=profile.raw_material_ton,
        production_ton=profile.production_ton,
        material_pcs=profile.material_pcs,
        production_pcs=profile.production_pcs,
        total_hrs=profile.total_hrs,
        availables_hrs=profile.availables_hrs,
        setup_time=profile.setup_time,
        program_stop_min=profile.program_stop_min,
        stand_change=profile.stand_change,
        production_stop_min=profile.production_stop_min,
        mechanic_stop_min=profile.mechanic_stop_min,
        electric_stop_min=profile.electric_stop_min,
        roll_shop_stop_min=profile.roll_shop_stop_min,
        test_rolling_stop_min=profile.test_rolling_stop_min,
        trial_rolling_stop_min=profile.trial_rolling_stop_min,
        others_stop_min=profile.others_stop_min,
        downtime_total_min=profile.downtime_total_min,
        rolling_hot_hrs=profile.rolling_hot_hrs,
        idle_hrs=profile.idle_hrs,
        rolling_hrs=profile.rolling_hrs,
        gas_total_day_nm3=profile.gas_total_day_nm3,
        kv_20=profile.kv_20,
        kv_33=profile.kv_33,
        electricity_total_kwh=profile.electricity_total_kwh,
    )


def create_prediction_log(
    db: Session,
    payload: PredictRequest,
) -> DailyProductionLog:
    existing_log = db.scalar(
        select(DailyProductionLog).where(
            DailyProductionLog.production_date == payload.production_date
        )
    )

    if existing_log is not None:
        raise DuplicateProductionDateError(payload.production_date)

    task_id = str(uuid4())
    total_output_ton = calculate_total_output_ton(payload)

    log = DailyProductionLog(
        production_date=payload.production_date,
        status=ProductionLogStatus.PROCESSING,
        task_id=task_id,
        total_output_ton=total_output_ton,
        estimasi_manual_class_b=payload.estimasi_manual_class_b,
        estimasi_manual_reject=payload.estimasi_manual_reject,
    )

    db.add(log)

    for detail_seq, profile in enumerate(payload.profiles, start=1):
        db.add(
            build_profile_detail(
                log=log,
                detail_seq=detail_seq,
                profile=profile,
            )
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateProductionDateError(payload.production_date) from exc

    db.refresh(log)

    return get_prediction_log_by_task_id(db, task_id=task_id)

def get_prediction_log_by_task_id(
    db: Session,
    task_id: str,
) -> DailyProductionLog | None:
    return db.scalar(
        select(DailyProductionLog)
        .options(selectinload(DailyProductionLog.profile_details))
        .where(DailyProductionLog.task_id == task_id)
    )

def mark_prediction_log_failed(
    db: Session,
    log: DailyProductionLog,
) -> DailyProductionLog:
    log.status = ProductionLogStatus.FAILED
    db.commit()
    db.refresh(log)

    return log

def list_prediction_logs(
    db: Session,
    limit: int,
    offset: int,
    status_filter: ProductionLogStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[DailyProductionLog], int]:
    list_statement = (
        select(DailyProductionLog)
        .options(
            selectinload(DailyProductionLog.profile_details)
        )
    )

    count_statement = (
        select(func.count())
        .select_from(DailyProductionLog)
    )

    if status_filter is not None:
        status_condition = (
            DailyProductionLog.status == status_filter
        )

        list_statement = list_statement.where(
            status_condition
        )
        count_statement = count_statement.where(
            status_condition
        )

    if date_from is not None:
        date_from_condition = (
            DailyProductionLog.production_date >= date_from
        )

        list_statement = list_statement.where(
            date_from_condition
        )
        count_statement = count_statement.where(
            date_from_condition
        )

    if date_to is not None:
        date_to_condition = (
            DailyProductionLog.production_date <= date_to
        )

        list_statement = list_statement.where(
            date_to_condition
        )
        count_statement = count_statement.where(
            date_to_condition
        )

    list_statement = (
        list_statement
        .order_by(
            DailyProductionLog.production_date.desc(),
            DailyProductionLog.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    logs = list(
        db.scalars(list_statement).all()
    )

    total = int(
        db.scalar(count_statement) or 0
    )

    return logs, total