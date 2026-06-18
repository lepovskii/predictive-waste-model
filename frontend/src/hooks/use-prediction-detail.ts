"use client";

import { useCallback, useEffect, useState } from "react";

import {
  getApiErrorMessage,
  getPredictionStatus,
} from "@/lib/api-client";
import type { PredictionStatusResponse } from "@/types/prediction";

const POLLING_INTERVAL_MS = 2000;

export function usePredictionDetail(taskId: string) {
  const [prediction, setPrediction] =
    useState<PredictionStatusResponse | null>(null);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(() => {
    setRefreshKey((current) => current + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let timeoutId: number | undefined;

    async function loadPrediction() {
      try {
        const result = await getPredictionStatus(
          taskId,
          controller.signal,
        );

        if (controller.signal.aborted) {
          return;
        }

        setPrediction(result);
        setErrorMessage(null);
        setIsLoading(false);

        if (result.status === "PROCESSING") {
          timeoutId = window.setTimeout(
            loadPrediction,
            POLLING_INTERVAL_MS,
          );
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setErrorMessage(getApiErrorMessage(error));
          setIsLoading(false);
        }
      }
    }

    void loadPrediction();

    return () => {
      controller.abort();

      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [taskId, refreshKey]);

  return {
    prediction,
    errorMessage,
    isLoading,
    refresh,
  };
}