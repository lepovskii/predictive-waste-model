from pathlib import Path
import json

import mlflow


EXPERIMENT_NAME = "wip_prediction_experiments"

FINAL_TEST_DIR = Path("ml_training/artifacts/wip_final_test_nov_dec")
METRICS_PATH = FINAL_TEST_DIR / "final_test_metrics.json"
PREDICTIONS_PATH = FINAL_TEST_DIR / "final_test_predictions.csv"
PLOTS_DIR = FINAL_TEST_DIR / "plots"


def main() -> None:
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment(EXPERIMENT_NAME)

    with METRICS_PATH.open("r", encoding="utf-8") as file:
        report = json.load(file)

    with mlflow.start_run(run_name="v1_final_test_nov_dec"):
        mlflow.log_param("target", report["target"])
        mlflow.log_param("model_path", report["model_path"])
        mlflow.log_param("train_csv", report["train_csv"])
        mlflow.log_param("test_csv", report["test_csv"])
        mlflow.log_param("rows_train", report["rows_train"])
        mlflow.log_param("rows_test", report["rows_test"])
        mlflow.log_param("train_date_min", report["train_period"]["date_min"])
        mlflow.log_param("train_date_max", report["train_period"]["date_max"])
        mlflow.log_param("test_date_min", report["test_period"]["date_min"])
        mlflow.log_param("test_date_max", report["test_period"]["date_max"])

        model_metrics = report["model_metrics"]
        mlflow.log_metric("rmse", model_metrics["rmse"])
        mlflow.log_metric("mae", model_metrics["mae"])
        mlflow.log_metric("r2", model_metrics["r2"])

        baseline_mean = report["baseline_mean_metrics"]
        mlflow.log_metric("baseline_mean_rmse", baseline_mean["rmse"])
        mlflow.log_metric("baseline_mean_mae", baseline_mean["mae"])
        mlflow.log_metric("baseline_mean_r2", baseline_mean["r2"])

        baseline_median = report["baseline_median_metrics"]
        mlflow.log_metric("baseline_median_rmse", baseline_median["rmse"])
        mlflow.log_metric("baseline_median_mae", baseline_median["mae"])
        mlflow.log_metric("baseline_median_r2", baseline_median["r2"])

        mlflow.log_artifact(str(METRICS_PATH))
        mlflow.log_artifact(str(PREDICTIONS_PATH))

        if PLOTS_DIR.exists():
            for plot_path in PLOTS_DIR.glob("*.png"):
                mlflow.log_artifact(str(plot_path), artifact_path="plots")

        print("MLflow logging selesai.")
        print("Refresh browser: http://127.0.0.1:5000")


if __name__ == "__main__":
    main()