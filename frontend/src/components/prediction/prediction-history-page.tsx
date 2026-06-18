"use client";

import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import { PredictionHistoryTable } from "@/components/prediction/prediction-history-table";
import {
  getApiErrorMessage,
  getPredictionHistory,
} from "@/lib/api-client";
import type {
  PredictionHistoryResponse,
  ProductionStatus,
} from "@/types/prediction";
import { FeedbackMessage } from "@/components/common/feedback-message";
import { LoadingCard } from "@/components/common/loading-card";

const PAGE_SIZE = 10;

type StatusFilter = ProductionStatus | "";

const statusLabels: Record<ProductionStatus, string> = {
  PROCESSING: "Processing",
  DRAFT: "Draft",
  ANOMALY: "Anomaly",
  FAILED: "Failed",
  RECONCILED: "Reconciled",
};

export function PredictionHistoryPage() {
  const [statusFilter, setStatusFilter] =
    useState<StatusFilter>("");

  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const [appliedStatus, setAppliedStatus] =
    useState<StatusFilter>("");

  const [appliedDateFrom, setAppliedDateFrom] =
    useState("");

  const [appliedDateTo, setAppliedDateTo] =
    useState("");

  const [offset, setOffset] = useState(0);

  const [history, setHistory] =
    useState<PredictionHistoryResponse | null>(null);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadHistory() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const result = await getPredictionHistory(
          {
            limit: PAGE_SIZE,
            offset,
            status: appliedStatus,
            dateFrom: appliedDateFrom,
            dateTo: appliedDateTo,
          },
          controller.signal,
        );

        setHistory(result);
      } catch (error) {
        if (!controller.signal.aborted) {
          setErrorMessage(getApiErrorMessage(error));
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadHistory();

    return () => {
      controller.abort();
    };
  }, [
    offset,
    appliedStatus,
    appliedDateFrom,
    appliedDateTo,
    refreshKey,
  ]);

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (dateFrom && dateTo && dateFrom > dateTo) {
      setErrorMessage(
        "Tanggal awal tidak boleh melebihi tanggal akhir.",
      );
      return;
    }

    setOffset(0);
    setAppliedStatus(statusFilter);
    setAppliedDateFrom(dateFrom);
    setAppliedDateTo(dateTo);
  }

  function resetFilters() {
    setStatusFilter("");
    setDateFrom("");
    setDateTo("");

    setOffset(0);
    setAppliedStatus("");
    setAppliedDateFrom("");
    setAppliedDateTo("");
    setErrorMessage(null);
  }

  const total = history?.total ?? 0;
  const currentStart =
    total === 0 ? 0 : offset + 1;

  const currentEnd = Math.min(
    offset + PAGE_SIZE,
    total,
  );

  const canGoPrevious = offset > 0;
  const canGoNext = offset + PAGE_SIZE < total;

  const activeFilters = [
    appliedStatus ? `Status: ${statusLabels[appliedStatus]}` : null,
    appliedDateFrom ? `Dari: ${appliedDateFrom}` : null,
    appliedDateTo ? `Sampai: ${appliedDateTo}` : null,
  ].filter(Boolean);

  return (
    <div className="space-y-6">
      <header className="rounded-[2rem] border border-[#d7d2c5] bg-white p-6 shadow-[0_18px_45px_rgba(32,45,38,0.05)]">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <p className="badge-text text-xs font-bold text-[#c65331]">
              Operational Logbook
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-[#173a30] sm:text-4xl">
              Riwayat hasil prediksi
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#66736d]">
              Pantau status task, estimasi WIP, estimasi prime, dan proses
              rekonsiliasi dari data produksi yang sudah masuk ke database.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:min-w-80">
            <div className="rounded-2xl bg-[#f6f1e8] p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-[#66736d]">
                Total data
              </p>
              <p className="value-text mt-2 text-2xl font-semibold text-[#173a30]">
                {isLoading && !history ? "..." : total}
              </p>
            </div>

            <div className="rounded-2xl bg-[#f6f1e8] p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-[#66736d]">
                Halaman ini
              </p>
              <p className="value-text mt-2 text-2xl font-semibold text-[#173a30]">
                {isLoading
                  ? "..."
                  : `${currentStart}-${currentEnd}`}
              </p>
            </div>
          </div>
        </div>
      </header>

      <form
        onSubmit={applyFilters}
        className="rounded-3xl border border-[#d7d2c5] bg-white p-5 shadow-[0_18px_45px_rgba(32,45,38,0.05)]"
      >
        <div className="mb-5 flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
          <div>
            <p className="badge-text text-xs font-bold text-[#c65331]">
              Filter
            </p>
            <h2 className="mt-1 text-xl font-semibold text-[#173a30]">
              Cari data prediksi
            </h2>
          </div>

          <p className="text-sm text-[#66736d]">
            Filter membaca riwayat yang tersimpan di database.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <label>
            <span className="text-sm font-medium text-[#33473e]">
              Status
            </span>

            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(
                  event.target.value as StatusFilter,
                )
              }
              className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-white px-3 py-2.5"
            >
              <option value="">Semua status</option>
              <option value="PROCESSING">Processing</option>
              <option value="DRAFT">Draft</option>
              <option value="ANOMALY">Anomaly</option>
              <option value="FAILED">Failed</option>
              <option value="RECONCILED">Reconciled</option>
            </select>
          </label>

          <label>
            <span className="text-sm font-medium text-[#33473e]">
              Dari tanggal
            </span>

            <input
              type="date"
              value={dateFrom}
              onChange={(event) =>
                setDateFrom(event.target.value)
              }
              className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-white px-3 py-2.5"
            />
          </label>

          <label>
            <span className="text-sm font-medium text-[#33473e]">
              Sampai tanggal
            </span>

            <input
              type="date"
              value={dateTo}
              onChange={(event) =>
                setDateTo(event.target.value)
              }
              className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-white px-3 py-2.5"
            />
          </label>

          <div className="flex items-end gap-2">
            <button
              type="submit"
              className="flex-1 rounded-xl bg-[#173a30] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#245547]"
            >
              Terapkan
            </button>

            <button
              type="button"
              onClick={resetFilters}
              className="rounded-xl border border-[#cfd5d1] px-4 py-2.5 text-sm font-semibold text-[#52625b]"
            >
              Reset
            </button>
          </div>
        </div>
      </form>

      {errorMessage && (
        <FeedbackMessage
          variant="error"
          title="Riwayat prediksi tidak dapat dimuat"
          action={
            <button
              type="button"
              onClick={() => {
                setErrorMessage(null);
                setRefreshKey((current) => current + 1);
              }}
              className="rounded-xl bg-[#173a30] px-4 py-2 text-sm font-semibold text-white"
            >
              Coba lagi
            </button>
          }
        >
          {errorMessage}
        </FeedbackMessage>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-[#66736d]">
            {isLoading
              ? "Memuat riwayat prediksi..."
              : `Menampilkan ${currentStart}-${currentEnd} dari ${total} data`}
          </p>

          <div className="mt-2 flex flex-wrap gap-2">
            {activeFilters.length > 0 ? (
              activeFilters.map((filter) => (
                <span
                  key={filter}
                  className="badge-text rounded-full bg-[#f1eee5] px-3 py-1 text-xs font-bold text-[#66736d]"
                >
                  {filter}
                </span>
              ))
            ) : (
              <span className="text-xs text-[#8b9691]">
                Tidak ada filter aktif.
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            disabled={!canGoPrevious || isLoading}
            onClick={() =>
              setOffset((current) =>
                Math.max(current - PAGE_SIZE, 0),
              )
            }
            className="rounded-lg border border-[#c8cec9] px-4 py-2 text-sm font-semibold text-[#173a30] disabled:opacity-40"
          >
            Sebelumnya
          </button>

          <button
            type="button"
            disabled={!canGoNext || isLoading}
            onClick={() =>
              setOffset((current) =>
                current + PAGE_SIZE,
              )
            }
            className="rounded-lg border border-[#c8cec9] px-4 py-2 text-sm font-semibold text-[#173a30] disabled:opacity-40"
          >
            Berikutnya
          </button>
        </div>
      </div>

      {isLoading && !history ? (
        <LoadingCard message="Memuat riwayat prediksi..." />
      ) : (
        <PredictionHistoryTable
          items={history?.items ?? []}
        />
      )}
    </div>
  );
}
