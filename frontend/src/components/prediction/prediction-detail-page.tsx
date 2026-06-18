"use client";

import Link from "next/link";

import { PredictionDisclaimer } from "@/components/prediction/prediction-disclaimer";
import { ProfilePredictionDetails } from "@/components/prediction/profile-prediction-details";
import { usePredictionDetail } from "@/hooks/use-prediction-detail";
import {
  formatDate,
  formatDateTime,
  formatTon,
} from "@/lib/formatters";
import type { ProductionStatus } from "@/types/prediction";
import { ReconciliationForm } from "@/components/prediction/reconciliation-form";
import { FeedbackMessage } from "@/components/common/feedback-message";
import { LoadingCard } from "@/components/common/loading-card";

interface PredictionDetailPageProps {
  taskId: string;
}

const statusStyles: Record<ProductionStatus, string> = {
  PROCESSING: "bg-[#dceaf4] text-[#275f7a]",
  DRAFT: "bg-[#e7e9e8] text-[#42524b]",
  ANOMALY: "bg-[#fff0c7] text-[#795500]",
  FAILED: "bg-[#ffe0d7] text-[#8a351d]",
  RECONCILED: "bg-[#d9eee2] text-[#175c38]",
};

interface SummaryCardProps {
  label: string;
  value: string;
  highlight?: boolean;
}

function SummaryCard({
  label,
  value,
  highlight = false,
}: SummaryCardProps) {
  return (
    <div className="rounded-2xl border border-[#d7d2c5] bg-white p-5">
      <p className="text-xs font-semibold uppercase tracking-wider text-[#65736d]">
        {label}
      </p>

      <p
        className={`value-text mt-2 text-xl font-semibold ${
          highlight ? "text-[#c65331]" : "text-[#173a30]"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

export function PredictionDetailPage({
  taskId,
}: PredictionDetailPageProps) {
  const {
    prediction,
    errorMessage,
    isLoading,
    refresh,
  } = usePredictionDetail(taskId);

  if (isLoading && !prediction) {
    return (
      <LoadingCard message="Memuat detail prediksi..." />
    );
  }

  if (!prediction) {
    return (
      <div className="space-y-5">
        <Link
          href="/predictions"
          className="text-sm font-semibold text-[#173a30]"
        >
          Kembali ke hasil prediksi
        </Link>

        <FeedbackMessage
          variant="error"
          title="Detail prediksi tidak dapat dimuat"
          action={
            <button
              type="button"
              onClick={refresh}
              className="rounded-xl bg-[#173a30] px-4 py-2 text-sm font-semibold text-white"
            >
              Coba lagi
            </button>
          }
        >
          {errorMessage ?? "Data prediksi tidak ditemukan."}
        </FeedbackMessage>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        href="/predictions"
        className="inline-flex text-sm font-semibold text-[#173a30] hover:text-[#c65331]"
      >
        Kembali ke hasil prediksi
      </Link>

      <header className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#c65331]">
            Prediction Detail
          </p>

          <h1 className="mt-3 text-4xl font-semibold tracking-tight">
            {formatDate(prediction.production_date)}
          </h1>

          <p className="value-text mt-3 break-all text-sm text-[#65736d]">
            Task ID: {prediction.task_id ?? taskId}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={`badge-text rounded-full px-4 py-2 text-xs font-bold ${statusStyles[prediction.status]}`}
          >
            {prediction.status}
          </span>

          <button
            type="button"
            onClick={refresh}
            className="rounded-xl border border-[#c8cec9] px-4 py-2 text-sm font-semibold text-[#173a30] hover:bg-[#edf2ee]"
          >
            Perbarui
          </button>
        </div>
      </header>

      {errorMessage && (
        <FeedbackMessage
          variant="error"
          title="Gagal memperbarui data"
        >
          {errorMessage}
        </FeedbackMessage>
      )}

      {prediction.status === "PROCESSING" && (
        <FeedbackMessage
          variant="info"
          title="Prediksi masih diproses"
        >
          Halaman akan diperbarui secara otomatis sampai backend memberi status final.
        </FeedbackMessage>
      )}

      {prediction.needs_retraining && (
        <FeedbackMessage
          variant="warning"
          title="Perlu perhatian saat evaluasi model"
        >
          Data aktual menunjukkan perbedaan besar terhadap prediksi. Ini bukan perintah otomatis untuk training ulang, tetapi penanda untuk evaluasi performa berikutnya.
        </FeedbackMessage>
      )}

      <ReconciliationForm
        key={`${prediction.task_id}-${prediction.updated_at}`}
        prediction={prediction}
        onReconciled={refresh}
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Total produksi"
          value={formatTon(prediction.total_output_ton)}
        />

        <SummaryCard
          label="Estimasi WIP"
          value={formatTon(prediction.estimasi_wip_total)}
          highlight
        />

        <SummaryCard
          label="Estimasi prime"
          value={formatTon(prediction.estimasi_prime)}
        />

        <SummaryCard
          label="Jumlah profile"
          value={String(prediction.profiles.length)}
        />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Manual Class B"
          value={formatTon(
            prediction.estimasi_manual_class_b,
          )}
        />

        <SummaryCard
          label="Manual reject"
          value={formatTon(
            prediction.estimasi_manual_reject,
          )}
        />

        <SummaryCard
          label="Aktual WIP"
          value={formatTon(prediction.aktual_wip)}
        />

        <SummaryCard
          label="Aktual prime"
          value={formatTon(prediction.aktual_prime)}
        />
      </section>

      <section className="rounded-3xl border border-[#d7d2c5] bg-white p-6 shadow-[0_18px_45px_rgba(32,45,38,0.05)]">
        <ProfilePredictionDetails prediction={prediction} />
      </section>

      <div className="text-xs text-[#65736d]">
        <p>Dibuat: {formatDateTime(prediction.created_at)}</p>
        <p className="mt-1">
          Diperbarui: {formatDateTime(prediction.updated_at)}
        </p>
      </div>

      <PredictionDisclaimer />
    </div>
  );
}
