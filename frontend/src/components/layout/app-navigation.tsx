"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigationItems = [
  {
    number: "01",
    label: "Overview",
    description: "Ringkasan sistem",
    href: "/",
  },
  {
    number: "02",
    label: "Upload CSV",
    description: "Adapter dan batch prediction",
    href: "/upload",
  },
  {
    number: "03",
    label: "Input Manual",
    description: "Prediksi satu hari produksi",
    href: "/manual",
  },
  {
    number: "04",
    label: "Hasil Prediksi",
    description: "Riwayat dan status prediksi",
    href: "/predictions",
  },
];

function isActivePath(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname.startsWith(href);
}

export function AppNavigation() {
  const pathname = usePathname();

  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 flex-col border-r border-white/10 bg-[#173a30] text-white lg:flex">
        <div className="border-b border-white/10 px-7 py-7">
          <Link href="/" className="block">
            <div className="flex items-center gap-3">
              <span className="flex size-11 items-center justify-center rounded-xl bg-[#c65331] font-mono text-sm font-semibold">
                PW
              </span>

              <div>
                <p className="font-semibold tracking-tight">
                  Predictive Waste
                </p>
                <p className="mt-0.5 text-xs text-[#aec4bb]">
                  Production quality system
                </p>
              </div>
            </div>
          </Link>
        </div>

        <nav aria-label="Navigasi utama" className="flex-1 px-4 py-6">
          <ul className="space-y-2">
            {navigationItems.map((item) => {
              const active = isActivePath(pathname, item.href);

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`group flex gap-4 rounded-2xl px-4 py-3 transition ${
                      active
                        ? "bg-white text-[#173a30]"
                        : "text-[#d8e3de] hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    <span
                      className={`pt-0.5 font-mono text-xs ${
                        active ? "text-[#c65331]" : "text-[#87a499]"
                      }`}
                    >
                      {item.number}
                    </span>

                    <span>
                      <span className="block text-sm font-semibold">
                        {item.label}
                      </span>

                      <span
                        className={`mt-1 block text-xs ${
                          active ? "text-[#60736b]" : "text-[#87a499]"
                        }`}
                      >
                        {item.description}
                      </span>
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="border-t border-white/10 px-7 py-6">
          <p className="text-xs uppercase tracking-[0.18em] text-[#87a499]">
            Model Aktif
          </p>
          <p className="mt-2 text-sm font-semibold">
            Extra Trees - WIP Ton
          </p>
        </div>
      </aside>

      <header className="sticky top-0 z-30 border-b border-[#d8d3c7] bg-[#f5f2e9]/95 px-4 py-3 backdrop-blur lg:hidden">
        <div className="space-y-3">
          <Link href="/" className="block font-semibold text-[#173a30]">
            Predictive Waste
          </Link>

          <nav
            aria-label="Navigasi mobile"
            className="-mx-1 flex gap-1 overflow-x-auto px-1 pb-1"
          >
            {navigationItems.map((item) => {
              const active = isActivePath(pathname, item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`whitespace-nowrap rounded-lg px-3 py-2 text-xs font-semibold ${
                    active
                      ? "bg-[#173a30] text-white"
                      : "text-[#5e6d66]"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
    </>
  );
}