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


def load_dataset(csv_path: str) -> pd.DataFrame:
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

    if df.isna().sum().sum() > 0:
        missing = df.isna().sum()
        missing = missing[missing > 0].sort_values(ascending=False)
        raise ValueError(f"Dataset masih memiliki missing value:\n{missing.to_string()}")

    shutdown_rows = df[df[PROFILE_COL].str.lower() == "shutdown"]
    if len(shutdown_rows) > 0:
        raise ValueError(
            "Dataset test masih memiliki row Shutdown. "
            "Exclude row Shutdown sebelum final testing."
        )

    df = df.sort_values([DATE_COL, PROFILE_COL]).reset_index(drop=True)

    return df


def get_expected_features(model, model_path: Path) -> list[str]:
    metadata_path = model_path.parent / "model_metadata.json"

    if metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as file:
            metadata = json.load(file)

        expected = metadata.get("features", {}).get("all_input_columns")
        if expected:
            return expected

    preprocessor = model.named_steps["preprocess"]
    expected = []

    for _, _, cols in preprocessor.transformers_:
        if isinstance(cols, list):
            expected.extend(cols)

    return expected


def build_features(df: pd.DataFrame, expected_features: list[str]) -> pd.DataFrame:
    drop_cols = {
        DATE_COL,
        TARGET_COL,
        *LEAKAGE_COLS,
    }

    feature_df = df[[col for col in df.columns if col not in drop_cols]].copy()

    missing_features = [col for col in expected_features if col not in feature_df.columns]
    extra_features = [col for col in feature_df.columns if col not in expected_features]

    if missing_features:
        raise ValueError(f"Fitur test tidak lengkap. Missing: {missing_features}")

    if extra_features:
        print(f"Info: fitur ekstra diabaikan: {extra_features}")

    return feature_df[expected_features].copy()


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def summarize_target(series: pd.Series) -> dict[str, float]:
    return {
        "count": int(series.count()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std()),
        "min": float(series.min()),
        "max": float(series.max()),
    }


def make_month_metrics(prediction_df: pd.DataFrame) -> list[dict]:
    rows = []

    for month, group in prediction_df.groupby("month"):
        y_true = group["actual_wip_ton"].to_numpy()
        y_pred = group["predicted_wip_ton"].to_numpy()

        metrics = calculate_metrics(y_true, y_pred)

        rows.append(
            {
                "month": month,
                "rows": int(len(group)),
                "actual_mean": float(group["actual_wip_ton"].mean()),
                "predicted_mean": float(group["predicted_wip_ton"].mean()),
                "rmse": metrics["rmse"],
                "mae": metrics["mae"],
                "r2": metrics["r2"],
            }
        )

    return rows


