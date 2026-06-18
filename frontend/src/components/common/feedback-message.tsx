import type { ReactNode } from "react";

type FeedbackVariant =
  | "info"
  | "success"
  | "warning"
  | "error";

interface FeedbackMessageProps {
  variant: FeedbackVariant;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}

const variantStyles: Record<FeedbackVariant, string> = {
  info: "border-[#b9d3e1] bg-[#edf7fc] text-[#275f7a]",
  success: "border-[#9ecdb3] bg-[#effaf3] text-[#175c38]",
  warning: "border-[#dfc98d] bg-[#fff8df] text-[#674e0b]",
  error: "border-[#e3a28c] bg-[#fff0eb] text-[#8a351d]",
};

export function FeedbackMessage({
  variant,
  title,
  children,
  action,
}: FeedbackMessageProps) {
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={`rounded-2xl border px-5 py-4 text-sm ${variantStyles[variant]}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="font-semibold">{title}</p>

          {children && (
            <div className="mt-1 leading-6">
              {children}
            </div>
          )}
        </div>

        {action && <div>{action}</div>}
      </div>
    </div>
  );
}