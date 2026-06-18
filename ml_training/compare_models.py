from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
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


def load_dataset(
    csv_path: str,
    use_calendar_features: bool,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, list[str], list[str]]:
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

    if use_calendar_features:
        df["month"] = df[DATE_COL].dt.month
        df["day_of_month"] = df[DATE_COL].dt.day

    drop_cols = {
        DATE_COL,
        TARGET_COL,
        *LEAKAGE_COLS,
    }

    feature_cols = [col for col in df.columns if col not in drop_cols]

    categorical_cols = [PROFILE_COL]
    numeric_cols = [col for col in feature_cols if col not in categorical_cols]

    X = df[feature_cols].copy()
    y = df[TARGET_COL].copy()
    meta = df[[DATE_COL, PROFILE_COL]].copy()

    return X, y, meta, numeric_cols, categorical_cols


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


def run_cv(
    model_name: str,
    pipeline: Pipeline,
    X: pd.DataFrame,
    y: pd.Series,
    meta: pd.DataFrame,
    n_splits: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    unique_dates = np.array(sorted(meta[DATE_COL].unique()))

    if len(unique_dates) < n_splits + 1:
        raise ValueError("Jumlah unique date tidak cukup untuk TimeSeriesSplit.")

    splitter = TimeSeriesSplit(n_splits=n_splits)

    fold_rows = []
    prediction_rows = []

    for fold, (train_idx, test_idx) in enumerate(splitter.split(unique_dates), start=1):
        train_dates = unique_dates[train_idx]
        test_dates = unique_dates[test_idx]

        train_mask = meta[DATE_COL].isin(train_dates)
        test_mask = meta[DATE_COL].isin(test_dates)

        X_train = X.loc[train_mask]
        y_train = y.loc[train_mask]
        X_test = X.loc[test_mask]
        y_test = y.loc[test_mask]

        fold_model = clone(pipeline)
        fold_model.fit(X_train, y_train)

        y_pred = fold_model.predict(X_test)
        y_pred = np.clip(y_pred, 0, None)

        baseline_pred = np.full(len(y_test), y_train.mean())

        model_metrics = calculate_metrics(y_test.to_numpy(), y_pred)
        baseline_metrics = calculate_metrics(y_test.to_numpy(), baseline_pred)

        fold_rows.append(
            {
                "model": model_name,
                "fold": fold,
                "train_rows": int(train_mask.sum()),
                "test_rows": int(test_mask.sum()),
                "train_date_min": str(pd.Timestamp(train_dates.min()).date()),
                "train_date_max": str(pd.Timestamp(train_dates.max()).date()),
                "test_date_min": str(pd.Timestamp(test_dates.min()).date()),
                "test_date_max": str(pd.Timestamp(test_dates.max()).date()),
                "model_rmse": model_metrics["rmse"],
                "model_mae": model_metrics["mae"],
                "model_r2": model_metrics["r2"],
                "baseline_rmse": baseline_metrics["rmse"],
                "baseline_mae": baseline_metrics["mae"],
                "baseline_r2": baseline_metrics["r2"],
            }
        )

        test_meta = meta.loc[test_mask].copy()

        prediction_rows.append(
            pd.DataFrame(
                {
                    "model": model_name,
                    "fold": fold,
                    "production_date": test_meta[DATE_COL].dt.strftime("%Y-%m-%d"),
                    "profile_name": test_meta[PROFILE_COL],
                    "actual_wip_ton": y_test.to_numpy(),
                    "predicted_wip_ton": y_pred,
                    "baseline_prediction": baseline_pred,
                }
            )
        )

    fold_metrics = pd.DataFrame(fold_rows)
    predictions = pd.concat(prediction_rows, ignore_index=True)

    return fold_metrics, predictions


def summarize_results(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for model_name, group in fold_metrics.groupby("model"):
        rows.append(
            {
                "model": model_name,
                "rmse_mean": float(group["model_rmse"].mean()),
                "mae_mean": float(group["model_mae"].mean()),
                "r2_mean": float(group["model_r2"].mean()),
                "rmse_std": float(group["model_rmse"].std(ddof=0)),
                "mae_std": float(group["model_mae"].std(ddof=0)),
                "r2_std": float(group["model_r2"].std(ddof=0)),
                "baseline_rmse_mean": float(group["baseline_rmse"].mean()),
                "baseline_mae_mean": float(group["baseline_mae"].mean()),
                "baseline_r2_mean": float(group["baseline_r2"].mean()),
                "rmse_improvement": float(group["baseline_rmse"].mean() - group["model_rmse"].mean()),
                "mae_improvement": float(group["baseline_mae"].mean() - group["model_mae"].mean()),
                "r2_improvement": float(group["model_r2"].mean() - group["baseline_r2"].mean()),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["mae_mean", "rmse_mean"], ascending=[True, True])
        .reset_index(drop=True)
    )


def save_feature_importance(pipeline: Pipeline, output_dir: Path) -> None:
    try:
        feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
        model_step = pipeline.named_steps["model"]

        if isinstance(model_step, TransformedTargetRegressor):
            fitted_model = model_step.regressor_
        else:
            fitted_model = model_step

        if not hasattr(fitted_model, "feature_importances_"):
            return

        importance_df = pd.DataFrame(
            {
                "feature": feature_names,
                "importance": fitted_model.feature_importances_,
            }
        ).sort_values("importance", ascending=False)

        importance_df.to_csv(output_dir / "best_feature_importance.csv", index=False)
    except Exception as error:
        (output_dir / "feature_importance_error.txt").write_text(str(error), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--csv", required=True, help="Path dataset CSV.")
    parser.add_argument("--out-dir", required=True, help="Folder output hasil comparison.")
    parser.add_argument("--n-splits", type=int, default=4, help="Jumlah split validasi time-series.")
    parser.add_argument(
        "--target-transform",
        choices=["none", "log1p"],
        default="log1p",
        help="Transformasi target. Default log1p karena WIP cenderung skewed.",
    )
    parser.add_argument(
        "--calendar-features",
        action="store_true",
        help="Aktifkan fitur kalender month dan day_of_month. Default mati.",
    )

    args = parser.parse_args()

    X, y, meta, numeric_cols, categorical_cols = load_dataset(
        csv_path=args.csv,
        use_calendar_features=args.calendar_features,
    )

    base_models = get_models()

    all_fold_metrics = []
    all_predictions = []

    for model_name, base_model in base_models.items():
        print(f"Training model: {model_name}")

        pipeline = build_pipeline(
            base_model=base_model,
            numeric_cols=numeric_cols,
            categorical_cols=categorical_cols,
            target_transform=args.target_transform,
        )

        fold_metrics, predictions = run_cv(
            model_name=model_name,
            pipeline=pipeline,
            X=X,
            y=y,
            meta=meta,
            n_splits=args.n_splits,
        )

        all_fold_metrics.append(fold_metrics)
        all_predictions.append(predictions)

    fold_metrics_df = pd.concat(all_fold_metrics, ignore_index=True)
    predictions_df = pd.concat(all_predictions, ignore_index=True)
    comparison_df = summarize_results(fold_metrics_df)

    best_model_name = comparison_df.iloc[0]["model"]
    best_base_model = base_models[best_model_name]

    best_pipeline = build_pipeline(
        base_model=best_base_model,
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
        target_transform=args.target_transform,
    )
    best_pipeline.fit(X, y)

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fold_metrics_df.to_csv(output_dir / "model_fold_metrics.csv", index=False)
    predictions_df.to_csv(output_dir / "model_oof_predictions.csv", index=False)
    comparison_df.to_csv(output_dir / "model_comparison.csv", index=False)

    joblib.dump(best_pipeline, output_dir / "best_pipeline.pkl")
    save_feature_importance(best_pipeline, output_dir)

    report = {
        "target": TARGET_COL,
        "target_transform": args.target_transform,
        "calendar_features": bool(args.calendar_features),
        "best_model": best_model_name,
        "rows_used": int(len(y)),
        "date_min": str(meta[DATE_COL].min().date()),
        "date_max": str(meta[DATE_COL].max().date()),
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "model_comparison": comparison_df.to_dict(orient="records"),
    }

    with (output_dir / "comparison_report.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\nComparison selesai.")
    print(f"Rows used: {len(y)}")
    print(f"Calendar features: {bool(args.calendar_features)}")
    print(f"Best model: {best_model_name}")
    print(f"Output dir: {output_dir}")
    print("\nRingkasan:")
    print(comparison_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()