import type { Metadata } from "next";

import { PredictionHistoryPage } from "@/components/prediction/prediction-history-page";

export const metadata: Metadata = {
  title: "Hasil Prediksi",
  description: "Riwayat dan status hasil prediksi WIP.",
};

export default function PredictionsPage() {
  return (
    <div>
      <header className="mb-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#c65331]">
          Prediction Records
        </p>

        <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
          Hasil prediksi
        </h1>

        <p className="mt-4 max-w-2xl leading-7 text-[#52625b]">
          Periksa riwayat prediksi berdasarkan tanggal dan status,
          kemudian buka detail untuk melihat hasil per profile.
        </p>
      </header>

      <PredictionHistoryPage />
    </div>
  );
}