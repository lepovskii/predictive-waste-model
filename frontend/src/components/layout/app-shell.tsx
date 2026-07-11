import type { ReactNode } from "react";

import { AppNavigation } from "@/components/layout/app-navigation";
import { ActiveModelBadge } from "@/components/layout/active-model-badge";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[#f1eee5] text-[#16241f]">
      <AppNavigation />

      <div className="relative lg:pl-72">
        <div
          aria-hidden="true"
          className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_85%_5%,rgba(198,83,49,0.09),transparent_30%),linear-gradient(rgba(23,58,48,0.025)_1px,transparent_1px),linear-gradient(90deg,rgba(23,58,48,0.025)_1px,transparent_1px)] bg-[size:auto,32px_32px,32px_32px] lg:left-72"
        />

        <header className="sticky top-0 z-20 hidden h-16 items-center justify-between border-b border-[#d8d3c7] bg-[#f5f2e9]/90 px-10 backdrop-blur lg:flex">
          <p className="text-sm font-medium text-[#586861]">
            Production intelligence workspace
          </p>

          <ActiveModelBadge />
        </header>

        <main className="relative mx-auto min-h-screen max-w-[1600px] px-4 py-6 sm:px-8 lg:px-10 lg:py-10">
          {children}
        </main>
      </div>
    </div>
  );
}