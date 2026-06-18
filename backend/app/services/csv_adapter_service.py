from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Any

import pandas as pd
from pydantic import ValidationError

from app.schemas.adapter import (
    AdapterIssue,
    AdapterIssueSeverity,
    AdapterPreviewResponse,
    AdapterPreviewStatus,
    AdapterSummary,
)
from app.schemas.prediction import PredictRequest


RAW_GYS_FORMAT = "gys_lsm_daily_prod_report"
CANONICAL_FORMAT = "canonical_process_csv_v1"
UNKNOWN_FORMAT = "unknown"


RAW_GYS_COLUMN_MAPPING = {
    "production_date": 0,
    "profile_name": 1,
    "raw_material_ton": 2,
    "production_ton": 3,
    "material_pcs": 6,
    "production_pcs": 7,
    "total_hrs": 8,
    "availables_hrs": 15,
    "setup_time": 17,
    "program_stop_min": 19,
    "stand_change": 23,
    "production_stop_min": 25,
    "mechanic_stop_min": 27,
    "electric_stop_min": 29,
    "roll_shop_stop_min": 31,
    "test_rolling_stop_min": 33,
    "trial_rolling_stop_min": 35,
    "others_stop_min": 37,
    "downtime_total_min": 39,
    "rolling_hot_hrs": 41,
    "idle_hrs": 46,
    "rolling_hrs": 47,
    "gas_total_day_nm3": 48,
    "kv_20": 54,
    "kv_33": 55,
    "electricity_total_kwh": 56,
}

PROFILE_FIELDS = [
    field_name
    for field_name in RAW_GYS_COLUMN_MAPPING
    if field_name not in {"production_date", "profile_name"}
]

INTEGER_FIELDS = {
    "material_pcs",
    "production_pcs",
}

POSITIVE_FIELDS = {
    "raw_material_ton",
    "production_ton",
    "material_pcs",
    "production_pcs",
    "total_hrs",
    "availables_hrs",
}

HARD_REQUIRED_FIELDS = {
    "production_date",
    "profile_name",
    "raw_material_ton",
    "production_ton",
    "material_pcs",
    "production_pcs",
    "total_hrs",
    "availables_hrs",
    "downtime_total_min",
    "gas_total_day_nm3",
    "electricity_total_kwh",
}

CANONICAL_MINIMUM_FIELDS = {
    "production_date",
    "profile_name",
    "raw_material_ton",
    "production_ton",
}

ZERO_LIKE_VALUES = {
    "",
    "-",
    "#DIV/0!",
    "#REF!",
    "N/A",
    "NA",
    "NULL",
    "NONE",
}

SKIPPED_PROFILE_NAMES = {
    "shutdown",
    "total",
}

INVALID_PROFILE_NAMES = {
    "",
    "#ref!",
}

FOOTER_ARTIFACT_VALUES = {
    "",
    "1",
    "total",
    "#ref!",
}

ENERGY_TOTAL_TOLERANCE_RATIO = Decimal("0.10")

MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

