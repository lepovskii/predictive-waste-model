import type { DecimalValue } from "@/types/prediction";

const decimalFormatter = new Intl.NumberFormat("id-ID", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const dateTimeFormatter = new Intl.DateTimeFormat("id-ID", {
  dateStyle: "medium",
  timeStyle: "short",
});

export function formatTon(
  value: DecimalValue | null,
): string {
  if (value === null) {
    return "-";
  }

  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return String(value);
  }

  return `${decimalFormatter.format(numericValue)} ton`;
}

export function formatWipPercentage(
  predictedWip: DecimalValue | null,
  productionTon: DecimalValue,
): string {
  if (predictedWip === null) {
    return "-";
  }

  const predictedValue = Number(predictedWip);
  const productionValue = Number(productionTon);

  if (
    !Number.isFinite(predictedValue) ||
    !Number.isFinite(productionValue) ||
    productionValue <= 0
  ) {
    return "-";
  }

  const percentage =
    (predictedValue / productionValue) * 100;

  return `${decimalFormatter.format(percentage)}%`;
}

export function formatDateTime(
  value: string,
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return dateTimeFormatter.format(date);
}

const dateFormatter = new Intl.DateTimeFormat("id-ID", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

export function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return dateFormatter.format(date);
}