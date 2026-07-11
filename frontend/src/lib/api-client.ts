import type { AdapterPreviewResponse } from "@/types/adapter";
import type {
  PredictAcceptedResponse,
  PredictBatchRequest,
  PredictBatchResponse,
  PredictRequest,
  PredictionStatusResponse,
  PredictionHistoryQuery,
  PredictionHistoryResponse,
} from "@/types/prediction";
import type {
  ReconcileRequest,
  ReconcileResponse,
} from "@/types/reconciliation";
import type {
  AvailableModelsResponse,
  SwitchModelResponse
} from "@/types/models";

const API_BASE_PATH = "/api/backend";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function readResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_PATH}${path}`, {
    ...options,
    cache: "no-store",
  });

  const responseBody = await readResponse(response);

  if (!response.ok) {
    throw new ApiError(
      `Request gagal dengan status ${response.status}.`,
      response.status,
      responseBody,
    );
  }

  return responseBody as T;
}

export async function previewCsv(
  file: File,
): Promise<AdapterPreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return request<AdapterPreviewResponse>("/adapter/preview", {
    method: "POST",
    body: formData,
  });
}

export async function submitPrediction(
  payload: PredictRequest,
): Promise<PredictAcceptedResponse> {
  return request<PredictAcceptedResponse>("/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function submitPredictionBatch(
  payload: PredictBatchRequest,
): Promise<PredictBatchResponse> {
  return request<PredictBatchResponse>("/predict/batch", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function getPredictionStatus(
  taskId: string,
  signal?: AbortSignal,
): Promise<PredictionStatusResponse> {
  const normalizedTaskId = taskId.trim();

  if (!normalizedTaskId) {
    throw new Error("Task ID tidak boleh kosong.");
  }

  return request<PredictionStatusResponse>(
    `/status/${encodeURIComponent(normalizedTaskId)}`,
    {
      method: "GET",
      signal,
    },
  );
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function getApiErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return error instanceof Error
      ? error.message
      : "Terjadi kesalahan yang tidak diketahui.";
  }

  if (!isRecord(error.details)) {
    return error.message;
  }

  const detail = error.details.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!isRecord(item)) {
          return null;
        }

        return typeof item.msg === "string"
          ? item.msg
          : null;
      })
      .filter((message): message is string => message !== null);

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return error.message;
}

export async function getPredictionHistory(
  query: PredictionHistoryQuery = {},
  signal?: AbortSignal,
): Promise<PredictionHistoryResponse> {
  const searchParams = new URLSearchParams();

  searchParams.set("limit", String(query.limit ?? 10));
  searchParams.set("offset", String(query.offset ?? 0));

  if (query.status) {
    searchParams.set("status", query.status);
  }

  if (query.dateFrom) {
    searchParams.set("date_from", query.dateFrom);
  }

  if (query.dateTo) {
    searchParams.set("date_to", query.dateTo);
  }

  if (query.sort) {
    searchParams.set("sort", query.sort);
  }

  return request<PredictionHistoryResponse>(
    `/predictions?${searchParams.toString()}`,
    {
      method: "GET",
      signal,
    },
  );
}

export async function submitReconciliation(
  payload: ReconcileRequest,
): Promise<ReconcileResponse> {
  return request<ReconcileResponse>("/reconcile", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function getAvailableModels(
  signal?: AbortSignal,
): Promise<AvailableModelsResponse> {
  return request<AvailableModelsResponse>("/models", {
    method: "GET",
    signal,
  });
}

export async function switchActiveModel(
  artifactId: string,
): Promise<SwitchModelResponse> {
  return request<SwitchModelResponse>("/models/switch", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ artifact_id: artifactId }),
  });
}