CANONICAL_HEADER_ALIASES = {
    "production_date": {
        "date",
        "productiondate",
        "production date",
        "tanggal",
        "tanggalproduksi",
        "tanggal produksi",
    },
    "profile_name": {
        "profile",
        "profilename",
        "profile name",
        "profil",
        "nama profil",
        "nama profile",
    },
    "raw_material_ton": {
        "rawmaterialton",
        "raw material ton",
        "raw_material_ton",
        "rawmaterial",
        "tonrawmaterial",
        "ton raw material",
        "bahanbakuton",
        "bahan baku ton",
        "tonbahanbaku",
        "ton bahan baku",
    },
    "production_ton": {
        "productionton",
        "production ton",
        "production_ton",
        "productiontons",
        "prodton",
        "prod ton",
        "tonproduksi",
        "ton produksi",
        "produksiton",
        "produksi ton",
    },
    "material_pcs": {
        "materialpcs",
        "material pcs",
        "material_pcs",
        "materialpc",
    },
    "production_pcs": {
        "productionpcs",
        "production pcs",
        "production_pcs",
        "productionpc",
        "prodpcs",
        "prod pcs",
        "pcsproduksi",
        "pcs produksi",
        "produksipcs",
        "produksi pcs",
    },
    "total_hrs": {
        "totalhrs",
        "total hrs",
        "totalhours",
        "total hours",
        "totaljam",
        "total jam",
    },
    "availables_hrs": {
        "availableshrs",
        "availablehrs",
        "available hrs",
        "availablehours",
        "available hours",
        "jamtersedia",
        "jam tersedia",
    },
    "setup_time": {"setuptime", "setup time", "setup"},
    "program_stop_min": {"programstopmin", "program stop min", "programstop", "program stop"},
    "stand_change": {"standchange", "stand change"},
    "production_stop_min": {
        "productionstopmin",
        "production stop min",
        "productionstop",
        "production stop",
        "production",
    },
    "mechanic_stop_min": {"mechanicstopmin", "mechanic stop min", "mechanicstop", "mechanic"},
    "electric_stop_min": {"electricstopmin", "electric stop min", "electricstop", "electric"},
    "roll_shop_stop_min": {"rollshopstopmin", "roll shop stop min", "rollshopstop", "rollshop"},
    "test_rolling_stop_min": {"testrollingstopmin", "test rolling stop min", "testrolling"},
    "trial_rolling_stop_min": {"trialrollingstopmin", "trial rolling stop min", "trialrolling"},
    "others_stop_min": {"othersstopmin", "others stop min", "othersstop", "others"},
    "downtime_total_min": {
        "downtimetotalmin",
        "downtime total min",
        "downtimetotal",
        "totalminute",
        "total minute",
        "totalminutes",
        "total minutes",
        "totalmin",
    },
    "rolling_hot_hrs": {"rollinghothrs", "rolling hot hrs", "rollinghothour", "rolling hot hour"},
    "idle_hrs": {"idlehrs", "idle hrs", "idlehour", "idle hour", "idlehmi"},
    "rolling_hrs": {"rollinghrs", "rolling hrs", "rollinghour", "rolling hour", "rollinghmi"},
    "gas_total_day_nm3": {"gastotaldaynm3", "gas total day nm3", "totaldaynm3", "total day nm3"},
    "kv_20": {"kv20", "kv 20", "kv20kwh", "kv 20 kwh"},
    "kv_33": {"kv33", "kv 33", "kv33kwh", "kv 33 kwh"},
    "electricity_total_kwh": {
        "electricitytotalkwh",
        "electricity total kwh",
        "totalkwh",
        "total kwh",
        "totaldaykwh",
        "total day kwh",
    },
}

IGNORED_COLUMNS = [
    "yield",
    "target_yield",
    "mill_available_percent",
    "total_rate_percent",
    "mill_utilization_percent",
    "op_ratio_percent",
    "rolling_rate_hot_hrs",
    "rolling_rate_available_hrs",
    "gas_nm3_per_ton",
    "electricity_kwh_per_ton",
    "finish_good_transfer_to_warehouse_ton",
    "dispatch_columns",
    "stock_columns",
    "raw_material_type_columns",
    "work_in_progress",
    "wip_ton",
    "class_b_ton",
    "reject_ton",
    "miss_roll_ton",
]


@dataclass(frozen=True)
class AdapterFormat:
    detected_format: str
    column_mapping: dict[str, int]
    data_start_index: int | None
    required_columns_missing: list[str]
    default_zero_fields: set[str]


