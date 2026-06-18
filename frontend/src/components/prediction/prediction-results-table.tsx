"use client";

import { Fragment, useState } from "react";

import { ProfilePredictionDetails } from "@/components/prediction/profile-prediction-details";
import type { PollingItem } from "@/hooks/use-prediction-polling";
import { formatTon } from "@/lib/formatters";
import type { ProductionStatus } from "@/types/prediction";
import { FeedbackMessage } from "@/components/common/feedback-message";

interface PredictionResultsTableProps {
  items: PollingItem[];
}

const statusStyles: Record<ProductionStatus, string> = {
  PROCESSING: "bg-[#dceaf4] text-[#275f7a]",
  DRAFT: "bg-[#e7e9e8] text-[#42524b]",
  ANOMALY: "bg-[#fff0c7] text-[#795500]",
  FAILED: "bg-[#ffe0d7] text-[#8a351d]",
  RECONCILED: "bg-[#d9eee2] text-[#175c38]",
};

function getPollingStatusLabel(item: PollingItem): string {
  if (item.phase === "ERROR") {
    return "ERROR";
  }

  if (item.phase === "TIMEOUT") {
    return "TIMEOUT";
  }

  return item.data?.status ?? "PROCESSING";
}

function getDetailButtonLabel(
  isExpanded: boolean,
  item: PollingItem,
): string {
  if (isExpanded) {
    return "Tutup detail";
  }

  if (item.phase === "POLLING") {
    return "Menunggu hasil";
  }

  if (item.phase === "ERROR" || item.phase === "TIMEOUT") {
    return "Tidak tersedia";
  }

  return "Lihat detail";
}

export function PredictionResultsTable({
  items,
}: PredictionResultsTableProps) {
  const [expandedTaskIds, setExpandedTaskIds] =
    useState<Set<string>>(() => new Set());

  function toggleTaskDetails(taskId: string) {
    setExpandedTaskIds((currentTaskIds) => {
      const nextTaskIds = new Set(currentTaskIds);

      if (nextTaskIds.has(taskId)) {
        nextTaskIds.delete(taskId);
      } else {
        nextTaskIds.add(taskId);
      }

      return nextTaskIds;
    });
  }

  return (
    <div className="mt-7 overflow-x-auto">
      {items.some(
        (item) =>
          item.phase === "ERROR" ||
          item.phase === "TIMEOUT",
      ) && (
        <div className="mb-5">
          <FeedbackMessage
            variant="warning"
            title="Sebagian status prediksi belum berhasil diambil"
          >
            Beberapa task tidak dapat dimuat oleh frontend. Coba buka halaman riwayat prediksi atau refresh halaman jika backend sudah selesai memproses.
          </FeedbackMessage>
        </div>
      )}
      <p className="mb-3 text-xs text-[#66736d] md:hidden">
        Geser tabel ke samping untuk melihat semua kolom.
      </p>
      <table className="w-full min-w-[860px] border-collapse text-left">
        <thead>
          <tr className="border-b border-[#d7d2c5] text-xs uppercase tracking-wider text-[#65736d]">
            <th className="px-3 py-3 font-semibold">Tanggal</th>
            <th className="px-3 py-3 font-semibold">Produksi</th>
            <th className="px-3 py-3 font-semibold">Estimasi WIP</th>
            <th className="px-3 py-3 font-semibold">Estimasi Prime</th>
            <th className="px-3 py-3 font-semibold">Profile</th>
            <th className="px-3 py-3 font-semibold">Status</th>
            <th className="px-3 py-3 font-semibold">Aksi</th>
          </tr>
        </thead>

        <tbody>
          {items.map((item) => {
            const status = item.data?.status ?? "PROCESSING";
            const isExpanded = expandedTaskIds.has(item.taskId);
            const canShowDetails =
              item.data !== null && item.data.profiles.length > 0;

            return (
              <Fragment key={item.taskId}>
                <tr className="border-b border-[#ebe8df] text-sm text-[#263a32]">
                  <td className="value-text px-3 py-4 font-semibold">
                    {item.productionDate}
                  </td>

                  <td className="value-text px-3 py-4">
                    {formatTon(item.data?.total_output_ton ?? null)}
                  </td>

                  <td className="value-text px-3 py-4 font-semibold text-[#ba4f2c]">
                    {formatTon(item.data?.estimasi_wip_total ?? null)}
                  </td>

                  <td className="value-text px-3 py-4">
                    {formatTon(item.data?.estimasi_prime ?? null)}
                  </td>

                  <td className="value-text px-3 py-4">
                    {item.data?.profiles.length ?? "-"}
                  </td>

                  <td className="px-3 py-4">
                    {item.phase === "ERROR" ||
                      item.phase === "TIMEOUT" ? (
                        <span className="badge-text rounded-full bg-[#ffe0d7] px-3 py-1 text-xs font-bold text-[#8a351d]">
                          {getPollingStatusLabel(item)}
                        </span>
                      ) : (
                        <span
                          className={`badge-text rounded-full px-3 py-1 text-xs font-bold ${statusStyles[status]}`}
                        >
                          {getPollingStatusLabel(item)}
                        </span>
                      )}

                    {item.errorMessage && (
                      <p className="mt-2 max-w-xs text-xs leading-5 text-[#8a351d]">
                        {item.errorMessage}
                      </p>
                    )}
                  </td>

                  <td className="px-3 py-4">
                    <button
                      type="button"
                      onClick={() =>
                        toggleTaskDetails(item.taskId)
                      }
                      disabled={!canShowDetails}
                      aria-expanded={isExpanded}
                      className="rounded-lg border border-[#bfc9c3] px-3 py-2 text-xs font-semibold text-[#183d32] transition hover:border-[#183d32] hover:bg-[#edf2ee] disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {getDetailButtonLabel(isExpanded, item)}
                    </button>

                    {item.phase === "POLLING" && (
                      <p className="mt-2 max-w-32 text-xs leading-5 text-[#66736d]">
                        Detail tersedia setelah prediksi selesai.
                      </p>
                    )}
                  </td>
                </tr>

                {isExpanded && item.data && (
                  <tr className="border-b border-[#d7d2c5]">
                    <td
                      colSpan={7}
                      className="bg-[#f5f5ef] px-5 py-5"
                    >
                      <ProfilePredictionDetails
                        prediction={item.data}
                      />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
