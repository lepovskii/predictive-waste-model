interface LoadingCardProps {
  message?: string;
}

export function LoadingCard({
  message = "Memuat data...",
}: LoadingCardProps) {
  return (
    <div className="rounded-3xl border border-[#d7d2c5] bg-white px-6 py-16 text-center text-[#66736d]">
      <div className="mx-auto mb-4 size-8 animate-spin rounded-full border-2 border-[#d7d2c5] border-t-[#c65331]" />

      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}