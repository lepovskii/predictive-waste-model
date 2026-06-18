import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="rounded-3xl border border-dashed border-[#c9c5ba] bg-white/60 px-6 py-16 text-center">
      <p className="text-lg font-semibold text-[#173a30]">
        {title}
      </p>

      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#66736d]">
        {description}
      </p>

      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}