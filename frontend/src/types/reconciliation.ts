import type {
  DecimalValue,
  ProductionStatus,
} from "@/types/prediction";

export interface ReconcileProfileActualInput {
  profile_name: string;
  actual_wip_ton: DecimalValue;
}

export interface ReconcileItemRequest {
  production_date: string;
  actual_wip_ton: DecimalValue;
  actual_prime_ton?: DecimalValue | null;
  profiles?: ReconcileProfileActualInput[];
}

export interface ReconcileRequest {
  items: ReconcileItemRequest[];
}

export type ReconcileItemResult =
  | "RECONCILED"
  | "UNCHANGED"
  | "NOT_FOUND"
  | "REJECTED"
  | "FAILED";

export interface ReconcileItemResponse {
  production_date: string;
  result: ReconcileItemResult;

  task_id: string | null;
  status: ProductionStatus | null;

  predicted_wip_ton: DecimalValue | null;
  actual_wip_ton: DecimalValue | null;
  absolute_error_ton: DecimalValue | null;

  needs_retraining: boolean;
  message: string;
}

export interface ReconcileResponse {
  total_items: number;
  reconciled_count: number;
  unchanged_count: number;
  not_found_count: number;
  rejected_count: number;
  failed_count: number;

  results: ReconcileItemResponse[];
}