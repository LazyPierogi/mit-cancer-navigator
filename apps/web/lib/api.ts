import { AnalyzeRunResponse, ImportBatch, ImportSummary, TracePayload, VignetteInput } from "@/lib/contracts";
import { sampleRun, sampleTrace } from "@/lib/sample-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const USING_LOCALHOST_FALLBACK = /127\.0\.0\.1|localhost/.test(API_BASE_URL);

function buildSampleRunResponse(): AnalyzeRunResponse {
  return {
    run: {
      id: sampleRun.id,
      status: sampleRun.status,
      rulesetVersion: sampleRun.rulesetVersion,
      corpusVersion: sampleRun.corpusVersion,
      createdAt: sampleRun.createdAt,
      latencyMs: sampleRun.latencyMs
    },
    topEvidence: sampleRun.topEvidence,
    secondaryReferences: sampleRun.secondaryReferences,
    uncertaintyFlags: sampleRun.uncertaintyFlags,
    safetyFooterKey: sampleRun.safetyFooterKey,
    traceId: sampleRun.traceId
  };
}

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
  if (USING_LOCALHOST_FALLBACK) {
    return buildSampleRunResponse();
  }

  try {
    return await apiFetch<AnalyzeRunResponse>("/api/v1/runs", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  } catch {
    return buildSampleRunResponse();
  }
}

export async function getRun(runId: string): Promise<AnalyzeRunResponse> {
  if (USING_LOCALHOST_FALLBACK && runId === sampleRun.id) {
    return buildSampleRunResponse();
  }

  try {
    return await apiFetch<AnalyzeRunResponse>(`/api/v1/runs/${runId}`);
  } catch {
    if (runId === sampleRun.id) {
      return buildSampleRunResponse();
    }

    throw new Error(`Run ${runId} is unavailable without a live API.`);
  }
}

export async function getRunTrace(runId: string): Promise<TracePayload> {
  if (USING_LOCALHOST_FALLBACK && runId === sampleTrace.runId) {
    return sampleTrace;
  }

  try {
    return await apiFetch<TracePayload>(`/api/v1/runs/${runId}/trace`);
  } catch {
    if (runId === sampleTrace.runId) {
      return sampleTrace;
    }

    throw new Error(`Trace for run ${runId} is unavailable without a live API.`);
  }
}

export async function getImportBatches(): Promise<ImportBatch[]> {
  return apiFetch<ImportBatch[]>("/api/v1/imports");
}

export async function getImportBatch(batchId: string): Promise<ImportBatch> {
  return apiFetch<ImportBatch>(`/api/v1/jobs/${batchId}`);
}

export async function getImportSummary(): Promise<ImportSummary> {
  return apiFetch<ImportSummary>("/api/v1/imports/summary");
}
