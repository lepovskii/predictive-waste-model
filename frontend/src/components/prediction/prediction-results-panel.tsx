"use client";

import { PredictionDisclaimer } from "@/components/prediction/prediction-disclaimer";
import { PredictionProgress } from "@/components/prediction/prediction-progress";
import { PredictionResultsTable } from "@/components/prediction/prediction-results-table";
import { usePredictionPolling } from "@/hooks/use-prediction-polling";
import type { PredictBatchResponse } from "@/types/prediction";

interface PredictionResultsPanelProps {
  batchResult: PredictBatchResponse;
}

export function PredictionResultsPanel({
  batchResult,
}: PredictionResultsPanelProps) {
  const {
    items,
    completedCount,
    processingCount,
    problemCount,
    resolvedCount,
    progressPercentage,
  } = usePredictionPolling(batchResult);

  if (items.length === 0) {
    return null;
  }

  return (
    <section className="rounded-3xl border border-[#d7d2c5] bg-white p-6 shadow-[0_20px_50px_rgba(32,45,38,0.07)] sm:p-8">
      <PredictionProgress
        totalCount={items.length}
        completedCount={completedCount}
        processingCount={processingCount}
        problemCount={problemCount}
        resolvedCount={resolvedCount}
        progressPercentage={progressPercentage}
      />

      <PredictionResultsTable items={items} />

      <PredictionDisclaimer />
    </section>
  );
}