def build_csv_adapter_preview(
    file_content: bytes,
    source_file_name: str,
) -> AdapterPreviewResponse:
    issues: list[AdapterIssue] = []

    try:
        raw_df = _read_csv(file_content)
    except Exception as exc:
        issues.append(
            _build_issue(
                severity=AdapterIssueSeverity.ERROR,
                code="CSV_READ_FAILED",
                message=f"CSV tidak bisa dibaca: {exc}",
                action="Pastikan file berbentuk CSV dan tidak sedang rusak.",
            )
        )

        return _build_response(
            source_file_name=source_file_name,
            detected_format=UNKNOWN_FORMAT,
            raw_rows=0,
            candidate_rows=0,
            normalized_payloads=[],
            issues=issues,
            required_columns_missing=[],
        )

    raw_rows = len(raw_df)
    adapter_format = _detect_adapter_format(raw_df)

    if adapter_format.detected_format == UNKNOWN_FORMAT:
        issues.append(
            _build_issue(
                severity=AdapterIssueSeverity.ERROR,
                code="UNSUPPORTED_FORMAT",
                message="Format CSV belum dikenali sebagai laporan produksi.",
                action=(
                    "Pastikan CSV memiliki kolom proses utama seperti date, profile, "
                    "raw_material_ton, production_ton, total_hours, total_kwh, "
                    "atau gunakan export laporan GYS LSM."
                ),
            )
        )

        return _build_response(
            source_file_name=source_file_name,
            detected_format=UNKNOWN_FORMAT,
            raw_rows=raw_rows,
            candidate_rows=0,
            normalized_payloads=[],
            issues=issues,
            required_columns_missing=[],
        )

    if adapter_format.required_columns_missing:
        issues.append(
            _build_issue(
                severity=AdapterIssueSeverity.ERROR,
                code="MISSING_REQUIRED_COLUMNS",
                message="Ada kolom wajib yang tidak ditemukan dalam CSV.",
                action="Lengkapi kolom wajib sebelum file dipakai untuk prediksi.",
            )
        )

        return _build_response(
            source_file_name=source_file_name,
            detected_format=adapter_format.detected_format,
            raw_rows=raw_rows,
            candidate_rows=0,
            normalized_payloads=[],
            issues=issues,
            required_columns_missing=adapter_format.required_columns_missing,
        )

    data_start_index = adapter_format.data_start_index

    if data_start_index is None:
        data_start_index = _find_data_start_index(
            raw_df=raw_df,
            column_mapping=adapter_format.column_mapping,
        )

    if data_start_index is None:
        issues.append(
            _build_issue(
                severity=AdapterIssueSeverity.ERROR,
                code="DATA_ROWS_NOT_FOUND",
                message="Tidak ditemukan baris data produksi dalam CSV.",
                action="Pastikan CSV berisi baris tanggal produksi.",
            )
        )

        return _build_response(
            source_file_name=source_file_name,
            detected_format=adapter_format.detected_format,
            raw_rows=raw_rows,
            candidate_rows=0,
            normalized_payloads=[],
            issues=issues,
            required_columns_missing=[],
        )

    for field_name in sorted(adapter_format.default_zero_fields):
        issues.append(
            _build_issue(
                severity=AdapterIssueSeverity.WARNING,
                code="MISSING_OPTIONAL_FEATURE_DEFAULTED",
                message=(
                    f"Feature '{field_name}' tidak ditemukan dan diisi 0 "
                    "agar payload tetap kompatibel dengan model."
                ),
                column_name=field_name,
                raw_value=None,
                action="Default value 0 applied.",
            )
        )

    profiles_by_date: dict[date, list[dict[str, Any]]] = defaultdict(list)
    candidate_rows = 0

    for row_index in range(data_start_index, len(raw_df)):
        row = raw_df.iloc[row_index]

        if _is_empty_data_candidate(row, adapter_format.column_mapping):
            continue

        candidate_rows += 1
        row_number = row_index + 1

        production_date = _parse_date(
            _get_cell(row, adapter_format.column_mapping["production_date"])
        )

        if production_date is None:
            raw_date_value = _get_cell(row, adapter_format.column_mapping["production_date"])
            normalized_raw_date = _normalize_text(raw_date_value).lower()

            is_footer_artifact = normalized_raw_date in FOOTER_ARTIFACT_VALUES

            issues.append(
                _build_issue(
                    severity=(
                       AdapterIssueSeverity.INFO
                       if is_footer_artifact
                       else AdapterIssueSeverity.WARNING
                    ),
                    code=(
                        "FOOTER_ARTIFACT_ROW_SKIPPED"
                        if is_footer_artifact
                        else "INVALID_DATE_ROW_SKIPPED"
                    ),
                    message=(
                        "Baris footer/artefak spreadsheet dilewati."
                        if is_footer_artifact
                        else "Baris dilewati karena tanggal tidak valid."
                    ),
                    row_number=row_number,
                    column_name="production_date",
                    raw_value=raw_date_value,
                    action="Row ignored.",
                )
            )
            continue    

        profile_name = _normalize_text(
            _get_cell(row, adapter_format.column_mapping["profile_name"])
        )
        profile_key = profile_name.lower()

        if profile_key in SKIPPED_PROFILE_NAMES:
            issues.append(
                _build_issue(
                    severity=AdapterIssueSeverity.INFO,
                    code="NON_PRODUCTION_ROW_SKIPPED",
                    message=f"Baris '{profile_name}' tidak dipakai untuk prediksi.",
                    row_number=row_number,
                    column_name="profile_name",
                    raw_value=profile_name,
                    action="Row ignored.",
                )
            )
            continue

        if profile_key in INVALID_PROFILE_NAMES:
            issues.append(
                _build_issue(
                    severity=AdapterIssueSeverity.WARNING,
                    code="INVALID_PROFILE_ROW_SKIPPED",
                    message="Baris dilewati karena profile tidak valid.",
                    row_number=row_number,
                    column_name="profile_name",
                    raw_value=profile_name,
                    action="Row ignored.",
                )
            )
            continue

        profile_payload = _build_profile_payload(
            row=row,
            row_number=row_number,
            column_mapping=adapter_format.column_mapping,
            default_zero_fields=adapter_format.default_zero_fields,
            issues=issues,
        )

        if profile_payload is None:
            continue

        profiles_by_date[production_date].append(profile_payload)

    normalized_payloads = _build_prediction_payloads(
        profiles_by_date=profiles_by_date,
        issues=issues,
    )

    if not normalized_payloads:
        issues.append(
            _build_issue(
                severity=AdapterIssueSeverity.ERROR,
                code="NO_ACCEPTED_ROWS",
                message="Tidak ada baris produksi yang valid untuk diprediksi.",
                action="Periksa apakah file hanya berisi Shutdown, Total, atau data invalid.",
            )
        )

    return _build_response(
        source_file_name=source_file_name,
        detected_format=adapter_format.detected_format,
        raw_rows=raw_rows,
        candidate_rows=candidate_rows,
        normalized_payloads=normalized_payloads,
        issues=issues,
        required_columns_missing=[],
    )


