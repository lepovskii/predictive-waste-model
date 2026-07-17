"use client";

import { type FormEvent, useState } from "react";

import {
  getApiErrorMessage,
  submitReconciliation,
} from "@/lib/api-client";
import { formatTon } from "@/lib/formatters";
import type { PredictionStatusResponse } from "@/types/prediction";
import type { ReconcileItemResponse } from "@/types/reconciliation";
import { FeedbackMessage } from "@/components/common/feedback-message";

interface ReconciliationFormProps {
  prediction: PredictionStatusResponse;
  onReconciled: () => void;
}

function normalizeDecimalInput(value: string): string {
  return value.trim().replace(",", ".");
}

function isValidNonNegativeNumber(value: string): boolean {
  if (!value.trim()) {
    return false;
  }

  const numericValue = Number(normalizeDecimalInput(value));

  return Number.isFinite(numericValue) && numericValue >= 0;
}

function getResultVariant(
  result: ReconcileItemResponse["result"],
) {
  if (result === "RECONCILED") {
    return "success";
  }

  if (result === "UNCHANGED") {
    return "info";
  }

  return "error";
}

export function ReconciliationForm({
  prediction,
  onReconciled,
}: ReconciliationFormProps) {
  const [actualWipTonPerProfile, setActualWipTonPerProfile] = useState<
    Record<string, string>
  >(() => {
    const initialState: Record<string, string> = {};
    for (const profile of prediction.profiles) {
      initialState[profile.profile_name] =
        profile.actual_wip_ton === null
          ? ""
          : String(profile.actual_wip_ton);
    }
    return initialState;
  });

  const totalActualWipTon = prediction.profiles.reduce((sum, profile) => {
    const val = actualWipTonPerProfile[profile.profile_name];
    if (val && isValidNonNegativeNumber(val)) {
      return sum + Number(normalizeDecimalInput(val));
    }
    return sum;
  }, 0);

  const [actualPrimeTon, setActualPrimeTon] = useState(
    prediction.aktual_prime === null
      ? ""
      : String(prediction.aktual_prime),
  );

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [result, setResult] =
    useState<ReconcileItemResponse | null>(null);

  const isDisabled =
    prediction.status === "PROCESSING" ||
    prediction.status === "FAILED";

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setErrorMessage(null);
    setResult(null);

    for (const profile of prediction.profiles) {
      const val = actualWipTonPerProfile[profile.profile_name];
      if (!isValidNonNegativeNumber(val || "")) {
        setErrorMessage(
          `Aktual WIP untuk profile ${profile.profile_name} wajib diisi dengan angka 0 atau lebih.`,
        );
        return;
      }
    }

    if (
      actualPrimeTon.trim() &&
      !isValidNonNegativeNumber(actualPrimeTon)
    ) {
      setErrorMessage(
        "Aktual prime harus berupa angka 0 atau lebih.",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await submitReconciliation({
        items: [
          {
            production_date: prediction.production_date,
            actual_wip_ton: String(totalActualWipTon),
            actual_prime_ton: actualPrimeTon.trim()
              ? normalizeDecimalInput(actualPrimeTon)
              : null,
            profiles: prediction.profiles.map(p => ({
              profile_name: p.profile_name,
              actual_wip_ton: Number(normalizeDecimalInput(actualWipTonPerProfile[p.profile_name])),
            }))
          },
        ],
      });

      const firstResult = response.results[0] ?? null;
      setResult(firstResult);

      if (
        firstResult &&
        (firstResult.result === "RECONCILED" ||
          firstResult.result === "UNCHANGED")
      ) {
        onReconciled();
      }
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="rounded-3xl border border-[#d7d2c5] bg-white p-6 shadow-[0_18px_45px_rgba(32,45,38,0.05)]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#c65331]">
            Reconciliation
          </p>

          <h2 className="mt-2 text-2xl font-semibold text-[#173a30]">
            Rekonsiliasi data aktual
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-[#65736d]">
            Masukkan aktual WIP dari laporan produksi untuk
            membandingkan hasil prediksi dengan kondisi aktual.
          </p>
        </div>

        <span className="badge-text rounded-full bg-[#f1eee5] px-4 py-2 text-xs font-bold text-[#52625b]">
          {prediction.status}
        </span>
      </div>

      {isDisabled && (
        <div className="mt-5">
          <FeedbackMessage
            variant="warning"
            title="Rekonsiliasi belum tersedia"
          >
            Rekonsiliasi hanya dapat dilakukan setelah prediksi selesai dan tidak berstatus FAILED.
          </FeedbackMessage>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="mt-6"
      >
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
          {prediction.profiles.map((profile) => (
            <label key={profile.detail_seq}>
              <span className="text-sm font-medium text-[#33473e] block truncate">
                Aktual WIP {profile.profile_name} (ton)
              </span>

              <input
                value={actualWipTonPerProfile[profile.profile_name] ?? ""}
                onChange={(event) =>
                  setActualWipTonPerProfile((prev) => ({
                    ...prev,
                    [profile.profile_name]: event.target.value,
                  }))
                }
                disabled={isDisabled || isSubmitting}
                inputMode="decimal"
                placeholder="contoh: 2.50"
                className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-white px-3 py-2.5 disabled:bg-[#f2f1ec] disabled:text-[#8b9691]"
              />
            </label>
          ))}
        </div>

        <div className="mt-6 border-t border-[#e4e2d9] pt-6 grid gap-4 md:grid-cols-[1fr_1fr_auto]">
          <label>
            <span className="text-sm font-medium text-[#33473e]">
              Total aktual WIP ton
            </span>

            <input
              value={totalActualWipTon > 0 || Object.values(actualWipTonPerProfile).some(v => v !== "") ? totalActualWipTon.toFixed(2) : ""}
              readOnly
              disabled
              placeholder="0.00 (Otomatis)"
              className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-[#f2f1ec] px-3 py-2.5 text-[#8b9691] font-semibold"
            />
          </label>

        <label>
          <span className="text-sm font-medium text-[#33473e]">
            Aktual prime ton
          </span>

          <input
            value={actualPrimeTon}
            onChange={(event) =>
              setActualPrimeTon(event.target.value)
            }
            disabled={isDisabled || isSubmitting}
            inputMode="decimal"
            placeholder="opsional"
            className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-white px-3 py-2.5 disabled:bg-[#f2f1ec] disabled:text-[#8b9691]"
          />
        </label>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={isDisabled || isSubmitting}
            className="w-full rounded-xl bg-[#173a30] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#245547] disabled:cursor-not-allowed disabled:bg-[#9ba6a0]"
          >
            {isSubmitting
              ? "Menyimpan..."
              : "Simpan aktual"}
          </button>
        </div>
        </div>
      </form>

      {errorMessage && (
        <div className="mt-5">
          <FeedbackMessage
            variant="error"
            title="Rekonsiliasi gagal"
          >
            {errorMessage}
          </FeedbackMessage>
        </div>
      )}

      {result && (
        <div className="mt-5">
          <FeedbackMessage
            variant={getResultVariant(result.result)}
            title={`${result.result}: ${result.message}`}
          >
            <div className="mt-3 grid gap-2 sm:grid-cols-3">
              <p>
                Prediksi WIP:{" "}
                <strong className="value-text">
                  {formatTon(result.predicted_wip_ton)}
                </strong>
              </p>

              <p>
                Aktual WIP:{" "}
                <strong className="value-text">
                  {formatTon(result.actual_wip_ton)}
                </strong>
              </p>

              <p>
                Error absolut:{" "}
                <strong className="value-text">
                  {formatTon(result.absolute_error_ton)}
                </strong>
              </p>
            </div>

            {result.needs_retraining && (
              <p className="mt-3">
                Error melebihi ambang evaluasi model. Data ini perlu diperhatikan saat evaluasi performa berikutnya.
              </p>
            )}
          </FeedbackMessage>
        </div>
      )}
    </section>
  );
}
