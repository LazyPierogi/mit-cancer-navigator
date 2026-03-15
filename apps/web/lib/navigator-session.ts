import type { AnalyzeRunResponse, VignetteInput } from "@/lib/contracts";

export type NavigatorSessionState = {
  activePresetId: string;
  vignette: VignetteInput;
  customInput: string;
  runResponse: AnalyzeRunResponse | null;
  lastPolicyRunResponse: AnalyzeRunResponse | null;
  lastAnalyzedFingerprint: string;
  sortMode: "alignment" | "recency" | "ers";
};

const STORAGE_KEY = "nsclc-navigator-session";

export function readNavigatorSessionState(): NavigatorSessionState | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as NavigatorSessionState;
  } catch {
    return null;
  }
}

export function writeNavigatorSessionState(state: NavigatorSessionState): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}
