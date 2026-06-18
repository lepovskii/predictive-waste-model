import type { Metadata } from "next";

import { CsvUploadForm } from "@/components/upload/csv-upload-form";

export const metadata: Metadata = {
  title: "Upload Data Produksi",
  description: "Validasi dan normalisasi CSV sebelum prediksi WIP.",
};

export default function UploadPage() {
  return (
    <div>
      <header className="mb-10">
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-[#c65331]">
          Production Quality Control
        </p>

        <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
          Upload data produksi
        </h1>

        <p className="mt-4 max-w-2xl leading-7 text-[#52625b]">
          Unggah laporan produksi dalam format CSV. Sistem akan
          memeriksa dan menormalisasi data sebelum prediksi WIP
          dijalankan.
        </p>
      </header>

      <CsvUploadForm />
    </div>
  );
}