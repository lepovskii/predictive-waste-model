from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from app.core.config import settings
from app.models.waste import DailyProfileDetail


MODEL_FEATURE_COLUMNS = [
    "profile_name",
    "raw_material_ton",
    "production_ton",
    "material_pcs",
    "production_pcs",
    "total_hrs",
    "availables_hrs",
    "setup_time",
    "program_stop_min",
    "stand_change",
    "production_stop_min",
    "mechanic_stop_min",
    "electric_stop_min",
    "roll_shop_stop_min",
    "test_rolling_stop_min",
    "trial_rolling_stop_min",
    "others_stop_min",
    "downtime_total_min",
    "rolling_hot_hrs",
    "idle_hrs",
    "rolling_hrs",
    "gas_total_day_nm3",
    "kv_20",
    "kv_33",
    "electricity_total_kwh",
]


@lru_cache(maxsize=1)
def load_model():
    model_path = Path(settings.MODEL_ARTIFACT_PATH)

    if not model_path.is_absolute():
        model_path = Path(__file__).resolve().parents[3] / model_path

    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact tidak ditemukan: {model_path}")

    return joblib.load(model_path)


def profile_detail_to_dict(detail: DailyProfileDetail) -> dict:
    return {
        "profile_name": detail.profile_name,
        "raw_material_ton": detail.raw_material_ton,
        "production_ton": detail.production_ton,
        "material_pcs": detail.material_pcs,
        "production_pcs": detail.production_pcs,
        "total_hrs": detail.total_hrs,
        "availables_hrs": detail.availables_hrs,
        "setup_time": detail.setup_time,
        "program_stop_min": detail.program_stop_min,
        "stand_change": detail.stand_change,
        "production_stop_min": detail.production_stop_min,
        "mechanic_stop_min": detail.mechanic_stop_min,
        "electric_stop_min": detail.electric_stop_min,
        "roll_shop_stop_min": detail.roll_shop_stop_min,
        "test_rolling_stop_min": detail.test_rolling_stop_min,
        "trial_rolling_stop_min": detail.trial_rolling_stop_min,
        "others_stop_min": detail.others_stop_min,
        "downtime_total_min": detail.downtime_total_min,
        "rolling_hot_hrs": detail.rolling_hot_hrs,
        "idle_hrs": detail.idle_hrs,
        "rolling_hrs": detail.rolling_hrs,
        "gas_total_day_nm3": detail.gas_total_day_nm3,
        "kv_20": detail.kv_20,
        "kv_33": detail.kv_33,
        "electricity_total_kwh": detail.electricity_total_kwh,
    }


def build_prediction_dataframe(
    profile_details: list[DailyProfileDetail],
) -> pd.DataFrame:
    rows = [profile_detail_to_dict(detail) for detail in profile_details]
    df = pd.DataFrame(rows)

    return df[MODEL_FEATURE_COLUMNS].copy()


def predict_profile_wip(
    profile_details: list[DailyProfileDetail],
) -> list[float]:
    model = load_model()
    feature_df = build_prediction_dataframe(profile_details)

    predictions = model.predict(feature_df)
    predictions = [max(float(value), 0.0) for value in predictions]

    return predictions