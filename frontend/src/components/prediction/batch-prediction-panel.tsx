"use client";

import type { AdapterPreviewResponse } from "@/types/adapter";
import type {
  BatchItemResult,
  PredictBatchResponse,
} from "@/types/prediction";
import { FeedbackMessage } from "@/components/common/feedback-message";

interface BatchPredictionPanelProps {
  preview: AdapterPreviewResponse | null;
  result: PredictBatchResponse | null;
  errorMessage: string | null;
  isSubmitting: boolean;
  onSubmit: () => void;
}

const resultStyles: Record<BatchItemResult, string> = {
  ACCEPTED: "bg-[#d9eee2] text-[#175c38]",
  DUPLICATE: "bg-[#fff0c7] text-[#795500]",
  FAILED: "bg-[#ffe0d7] text-[#8a351d]",
};

export function BatchPredictionPanel({
  preview,
  result,
  errorMessage,
  isSubmitting,
  onSubmit,
}: BatchPredictionPanelProps) {
  if (!preview) {
    return null;
  }

  const payloadCount = preview.normalized_payloads.length;

  const canSubmit =
    preview.is_valid_for_prediction &&
    payloadCount > 0 &&
    payloadCount <= 100 &&
    !result;

  return (
    <section className="rounded-3xl border border-[#d7d2c5] bg-white p-6 shadow-[0_20px_50px_rgba(32,45,38,0.07)] sm:p-8">
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#ba4f2c]">
            Batch Prediction
          </p>

          <h2 className="mt-2 text-2xl font-semibold text-[#15251f]">
            Jalankan prediksi WIP
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-[#65736d]">
            Sistem akan mengirim {payloadCount} hari produksi ke database dan
            antrean Celery. Setiap tanggal akan diproses sebagai satu task.
          </p>
        </div>

        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit || isSubmitting}
          className="shrink-0 rounded-xl bg-[#ba4f2c] px-6 py-3 font-semibold text-white transition hover:bg-[#9f3f22] disabled:cursor-not-allowed disabled:bg-[#b9b9b1]"
        >
          {isSubmitting ? "Mengirim prediksi..." : "Jalankan prediksi"}
        </button>
      </div>

      {!preview.is_valid_for_prediction && (
        <div className="mt-5">
          <FeedbackMessage
            variant="error"
            title="Prediksi belum dapat dijalankan"
          >
            Hasil adapter masih invalid. Periksa temuan validasi CSV sebelum melanjutkan.
          </FeedbackMessage>
        </div>
      )}

      {payloadCount > 100 && (
        <div className="mt-5">
          <FeedbackMessage
            variant="warning"
            title="Batch terlalu besar"
          >
            Maksimal 100 hari produksi dapat dikirim dalam satu batch.
          </FeedbackMessage>
        </div>
      )}

      {errorMessage && (
        <div className="mt-5">
          <FeedbackMessage
            variant="error"
            title="Batch prediction gagal"
          >
            {errorMessage}
          </FeedbackMessage>
        </div>
      )}

      {result && (
        <div className="mt-7 border-t border-[#e3dfd4] pt-7">
          <FeedbackMessage
            variant={
              result.failed_count > 0
                ? "warning"
                : result.duplicate_count > 0
                  ? "warning"
                  : "success"
            }
            title="Batch prediction selesai dikirim"
          >
            {result.accepted_count} task diterima, {result.duplicate_count} duplikat, dan {result.failed_count} gagal.
          </FeedbackMessage>
          <div className="mt-5 grid gap-3 sm:grid-cols-4">
            <Summary label="Total" value={result.total_items} />
            <Summary label="Diterima" value={result.accepted_count} />
            <Summary label="Duplikat" value={result.duplicate_count} />
            <Summary label="Gagal" value={result.failed_count} />
          </div>

          <h3 className="mt-7 font-semibold text-[#15251f]">
            Hasil per tanggal
          </h3>

          <ul className="mt-3 max-h-96 space-y-3 overflow-y-auto pr-1">
            {result.results.map((item) => (
              <li
                key={item.production_date}
                className="rounded-xl border border-[#dedbd1] bg-[#f8f8f3] p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="value-text font-semibold text-[#15251f]">
                    {item.production_date}
                  </span>

                  <span
                    className={`badge-text rounded-full px-3 py-1 text-xs font-bold ${
                      resultStyles[item.result]
                    }`}
                  >
                    {item.result}
                  </span>
                </div>

                <p className="mt-2 text-sm leading-6 text-[#65736d]">
                  {item.message}
                </p>

                {item.task_id && (
                  <p className="value-text mt-2 break-all text-xs text-[#52625b]">
                    Task ID: {item.task_id}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

interface SummaryProps {
  label: string;
  value: number;
}

function Summary({ label, value }: SummaryProps) {
  return (
    <div className="rounded-xl bg-[#edf2ee] p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-[#65736d]">
        {label}
      </p>
      <p className="value-text mt-1 text-2xl font-semibold text-[#183d32]">
        {value}
      </p>
    </div>
  );
}
