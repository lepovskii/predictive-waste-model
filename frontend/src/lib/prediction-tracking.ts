import type {
  PredictAcceptedResponse,
  PredictBatchResponse,
} from "@/types/prediction";

export function createSinglePredictionTracking(
  response: PredictAcceptedResponse,
): PredictBatchResponse {
  return {
    total_items: 1,
    accepted_count: 1,
    duplicate_count: 0,
    failed_count: 0,
    results: [
      {
        production_date: response.production_date,
        result: "ACCEPTED",
        task_id: response.task_id,
        status: response.status,
        profile_count: response.profile_count,
        total_output_ton: response.total_output_ton,
        message: response.message,
      },
    ],
  };
}