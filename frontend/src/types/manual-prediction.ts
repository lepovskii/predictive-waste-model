export interface ManualProfileFormState {
  id: string;
  profile_name: string;

  raw_material_ton: string;
  production_ton: string;
  material_pcs: string;
  production_pcs: string;

  total_hrs: string;
  availables_hrs: string;

  setup_time: string;
  program_stop_min: string;
  stand_change: string;
  production_stop_min: string;
  mechanic_stop_min: string;
  electric_stop_min: string;
  roll_shop_stop_min: string;
  test_rolling_stop_min: string;
  trial_rolling_stop_min: string;
  others_stop_min: string;
  downtime_total_min: string;

  rolling_hot_hrs: string;
  idle_hrs: string;
  rolling_hrs: string;

  gas_total_day_nm3: string;
  kv_20: string;
  kv_33: string;
  electricity_total_kwh: string;
}

export interface ManualPredictionFormState {
  production_date: string;
  estimasi_manual_class_b: string;
  estimasi_manual_reject: string;
  profiles: ManualProfileFormState[];
}