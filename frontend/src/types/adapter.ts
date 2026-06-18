import type { PredictRequest } from "@/types/prediction";

export type AdapterPreviewStatus = "VALID" | "WARNING" | "INVALID";

export type AdapterIssueSeverity = "INFO" | "WARNING" | "ERROR";

export interface AdapterSummary {
  raw_rows: number;
  candidate_rows: number;
  accepted_rows: number;
  skipped_rows: number;
  accepted_days: number;
  accepted_profiles: number;
  warning_count: number;
  error_count: number;
}

export interface AdapterIssue {
  severity: AdapterIssueSeverity;
  code: string;
  message: string;
  row_number: number | null;
  column_name: string | null;
  raw_value: string | null;
  action: string | null;
}

export interface AdapterPreviewResponse {
  contract_version: string;
  source_file_name: string;
  detected_format: string;
  preview_status: AdapterPreviewStatus;
  is_valid_for_prediction: boolean;
  summary: AdapterSummary;
  normalized_payloads: PredictRequest[];
  issues: AdapterIssue[];
  required_columns_missing: string[];
  ignored_columns: string[];
}