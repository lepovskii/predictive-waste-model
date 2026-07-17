from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.waste import (
    DailyProductionLog,
    DailyProfileDetail,
    ProductionLogStatus,
)
from app.schemas.reconciliation import (
    ReconcileItemRequest,
    ReconcileItemResponse,
    ReconcileItemResult,
    ReconcileRequest,
    ReconcileResponse,
)


DECIMAL_PLACES = Decimal("0.01")
VALUE_TOLERANCE = Decimal("0.01")

# Berdasarkan MAE final test model, bukan perintah otomatis retraining.
RETRAINING_ERROR_THRESHOLD_TON = Decimal("110.00")


def round_ton(value: Decimal) -> Decimal:
    return value.quantize(
        DECIMAL_PLACES,
        rounding=ROUND_HALF_UP,
    )


def normalize_profile_name(value: str) -> str:
    return " ".join(value.lower().split())


def get_log_by_production_date(
    db: Session,
    production_date,
) -> DailyProductionLog | None:
    return db.scalar(
        select(DailyProductionLog)
        .options(
            selectinload(
                DailyProductionLog.profile_details
            )
        )
        .where(
            DailyProductionLog.production_date
            == production_date
        )
    )


def build_profile_map(
    details: list[DailyProfileDetail],
) -> dict[str, DailyProfileDetail]:
    return {
        normalize_profile_name(detail.profile_name): detail
        for detail in details
    }


def validate_reconciliation(
    log: DailyProductionLog,
    item: ReconcileItemRequest,
) -> str | None:
    if log.status == ProductionLogStatus.PROCESSING:
        return (
            "Prediksi masih diproses dan belum dapat "
            "direkonsiliasi."
        )

    if log.status == ProductionLogStatus.FAILED:
        return (
            "Prediksi berstatus FAILED dan tidak dapat "
            "direkonsiliasi."
        )

    if log.estimasi_wip_total is None:
        return "Nilai estimasi WIP belum tersedia."

    if item.actual_wip_ton > log.total_output_ton:
        return (
            "Aktual WIP tidak boleh melebihi total "
            "produksi."
        )

    if item.actual_prime_ton is not None:
        actual_quality_total = (
            item.actual_wip_ton
            + item.actual_prime_ton
        )

        if (
            actual_quality_total
            > log.total_output_ton + VALUE_TOLERANCE
        ):
            return (
                "Jumlah aktual WIP dan aktual prime "
                "melebihi total produksi."
            )

    if not item.profiles:
        return "DEBUG: item.profiles is empty! You are using the old frontend."
    else:
        return f"DEBUG: item.profiles has {len(item.profiles)} items."

    stored_profiles = build_profile_map(
        log.profile_details
    )

    submitted_profiles = {
        normalize_profile_name(profile.profile_name)
        for profile in item.profiles
    }

    stored_profile_names = set(stored_profiles)

    if submitted_profiles != stored_profile_names:
        missing_profiles = sorted(
            stored_profile_names - submitted_profiles
        )

        unknown_profiles = sorted(
            submitted_profiles - stored_profile_names
        )

        messages: list[str] = []

        if missing_profiles:
            messages.append(
                "profile belum dikirim: "
                + ", ".join(missing_profiles)
            )

        if unknown_profiles:
            messages.append(
                "profile tidak ditemukan: "
                + ", ".join(unknown_profiles)
            )

        return "; ".join(messages)

    for profile in item.profiles:
        detail = stored_profiles[
            normalize_profile_name(
                profile.profile_name
            )
        ]

        if (
            profile.actual_wip_ton
            > detail.production_ton
        ):
            return (
                f"Aktual WIP profile "
                f"'{detail.profile_name}' melebihi "
                "produksi profile tersebut."
            )

    return None


def profile_values_are_unchanged(
    log: DailyProductionLog,
    item: ReconcileItemRequest,
) -> bool:
    if not item.profiles:
        return True

    stored_profiles = build_profile_map(
        log.profile_details
    )

    for profile in item.profiles:
        detail = stored_profiles[
            normalize_profile_name(
                profile.profile_name
            )
        ]

        if (
            detail.actual_wip_ton
            != round_ton(profile.actual_wip_ton)
        ):
            return False

    return True


