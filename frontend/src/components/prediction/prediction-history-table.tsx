import Link from "next/link";

import {
  formatDate,
  formatDateTime,
  formatTon,
} from "@/lib/formatters";
import type {
  PredictionHistoryItem,
  ProductionStatus,
} from "@/types/prediction";
import { EmptyState } from "@/components/common/empty-state";

interface PredictionHistoryTableProps {
  items: PredictionHistoryItem[];
}

const statusStyles: Record<ProductionStatus, string> = {
  PROCESSING: "bg-[#dceaf4] text-[#275f7a]",
  DRAFT: "bg-[#e7e9e8] text-[#42524b]",
  ANOMALY: "bg-[#fff0c7] text-[#795500]",
  FAILED: "bg-[#ffe0d7] text-[#8a351d]",
  RECONCILED: "bg-[#d9eee2] text-[#175c38]",
};

export function PredictionHistoryTable({
  items,
}: PredictionHistoryTableProps) {
  if (items.length === 0) {
    return (
      <EmptyState
        title="Belum ada hasil yang sesuai"
        description="Ubah filter atau jalankan prediksi produksi baru."
        action={
          <Link
            href="/upload"
            className="inline-flex rounded-xl bg-[#173a30] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#245547]"
          >
            Upload CSV produksi
          </Link>
        }
      />
    );
  }

  return (
    <div className="overflow-x-auto rounded-3xl border border-[#d7d2c5] bg-white shadow-[0_18px_45px_rgba(32,45,38,0.06)]">
      <p className="px-5 py-3 text-xs text-[#66736d] md:hidden">
        Geser tabel ke samping untuk melihat semua kolom.
      </p>
      <table className="w-full min-w-[980px] text-left">
        <thead>
          <tr className="border-b border-[#d7d2c5] bg-[#f7f6f1] text-xs uppercase tracking-wider text-[#65736d]">
            <th className="px-5 py-4 font-semibold">Tanggal</th>
            <th className="px-5 py-4 font-semibold">Produksi</th>
            <th className="px-5 py-4 font-semibold">Estimasi WIP</th>
            <th className="px-5 py-4 font-semibold">Estimasi Prime</th>
            <th className="px-5 py-4 font-semibold">Profile</th>
            <th className="px-5 py-4 font-semibold">Status</th>
            <th className="px-5 py-4 font-semibold">Diperbarui</th>
            <th className="px-5 py-4 font-semibold">Aksi</th>
          </tr>
        </thead>

        <tbody>
          {items.map((item) => (
            <tr
              key={
                item.task_id ??
                `${item.production_date}-${item.created_at}`
              }
              className="border-b border-[#ebe8df] text-sm text-[#263a32] transition hover:bg-[#fbfaf6] last:border-b-0"
            >
              <td className="value-text px-5 py-4 font-semibold">
                {formatDate(item.production_date)}
              </td>

              <td className="value-text px-5 py-4">
                {formatTon(item.total_output_ton)}
              </td>

              <td className="value-text px-5 py-4 font-semibold text-[#c65331]">
                {formatTon(item.estimasi_wip_total)}
              </td>

              <td className="value-text px-5 py-4">
                {formatTon(item.estimasi_prime)}
              </td>

              <td className="value-text px-5 py-4">
                {item.profile_count}
              </td>

              <td className="px-5 py-4">
                <span
                  className={`badge-text rounded-full px-3 py-1 text-xs font-bold ${statusStyles[item.status]}`}
                >
                  {item.status}
                </span>

                {item.model_artifact_id && (
                  <p className="mt-2 text-[11px] font-semibold text-[#42524b] bg-[#e7e9e8] px-2 py-0.5 rounded inline-block">
                    {item.model_artifact_id}
                  </p>
                )}
              </td>

              <td className="value-text px-5 py-4 text-xs text-[#66736d]">
                {formatDateTime(item.updated_at)}
              </td>
              <td className="px-5 py-4">
                {item.task_id ? (
                  <Link
                    href={`/predictions/${item.task_id}`}
                    className="inline-flex rounded-lg bg-[#173a30] px-3 py-2 text-xs font-semibold text-white transition hover:bg-[#245547]"
                  >
                    Lihat hasil
                  </Link>
                ) : (
                  <span className="text-xs text-[#8b9691]">
                    Tidak tersedia
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
