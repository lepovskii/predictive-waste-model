import type { Metadata } from "next";

import { PredictionDetailPage } from "@/components/prediction/prediction-detail-page";

export const metadata: Metadata = {
  title: "Detail Prediksi",
  description: "Detail hasil prediksi WIP per profile produksi.",
};

interface PredictionDetailRouteProps {
  params: Promise<{
    taskId: string;
  }>;
}

export default async function PredictionDetailRoute({
  params,
}: PredictionDetailRouteProps) {
  const { taskId } = await params;

  return <PredictionDetailPage taskId={taskId} />;
}