def _read_csv(file_content: bytes) -> pd.DataFrame:
    last_error: Exception | None = None

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            text = file_content.decode(encoding)
            delimiter = _detect_delimiter(text)
            rows = list(csv.reader(StringIO(text), delimiter=delimiter))

            if not rows:
                return pd.DataFrame()

            max_columns = max(len(row) for row in rows)
            normalized_rows = [
                row + [""] * (max_columns - len(row))
                for row in rows
            ]

            return pd.DataFrame(normalized_rows).fillna("")
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error

    raise ValueError("CSV reader failed without a specific error.")


def _detect_delimiter(text: str) -> str:
    sample = text[:4096]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        return dialect.delimiter
    except csv.Error:
        pass

    non_empty_lines = [
        line
        for line in text.splitlines()[:20]
        if line.strip()
    ]

    if not non_empty_lines:
        return ","

    delimiter_scores = {
        delimiter: sum(line.count(delimiter) for line in non_empty_lines)
        for delimiter in [",", ";", "\t"]
    }

    return max(delimiter_scores, key=delimiter_scores.get)

def _detect_adapter_format(raw_df: pd.DataFrame) -> AdapterFormat:
    if _looks_like_raw_gys_format(raw_df):
        required_columns_missing = _get_missing_required_columns(
            raw_df=raw_df,
            column_mapping=RAW_GYS_COLUMN_MAPPING,
            required_fields=HARD_REQUIRED_FIELDS,
        )

        return AdapterFormat(
            detected_format=RAW_GYS_FORMAT,
            column_mapping=RAW_GYS_COLUMN_MAPPING,
            data_start_index=None,
            required_columns_missing=required_columns_missing,
            default_zero_fields=set(),
        )

    canonical_format = _detect_canonical_format(raw_df)

    if canonical_format.detected_format != UNKNOWN_FORMAT:
        return canonical_format

    return AdapterFormat(
        detected_format=UNKNOWN_FORMAT,
        column_mapping={},
        data_start_index=None,
        required_columns_missing=[],
        default_zero_fields=set(),
    )


