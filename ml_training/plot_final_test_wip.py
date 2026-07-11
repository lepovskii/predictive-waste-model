from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PREDICTION_CSV = Path(
    "ml_training/artifacts/wip_final_test_nov_dec/final_test_predictions.csv"
)

OUTPUT_DIR = Path(
    "ml_training/artifacts/wip_final_test_nov_dec/plots"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def format_label(date_value: str, profile_name: str) -> str:
    return f"{date_value}\n{profile_name}"


def plot_daily_actual_vs_predicted(df: pd.DataFrame) -> None:
    daily_df = (
        df.groupby("production_date", as_index=False)
        .agg(
            actual_wip_ton=("actual_wip_ton", "sum"),
            predicted_wip_ton=("predicted_wip_ton", "sum"),
        )
        .sort_values("production_date")
    )

    plt.figure(figsize=(12, 6))
    plt.plot(
        daily_df["production_date"],
        daily_df["actual_wip_ton"],
        marker="o",
        linewidth=2,
        label="Actual WIP",
    )
    plt.plot(
        daily_df["production_date"],
        daily_df["predicted_wip_ton"],
        marker="o",
        linewidth=2,
        label="Predicted WIP",
    )

    plt.title("Perbandingan Aktual dan Prediksi WIP per Tanggal Produksi")
    plt.xlabel("Tanggal Produksi")
    plt.ylabel("WIP (Ton)")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / "daily_actual_vs_predicted_wip.png", dpi=300)
    plt.close()


def plot_profile_actual_vs_predicted(df: pd.DataFrame) -> None:
    plot_df = df.sort_values(["production_date", "profile_name"]).copy()
    plot_df["label"] = [
        format_label(row.production_date, row.profile_name)
        for row in plot_df.itertuples()
    ]

    x = range(len(plot_df))
    width = 0.4

    plt.figure(figsize=(16, 7))
    plt.bar(
        [i - width / 2 for i in x],
        plot_df["actual_wip_ton"],
        width=width,
        label="Actual WIP",
    )
    plt.bar(
        [i + width / 2 for i in x],
        plot_df["predicted_wip_ton"],
        width=width,
        label="Predicted WIP",
    )

    plt.title("Perbandingan Aktual dan Prediksi WIP per Profile")
    plt.xlabel("Tanggal Produksi dan Profile")
    plt.ylabel("WIP (Ton)")
    plt.xticks(list(x), plot_df["label"], rotation=75, ha="right")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / "profile_actual_vs_predicted_wip.png", dpi=300)
    plt.close()


def plot_actual_vs_predicted_scatter(df: pd.DataFrame) -> None:
    actual = df["actual_wip_ton"]
    predicted = df["predicted_wip_ton"]

    min_value = min(actual.min(), predicted.min())
    max_value = max(actual.max(), predicted.max())

    plt.figure(figsize=(7, 7))
    plt.scatter(actual, predicted, alpha=0.75)
    plt.plot(
        [min_value, max_value],
        [min_value, max_value],
        linestyle="--",
        label="Garis Ideal",
    )

    plt.title("Scatter Plot Aktual vs Prediksi WIP")
    plt.xlabel("Actual WIP (Ton)")
    plt.ylabel("Predicted WIP (Ton)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / "scatter_actual_vs_predicted_wip.png", dpi=300)
    plt.close()


def main() -> None:
    df = pd.read_csv(PREDICTION_CSV)

    numeric_columns = [
        "actual_wip_ton",
        "predicted_wip_ton",
        "absolute_error",
        "squared_error",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["production_date"] = pd.to_datetime(
        df["production_date"]
    ).dt.strftime("%Y-%m-%d")

    plot_daily_actual_vs_predicted(df)
    plot_profile_actual_vs_predicted(df)
    plot_actual_vs_predicted_scatter(df)

    print("Grafik berhasil dibuat di:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()