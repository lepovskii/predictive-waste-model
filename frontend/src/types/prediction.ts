export type DecimalValue = string | number;

export type ProductionStatus =
  | "PROCESSING"
  | "DRAFT"
  | "ANOMALY"
  | "FAILED"
  | "RECONCILED";

export interface ProfileInput {
  profile_name: string;

  raw_material_ton: DecimalValue;
  production_ton: DecimalValue;
  material_pcs: number;
  production_pcs: number;

  total_hrs: DecimalValue;
  availables_hrs: DecimalValue;

  setup_time: DecimalValue;
  program_stop_min: DecimalValue;
  stand_change: DecimalValue;
  production_stop_min: DecimalValue;
  mechanic_stop_min: DecimalValue;
  electric_stop_min: DecimalValue;
  roll_shop_stop_min: DecimalValue;
  test_rolling_stop_min: DecimalValue;
  trial_rolling_stop_min: DecimalValue;
  others_stop_min: DecimalValue;
  downtime_total_min: DecimalValue;

  rolling_hot_hrs: DecimalValue;
  idle_hrs: DecimalValue;
  rolling_hrs: DecimalValue;

  gas_total_day_nm3: DecimalValue;
  kv_20: DecimalValue;
  kv_33: DecimalValue;
  electricity_total_kwh: DecimalValue;
}

export interface PredictRequest {
  production_date: string;
  profiles: ProfileInput[];
  estimasi_manual_class_b: DecimalValue;
  estimasi_manual_reject: DecimalValue;
}

export interface ProfileAcceptedResponse {
  detail_seq: number;
  profile_name: string;
  production_ton: DecimalValue;
}

export interface PredictAcceptedResponse {
  task_id: string;
  status: ProductionStatus;
  production_date: string;
  profile_count: number;
  total_output_ton: DecimalValue;
  profiles: ProfileAcceptedResponse[];
  message: string;
}

export interface PredictBatchRequest {
  items: PredictRequest[];
}

export type BatchItemResult = "ACCEPTED" | "DUPLICATE" | "FAILED";

export interface PredictBatchItemResponse {
  production_date: string;
  result: BatchItemResult;
  task_id: string | null;
  status: ProductionStatus | null;
  profile_count: number | null;
  total_output_ton: DecimalValue | null;
  message: string;
}

export interface PredictBatchResponse {
  total_items: number;
  accepted_count: number;
  duplicate_count: number;
  failed_count: number;
  results: PredictBatchItemResponse[];
}

export interface ProfilePredictionStatus {
  detail_seq: number;
  profile_name: string;
  production_ton: DecimalValue;
  predicted_wip_ton: DecimalValue | null;
  actual_wip_ton: DecimalValue | null;
}

export interface PredictionStatusResponse {
  task_id: string | null;
  status: ProductionStatus;
  production_date: string;

  total_output_ton: DecimalValue;
  estimasi_wip_total: DecimalValue | null;
  estimasi_manual_class_b: DecimalValue;
  estimasi_manual_reject: DecimalValue;
  estimasi_prime: DecimalValue | null;

  aktual_wip: DecimalValue | null;
  aktual_prime: DecimalValue | null;
  needs_retraining: boolean;

  profiles: ProfilePredictionStatus[];

  created_at: string;
  updated_at: string;
}

export interface PredictionHistoryItem {
  task_id: string | null;
  status: ProductionStatus;
  production_date: string;

  profile_count: number;
  total_output_ton: DecimalValue;
  estimasi_wip_total: DecimalValue | null;
  estimasi_prime: DecimalValue | null;

  needs_retraining: boolean;

  created_at: string;
  updated_at: string;
}

export interface PredictionHistoryResponse {
  total: number;
  limit: number;
  offset: number;
  items: PredictionHistoryItem[];
}

export interface PredictionHistoryQuery {
  limit?: number;
  offset?: number;
  status?: ProductionStatus | "";
  dateFrom?: string;
  dateTo?: string;
}