def _detect_canonical_format(raw_df: pd.DataFrame) -> AdapterFormat:
    max_header_scan_rows = min(10, len(raw_df))

    best_mapping: dict[str, int] = {}
    best_data_start_index: int | None = None
    best_missing_required_fields: list[str] = []
    best_default_zero_fields: set[str] = set()
    best_score = 0

    for row_index in range(max_header_scan_rows):
        column_mapping = _build_canonical_column_mapping(raw_df.iloc[row_index])

        if not CANONICAL_MINIMUM_FIELDS.issubset(column_mapping):
            continue

        mapped_fields = set(column_mapping)
        missing_required_fields = sorted(HARD_REQUIRED_FIELDS - mapped_fields)
        default_zero_fields = {
            field_name
            for field_name in PROFILE_FIELDS
            if field_name not in mapped_fields and field_name not in HARD_REQUIRED_FIELDS
        }

        score = len(mapped_fields)

        if not missing_required_fields:
            return AdapterFormat(
                detected_format=CANONICAL_FORMAT,
                column_mapping=column_mapping,
                data_start_index=row_index + 1,
                required_columns_missing=[],
                default_zero_fields=default_zero_fields,
            )

        if score > best_score:
            best_mapping = column_mapping
            best_data_start_index = row_index + 1
            best_missing_required_fields = missing_required_fields
            best_default_zero_fields = default_zero_fields
            best_score = score

    if best_mapping:
        return AdapterFormat(
            detected_format=CANONICAL_FORMAT,
            column_mapping=best_mapping,
            data_start_index=best_data_start_index,
            required_columns_missing=best_missing_required_fields,
            default_zero_fields=best_default_zero_fields,
        )

    return AdapterFormat(
        detected_format=UNKNOWN_FORMAT,
        column_mapping={},
        data_start_index=None,
        required_columns_missing=[],
        default_zero_fields=set(),
    )


def _build_canonical_column_mapping(header_row: pd.Series) -> dict[str, int]:
    normalized_aliases: dict[str, str] = {}

    for field_name, aliases in CANONICAL_HEADER_ALIASES.items():
        for alias in aliases:
            normalized_aliases[_normalize_header(alias)] = field_name

    column_mapping: dict[str, int] = {}

    for column_index, raw_header in enumerate(header_row.tolist()):
        normalized_header = _normalize_header(str(raw_header))

        if not normalized_header:
            continue

        field_name = normalized_aliases.get(normalized_header)

        if field_name is None:
            continue

        if field_name not in column_mapping:
            column_mapping[field_name] = column_index

    return column_mapping


def _looks_like_raw_gys_format(raw_df: pd.DataFrame) -> bool:
    preview_text = " ".join(
        str(value).lower()
        for value in raw_df.head(10).to_numpy().flatten().tolist()
        if str(value).strip()
    )

    required_anchors = [
        "date",
        "profile",
        "raw material",
        "production",
        "downtime",
    ]

    return all(anchor in preview_text for anchor in required_anchors)


