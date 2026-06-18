import type { ManualProfileFormState } from "@/types/manual-prediction";

interface ManualProfileFormProps {
  profile: ManualProfileFormState;
  profileIndex: number;
  canRemove: boolean;
  disabled: boolean;
  onChange: (
    profileId: string,
    field: keyof ManualProfileFormState,
    value: string,
  ) => void;
  onRemove: (profileId: string) => void;
}

interface FieldDefinition {
  field: keyof ManualProfileFormState;
  label: string;
  unit?: string;
  required?: boolean;
  step?: string;
}

const productionFields: FieldDefinition[] = [
  {
    field: "raw_material_ton",
    label: "Raw material",
    unit: "ton",
    required: true,
  },
  {
    field: "production_ton",
    label: "Production",
    unit: "ton",
    required: true,
  },
  {
    field: "material_pcs",
    label: "Material",
    unit: "pcs",
    required: true,
    step: "1",
  },
  {
    field: "production_pcs",
    label: "Production",
    unit: "pcs",
    required: true,
    step: "1",
  },
];

const timeFields: FieldDefinition[] = [
  {
    field: "total_hrs",
    label: "Total hours",
    unit: "jam",
    required: true,
  },
  {
    field: "availables_hrs",
    label: "Available hours",
    unit: "jam",
    required: true,
  },
  {
    field: "rolling_hot_hrs",
    label: "Rolling hot hour",
    unit: "jam",
  },
];

const downtimeFields: FieldDefinition[] = [
  { field: "setup_time", label: "Set up time" },
  { field: "program_stop_min", label: "Program stop" },
  { field: "stand_change", label: "Stand change" },
  { field: "production_stop_min", label: "Production stop" },
  { field: "mechanic_stop_min", label: "Mechanic" },
  { field: "electric_stop_min", label: "Electric" },
  { field: "roll_shop_stop_min", label: "Roll shop" },
  { field: "test_rolling_stop_min", label: "Test rolling" },
  { field: "trial_rolling_stop_min", label: "Trial rolling" },
  { field: "others_stop_min", label: "Others" },
  {
    field: "downtime_total_min",
    label: "Total downtime",
  },
];

const gasFields: FieldDefinition[] = [
  {
    field: "idle_hrs",
    label: "Idle hour HMI / CP1",
    unit: "Nm3",
  },
  {
    field: "rolling_hrs",
    label: "Rolling hour HMI / CP1",
    unit: "Nm3",
  },
  {
    field: "gas_total_day_nm3",
    label: "Gas total day",
    unit: "Nm3",
  },
];

const electricityFields: FieldDefinition[] = [
  {
    field: "kv_20",
    label: "KV 20",
    unit: "kWh",
  },
  {
    field: "kv_33",
    label: "KV 33",
    unit: "kWh",
  },
  {
    field: "electricity_total_kwh",
    label: "Electricity total",
    unit: "kWh",
  },
];

