"use client";

import { useState } from "react";
import type {
  AdapterIssueSeverity,
  AdapterPreviewResponse,
  AdapterPreviewStatus,
} from "@/types/adapter";

interface AdapterPreviewPanelProps {
  preview: AdapterPreviewResponse | null;
}

const statusStyles: Record<AdapterPreviewStatus, string> = {
  VALID: "bg-[#d9eee2] text-[#175c38]",
  WARNING: "bg-[#fff0c7] text-[#795500]",
  INVALID: "bg-[#ffe0d7] text-[#8a351d]",
};

const issueStyles: Record<AdapterIssueSeverity, string> = {
  INFO: "border-[#b7c9d5] bg-[#edf5fa] text-[#345668]",
  WARNING: "border-[#e5c76d] bg-[#fff8df] text-[#725400]",
  ERROR: "border-[#e3a28c] bg-[#fff0eb] text-[#8a351d]",
import type {
  AdapterIssueSeverity,
  AdapterPreviewResponse,
  AdapterPreviewStatus,
} from "@/types/adapter";

interface AdapterPreviewPanelProps {
  preview: AdapterPreviewResponse | null;
}

const statusStyles: Record<AdapterPreviewStatus, string> = {
  VALID: "bg-[#d9eee2] text-[#175c38]",
  WARNING: "bg-[#fff0c7] text-[#795500]",
  INVALID: "bg-[#ffe0d7] text-[#8a351d]",
};

const issueStyles: Record<AdapterIssueSeverity, string> = {
  INFO: "border-[#b7c9d5] bg-[#edf5fa] text-[#345668]",
  WARNING: "border-[#e5c76d] bg-[#fff8df] text-[#725400]",
  ERROR: "border-[#e3a28c] bg-[#fff0eb] text-[#8a351d]",
};

function formatFieldName(fieldName: string): string {
  return fieldName.replaceAll("_", " ");
}

export function AdapterPreviewPanel({
  preview,
}: AdapterPreviewPanelProps) {
  const [visibleIssuesCount, setVisibleIssuesCount] = useState(4);
  if (!preview) {
    return (
      <aside className="rounded-3xl bg-[#183d32] p-6 text-white sm:p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#edb89f]">
          Adapter Status
        </p>

        <p className="mt-5 leading-7 text-[#d4dfda]">
          Ringkasan hasil validasi akan muncul setelah CSV diperiksa.
        </p>
      </aside>
    );
  }

  return (
    <aside className="rounded-3xl bg-[#183d32] p-6 text-white sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#edb89f]">
            Adapter Status
          </p>

          <p className="value-text mt-2 break-all text-sm text-[#d4dfda]">
            {preview.source_file_name}
          </p>
        </div>

        <span
          className={`badge-text rounded-full px-3 py-1 text-xs font-bold ${statusStyles[preview.preview_status]}`}
        >
          {preview.preview_status}
        </span>
      </div>

      <dl className="mt-6 grid grid-cols-2 gap-3">
        <SummaryItem
          label="Baris diterima"
          value={preview.summary.accepted_rows}
        />
        <SummaryItem
          label="Hari produksi"
          value={preview.summary.accepted_days}
        />
        <SummaryItem
          label="Profil diterima"
          value={preview.summary.accepted_profiles}
        />
        <SummaryItem
          label="Baris dilewati"
          value={preview.summary.skipped_rows}
        />
        <SummaryItem
          label="Peringatan"
          value={preview.summary.warning_count}
        />
        <SummaryItem
          label="Error"
          value={preview.summary.error_count}
        />
      </dl>

      {preview.required_columns_missing.length > 0 && (
        <div className="mt-6">
          <p className="text-sm font-semibold text-[#ffd0bf]">
            Kolom wajib yang belum ditemukan
          </p>

          <ul className="mt-3 flex flex-wrap gap-2">
            {preview.required_columns_missing.map((column) => (
              <li
                key={column}
                className="rounded-lg bg-white/10 px-3 py-1 text-xs text-white"
              >
                {formatFieldName(column)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {preview.issues.length > 0 && (
        <div className="mt-6 border-t border-white/20 pt-5">
          <p className="text-sm font-semibold">Temuan validasi</p>

          <ul className="mt-3 max-h-[320px] space-y-3 overflow-y-auto pr-2 custom-scrollbar">
            {preview.issues.slice(0, visibleIssuesCount).map((issue, index) => (
              <li
                key={`${issue.code}-${issue.row_number ?? "general"}-${index}`}
                className={`rounded-xl border p-3 text-sm ${issueStyles[issue.severity]}`}
              >
                <div className="flex justify-between gap-3">
                  <span className="badge-text font-bold">
                    {issue.severity}
                  </span>

                  {issue.row_number && (
                    <span className="value-text text-xs">
                      Baris {issue.row_number}
                    </span>
                  )}
                </div>

                <p className="mt-1 leading-5">{issue.message}</p>

                {issue.action && (
                  <p className="mt-2 text-xs leading-5 opacity-80">
                    Tindakan: {issue.action}
                  </p>
                )}
              </li>
            ))}
          </ul>

          {preview.issues.length > visibleIssuesCount && (
            <button
              onClick={() => setVisibleIssuesCount((prev) => prev + 10)}
              className="mt-4 flex w-full cursor-pointer items-center justify-center rounded-xl bg-white/10 px-4 py-2.5 text-xs font-medium transition-colors hover:bg-white/20"
            >
              Masih ada {preview.issues.length - visibleIssuesCount} temuan lainnya...
            </button>
          )}
        </div>
      )}

      <p className="mt-6 border-t border-white/20 pt-5 text-sm leading-6 text-[#d4dfda]">
        {preview.is_valid_for_prediction
          ? "Data dapat dilanjutkan ke proses prediksi."
          : "Data belum dapat digunakan untuk prediksi. Periksa temuan di atas."}
      </p>
    </aside>
  );
}

interface SummaryItemProps {
  label: string;
  value: number;
}

function SummaryItem({ label, value }: SummaryItemProps) {
  return (
    <div className="rounded-xl bg-white/10 p-3">
      <dt className="text-xs leading-4 text-[#b9cbc3]">{label}</dt>
      <dd className="value-text mt-1 text-xl font-semibold">{value}</dd>
    </div>
  );
}