def _get_missing_required_columns(
    raw_df: pd.DataFrame,
    column_mapping: dict[str, int],
    required_fields: set[str],
) -> list[str]:
    column_count = raw_df.shape[1]
    missing_columns: list[str] = []

    for field_name in sorted(required_fields):
        column_index = column_mapping.get(field_name)

        if column_index is None or column_index >= column_count:
            missing_columns.append(field_name)

    return missing_columns


def _find_data_start_index(
    raw_df: pd.DataFrame,
    column_mapping: dict[str, int],
) -> int | None:
    date_column_index = column_mapping["production_date"]

    for row_index in range(len(raw_df)):
        raw_date = _get_cell(raw_df.iloc[row_index], date_column_index)

        if _parse_date(raw_date) is not None:
            return row_index

    return None


def _is_empty_data_candidate(
    row: pd.Series,
    column_mapping: dict[str, int],
) -> bool:
    raw_date = _get_cell(row, column_mapping["production_date"])
    raw_profile = _get_cell(row, column_mapping["profile_name"])

    return not raw_date.strip() and not raw_profile.strip()

def _append_energy_consistency_issue(
    payload: dict[str, Any],
    row_number: int,
    issues: list[AdapterIssue],
) -> None:
    kv_20 = _to_decimal(payload.get("kv_20"))
    kv_33 = _to_decimal(payload.get("kv_33"))
    electricity_total_kwh = _to_decimal(payload.get("electricity_total_kwh"))

    if electricity_total_kwh <= 0:
        return

    component_total = kv_20 + kv_33

    if component_total <= 0:
        return

    same_unit_difference = abs(component_total - electricity_total_kwh)
    scaled_difference = abs((component_total * Decimal("1000")) - electricity_total_kwh)

    tolerance = electricity_total_kwh * ENERGY_TOTAL_TOLERANCE_RATIO

    if same_unit_difference <= tolerance or scaled_difference <= tolerance:
        return

    issues.append(
        _build_issue(
            severity=AdapterIssueSeverity.WARNING,
            code="ENERGY_TOTAL_MISMATCH",
            message=(
                "Nilai kv_20 + kv_33 tidak konsisten dengan electricity_total_kwh."
            ),
            row_number=row_number,
            column_name="electricity_total_kwh",
            raw_value=(
                f"kv_20={kv_20}, kv_33={kv_33}, "
                f"electricity_total_kwh={electricity_total_kwh}"
            ),
            action=(
                "Periksa apakah kolom energi memakai satuan atau posisi yang benar."
            ),
        )
    )

def _build_profile_payload(
    row: pd.Series,
    row_number: int,
    column_mapping: dict[str, int],
    default_zero_fields: set[str],
    issues: list[AdapterIssue],
) -> dict[str, Any] | None:
    payload: dict[str, Any] = {
        "profile_name": _normalize_text(_get_cell(row, column_mapping["profile_name"])),
    }

    for field_name in PROFILE_FIELDS:
        if field_name in default_zero_fields:
            payload[field_name] = 0 if field_name in INTEGER_FIELDS else Decimal("0")
            continue

        column_index = column_mapping.get(field_name)

        if column_index is None:
            issues.append(
                _build_issue(
                    severity=AdapterIssueSeverity.ERROR,
                    code="MISSING_MODEL_FEATURE",
                    message=f"Feature '{field_name}' tidak ditemukan dalam mapping adapter.",
                    row_number=row_number,
                    column_name=field_name,
                    action="Row ignored.",
                )
            )
            return None

        raw_value = _get_cell(row, column_index)
        decimal_value = _parse_decimal(raw_value)

        if decimal_value is None:
            issues.append(
                _build_issue(
                    severity=AdapterIssueSeverity.WARNING,
                    code="INVALID_NUMERIC_VALUE_ROW_SKIPPED",
                    message=f"Baris dilewati karena nilai '{field_name}' tidak valid.",
                    row_number=row_number,
                    column_name=field_name,
                    raw_value=raw_value,
                    action="Row ignored.",
                )
            )
            return None

        if field_name in POSITIVE_FIELDS and decimal_value <= 0:
            issues.append(
                _build_issue(
                    severity=AdapterIssueSeverity.WARNING,
                    code="NON_POSITIVE_REQUIRED_VALUE_ROW_SKIPPED",
                    message=f"Baris dilewati karena '{field_name}' harus lebih dari 0.",
                    row_number=row_number,
                    column_name=field_name,
                    raw_value=raw_value,
                    action="Row ignored.",
                )
            )
            return None

        if decimal_value < 0:
            issues.append(
                _build_issue(
                    severity=AdapterIssueSeverity.WARNING,
                    code="NEGATIVE_VALUE_ROW_SKIPPED",
                    message=f"Baris dilewati karena '{field_name}' bernilai negatif.",
                    row_number=row_number,
                    column_name=field_name,
                    raw_value=raw_value,
                    action="Row ignored.",
                )
            )
            return None

        if field_name in INTEGER_FIELDS:
            if decimal_value != decimal_value.to_integral_value():
                issues.append(
                    _build_issue(
                        severity=AdapterIssueSeverity.WARNING,
                        code="INVALID_INTEGER_VALUE_ROW_SKIPPED",
                        message=f"Baris dilewati karena '{field_name}' harus bilangan bulat.",
                        row_number=row_number,
                        column_name=field_name,
                        raw_value=raw_value,
                        action="Row ignored.",
                    )
                )
                return None

            payload[field_name] = int(decimal_value)
        else:
            payload[field_name] = decimal_value

    _append_energy_consistency_issue(
        payload=payload,
        row_number=row_number,
        issues=issues,
    )

    return payload


