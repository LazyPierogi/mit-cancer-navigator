"use client";

import { useEffect, useState } from "react";

type VersionBadgeProps = {
  productVersion: string;
  uiVersion: string;
  buildLabel: string;
};

type ApiVersionPayload = {
  backendVersion: string;
  productVersion: string;
  buildLabel: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export function VersionBadge({ productVersion, uiVersion, buildLabel }: VersionBadgeProps) {
  const [backendVersion, setBackendVersion] = useState<string>("checking");
  const [backendState, setBackendState] = useState<"checking" | "ok" | "offline">("checking");

  useEffect(() => {
    let cancelled = false;

    async function loadBackendVersion() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/meta/version`, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const payload = (await response.json()) as ApiVersionPayload;
        if (!cancelled) {
          setBackendVersion(payload.backendVersion);
          setBackendState("ok");
        }
      } catch {
        if (!cancelled) {
          setBackendVersion("offline");
          setBackendState("offline");
        }
      }
    }

    loadBackendVersion();
    return () => {
      cancelled = true;
    };
  }, []);

  const backendBadgeClass =
    backendState === "ok"
      ? "text-[#DCE9E1] border-white/10"
      : backendState === "checking"
        ? "text-[#E8D7B8] border-white/10"
        : "text-[#F0C0B8] border-[#A63D2F]/40";

  return (
    <div className="flex flex-wrap items-center justify-end gap-2 text-[10px] font-bold uppercase tracking-[0.18em]">
      <span className="px-3 py-1 rounded-full border border-white/10 text-[#DCE9E1]">
        Product v{productVersion}
      </span>
      <span className="px-3 py-1 rounded-full border border-white/10 text-[#DCE9E1]">
        UI v{uiVersion}
      </span>
      <span className={`px-3 py-1 rounded-full border ${backendBadgeClass}`}>
        API {backendVersion === "checking" ? "checking" : `v${backendVersion}`}
      </span>
      <span className="px-3 py-1 rounded-full border border-white/10 text-[#EAE6DF]/60">
        {buildLabel}
      </span>
    </div>
  );
}
