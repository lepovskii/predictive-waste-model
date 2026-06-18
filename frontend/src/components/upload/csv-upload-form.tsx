"use client";

import { type ChangeEvent, type FormEvent, useState } from "react";

import { BatchPredictionPanel } from "@/components/prediction/batch-prediction-panel";
import { AdapterPreviewPanel } from "@/components/upload/adapter-preview-panel";
import {
  getApiErrorMessage,
  previewCsv,
  submitPredictionBatch,
} from "@/lib/api-client";
import type { AdapterPreviewResponse } from "@/types/adapter";
import type { PredictBatchResponse } from "@/types/prediction";
import { PredictionResultsPanel } from "@/components/prediction/prediction-results-panel";
import { FeedbackMessage } from "@/components/common/feedback-message";

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

function validateFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    return "File harus menggunakan format CSV.";
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return "Ukuran file tidak boleh melebihi 5 MB.";
  }

  return null;
}

export function CsvUploadForm() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] =
    useState<AdapterPreviewResponse | null>(null);

  const [batchResult, setBatchResult] =
    useState<PredictBatchResponse | null>(null);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [predictionError, setPredictionError] =
    useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;

    setSelectedFile(file);
    setPreview(null);
    setErrorMessage(file ? validateFile(file) : null);
    setBatchResult(null);
    setPredictionError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile) {
      setErrorMessage("Pilih file CSV terlebih dahulu.");
      return;
    }

    const validationError = validateFile(selectedFile);

    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    setBatchResult(null);
    setPredictionError(null);
    setIsLoading(true);
    setErrorMessage(null);
    setPreview(null);

    try {
      const result = await previewCsv(selectedFile);
      setPreview(result);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  async function handlePredictionSubmit() {
    if (!preview?.is_valid_for_prediction) {
      setPredictionError(
        "CSV belum memenuhi syarat untuk menjalankan prediksi.",
      );
      return;
    }

    const items = preview.normalized_payloads;

    if (items.length === 0) {
      setPredictionError("Tidak ada data produksi yang dapat diprediksi.");
      return;
    }

    if (items.length > 100) {
      setPredictionError(
        "Maksimal 100 hari produksi dapat dikirim dalam satu batch.",
      );
      return;
    }

    setIsSubmitting(true);
    setPredictionError(null);
    setBatchResult(null);

    try {
      const result = await submitPredictionBatch({ items });
      setBatchResult(result);
    } catch (error) {
      setPredictionError(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  const predictionResultsKey = batchResult?.results
  .map(
    (item) =>
      item.task_id ??
      `${item.production_date}-${item.result}`,
  )
  .join("|");

  return (
    <div className="space-y-6">
      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <form
          onSubmit={handleSubmit}
          className="rounded-3xl border border-[#d7d2c5] bg-white p-4 shadow-[0_24px_60px_rgba(32,45,38,0.08)] sm:p-8"
        >
          <div className="rounded-2xl border-2 border-dashed border-[#aeb9b2] bg-[#f8f8f3] p-5 text-center sm:p-8">
            <label
              htmlFor="production-csv"
              className="block text-lg font-semibold"
            >
              Pilih laporan produksi
            </label>
            
            <p className="mt-2 text-sm leading-6 text-[#65736d]">
              Format yang didukung adalah CSV dengan ukuran maksimal 5 MB.
            </p>

            <input
              id="production-csv"
              name="production-csv"
              type="file"
              accept=".csv,text/csv"
              onChange={handleFileChange}
              disabled={isLoading}
              className="mt-6 block w-full cursor-pointer rounded-xl border border-[#cdd4cf] bg-white p-3 text-sm file:mr-4 file:rounded-lg file:border-0 file:bg-[#183d32] file:px-4 file:py-2 file:font-semibold file:text-white hover:file:bg-[#245547]"
            />
          </div>

          {selectedFile && (
            <div className="mt-5 rounded-xl bg-[#edf2ee] px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-[#66736d]">
                File terpilih
              </p>
              <p className="mt-1 break-all font-medium">{selectedFile.name}</p>
            </div>
          )}

          {errorMessage && (
            <div className="mt-5">
              <FeedbackMessage
                variant="error"
                title="CSV tidak dapat diproses"
              >
                {errorMessage}
              </FeedbackMessage>
            </div>
          )}

          <button
            type="submit"
            disabled={!selectedFile || isLoading || Boolean(errorMessage)}
            className="mt-6 w-full rounded-xl bg-[#ba4f2c] px-5 py-3 font-semibold text-white transition hover:bg-[#9f3f22] disabled:cursor-not-allowed disabled:bg-[#b9b9b1]"
          >
            {isLoading ? "Memeriksa CSV..." : "Periksa dan normalisasi CSV"}
          </button>
        </form>

        <AdapterPreviewPanel preview={preview} />
      </section>

      <BatchPredictionPanel
        preview={preview}
        result={batchResult}
        errorMessage={predictionError}
        isSubmitting={isSubmitting}
        onSubmit={handlePredictionSubmit}
      />

      {batchResult && (
        <PredictionResultsPanel
          key={predictionResultsKey}
          batchResult={batchResult}
        />
      )}
    </div>
  );
}