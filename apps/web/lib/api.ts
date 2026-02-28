import { AnalyzeRunResponse, TracePayload, VignetteInput } from "@/lib/contracts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function createRun(payload: VignetteInput): Promise<AnalyzeRunResponse> {
  return apiFetch<AnalyzeRunResponse>("/api/v1/runs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getRun(runId: string): Promise<AnalyzeRunResponse> {
  return apiFetch<AnalyzeRunResponse>(`/api/v1/runs/${runId}`);
}

export async function getRunTrace(runId: string): Promise<TracePayload> {
  return apiFetch<TracePayload>(`/api/v1/runs/${runId}/trace`);
}

