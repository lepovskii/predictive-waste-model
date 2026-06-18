import {
  formatDateTime,
  formatTon,
  formatWipPercentage,
} from "@/lib/formatters";
import type { PredictionStatusResponse } from "@/types/prediction";

interface ProfilePredictionDetailsProps {
  prediction: PredictionStatusResponse;
}

export function ProfilePredictionDetails({
  prediction,
}: ProfilePredictionDetailsProps) {
  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-[#183d32]">
            Prediksi per profile
          </h3>

          <p className="value-text mt-1 text-xs text-[#65736d]">
            Task ID: {prediction.task_id ?? "-"}
          </p>
        </div>

        <p className="value-text text-xs text-[#65736d]">
          Diperbarui: {formatDateTime(prediction.updated_at)}
        </p>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[680px] text-left text-sm">
          <thead>
            <tr className="border-b border-[#d7d2c5] text-xs uppercase tracking-wider text-[#65736d]">
              <th className="px-3 py-3 font-semibold">Profile</th>
              <th className="px-3 py-3 font-semibold">Produksi</th>
              <th className="px-3 py-3 font-semibold">Estimasi WIP</th>
              <th className="px-3 py-3 font-semibold">Proporsi WIP</th>
              <th className="px-3 py-3 font-semibold">Aktual WIP</th>
            </tr>
          </thead>

          <tbody>
            {prediction.profiles.map((profile) => (
              <tr
                key={profile.detail_seq}
                className="border-b border-[#e4e2d9]"
              >
                <td className="px-3 py-3 font-semibold text-[#263a32]">
                  {profile.profile_name}
                </td>

                <td className="value-text px-3 py-3">
                  {formatTon(profile.production_ton)}
                </td>

                <td className="value-text px-3 py-3 font-semibold text-[#ba4f2c]">
                  {formatTon(profile.predicted_wip_ton)}
                </td>

                <td className="value-text px-3 py-3">
                  {formatWipPercentage(
                    profile.predicted_wip_ton,
                    profile.production_ton,
                  )}
                </td>

                <td className="value-text px-3 py-3 text-[#65736d]">
                  {profile.actual_wip_ton === null
                    ? "Belum tersedia"
                    : formatTon(profile.actual_wip_ton)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
