"use client";

import { useEffect, useState } from "react";

import { getPredictionStatus } from "@/lib/api-client";
import type {
  PredictBatchResponse,
  PredictionStatusResponse,
} from "@/types/prediction";

const POLLING_DELAYS_MS = [500, 1000, 2000, 4000];
const MAX_POLLING_DURATION_MS = 11 * 60 * 1000;
const MAX_CONSECUTIVE_FAILURES = 5;

export type PollingPhase =
  | "POLLING"
  | "COMPLETE"
  | "ERROR"
  | "TIMEOUT";

export interface PollingItem {
  taskId: string;
  productionDate: string;
  phase: PollingPhase;
  data: PredictionStatusResponse | null;
  errorMessage: string | null;
  consecutiveFailures: number;
}

interface PredictionPollingResult {
  items: PollingItem[];
  completedCount: number;
  processingCount: number;
  problemCount: number;
  resolvedCount: number;
  progressPercentage: number;
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Tidak dapat mengambil status prediksi.";
}

function createPollingItems(
  batchResult: PredictBatchResponse,
): PollingItem[] {
  return batchResult.results
    .filter(
      (item) =>
        item.result === "ACCEPTED" &&
        item.task_id !== null,
    )
    .map((item) => ({
      taskId: item.task_id as string,
      productionDate: item.production_date,
      phase: "POLLING",
      data: null,
      errorMessage: null,
      consecutiveFailures: 0,
    }));
}

export function usePredictionPolling(
  batchResult: PredictBatchResponse,
): PredictionPollingResult {
  const [items, setItems] = useState<PollingItem[]>(() =>
    createPollingItems(batchResult),
  );

  useEffect(() => {
    const initialItems = createPollingItems(batchResult);

    const tracker = new Map(
      initialItems.map((item) => [item.taskId, item]),
    );

    if (tracker.size === 0) {
      return;
    }

    let cancelled = false;
    const controller = new AbortController();

    function publishItems() {
      if (!cancelled) {
        setItems(Array.from(tracker.values()));
      }
    }

    async function runPolling() {
      const startedAt = Date.now();
      let delayIndex = 0;

      while (!cancelled) {
        const pendingItems = Array.from(
          tracker.values(),
        ).filter((item) => item.phase === "POLLING");

        if (pendingItems.length === 0) {
          return;
        }

        if (
          Date.now() - startedAt >=
          MAX_POLLING_DURATION_MS
        ) {
          for (const item of pendingItems) {
            tracker.set(item.taskId, {
              ...item,
              phase: "TIMEOUT",
              errorMessage:
                "Waktu tunggu frontend berakhir. Task mungkin masih diproses oleh backend.",
            });
          }

          publishItems();
          return;
        }

        const requests = pendingItems.map((item) =>
          getPredictionStatus(
            item.taskId,
            controller.signal,
          ),
        );

        const results =
          await Promise.allSettled(requests);

        if (cancelled) {
          return;
        }

        results.forEach((result, index) => {
          const currentItem = pendingItems[index];

          if (result.status === "fulfilled") {
            const prediction = result.value;

            tracker.set(currentItem.taskId, {
              ...currentItem,
              phase:
                prediction.status === "PROCESSING"
                  ? "POLLING"
                  : "COMPLETE",
              data: prediction,
              errorMessage: null,
              consecutiveFailures: 0,
            });

            return;
          }

          const failureCount =
            currentItem.consecutiveFailures + 1;

          tracker.set(currentItem.taskId, {
            ...currentItem,
            phase:
              failureCount >= MAX_CONSECUTIVE_FAILURES
                ? "ERROR"
                : "POLLING",
            errorMessage:
              failureCount >= MAX_CONSECUTIVE_FAILURES
                ? getErrorMessage(result.reason)
                : "Koneksi terganggu. Sistem akan mencoba kembali.",
            consecutiveFailures: failureCount,
          });
        });

        publishItems();

        const stillProcessing = Array.from(
          tracker.values(),
        ).some((item) => item.phase === "POLLING");

        if (!stillProcessing) {
          return;
        }

        const delay =
          POLLING_DELAYS_MS[
            Math.min(
              delayIndex,
              POLLING_DELAYS_MS.length - 1,
            )
          ];

        delayIndex += 1;
        await wait(delay);
      }
    }

    void runPolling();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [batchResult]);

  const completedCount = items.filter(
    (item) => item.phase === "COMPLETE",
  ).length;

  const processingCount = items.filter(
    (item) => item.phase === "POLLING",
  ).length;

  const problemCount = items.filter(
    (item) =>
      item.phase === "ERROR" ||
      item.phase === "TIMEOUT",
  ).length;

  const resolvedCount =
    completedCount + problemCount;

  const progressPercentage =
    items.length === 0
      ? 0
      : Math.round(
          (resolvedCount / items.length) * 100,
        );

  return {
    items,
    completedCount,
    processingCount,
    problemCount,
    resolvedCount,
    progressPercentage,
  };
}