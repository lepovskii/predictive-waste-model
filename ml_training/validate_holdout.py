from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


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
}


def clean_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .replace({"": np.nan, "-": np.nan, "nan": np.nan, "NaN": np.nan})
    )

    return pd.to_numeric(cleaned, errors="coerce")


def load_dataset(csv_path: str) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    df = pd.read_csv(csv_path)

    required_cols = {DATE_COL, PROFILE_COL, TARGET_COL}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        raise ValueError(f"Kolom wajib tidak ditemukan: {sorted(missing_cols)}")

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
        raise ValueError("Ada duplikasi production_date + profile_name.")

    if df[TARGET_COL].isna().any():
        raise ValueError(f"Target {TARGET_COL} masih memiliki nilai kosong/invalid.")

    if (df[TARGET_COL] < 0).any():
        raise ValueError(f"Target {TARGET_COL} memiliki nilai negatif.")

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

    return X, y, meta


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_pred = np.clip(y_pred, 0, None)

    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--model", required=True, help="Path best_pipeline.pkl hasil training.")
    parser.add_argument("--csv", required=True, help="Path CSV holdout/validation.")
    parser.add_argument("--train-csv", required=True, help="Path CSV training untuk menghitung baseline.")
    parser.add_argument("--out-dir", required=True, help="Folder output hasil validasi.")

    args = parser.parse_args()

    model = joblib.load(args.model)

    X_holdout, y_holdout, meta_holdout = load_dataset(args.csv)
    _, y_train, meta_train = load_dataset(args.train_csv)

    expected_features = list(model.named_steps["preprocess"].feature_names_in_)

    missing_features = [col for col in expected_features if col not in X_holdout.columns]
    extra_features = [col for col in X_holdout.columns if col not in expected_features]

    if missing_features:
        raise ValueError(f"Fitur yang dibutuhkan model tidak ada di CSV holdout: {missing_features}")

    if extra_features:
        print(f"Info: fitur ekstra di CSV holdout akan diabaikan: {extra_features}")

    X_holdout = X_holdout[expected_features]

    y_pred = model.predict(X_holdout)
    y_pred = np.clip(y_pred, 0, None)

    train_mean_value = float(y_train.mean())
    train_median_value = float(y_train.median())

    baseline_mean_pred = np.full(len(y_holdout), train_mean_value)
    baseline_median_pred = np.full(len(y_holdout), train_median_value)

    model_metrics = calculate_metrics(y_holdout.to_numpy(), y_pred)
    baseline_mean_metrics = calculate_metrics(y_holdout.to_numpy(), baseline_mean_pred)
    baseline_median_metrics = calculate_metrics(y_holdout.to_numpy(), baseline_median_pred)

    predictions = pd.DataFrame(
        {
            "production_date": meta_holdout[DATE_COL].dt.strftime("%Y-%m-%d"),
            "profile_name": meta_holdout[PROFILE_COL],
            "actual_wip_ton": y_holdout,
            "predicted_wip_ton": y_pred,
            "baseline_mean_prediction": baseline_mean_pred,
            "baseline_median_prediction": baseline_median_pred,
            "absolute_error": np.abs(y_holdout.to_numpy() - y_pred),
            "baseline_mean_absolute_error": np.abs(y_holdout.to_numpy() - baseline_mean_pred),
            "baseline_median_absolute_error": np.abs(y_holdout.to_numpy() - baseline_median_pred),
        }
    )

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    predictions.to_csv(output_dir / "holdout_predictions.csv", index=False)

    report = {
        "model_path": args.model,
        "holdout_csv_path": args.csv,
        "train_csv_path": args.train_csv,
        "rows_train": int(len(y_train)),
        "rows_holdout": int(len(y_holdout)),
        "train_date_min": str(meta_train[DATE_COL].min().date()),
        "train_date_max": str(meta_train[DATE_COL].max().date()),
        "holdout_date_min": str(meta_holdout[DATE_COL].min().date()),
        "holdout_date_max": str(meta_holdout[DATE_COL].max().date()),
        "target": TARGET_COL,
        "train_target_summary": {
            "mean": train_mean_value,
            "median": train_median_value,
            "min": float(y_train.min()),
            "max": float(y_train.max()),
        },
        "holdout_target_summary": {
            "mean": float(y_holdout.mean()),
            "median": float(y_holdout.median()),
            "min": float(y_holdout.min()),
            "max": float(y_holdout.max()),
        },
        "model_metrics": model_metrics,
        "baseline_mean_metrics": baseline_mean_metrics,
        "baseline_median_metrics": baseline_median_metrics,
        "improvement_vs_train_mean_baseline": {
            "rmse": float(baseline_mean_metrics["rmse"] - model_metrics["rmse"]),
            "mae": float(baseline_mean_metrics["mae"] - model_metrics["mae"]),
            "r2": float(model_metrics["r2"] - baseline_mean_metrics["r2"]),
        },
        "improvement_vs_train_median_baseline": {
            "rmse": float(baseline_median_metrics["rmse"] - model_metrics["rmse"]),
            "mae": float(baseline_median_metrics["mae"] - model_metrics["mae"]),
            "r2": float(model_metrics["r2"] - baseline_median_metrics["r2"]),
        },
        "features_used": expected_features,
    }

    with (output_dir / "holdout_metrics.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("Validasi holdout selesai.")
    print(f"Train rows: {len(y_train)}")
    print(f"Holdout rows: {len(y_holdout)}")
    print(f"Holdout date range: {report['holdout_date_min']} to {report['holdout_date_max']}")
    print(f"Output dir: {output_dir}")

    print("\nModel metrics:")
    print(json.dumps(model_metrics, indent=2))

    print("\nBaseline mean metrics:")
    print(json.dumps(baseline_mean_metrics, indent=2))

    print("\nBaseline median metrics:")
    print(json.dumps(baseline_median_metrics, indent=2))

    print("\nImprovement vs train mean baseline:")
    print(json.dumps(report["improvement_vs_train_mean_baseline"], indent=2))

    print("\nImprovement vs train median baseline:")
    print(json.dumps(report["improvement_vs_train_median_baseline"], indent=2))


if __name__ == "__main__":
    main()