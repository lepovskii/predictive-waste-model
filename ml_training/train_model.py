from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATE_COL = "production_date"
PROFILE_COL = "profile_name"
TARGET_COL = "wip_ton"

LEAKAGE_COLS = {
    "transfer_to_warehouse_ton",
    "reject_ton",
    "miss_roll_ton",
    "class_b_ton",
    "dispatch_total",
    "stock_total",
    "wip_percentage",
    "reject_percentage",
    "miss_roll_percentage",
    "class_b_percentage",
}


def clean_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .replace(
            {
                "": np.nan,
                "-": np.nan,
                "nan": np.nan,
                "NaN": np.nan,
                "None": np.nan,
                "null": np.nan,
                "NULL": np.nan,
            }
        )
    )

    return pd.to_numeric(cleaned, errors="coerce")


def make_ohe() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_dataset(csv_path: str) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, dict]:
    df = pd.read_csv(csv_path)

    required_cols = {DATE_COL, PROFILE_COL, TARGET_COL}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        raise ValueError(f"Kolom wajib tidak ditemukan: {sorted(missing_cols)}")

    original_rows = len(df)

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], format="%Y-%m-%d", errors="raise")

    df[PROFILE_COL] = (
        df[PROFILE_COL]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    df = df[df[PROFILE_COL].str.lower() != "shutdown"].copy()

    for col in df.columns:
        if col not in {DATE_COL, PROFILE_COL}:
            df[col] = clean_number(df[col])

    if df.duplicated([DATE_COL, PROFILE_COL]).any():
        duplicated_rows = df[df.duplicated([DATE_COL, PROFILE_COL], keep=False)]
        raise ValueError(
            "Ada duplikasi production_date + profile_name:\n"
            f"{duplicated_rows[[DATE_COL, PROFILE_COL]].to_string(index=False)}"
        )

    if df[TARGET_COL].isna().any():
        raise ValueError(f"Target {TARGET_COL} masih memiliki nilai kosong/invalid.")

    if (df[TARGET_COL] < 0).any():
        raise ValueError(f"Target {TARGET_COL} memiliki nilai negatif.")

    if (df[TARGET_COL] == 0).any():
        zero_rows = df[df[TARGET_COL] == 0][[DATE_COL, PROFILE_COL, TARGET_COL]]
        raise ValueError(
            f"Target {TARGET_COL} masih memiliki nilai 0. "
            "Cek apakah ini valid atau anomali:\n"
            f"{zero_rows.to_string(index=False)}"
        )

    df = df.sort_values([DATE_COL, PROFILE_COL]).reset_index(drop=True)

    drop_cols = {
        DATE_COL,
        TARGET_COL,
        *LEAKAGE_COLS,
    }

    feature_cols = [col for col in df.columns if col not in drop_cols]

    X = df[feature_cols].copy()
    y = df[TARGET_COL].copy()
    meta = df[[DATE_COL, PROFILE_COL]].copy()

    report = {
        "csv_path": str(csv_path),
        "original_rows": int(original_rows),
        "rows_used": int(len(df)),
        "date_min": str(df[DATE_COL].min().date()),
        "date_max": str(df[DATE_COL].max().date()),
        "unique_dates": int(df[DATE_COL].nunique()),
        "unique_profiles": int(df[PROFILE_COL].nunique()),
        "dropped_leakage_columns_present": sorted(set(df.columns) & LEAKAGE_COLS),
        "target_summary": {
            "min": float(y.min()),
            "max": float(y.max()),
            "mean": float(y.mean()),
            "median": float(y.median()),
            "std": float(y.std()),
        },
    }

    return X, y, meta, report


def build_pipeline(numeric_cols: list[str], categorical_cols: list[str]) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                numeric_cols,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", make_ohe()),
                    ]
                ),
                categorical_cols,
            ),
        ],
        remainder="drop",
    )

    model = ExtraTreesRegressor(
        n_estimators=300,
        max_depth=4,
        min_samples_leaf=1,
        max_features=0.7,
        bootstrap=True,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )


def save_feature_importance(pipeline: Pipeline, out_dir: Path) -> None:
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    importances = pipeline.named_steps["model"].feature_importances_

    importance_df = (
        pd.DataFrame(
            {
                "feature": feature_names,
                "importance": importances,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    importance_df.to_csv(out_dir / "feature_importance.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--csv",
        required=True,
        help="Path dataset final training Jan-Oct.",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Folder output artefak final model.",
    )

    args = parser.parse_args()

    X, y, meta, data_report = load_dataset(args.csv)

    categorical_cols = [PROFILE_COL]
    numeric_cols = [col for col in X.columns if col not in categorical_cols]

    pipeline = build_pipeline(
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
    )

    pipeline.fit(X, y)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, out_dir / "pipeline.pkl")

    save_feature_importance(pipeline, out_dir)

    metadata = {
        "model_purpose": "Final training model for WIP ton prediction",
        "target": TARGET_COL,
        "algorithm": "ExtraTreesRegressor",
        "model_params": {
            "n_estimators": 300,
            "max_depth": 4,
            "min_samples_leaf": 1,
            "max_features": 0.7,
            "bootstrap": True,
            "random_state": 42,
        },
        "features": {
            "numeric": numeric_cols,
            "categorical": categorical_cols,
            "all_input_columns": list(X.columns),
        },
        "data_report": data_report,
        "postprocess": {
            "clip_negative_prediction_to_zero": True,
            "reason": "WIP ton cannot be negative in production context.",
        },
        "important_note": (
            "This artifact is trained on Jan-Oct data after model selection and tuning. "
            "Do not use this report as final performance evaluation. "
            "Final performance must be measured on untouched Nov-Dec test data."
        ),
    }

    with (out_dir / "model_metadata.json").open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    train_predictions = pipeline.predict(X)
    train_predictions = np.clip(train_predictions, 0, None)

    prediction_df = pd.DataFrame(
        {
            "production_date": meta[DATE_COL].dt.strftime("%Y-%m-%d"),
            "profile_name": meta[PROFILE_COL],
            "actual_wip_ton": y,
            "predicted_wip_ton": train_predictions,
            "absolute_error": np.abs(y.to_numpy() - train_predictions),
        }
    )

    prediction_df.to_csv(out_dir / "train_predictions_diagnostic.csv", index=False)

    print("Final training selesai.")
    print(f"Rows used: {len(y)}")
    print(f"Date range: {data_report['date_min']} sampai {data_report['date_max']}")
    print(f"Output dir: {out_dir}")
    print("Artifact utama: pipeline.pkl")
    print("Catatan: metrics final tetap harus dihitung memakai dataset Nov-Dec.")


if __name__ == "__main__":
    main()