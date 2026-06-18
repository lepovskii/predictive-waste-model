from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeRegressor

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None


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


def make_ohe() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


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


def get_models() -> dict[str, object]:
    models: dict[str, object] = {
        "decision_tree": DecisionTreeRegressor(
            max_depth=4,
            min_samples_leaf=5,
            random_state=42,
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=500,
            max_depth=5,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        ),
        "extra_trees": ExtraTreesRegressor(
            n_estimators=500,
            max_depth=5,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.03,
            max_depth=2,
            min_samples_leaf=4,
            random_state=42,
        ),
    }

    if XGBRegressor is not None:
        models["xgboost"] = XGBRegressor(
            objective="reg:squarederror",
            n_estimators=300,
            max_depth=2,
            learning_rate=0.03,
            subsample=0.85,
            colsample_bytree=0.85,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=5.0,
            random_state=42,
            n_jobs=4,
        )
    else:
        print("Warning: xgboost tidak tersedia, model xgboost dilewati.")

    return models


def build_pipeline(
    base_model: object,
    numeric_cols: list[str],
    categorical_cols: list[str],
    target_transform: str,
) -> Pipeline:
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
        ]
    )

    if target_transform == "log1p":
        model = TransformedTargetRegressor(
            regressor=base_model,
            func=np.log1p,
            inverse_func=np.expm1,
        )
    elif target_transform == "none":
        model = base_model
    else:
        raise ValueError(f"target_transform tidak dikenal: {target_transform}")

    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_pred = np.clip(y_pred, 0, None)

    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def align_holdout_features(
    X_train: pd.DataFrame,
    X_holdout: pd.DataFrame,
) -> pd.DataFrame:
    missing_features = [col for col in X_train.columns if col not in X_holdout.columns]
    extra_features = [col for col in X_holdout.columns if col not in X_train.columns]

    if missing_features:
        raise ValueError(f"Fitur training tidak ada di holdout: {missing_features}")

    if extra_features:
        print(f"Info: fitur ekstra di holdout diabaikan: {extra_features}")

    return X_holdout[X_train.columns].copy()


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--train-csv", required=True, help="Path dataset training Jan-Aug.")
    parser.add_argument("--holdout-csv", required=True, help="Path dataset validation September.")
    parser.add_argument("--out-dir", required=True, help="Folder output hasil validasi kandidat model.")
    parser.add_argument(
        "--target-transform",
        choices=["none", "log1p"],
        default="none",
        help="Transformasi target. Default none untuk WIP aktual terbaru.",
    )

    args = parser.parse_args()

    X_train, y_train, meta_train = load_dataset(args.train_csv)
    X_holdout, y_holdout, meta_holdout = load_dataset(args.holdout_csv)

    X_holdout = align_holdout_features(X_train, X_holdout)

    categorical_cols = [PROFILE_COL]
    numeric_cols = [col for col in X_train.columns if col not in categorical_cols]

    train_mean_value = float(y_train.mean())
    train_median_value = float(y_train.median())

    baseline_mean_pred = np.full(len(y_holdout), train_mean_value)
    baseline_median_pred = np.full(len(y_holdout), train_median_value)

    baseline_mean_metrics = calculate_metrics(y_holdout.to_numpy(), baseline_mean_pred)
    baseline_median_metrics = calculate_metrics(y_holdout.to_numpy(), baseline_median_pred)

    model_rows = []
    prediction_frames = []

    models = get_models()

    best_model_name = None
    best_mae = None
    best_pipeline = None

    for model_name, base_model in models.items():
        print(f"Training dan validasi model: {model_name}")

        pipeline = build_pipeline(
            base_model=base_model,
            numeric_cols=numeric_cols,
            categorical_cols=categorical_cols,
            target_transform=args.target_transform,
        )

        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_holdout)
        y_pred = np.clip(y_pred, 0, None)

        model_metrics = calculate_metrics(y_holdout.to_numpy(), y_pred)

        model_rows.append(
            {
                "model": model_name,
                "rmse": model_metrics["rmse"],
                "mae": model_metrics["mae"],
                "r2": model_metrics["r2"],
                "baseline_mean_rmse": baseline_mean_metrics["rmse"],
                "baseline_mean_mae": baseline_mean_metrics["mae"],
                "baseline_mean_r2": baseline_mean_metrics["r2"],
                "baseline_median_rmse": baseline_median_metrics["rmse"],
                "baseline_median_mae": baseline_median_metrics["mae"],
                "baseline_median_r2": baseline_median_metrics["r2"],
                "rmse_improvement_vs_mean": baseline_mean_metrics["rmse"] - model_metrics["rmse"],
                "mae_improvement_vs_mean": baseline_mean_metrics["mae"] - model_metrics["mae"],
                "r2_improvement_vs_mean": model_metrics["r2"] - baseline_mean_metrics["r2"],
                "rmse_improvement_vs_median": baseline_median_metrics["rmse"] - model_metrics["rmse"],
                "mae_improvement_vs_median": baseline_median_metrics["mae"] - model_metrics["mae"],
                "r2_improvement_vs_median": model_metrics["r2"] - baseline_median_metrics["r2"],
            }
        )

        prediction_frames.append(
            pd.DataFrame(
                {
                    "model": model_name,
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
        )

        if best_mae is None or model_metrics["mae"] < best_mae:
            best_mae = model_metrics["mae"]
            best_model_name = model_name
            best_pipeline = pipeline

    comparison = (
        pd.DataFrame(model_rows)
        .sort_values(["mae", "rmse"], ascending=[True, True])
        .reset_index(drop=True)
    )

    predictions = pd.concat(prediction_frames, ignore_index=True)

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison.to_csv(output_dir / "holdout_model_comparison.csv", index=False)
    predictions.to_csv(output_dir / "holdout_model_predictions.csv", index=False)

    if best_pipeline is not None:
        joblib.dump(best_pipeline, output_dir / "best_holdout_pipeline.pkl")

    report = {
        "target": TARGET_COL,
        "target_transform": args.target_transform,
        "best_model_by_holdout_mae": best_model_name,
        "rows_train": int(len(y_train)),
        "rows_holdout": int(len(y_holdout)),
        "train_date_min": str(meta_train[DATE_COL].min().date()),
        "train_date_max": str(meta_train[DATE_COL].max().date()),
        "holdout_date_min": str(meta_holdout[DATE_COL].min().date()),
        "holdout_date_max": str(meta_holdout[DATE_COL].max().date()),
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
        "baseline_mean_metrics": baseline_mean_metrics,
        "baseline_median_metrics": baseline_median_metrics,
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "model_comparison": comparison.to_dict(orient="records"),
    }

    with (output_dir / "holdout_candidate_report.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\nValidasi kandidat model selesai.")
    print(f"Train rows: {len(y_train)}")
    print(f"Holdout rows: {len(y_holdout)}")
    print(f"Best model by holdout MAE: {best_model_name}")
    print(f"Output dir: {output_dir}")
    print("\nRingkasan:")
    print(comparison.round(4).to_string(index=False))


if __name__ == "__main__":
    main()