def write_summary_md(report: dict, out_path: Path) -> None:
    best_vs_mean = "mengungguli" if report["comparison"]["model_beats_baseline_mean_by_mae"] else "belum mengungguli"
    best_vs_median = "mengungguli" if report["comparison"]["model_beats_baseline_median_by_mae"] else "belum mengungguli"

    lines = [
        "# Final Test Summary",
        "",
        "## Dataset",
        "",
        f"- Train period: {report['train_period']['date_min']} sampai {report['train_period']['date_max']}",
        f"- Test period: {report['test_period']['date_min']} sampai {report['test_period']['date_max']}",
        f"- Test rows: {report['rows_test']}",
        "",
        "## Final Test Metrics",
        "",
        "| Metric | Model | Baseline Mean | Baseline Median |",
        "|---|---:|---:|---:|",
        (
            f"| RMSE | {report['model_metrics']['rmse']:.4f} | "
            f"{report['baseline_mean_metrics']['rmse']:.4f} | "
            f"{report['baseline_median_metrics']['rmse']:.4f} |"
        ),
        (
            f"| MAE | {report['model_metrics']['mae']:.4f} | "
            f"{report['baseline_mean_metrics']['mae']:.4f} | "
            f"{report['baseline_median_metrics']['mae']:.4f} |"
        ),
        (
            f"| R2 | {report['model_metrics']['r2']:.4f} | "
            f"{report['baseline_mean_metrics']['r2']:.4f} | "
            f"{report['baseline_median_metrics']['r2']:.4f} |"
        ),
        "",
        "## Interpretation",
        "",
        f"- Berdasarkan MAE, model {best_vs_mean} baseline mean Jan-Oct.",
        f"- Berdasarkan MAE, model {best_vs_median} baseline median Jan-Oct.",
        "- Hasil ini merupakan final test pada data Nov-Dec yang tidak digunakan saat training/tuning.",
        "- Setelah hasil ini keluar, jangan tuning ulang menggunakan Nov-Dec agar evaluasi tetap jujur.",
        "",
        "## Largest Errors",
        "",
        "| Date | Profile | Actual WIP | Predicted WIP | Absolute Error |",
        "|---|---|---:|---:|---:|",
    ]

    for row in report["top_errors"]:
        lines.append(
            f"| {row['production_date']} | {row['profile_name']} | "
            f"{row['actual_wip_ton']:.4f} | {row['predicted_wip_ton']:.4f} | "
            f"{row['absolute_error']:.4f} |"
        )

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        required=True,
        help="Path pipeline.pkl final model.",
    )
    parser.add_argument(
        "--train-csv",
        required=True,
        help="Path dataset final train Jan-Oct untuk baseline.",
    )
    parser.add_argument(
        "--test-csv",
        required=True,
        help="Path dataset final test Nov-Dec.",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Folder output hasil final test.",
    )

    args = parser.parse_args()

    model_path = Path(args.model)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model = joblib.load(model_path)

    train_df = load_dataset(args.train_csv)
    test_df = load_dataset(args.test_csv)

    expected_features = get_expected_features(model, model_path)
    X_test = build_features(test_df, expected_features)

    y_train = train_df[TARGET_COL]
    y_test = test_df[TARGET_COL].to_numpy()

    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0, None)

    train_mean = float(y_train.mean())
    train_median = float(y_train.median())

    baseline_mean_pred = np.full(len(y_test), train_mean)
    baseline_median_pred = np.full(len(y_test), train_median)

    model_metrics = calculate_metrics(y_test, y_pred)
    baseline_mean_metrics = calculate_metrics(y_test, baseline_mean_pred)
    baseline_median_metrics = calculate_metrics(y_test, baseline_median_pred)

    prediction_df = pd.DataFrame(
        {
            "production_date": test_df[DATE_COL].dt.strftime("%Y-%m-%d"),
            "profile_name": test_df[PROFILE_COL],
            "actual_wip_ton": y_test,
            "predicted_wip_ton": y_pred,
            "absolute_error": np.abs(y_test - y_pred),
            "squared_error": np.square(y_test - y_pred),
            "baseline_mean_prediction": baseline_mean_pred,
            "baseline_mean_absolute_error": np.abs(y_test - baseline_mean_pred),
            "baseline_median_prediction": baseline_median_pred,
            "baseline_median_absolute_error": np.abs(y_test - baseline_median_pred),
        }
    )

    prediction_df["month"] = pd.to_datetime(prediction_df["production_date"]).dt.to_period("M").astype(str)

    prediction_df.to_csv(out_dir / "final_test_predictions.csv", index=False)

    top_errors_df = (
        prediction_df
        .sort_values("absolute_error", ascending=False)
        .head(10)
        .copy()
    )

    top_errors = []
    for row in top_errors_df.to_dict(orient="records"):
        top_errors.append(
            {
                "production_date": row["production_date"],
                "profile_name": row["profile_name"],
                "actual_wip_ton": float(row["actual_wip_ton"]),
                "predicted_wip_ton": float(row["predicted_wip_ton"]),
                "absolute_error": float(row["absolute_error"]),
            }
        )

    report = {
        "target": TARGET_COL,
        "model_path": str(model_path),
        "train_csv": str(args.train_csv),
        "test_csv": str(args.test_csv),
        "rows_train": int(len(train_df)),
        "rows_test": int(len(test_df)),
        "train_period": {
            "date_min": str(train_df[DATE_COL].min().date()),
            "date_max": str(train_df[DATE_COL].max().date()),
        },
        "test_period": {
            "date_min": str(test_df[DATE_COL].min().date()),
            "date_max": str(test_df[DATE_COL].max().date()),
        },
        "train_target_summary": summarize_target(train_df[TARGET_COL]),
        "test_target_summary": summarize_target(test_df[TARGET_COL]),
        "baseline_values": {
            "train_mean": train_mean,
            "train_median": train_median,
        },
        "model_metrics": model_metrics,
        "baseline_mean_metrics": baseline_mean_metrics,
        "baseline_median_metrics": baseline_median_metrics,
        "comparison": {
            "model_beats_baseline_mean_by_rmse": model_metrics["rmse"] < baseline_mean_metrics["rmse"],
            "model_beats_baseline_mean_by_mae": model_metrics["mae"] < baseline_mean_metrics["mae"],
            "model_beats_baseline_mean_by_r2": model_metrics["r2"] > baseline_mean_metrics["r2"],
            "model_beats_baseline_median_by_rmse": model_metrics["rmse"] < baseline_median_metrics["rmse"],
            "model_beats_baseline_median_by_mae": model_metrics["mae"] < baseline_median_metrics["mae"],
            "model_beats_baseline_median_by_r2": model_metrics["r2"] > baseline_median_metrics["r2"],
            "rmse_improvement_vs_mean": baseline_mean_metrics["rmse"] - model_metrics["rmse"],
            "mae_improvement_vs_mean": baseline_mean_metrics["mae"] - model_metrics["mae"],
            "r2_improvement_vs_mean": model_metrics["r2"] - baseline_mean_metrics["r2"],
            "rmse_improvement_vs_median": baseline_median_metrics["rmse"] - model_metrics["rmse"],
            "mae_improvement_vs_median": baseline_median_metrics["mae"] - model_metrics["mae"],
            "r2_improvement_vs_median": model_metrics["r2"] - baseline_median_metrics["r2"],
        },
        "month_metrics": make_month_metrics(prediction_df),
        "top_errors": top_errors,
        "expected_features": expected_features,
        "note": (
            "This is the final test on Nov-Dec data. "
            "Do not tune the model using this result."
        ),
    }

    with (out_dir / "final_test_metrics.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    write_summary_md(report, out_dir / "final_test_summary.md")

    print("Final test selesai.")
    print(f"Rows test: {len(test_df)}")
    print(f"Output dir: {out_dir}")
    print("")
    print("Model metrics:")
    print(json.dumps(model_metrics, indent=2))
    print("")
    print("Baseline mean metrics:")
    print(json.dumps(baseline_mean_metrics, indent=2))
    print("")
    print("Baseline median metrics:")
    print(json.dumps(baseline_median_metrics, indent=2))


if __name__ == "__main__":
    main()