def _build_prediction_payloads(
    profiles_by_date: dict[date, list[dict[str, Any]]],
    issues: list[AdapterIssue],
) -> list[PredictRequest]:
    normalized_payloads: list[PredictRequest] = []

    for production_date in sorted(profiles_by_date):
        profiles = profiles_by_date[production_date]

        try:
            payload = PredictRequest(
                production_date=production_date,
                profiles=profiles,
                estimasi_manual_class_b=Decimal("0"),
                estimasi_manual_reject=Decimal("0"),
            )
        except ValidationError as exc:
            issues.append(
                _build_issue(
                    severity=AdapterIssueSeverity.ERROR,
                    code="PREDICT_PAYLOAD_VALIDATION_FAILED",
                    message=(
                        "Payload hasil adapter gagal melewati validasi PredictRequest "
                        f"untuk tanggal {production_date}: {exc}"
                    ),
                    action="Periksa duplicate profile atau nilai yang tidak sesuai kontrak.",
                )
            )
            continue

        normalized_payloads.append(payload)

    return normalized_payloads


def _parse_decimal(raw_value: str) -> Decimal | None:
    value = _normalize_text(raw_value)

    if _is_zero_like(value):
        return Decimal("0")

    value = value.replace(" ", "")
    value = value.replace("%", "")
    value = value.strip()

    is_negative_parentheses = value.startswith("(") and value.endswith(")")

    if is_negative_parentheses:
        value = value[1:-1]

    value = _normalize_number_separators(value)

    if is_negative_parentheses:
        value = f"-{value}"

    try:
        return Decimal(value)
    except InvalidOperation:
        return None

def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value

    if isinstance(value, int):
        return Decimal(value)

    if isinstance(value, float):
        return Decimal(str(value))

    parsed_value = _parse_decimal(str(value))

    if parsed_value is None:
        return Decimal("0")

    return parsed_value

def _normalize_number_separators(value: str) -> str:
    has_comma = "," in value
    has_dot = "." in value

    if has_comma and has_dot:
        last_comma = value.rfind(",")
        last_dot = value.rfind(".")

        if last_comma > last_dot:
            return value.replace(".", "").replace(",", ".")

        return value.replace(",", "")

    if has_comma:
        parts = value.split(",")

        if _looks_like_thousands_groups(parts):
            return "".join(parts)

        return value.replace(",", ".")

    if has_dot:
        parts = value.split(".")

        if len(parts) > 2 and _looks_like_thousands_groups(parts):
            return "".join(parts)

    return value


