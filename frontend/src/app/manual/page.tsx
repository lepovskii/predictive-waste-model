import type { Metadata } from "next";

import { ManualPredictionForm } from "@/components/manual/manual-prediction-form";

export const metadata: Metadata = {
  title: "Input Produksi Manual",
  description:
    "Input data produksi harian secara manual untuk prediksi WIP.",
};

export default function ManualInputPage() {
  return (
    <div>
      <header className="mb-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#c65331]">
          Manual Prediction
        </p>

        <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
          Input produksi manual
        </h1>

        <p className="mt-4 max-w-2xl leading-7 text-[#52625b]">
          Masukkan data produksi untuk satu tanggal. Kamu dapat
          menambahkan beberapa profile sebelum menjalankan prediksi WIP.
        </p>
      </header>

      <ManualPredictionForm />
    </div>
  );
}