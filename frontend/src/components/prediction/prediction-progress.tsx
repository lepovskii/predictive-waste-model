interface PredictionProgressProps {
  totalCount: number;
  completedCount: number;
  processingCount: number;
  problemCount: number;
  resolvedCount: number;
  progressPercentage: number;
}

export function PredictionProgress({
  totalCount,
  completedCount,
  processingCount,
  problemCount,
  resolvedCount,
  progressPercentage,
}: PredictionProgressProps) {
  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#ba4f2c]">
            Prediction Results
          </p>

          <h2 className="mt-2 text-2xl font-semibold text-[#15251f]">
            Hasil prediksi WIP
          </h2>

          <p className="value-text mt-2 text-sm text-[#65736d]">
            {resolvedCount} dari {totalCount} prediksi telah selesai.
          </p>
        </div>

        <div className="flex flex-wrap gap-3 text-sm">
          <span className="badge-text rounded-full bg-[#dceaf4] px-3 py-1 text-[#275f7a]">
            Diproses: {processingCount}
          </span>

          <span className="badge-text rounded-full bg-[#d9eee2] px-3 py-1 text-[#175c38]">
            Selesai: {completedCount}
          </span>

          {problemCount > 0 && (
            <span className="badge-text rounded-full bg-[#ffe0d7] px-3 py-1 text-[#8a351d]">
              Bermasalah: {problemCount}
            </span>
          )}
        </div>
      </div>

      <div
        className="mt-6 h-2 overflow-hidden rounded-full bg-[#e5e6df]"
        role="progressbar"
        aria-label="Progress prediksi"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progressPercentage}
      >
        <div
          className="h-full rounded-full bg-[#ba4f2c] transition-all duration-500"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>
    </>
  );
}
