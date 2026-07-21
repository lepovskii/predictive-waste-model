"use client";

import {
  type FormEvent,
  useState,
  useEffect
} from "react";

import { ManualProfileForm } from "@/components/manual/manual-profile-form";
import { PredictionResultsPanel } from "@/components/prediction/prediction-results-panel";
import { FeedbackMessage } from "@/components/common/feedback-message";
import {
  getApiErrorMessage,
  submitPrediction,
  getAvailableModels,
} from "@/lib/api-client";

import {
  buildManualPredictionPayload,
  createEmptyProfile,
  createInitialManualForm,
  ManualFormValidationError,
  MAX_MANUAL_PROFILES,
} from "@/lib/manual-prediction";

import { createSinglePredictionTracking } from "@/lib/prediction-tracking";
import type {
  ManualPredictionFormState,
  ManualProfileFormState,
} from "@/types/manual-prediction";

import type { PredictBatchResponse } from "@/types/prediction";

export function ManualPredictionForm() {
  const [form, setForm] =
    useState<ManualPredictionFormState>(
      createInitialManualForm,
    );

  const [trackingResult, setTrackingResult] =
    useState<PredictBatchResponse | null>(null);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [requiredFeatures, setRequiredFeatures] = useState<string[] | null>(null);

  useEffect(() => {
    async function loadFeatures() {
      try {
        const response = await getAvailableModels();
        const activeModel = response.models.find(m => m.is_active);
        if (activeModel) {
          setRequiredFeatures(activeModel.metadata.features.all_input_columns);
        }
      } catch (error) {
        console.error("Gagal memuat metadata model:", error);
      }
    }
    loadFeatures();
  }, []);

  function updateGeneralField(
    field:
      | "production_date"
      | "estimasi_manual_class_b"
      | "estimasi_manual_reject",
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));

    setErrorMessage(null);
    setTrackingResult(null);
  }

  function updateProfile(
    profileId: string,
    field: keyof ManualProfileFormState,
    value: string,
  ) {
    if (field === "id") {
      return;
    }

    setForm((current) => ({
      ...current,
      profiles: current.profiles.map((profile) =>
        profile.id === profileId
          ? {
            ...profile,
            [field]: value,
          }
          : profile,
      ),
    }));

    setErrorMessage(null);
    setTrackingResult(null);
  }

  function addProfile() {
    if (form.profiles.length >= MAX_MANUAL_PROFILES) {
      setErrorMessage(
        `Maksimal ${MAX_MANUAL_PROFILES} profile dalam satu tanggal produksi.`,
      );
      setTrackingResult(null);
      return;
    }

    const profileId = `profile-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 9)}`;

    setForm((current) => ({
      ...current,
      profiles: [
        ...current.profiles,
        createEmptyProfile(profileId),
      ],
    }));

    setErrorMessage(null);
    setTrackingResult(null);
  }

  function removeProfile(profileId: string) {
    setForm((current) => {
      if (current.profiles.length <= 1) {
        return current;
      }

      return {
        ...current,
        profiles: current.profiles.filter(
          (profile) => profile.id !== profileId,
        ),
      };
    });

    setErrorMessage(null);
    setTrackingResult(null);
  }

  function resetForm() {
    setForm(createInitialManualForm());
    setTrackingResult(null);
    setErrorMessage(null);
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setErrorMessage(null);
    setTrackingResult(null);

    let payload;

    try {
      payload = buildManualPredictionPayload(form);
    } catch (error) {
      setErrorMessage(
        error instanceof ManualFormValidationError
          ? error.message
          : "Form belum dapat diproses.",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await submitPrediction(payload);

      setTrackingResult(
        createSinglePredictionTracking(response),
      );
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  const trackingKey =
    trackingResult?.results[0]?.task_id ?? "manual-result";

  return (
    <div className="space-y-8">
      <form onSubmit={handleSubmit} className="space-y-6">
        <section className="rounded-3xl border border-[#d7d2c5] bg-white p-6 shadow-[0_18px_45px_rgba(32,45,38,0.06)]">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.16em] text-[#c65331]">
              Production Log
            </p>

            <h2 className="mt-2 text-2xl font-semibold text-[#173a30]">
              Informasi produksi harian
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#66736d]">
              Satu request mewakili satu tanggal produksi dan dapat
              memiliki beberapa profile.
            </p>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <label htmlFor="production-date">
              <span className="text-sm font-medium text-[#33473e]">
                Tanggal produksi
              </span>

              <input
                id="production-date"
                type="date"
                required
                disabled={isSubmitting}
                value={form.production_date}
                onChange={(event) =>
                  updateGeneralField(
                    "production_date",
                    event.target.value,
                  )
                }
                className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-white px-3 py-2.5 outline-none transition focus:border-[#c65331] focus:ring-4 focus:ring-[#c65331]/10"
              />
            </label>

            <NumberInput
              id="manual-class-b"
              label="Estimasi manual Class B"
              unit="ton"
              value={form.estimasi_manual_class_b}
              disabled={isSubmitting}
              onChange={(value) =>
                updateGeneralField(
                  "estimasi_manual_class_b",
                  value,
                )
              }
            />

            <NumberInput
              id="manual-reject"
              label="Estimasi manual Reject"
              unit="ton"
              value={form.estimasi_manual_reject}
              disabled={isSubmitting}
              onChange={(value) =>
                updateGeneralField(
                  "estimasi_manual_reject",
                  value,
                )
              }
            />
          </div>

          <div className="mt-4">
            <FeedbackMessage
              variant="info"
              title="Class B dan Reject tidak diprediksi model"
            >
              Nilai tersebut bersifat opsional dan digunakan dalam kalkulasi estimasi prime.
            </FeedbackMessage>
          </div>
        </section>

        <div className="space-y-6">
          {form.profiles.map((profile, index) => (
            <ManualProfileForm
              key={profile.id}
              profile={profile}
              profileIndex={index}
              canRemove={form.profiles.length > 1}
              disabled={isSubmitting || requiredFeatures === null}
              requiredFeatures={requiredFeatures}
              onChange={updateProfile}
              onRemove={removeProfile}
            />
          ))}
        </div>

        {errorMessage && (
          <FeedbackMessage
            variant="error"
            title="Form prediksi belum dapat dikirim"
          >
            {errorMessage}
          </FeedbackMessage>
        )}

        <section className="flex flex-col justify-between gap-4 rounded-3xl bg-[#173a30] p-6 text-white sm:flex-row sm:items-center">
          <div>
            <p className="font-semibold">
              {form.profiles.length} dari {MAX_MANUAL_PROFILES} profile
            </p>

            <p className="mt-1 text-sm text-[#c8d8d1]">
              Setiap card profile yang ditambahkan wajib diisi sebelum prediksi.
            </p>
          </div>

          <div className="grid w-full gap-3 sm:w-auto sm:grid-cols-3">
            <button
              type="button"
              onClick={addProfile}
              disabled={
                isSubmitting ||
                form.profiles.length >= MAX_MANUAL_PROFILES
              }
              className="w-full rounded-xl border border-white/25 px-4 py-2.5 text-sm font-semibold transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Tambah profile produksi
            </button>

            <button
              type="button"
              onClick={resetForm}
              disabled={isSubmitting}
              className="w-full rounded-xl border border-white/25 px-4 py-2.5 text-sm font-semibold transition hover:bg-white/10 disabled:opacity-50"
            >
              Reset
            </button>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-xl bg-[#c65331] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#a94428] disabled:cursor-not-allowed disabled:bg-[#8d817b]"
            >
              {isSubmitting
                ? "Mengirim prediksi..."
                : "Jalankan prediksi"}
            </button>
          </div>
        </section>

        {trackingResult && (
          <FeedbackMessage
            variant="success"
            title="Prediksi manual berhasil dikirim"
          >
            Task sudah masuk ke antrean backend. Status hasil prediksi akan dipantau di panel bawah.
          </FeedbackMessage>
        )}

      </form>

      {trackingResult && (
        <PredictionResultsPanel
          key={trackingKey}
          batchResult={trackingResult}
        />
      )}
    </div>
  );
}

interface NumberInputProps {
  id: string;
  label: string;
  unit: string;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
}

function NumberInput({
  id,
  label,
  unit,
  value,
  disabled,
  onChange,
}: NumberInputProps) {
  return (
    <label htmlFor={id}>
      <span className="flex justify-between gap-2 text-sm font-medium text-[#33473e]">
        {label}
        <span className="text-xs font-normal text-[#78847e]">
          {unit}
        </span>
      </span>

      <input
        id={id}
        type="number"
        min="0"
        step="any"
        required
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-white px-3 py-2.5 outline-none transition focus:border-[#c65331] focus:ring-4 focus:ring-[#c65331]/10"
      />
    </label>
  );
}