def reconcile_item(
    db: Session,
    item: ReconcileItemRequest,
) -> ReconcileItemResponse:
    log = get_log_by_production_date(
        db=db,
        production_date=item.production_date,
    )

    if log is None:
        return ReconcileItemResponse(
            production_date=item.production_date,
            result=ReconcileItemResult.NOT_FOUND,
            message=(
                "Data prediksi untuk tanggal tersebut "
                "tidak ditemukan."
            ),
        )

    validation_error = validate_reconciliation(
        log=log,
        item=item,
    )

    if validation_error is not None:
        return ReconcileItemResponse(
            production_date=item.production_date,
            result=ReconcileItemResult.REJECTED,
            task_id=log.task_id,
            status=log.status,
            predicted_wip_ton=log.estimasi_wip_total,
            actual_wip_ton=log.aktual_wip,
            needs_retraining=log.needs_retraining,
            message=validation_error,
        )

    actual_wip = round_ton(item.actual_wip_ton)

    actual_prime = (
        round_ton(item.actual_prime_ton)
        if item.actual_prime_ton is not None
        else log.aktual_prime
    )

    predicted_wip = round_ton(
        log.estimasi_wip_total
    )

    absolute_error = round_ton(
        abs(predicted_wip - actual_wip)
    )

    needs_retraining = (
        absolute_error
        > RETRAINING_ERROR_THRESHOLD_TON
    )

    unchanged = (
        log.status == ProductionLogStatus.RECONCILED
        and log.aktual_wip == actual_wip
        and log.aktual_prime == actual_prime
        and log.needs_retraining == needs_retraining
        and profile_values_are_unchanged(
            log=log,
            item=item,
        )
    )

    if unchanged:
        return ReconcileItemResponse(
            production_date=item.production_date,
            result=ReconcileItemResult.UNCHANGED,
            task_id=log.task_id,
            status=log.status,
            predicted_wip_ton=predicted_wip,
            actual_wip_ton=actual_wip,
            absolute_error_ton=absolute_error,
            needs_retraining=needs_retraining,
            message="Data aktual sudah pernah direkonsiliasi.",
        )

    log.aktual_wip = actual_wip
    log.aktual_prime = actual_prime
    log.needs_retraining = needs_retraining
    log.status = ProductionLogStatus.RECONCILED

    if item.profiles:
        stored_profiles = build_profile_map(
            log.profile_details
        )

        for profile in item.profiles:
            detail = stored_profiles[
                normalize_profile_name(
                    profile.profile_name
                )
            ]

            detail.actual_wip_ton = round_ton(
                profile.actual_wip_ton
            )

    db.commit()

    return ReconcileItemResponse(
        production_date=item.production_date,
        result=ReconcileItemResult.RECONCILED,
        task_id=log.task_id,
        status=log.status,
        predicted_wip_ton=predicted_wip,
        actual_wip_ton=actual_wip,
        absolute_error_ton=absolute_error,
        needs_retraining=needs_retraining,
        message="Data aktual berhasil direkonsiliasi.",
    )


def reconcile_predictions(
    db: Session,
    payload: ReconcileRequest,
) -> ReconcileResponse:
    results: list[ReconcileItemResponse] = []

    for item in payload.items:
        try:
            result = reconcile_item(
                db=db,
                item=item,
            )
        except SQLAlchemyError:
            db.rollback()

            result = ReconcileItemResponse(
                production_date=item.production_date,
                result=ReconcileItemResult.FAILED,
                message=(
                    "Terjadi kesalahan database ketika "
                    "melakukan rekonsiliasi."
                ),
            )

        results.append(result)

    return ReconcileResponse(
        total_items=len(results),
        reconciled_count=sum(
            result.result
            == ReconcileItemResult.RECONCILED
            for result in results
        ),
        unchanged_count=sum(
            result.result
            == ReconcileItemResult.UNCHANGED
            for result in results
        ),
        not_found_count=sum(
            result.result
            == ReconcileItemResult.NOT_FOUND
            for result in results
        ),
        rejected_count=sum(
            result.result
            == ReconcileItemResult.REJECTED
            for result in results
        ),
        failed_count=sum(
            result.result
            == ReconcileItemResult.FAILED
            for result in results
        ),
        results=results,
    )