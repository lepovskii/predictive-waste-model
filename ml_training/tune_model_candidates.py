from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

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


def align_holdout_features(X_train: pd.DataFrame, X_holdout: pd.DataFrame) -> pd.DataFrame:
    missing_features = [col for col in X_train.columns if col not in X_holdout.columns]
    extra_features = [col for col in X_holdout.columns if col not in X_train.columns]

    if missing_features:
        raise ValueError(f"Fitur training tidak ada di holdout: {missing_features}")

    if extra_features:
        print(f"Info: fitur ekstra di holdout diabaikan: {extra_features}")

    return X_holdout[X_train.columns].copy()


def build_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
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


def build_pipeline(
    model_name: str,
    params: dict,
    numeric_cols: list[str],
    categorical_cols: list[str],
) -> Pipeline:
    if model_name == "extra_trees":
        model = ExtraTreesRegressor(
            random_state=42,
            n_jobs=-1,
            **params,
        )
    elif model_name == "random_forest":
        model = RandomForestRegressor(
            random_state=42,
            n_jobs=-1,
            **params,
        )
    elif model_name == "xgboost":
        if XGBRegressor is None:
            raise RuntimeError("xgboost tidak tersedia di environment ini.")

        model = XGBRegressor(
            objective="reg:squarederror",
            random_state=42,
            n_jobs=4,
            **params,
        )
    else:
        raise ValueError(f"Model tidak dikenal: {model_name}")

    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor(numeric_cols, categorical_cols)),
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


def param_product(grid: dict[str, list]) -> list[dict]:
    keys = list(grid.keys())
    values = list(grid.values())

    return [dict(zip(keys, combo)) for combo in itertools.product(*values)]


def get_param_grids() -> dict[str, list[dict]]:
    grids = {
        "extra_trees": param_product(
            {
                "n_estimators": [300, 500],
                "max_depth": [4, 6, None],
                "min_samples_leaf": [1, 3, 5],
                "max_features": ["sqrt", 0.7, 1.0],
                "bootstrap": [False, True],
            }
        ),
        "random_forest": param_product(
            {
                "n_estimators": [300, 500],
                "max_depth": [4, 6, None],
                "min_samples_leaf": [1, 3, 5],
                "max_features": ["sqrt", 0.7, 1.0],
                "bootstrap": [True],
            }
        ),
        "xgboost": param_product(
            {
                "n_estimators": [100, 300, 500],
                "learning_rate": [0.03, 0.05, 0.1],
                "max_depth": [2, 3, 4],
                "min_child_weight": [1, 3],
                "subsample": [0.8, 1.0],
                "colsample_bytree": [0.8, 1.0],
                "reg_lambda": [1.0, 3.0, 5.0],
                "reg_alpha": [0.0, 0.1],
            }
        ),
    }

    if XGBRegressor is None:
        grids.pop("xgboost", None)

    return grids


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--train-csv", required=True, help="Path dataset training Jan-Aug.")
    parser.add_argument("--holdout-csv", required=True, help="Path dataset validation September.")
    parser.add_argument("--out-dir", required=True, help="Folder output hasil tuning.")
    parser.add_argument(
        "--max-xgb-trials",
        type=int,
        default=80,
        help="Batasi jumlah kombinasi XGBoost agar tuning tidak terlalu lama.",
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

    grids = get_param_grids()

    if "xgboost" in grids and len(grids["xgboost"]) > args.max_xgb_trials:
        rng = np.random.default_rng(42)
        selected_idx = rng.choice(len(grids["xgboost"]), size=args.max_xgb_trials, replace=False)
        grids["xgboost"] = [grids["xgboost"][i] for i in selected_idx]

    results = []
    best_pipeline = None
    best_result = None
    best_predictions = None

    total_trials = sum(len(params_list) for params_list in grids.values())
    trial_number = 0

    for model_name, params_list in grids.items():
        for params in params_list:
            trial_number += 1
            print(f"[{trial_number}/{total_trials}] Tuning {model_name}: {params}")

            pipeline = build_pipeline(
                model_name=model_name,
                params=params,
                numeric_cols=numeric_cols,
                categorical_cols=categorical_cols,
            )

            pipeline.fit(X_train, y_train)

            y_pred = pipeline.predict(X_holdout)
            y_pred = np.clip(y_pred, 0, None)

            metrics = calculate_metrics(y_holdout.to_numpy(), y_pred)

            row = {
                "model": model_name,
                "rmse": metrics["rmse"],
                "mae": metrics["mae"],
                "r2": metrics["r2"],
                "baseline_mean_rmse": baseline_mean_metrics["rmse"],
                "baseline_mean_mae": baseline_mean_metrics["mae"],
                "baseline_mean_r2": baseline_mean_metrics["r2"],
                "baseline_median_rmse": baseline_median_metrics["rmse"],
                "baseline_median_mae": baseline_median_metrics["mae"],
                "baseline_median_r2": baseline_median_metrics["r2"],
                "rmse_improvement_vs_mean": baseline_mean_metrics["rmse"] - metrics["rmse"],
                "mae_improvement_vs_mean": baseline_mean_metrics["mae"] - metrics["mae"],
                "r2_improvement_vs_mean": metrics["r2"] - baseline_mean_metrics["r2"],
                "rmse_improvement_vs_median": baseline_median_metrics["rmse"] - metrics["rmse"],
                "mae_improvement_vs_median": baseline_median_metrics["mae"] - metrics["mae"],
                "r2_improvement_vs_median": metrics["r2"] - baseline_median_metrics["r2"],
                "params": json.dumps(params),
            }

            results.append(row)

            if best_result is None or row["mae"] < best_result["mae"]:
                best_result = row
                best_pipeline = pipeline
                best_predictions = pd.DataFrame(
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

    results_df = (
        pd.DataFrame(results)
        .sort_values(["mae", "rmse"], ascending=[True, True])
        .reset_index(drop=True)
    )

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(output_dir / "tuning_results.csv", index=False)

    if best_pipeline is not None:
        joblib.dump(best_pipeline, output_dir / "best_tuned_pipeline.pkl")

    if best_predictions is not None:
        best_predictions.to_csv(output_dir / "best_tuned_predictions.csv", index=False)

    report = {
        "target": TARGET_COL,
        "selection_metric": "mae",
        "best_result": best_result,
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
        "trials_per_model": {model: len(params) for model, params in grids.items()},
    }

    with (output_dir / "tuning_report.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\nTuning selesai.")
    print(f"Total trials: {len(results_df)}")
    print(f"Output dir: {output_dir}")
    print("\nTop 10 results:")
    print(results_df.head(10).round(4).to_string(index=False))


if __name__ == "__main__":
    main()