export function ManualProfileForm({
  profile,
  profileIndex,
  canRemove,
  disabled,
  onChange,
  onRemove,
}: ManualProfileFormProps) {
  return (
    <article className="rounded-3xl border border-[#d7d2c5] bg-white shadow-[0_18px_45px_rgba(32,45,38,0.06)]">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#e5e1d7] px-6 py-5">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-[#c65331]">
            Profile {String(profileIndex + 1).padStart(2, "0")}
          </p>

          <h2 className="mt-1 text-xl font-semibold text-[#173a30]">
            {profile.profile_name.trim() || "Profile produksi baru"}
          </h2>
        </div>

        <button
          type="button"
          onClick={() => onRemove(profile.id)}
          disabled={!canRemove || disabled}
          className="rounded-lg border border-[#dfb6a8] px-3 py-2 text-xs font-semibold text-[#a34226] transition hover:bg-[#fff0eb] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Hapus profile
        </button>
      </header>

      <div className="space-y-8 p-6">
        <section>
          <SectionHeading
            title="Identitas dan produksi"
            description="Data utama profile dan hasil proses produksi."
          />

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <TextField
              id={`${profile.id}-profile-name`}
              label="Profile name"
              value={profile.profile_name}
              required
              disabled={disabled}
              placeholder="Contoh: IWF 250x125"
              className="sm:col-span-2 lg:col-span-4"
              onChange={(value) =>
                onChange(profile.id, "profile_name", value)
              }
            />

            {productionFields.map((definition) => (
              <NumberField
                key={definition.field}
                profile={profile}
                definition={definition}
                disabled={disabled}
                onChange={onChange}
              />
            ))}
          </div>
        </section>

        <section>
          <SectionHeading
            title="Waktu produksi"
            description="Jam kerja dan waktu rolling pada profile ini."
          />

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {timeFields.map((definition) => (
              <NumberField
                key={definition.field}
                profile={profile}
                definition={definition}
                disabled={disabled}
                onChange={onChange}
              />
            ))}
          </div>
        </section>

        <details className="group rounded-2xl border border-[#dedbd1] bg-[#faf9f5]">
          <summary className="cursor-pointer list-none px-5 py-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h3 className="font-semibold text-[#173a30]">
                  Downtime
                </h3>
                <p className="mt-1 text-sm text-[#66736d]">
                  Rincian penghentian produksi dalam menit.
                </p>
              </div>

              <span className="font-mono text-xl text-[#c65331] transition group-open:rotate-45">
                +
              </span>
            </div>
          </summary>

          <div className="grid gap-4 border-t border-[#dedbd1] p-5 sm:grid-cols-2 lg:grid-cols-4">
            {downtimeFields.map((definition) => (
              <NumberField
                key={definition.field}
                profile={profile}
                definition={{
                  ...definition,
                  unit: "menit",
                }}
                disabled={disabled}
                onChange={onChange}
              />
            ))}
          </div>
        </details>

        <section>
          <SectionHeading
            title="Konsumsi proses"
            description="Gas dan listrik yang tercatat selama produksi."
          />

          <div className="mt-4 grid gap-6 xl:grid-cols-2">
            <FieldGroup title="Gas consumption">
              {gasFields.map((definition) => (
                <NumberField
                  key={definition.field}
                  profile={profile}
                  definition={definition}
                  disabled={disabled}
                  onChange={onChange}
                />
              ))}
            </FieldGroup>

            <FieldGroup title="Electrical consumption">
              {electricityFields.map((definition) => (
                <NumberField
                  key={definition.field}
                  profile={profile}
                  definition={definition}
                  disabled={disabled}
                  onChange={onChange}
                />
              ))}
            </FieldGroup>
          </div>
        </section>
      </div>
    </article>
  );
}

interface NumberFieldProps {
  profile: ManualProfileFormState;
  definition: FieldDefinition;
  disabled: boolean;
  onChange: ManualProfileFormProps["onChange"];
}

function NumberField({
  profile,
  definition,
  disabled,
  onChange,
}: NumberFieldProps) {
  const inputId = `${profile.id}-${definition.field}`;

  return (
    <label htmlFor={inputId} className="block">
      <span className="flex items-center justify-between gap-2 text-sm font-medium text-[#33473e]">
        {definition.label}

        {definition.unit && (
          <span className="text-xs font-normal text-[#78847e]">
            {definition.unit}
          </span>
        )}
      </span>

      <input
        id={inputId}
        type="number"
        min="0"
        step={definition.step ?? "any"}
        required={definition.required}
        disabled={disabled}
        value={profile[definition.field]}
        onChange={(event) =>
          onChange(
            profile.id,
            definition.field,
            event.target.value,
          )
        }
        className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-white px-3 py-2.5 text-[#182b23] outline-none transition placeholder:text-[#a1aaa5] focus:border-[#c65331] focus:ring-4 focus:ring-[#c65331]/10 disabled:cursor-not-allowed disabled:bg-[#efeee8]"
      />
    </label>
  );
}

interface TextFieldProps {
  id: string;
  label: string;
  value: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  onChange: (value: string) => void;
}

function TextField({
  id,
  label,
  value,
  placeholder,
  required = false,
  disabled = false,
  className,
  onChange,
}: TextFieldProps) {
  return (
    <label htmlFor={id} className={className}>
      <span className="text-sm font-medium text-[#33473e]">
        {label}
      </span>

      <input
        id={id}
        type="text"
        value={value}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        maxLength={120}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-xl border border-[#cfd5d1] bg-white px-3 py-2.5 text-[#182b23] outline-none transition placeholder:text-[#a1aaa5] focus:border-[#c65331] focus:ring-4 focus:ring-[#c65331]/10 disabled:cursor-not-allowed disabled:bg-[#efeee8]"
      />
    </label>
  );
}

interface SectionHeadingProps {
  title: string;
  description: string;
}

function SectionHeading({
  title,
  description,
}: SectionHeadingProps) {
  return (
    <div>
      <h3 className="font-semibold text-[#173a30]">{title}</h3>
      <p className="mt-1 text-sm text-[#66736d]">{description}</p>
    </div>
  );
}

interface FieldGroupProps {
  title: string;
  children: React.ReactNode;
}

function FieldGroup({ title, children }: FieldGroupProps) {
  return (
    <div className="rounded-2xl border border-[#dedbd1] bg-[#faf9f5] p-5">
      <h3 className="font-semibold text-[#173a30]">{title}</h3>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {children}
      </div>
    </div>
  );
}