def _looks_like_thousands_groups(parts: list[str]) -> bool:
    if len(parts) <= 1:
        return False

    first_part = parts[0]
    remaining_parts = parts[1:]

    if not first_part or len(first_part) > 3:
        return False

    return all(len(part) == 3 and part.isdigit() for part in remaining_parts)


def _parse_date(raw_value: str) -> date | None:
    value = _normalize_text(raw_value)

    if not value:
        return None

    if _is_zero_like(value):
        return None

    iso_parts = value.split("-")

    if len(iso_parts) == 3 and len(iso_parts[0]) == 4:
        try:
            return date(
                year=int(iso_parts[0]),
                month=int(iso_parts[1]),
                day=int(iso_parts[2]),
            )
        except ValueError:
            return None

    normalized = value.replace("/", "-")
    parts = normalized.split("-")

    if len(parts) != 3:
        return None

    day_text, month_text, year_text = parts

    if not day_text.isdigit():
        return None

    day = int(day_text)

    month_key = month_text.strip().lower()
    month = MONTH_MAP.get(month_key)

    if month is None:
        if month_text.isdigit():
            month = int(month_text)
        else:
            return None

    if not year_text.isdigit():
        return None

    year = int(year_text)

    if year < 100:
        year += 2000

    try:
        return date(year=year, month=month, day=day)
    except ValueError:
        return None


def _get_cell(row: pd.Series, column_index: int) -> str:
    if column_index >= len(row):
        return ""

    return str(row.iloc[column_index])


def _normalize_text(value: str) -> str:
    return " ".join(str(value).strip().split())


def _normalize_header(value: str) -> str:
    return "".join(
        character
        for character in str(value).strip().lower()
        if character.isalnum()
    )


def _is_zero_like(value: str) -> bool:
    return _normalize_text(value).upper() in ZERO_LIKE_VALUES


def _build_issue(
    severity: AdapterIssueSeverity,
    code: str,
    message: str,
    row_number: int | None = None,
    column_name: str | None = None,
    raw_value: str | None = None,
    action: str | None = None,
) -> AdapterIssue:
    return AdapterIssue(
        severity=severity,
        code=code,
        message=message,
        row_number=row_number,
        column_name=column_name,
        raw_value=raw_value,
        action=action,
    )


def _build_response(
    source_file_name: str,
    detected_format: str,
    raw_rows: int,
    candidate_rows: int,
    normalized_payloads: list[PredictRequest],
    issues: list[AdapterIssue],
    required_columns_missing: list[str],
) -> AdapterPreviewResponse:
    warning_count = sum(
        1 for issue in issues if issue.severity == AdapterIssueSeverity.WARNING
    )
    error_count = sum(
        1 for issue in issues if issue.severity == AdapterIssueSeverity.ERROR
    )

    accepted_days = len(normalized_payloads)
    accepted_profiles = sum(len(payload.profiles) for payload in normalized_payloads)
    skipped_rows = max(candidate_rows - accepted_profiles, 0)

    if error_count > 0:
        preview_status = AdapterPreviewStatus.INVALID
    elif warning_count > 0:
        preview_status = AdapterPreviewStatus.WARNING
    else:
        preview_status = AdapterPreviewStatus.VALID

    return AdapterPreviewResponse(
        source_file_name=source_file_name,
        detected_format=detected_format,
        preview_status=preview_status,
        is_valid_for_prediction=preview_status != AdapterPreviewStatus.INVALID,
        summary=AdapterSummary(
            raw_rows=raw_rows,
            candidate_rows=candidate_rows,
            accepted_rows=accepted_profiles,
            skipped_rows=skipped_rows,
            accepted_days=accepted_days,
            accepted_profiles=accepted_profiles,
            warning_count=warning_count,
            error_count=error_count,
        ),
        normalized_payloads=normalized_payloads,
        issues=issues,
        required_columns_missing=required_columns_missing,
        ignored_columns=IGNORED_COLUMNS,
    )