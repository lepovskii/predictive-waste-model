import type {
  ManualPredictionFormState,
  ManualProfileFormState,
} from "@/types/manual-prediction";
import type {
  PredictRequest,
  ProfileInput,
} from "@/types/prediction";

export const MAX_MANUAL_PROFILES = 20;

export class ManualFormValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ManualFormValidationError";
  }
}

export function createEmptyProfile(
  id: string,
): ManualProfileFormState {
  return {
    id,
    profile_name: "",

    raw_material_ton: "",
    production_ton: "",
    material_pcs: "",
    production_pcs: "",

    total_hrs: "24",
    availables_hrs: "",

    setup_time: "0",
    program_stop_min: "0",
    stand_change: "0",
    production_stop_min: "0",
    mechanic_stop_min: "0",
    electric_stop_min: "0",
    roll_shop_stop_min: "0",
    test_rolling_stop_min: "0",
    trial_rolling_stop_min: "0",
    others_stop_min: "0",
    downtime_total_min: "0",

    rolling_hot_hrs: "0",
    idle_hrs: "0",
    rolling_hrs: "0",

    gas_total_day_nm3: "0",
    kv_20: "0",
    kv_33: "0",
    electricity_total_kwh: "0",
  };
}

export function createInitialManualForm(): ManualPredictionFormState {
  return {
    production_date: "",
    estimasi_manual_class_b: "0",
    estimasi_manual_reject: "0",
    profiles: [createEmptyProfile("profile-1")],
  };
}

function parseNumber(
  value: string,
  label: string,
  options: {
    positive?: boolean;
    integer?: boolean;
  } = {},
): number {
  const normalizedValue = value.trim();

  if (!normalizedValue) {
    throw new ManualFormValidationError(
      `${label} harus diisi.`,
    );
  }

  const numericValue = Number(normalizedValue);

  if (!Number.isFinite(numericValue)) {
    throw new ManualFormValidationError(
      `${label} harus berupa angka yang valid.`,
    );
  }

  if (options.positive && numericValue <= 0) {
    throw new ManualFormValidationError(
      `${label} harus lebih besar dari 0.`,
    );
  }

  if (!options.positive && numericValue < 0) {
    throw new ManualFormValidationError(
      `${label} tidak boleh bernilai negatif.`,
    );
  }

  if (options.integer && !Number.isInteger(numericValue)) {
    throw new ManualFormValidationError(
      `${label} harus berupa bilangan bulat.`,
    );
  }

  return numericValue;
}

