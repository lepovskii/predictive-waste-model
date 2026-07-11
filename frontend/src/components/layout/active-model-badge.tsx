"use client";

import { useEffect, useState } from "react";
import { getAvailableModels } from "@/lib/api-client";

import Link from "next/link";

export function ActiveModelBadge() {
    const [activeModelName, setActiveModelName] = useState<string>("Loading...");

    useEffect(() => {
        getAvailableModels()
            .then((res) => {
                const active = res.models.find(m => m.is_active);
                if (active) setActiveModelName(active.folder_name);
            })
            .catch(() => setActiveModelName("WIP Model"));
    }, []);

    return (
        <Link 
            href="/models"
            className="block rounded-full border border-[#c8cfc9] bg-white/70 px-3 py-1 text-xs font-semibold text-[#42574e] transition-colors hover:bg-white hover:border-[#173a30] hover:text-[#173a30] shadow-sm"
        >
            Model: {activeModelName}
        </Link>
    );
}
