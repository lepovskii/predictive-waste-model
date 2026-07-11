from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
import redis

from app.core.config import settings
from app.models.waste import DailyProfileDetail

# Global dynamic cache
_current_artifact_id: str | None = None
_cached_model = None
_cached_metadata: dict | None = None

_redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_active_artifact_id() -> str:
    try:
        artifact_id = _redis_client.get("active_model_artifact_id")
        if artifact_id:
            return artifact_id
    except Exception:
        pass
        
    # Fallback to settings
    active_path = Path(settings.MODEL_ARTIFACT_PATH)
    return active_path.parent.name

def get_model_path(artifact_id: str) -> Path:
    return Path(__file__).resolve().parents[3] / "ml_training" / "artifacts" / artifact_id / "pipeline.pkl"

def _ensure_cache():
    global _current_artifact_id, _cached_model, _cached_metadata
    
    current_id = get_active_artifact_id()
    
    if _current_artifact_id != current_id or _cached_model is None:
        model_path = get_model_path(current_id)
        metadata_path = model_path.parent / "model_metadata.json"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model artifact tidak ditemukan: {model_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Model metadata tidak ditemukan: {metadata_path}")
            
        _cached_model = joblib.load(model_path)
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            _cached_metadata = json.load(f)
            
        _current_artifact_id = current_id

def load_model():
    _ensure_cache()
    return _cached_model

def load_model_metadata() -> dict:
    _ensure_cache()
    return _cached_metadata

def clear_model_cache():
    """Panggil ini saat model aktif diganti agar cache di-reset"""
    global _current_artifact_id, _cached_model, _cached_metadata
    _current_artifact_id = None
    _cached_model = None
    _cached_metadata = None

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
    
    # Ambil daftar kolom yang dibutuhkan secara dinamis dari metadata
    metadata = load_model_metadata()
    feature_columns = metadata["features"]["all_input_columns"]

    return df[feature_columns].copy()

def predict_profile_wip(
    profile_details: list[DailyProfileDetail],
) -> list[float]:
    model = load_model()
    feature_df = build_prediction_dataframe(profile_details)

    predictions = model.predict(feature_df)
    predictions = [max(float(value), 0.0) for value in predictions]

    return predictions