function buildProfilePayload(
  profile: ManualProfileFormState,
  profileIndex: number,
): ProfileInput {
  const profileLabel = `Profile ${profileIndex + 1}`;
  const profileName = profile.profile_name
    .trim()
    .replace(/\s+/g, " ");

  if (!profileName) {
    throw new ManualFormValidationError(
      `${profileLabel}: nama profile harus diisi.`,
    );
  }

  if (profileName.toLowerCase() === "shutdown") {
    throw new ManualFormValidationError(
      `${profileLabel}: Shutdown tidak dapat diprediksi.`,
    );
  }

  const totalHours = parseNumber(
    profile.total_hrs,
    `${profileLabel} - Total hours`,
    { positive: true },
  );

  const availableHours = parseNumber(
    profile.availables_hrs,
    `${profileLabel} - Available hours`,
    { positive: true },
  );

  if (availableHours > totalHours) {
    throw new ManualFormValidationError(
      `${profileLabel}: Available hours tidak boleh melebihi total hours.`,
    );
  }

  return {
    profile_name: profileName,

    raw_material_ton: parseNumber(
      profile.raw_material_ton,
      `${profileLabel} - Raw material`,
      { positive: true },
    ),

    production_ton: parseNumber(
      profile.production_ton,
      `${profileLabel} - Production ton`,
      { positive: true },
    ),

    material_pcs: parseNumber(
      profile.material_pcs,
      `${profileLabel} - Material pcs`,
      { positive: true, integer: true },
    ),

    production_pcs: parseNumber(
      profile.production_pcs,
      `${profileLabel} - Production pcs`,
      { positive: true, integer: true },
    ),

    total_hrs: totalHours,
    availables_hrs: availableHours,

    setup_time: parseNumber(
      profile.setup_time,
      `${profileLabel} - Set up time`,
    ),

    program_stop_min: parseNumber(
      profile.program_stop_min,
      `${profileLabel} - Program stop`,
    ),

    stand_change: parseNumber(
      profile.stand_change,
      `${profileLabel} - Stand change`,
    ),

    production_stop_min: parseNumber(
      profile.production_stop_min,
      `${profileLabel} - Production stop`,
    ),

    mechanic_stop_min: parseNumber(
      profile.mechanic_stop_min,
      `${profileLabel} - Mechanic stop`,
    ),

    electric_stop_min: parseNumber(
      profile.electric_stop_min,
      `${profileLabel} - Electric stop`,
    ),

    roll_shop_stop_min: parseNumber(
      profile.roll_shop_stop_min,
      `${profileLabel} - Roll shop stop`,
    ),

    test_rolling_stop_min: parseNumber(
      profile.test_rolling_stop_min,
      `${profileLabel} - Test rolling`,
    ),

    trial_rolling_stop_min: parseNumber(
      profile.trial_rolling_stop_min,
      `${profileLabel} - Trial rolling`,
    ),

    others_stop_min: parseNumber(
      profile.others_stop_min,
      `${profileLabel} - Others stop`,
    ),

    downtime_total_min: parseNumber(
      profile.downtime_total_min,
      `${profileLabel} - Total downtime`,
    ),

    rolling_hot_hrs: parseNumber(
      profile.rolling_hot_hrs,
      `${profileLabel} - Rolling hot hour`,
    ),

    idle_hrs: parseNumber(
      profile.idle_hrs,
      `${profileLabel} - Idle HMI`,
    ),

    rolling_hrs: parseNumber(
      profile.rolling_hrs,
      `${profileLabel} - Rolling HMI`,
    ),

    gas_total_day_nm3: parseNumber(
      profile.gas_total_day_nm3,
      `${profileLabel} - Gas total day`,
    ),

    kv_20: parseNumber(
      profile.kv_20,
      `${profileLabel} - KV 20`,
    ),

    kv_33: parseNumber(
      profile.kv_33,
      `${profileLabel} - KV 33`,
    ),

    electricity_total_kwh: parseNumber(
      profile.electricity_total_kwh,
      `${profileLabel} - Electricity total`,
    ),
  };
}

export function buildManualPredictionPayload(
  form: ManualPredictionFormState,
): PredictRequest {
  if (!form.production_date) {
    throw new ManualFormValidationError(
      "Tanggal produksi harus dipilih.",
    );
  }

  if (form.profiles.length === 0) {
    throw new ManualFormValidationError(
      "Minimal satu profile harus tersedia.",
    );
  }

  if (form.profiles.length > MAX_MANUAL_PROFILES) {
    throw new ManualFormValidationError(
      `Maksimal ${MAX_MANUAL_PROFILES} profile dalam satu tanggal produksi.`,
    );
  }

  const profiles = form.profiles.map(buildProfilePayload);
  const profileNames = new Set<string>();

  for (const profile of profiles) {
    const normalizedName = profile.profile_name.toLowerCase();

    if (profileNames.has(normalizedName)) {
      throw new ManualFormValidationError(
        `Profile duplikat ditemukan: ${profile.profile_name}.`,
      );
    }

    profileNames.add(normalizedName);
  }

  return {
    production_date: form.production_date,
    profiles,

    estimasi_manual_class_b: parseNumber(
      form.estimasi_manual_class_b,
      "Estimasi manual Class B",
    ),

    estimasi_manual_reject: parseNumber(
      form.estimasi_manual_reject,
      "Estimasi manual Reject",
    ),
  };
}