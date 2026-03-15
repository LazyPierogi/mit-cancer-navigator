import {
  AnalyzeRunResponse,
  DatasetBrowserResponse,
  EvidenceExplainability,
  EmbeddingManifest,
  EmbeddingNeighbor,
  EmbeddingPoint,
  EngineBenchmarkRequest,
  EngineBenchmarkResult,
  ImportBatch,
  ImportDebugConfig,
  ImportDebugLogEntry,
  ImportSummary,
  SemanticImportStatus,
  ValidationReport,
  TracePayload,
  UncertaintyFlagsExplainability,
  VignetteInput
} from "@/lib/contracts";
import {
  sampleImportDebugConfig,
  sampleImportDebugLogs,
  sampleImportSummary,
  sampleEngineBenchmark,
  sampleRun,
  sampleTrace
} from "@/lib/sample-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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
    engine: sampleRun.engine,
    retrievalMode: sampleRun.retrievalMode,
    vectorStore: sampleRun.vectorStore,
    embeddingModel: sampleRun.embeddingModel,
    chunkingStrategyVersion: sampleRun.chunkingStrategyVersion,
    topEvidence: sampleRun.topEvidence,
    manualReviewEvidence: sampleRun.manualReviewEvidence,
    secondaryReferences: sampleRun.secondaryReferences,
    uncertaintyFlags: sampleRun.uncertaintyFlags,
    safetyFooterKey: sampleRun.safetyFooterKey,
    traceId: sampleRun.traceId,
    retrievalCandidateCount: sampleRun.retrievalCandidateCount,
    semanticEvidence: sampleRun.semanticEvidence,
    semanticGuidelineCandidates: sampleRun.semanticGuidelineCandidates,
    explainabilitySummary: sampleRun.explainabilitySummary,
    semanticCandidateOnlyCount: sampleRun.semanticCandidateOnlyCount
  };
}

function buildSampleEvidenceExplainability(evidenceId: string): EvidenceExplainability {
  return {
    evidenceId,
    scoreRationale:
      "ERS 53/100 reflects strong evidence strength, solid dataset structure, credible source quality, and recent publication timing. The item stays aligned to the metastatic PD-L1-high first-line topic and the applicability note confirms a clean patient fit.",
    studySummary: {
      objective: "Evaluate first-line pembrolizumab in metastatic NSCLC with PD-L1 expression of 50% or greater.",
      signal: "The study reports longer overall and progression-free survival than platinum-based chemotherapy in the matched population.",
      takeaway: "This is strong, patient-fit evidence for the displayed ranking context, but it still serves as support rather than a treatment recommendation."
    },
    sourceAnchors: [
      {
        sourceId: "PMID-10001",
        title: "Pembrolizumab first-line therapy in metastatic NSCLC with PD-L1 >= 50%",
        snippet: "The trial demonstrated significantly longer overall survival and progression-free survival compared to platinum-based chemotherapy.",
        year: 2024
      },
      {
        sourceId: "PMID-10001",
        title: "Pembrolizumab first-line therapy in metastatic NSCLC with PD-L1 >= 50%",
        snippet: "The study evaluated pembrolizumab as a first-line therapy in patients with metastatic NSCLC and a PD-L1 tumor proportion score of 50% or greater.",
        year: 2024
      }
    ],
    grounded: true,
    providerStatus: "grounded_local",
    provider: null,
    model: null,
    promptVersion: "local-evidence-v1",
    latencyMs: null,
    validationStatus: "not_attempted",
    sourceIds: ["PMID-10001"]
  };
}

function buildSampleUncertaintyFlagsExplainability(flags: string[]): UncertaintyFlagsExplainability {
  return {
    summary:
      flags.length > 0
        ? "These flags mark places where the run is still carrying ambiguity, so the interface surfaces that uncertainty instead of pretending the evidence is cleaner than it is."
        : "No uncertainty flags were raised in this run, which means the current ambiguity checks did not fire for the promoted evidence.",
    whyFlagsExist:
      "They exist as operator-facing guardrails. We use them to make incomplete biomarker fit, coarse structured metadata, or other ambiguity visible before someone overreads the ranked output.",
    whatItMeans:
      flags.length > 0
        ? "A flag is a caution label, not a failure state. It means the evidence may still be useful, but the reviewer should treat applicability or evidence structure as something to double-check."
        : "Zero flags is cleaner, not magical. It means the current run did not trip the uncertainty heuristics we expose in the panel.",
    flags,
    grounded: true,
    providerStatus: "grounded_local",
    provider: null,
    model: null,
    promptVersion: "local-uncertainty-flags-v1",
    latencyMs: null,
    validationStatus: "not_attempted"
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
  try {
    return await apiFetch<TracePayload>(`/api/v1/runs/${runId}/trace`);
  } catch {
    if (runId === sampleTrace.runId) {
      return sampleTrace;
    }

    throw new Error(`Trace for run ${runId} is unavailable without a live API.`);
  }
}

export async function getEvidenceExplainability(runId: string, evidenceId: string): Promise<EvidenceExplainability> {
  try {
    return await apiFetch<EvidenceExplainability>(`/api/v1/runs/${runId}/evidence/${evidenceId}/explainability`);
  } catch {
    if (runId === sampleRun.id && evidenceId === sampleRun.topEvidence[0]?.evidenceId) {
      return buildSampleEvidenceExplainability(evidenceId);
    }

    throw new Error(`Explainability for ${evidenceId} is unavailable without a live API.`);
  }
}

export async function getUncertaintyFlagsExplainability(runId: string, flags: string[]): Promise<UncertaintyFlagsExplainability> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 3000);

  try {
    return await apiFetch<UncertaintyFlagsExplainability>(`/api/v1/runs/${runId}/uncertainty-flags/explainability`, {
      signal: controller.signal,
    });
  } catch {
    return buildSampleUncertaintyFlagsExplainability(flags.slice(0, 10));
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function getImportBatches(): Promise<ImportBatch[]> {
  return apiFetch<ImportBatch[]>("/api/v1/imports");
}

export async function getImportBatch(batchId: string): Promise<ImportBatch> {
  return apiFetch<ImportBatch>(`/api/v1/jobs/${batchId}`);
}

export async function getImportSummary(): Promise<ImportSummary> {
  try {
    return await apiFetch<ImportSummary>("/api/v1/imports/summary");
  } catch {
    return sampleImportSummary;
  }
}

export async function getImportDebugConfig(): Promise<ImportDebugConfig> {
  try {
    return await apiFetch<ImportDebugConfig>("/api/v1/imports/debug/config");
  } catch {
    return sampleImportDebugConfig;
  }
}

export async function updateImportDebugConfig(payload: ImportDebugConfig): Promise<ImportDebugConfig> {
  try {
    return await apiFetch<ImportDebugConfig>("/api/v1/imports/debug/config", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  } catch {
    return payload;
  }
}

export async function getImportDebugLogs(limit = 80): Promise<ImportDebugLogEntry[]> {
  try {
    return await apiFetch<ImportDebugLogEntry[]>(`/api/v1/imports/debug/logs?limit=${limit}`);
  } catch {
    return sampleImportDebugLogs.slice(0, limit);
  }
}

export async function validateDataset(datasetKind: "esmo" | "pubmed", path?: string): Promise<ValidationReport> {
  return apiFetch<ValidationReport>(`/api/v1/validate/${datasetKind}`, {
    method: "POST",
    body: JSON.stringify({ path })
  });
}

export async function importDataset(
  datasetKind: "esmo" | "pubmed",
  path?: string,
  mode: "replace" | "append" = "replace"
): Promise<ImportBatch> {
  return apiFetch<ImportBatch>(`/api/v1/import/${datasetKind}`, {
    method: "POST",
    body: JSON.stringify({ path, mode })
  });
}

export async function getDatasetBrowser(datasetKind: "esmo" | "pubmed"): Promise<DatasetBrowserResponse> {
  return apiFetch<DatasetBrowserResponse>(`/api/v1/imports/browse/${datasetKind}`);
}

export async function importSemanticDataset(datasetKind: "esmo" | "pubmed", path?: string): Promise<SemanticImportStatus> {
  return apiFetch<SemanticImportStatus>(`/api/v1/import/semantic/${datasetKind}`, {
    method: "POST",
    body: JSON.stringify({ path })
  });
}

export async function getSemanticImportStatus(datasetKind: "esmo" | "pubmed"): Promise<SemanticImportStatus> {
  try {
    return await apiFetch<SemanticImportStatus>(`/api/v1/imports/semantic/status/${datasetKind}`);
  } catch {
    return {
      datasetKind,
      latestBatchId: null,
      latestStatus: null,
      documentCount: 0,
      chunkCount: 0,
      latestJob: null
    };
  }
}

export async function prewarmRuntime(options?: {
  includeSemantic?: boolean;
  includeBenchmark?: boolean;
  timeoutMs?: number;
}): Promise<boolean> {
  const includeSemantic = options?.includeSemantic ?? false;
  const includeBenchmark = options?.includeBenchmark ?? false;
  const timeoutMs = options?.timeoutMs ?? 15000;
  const params = new URLSearchParams();
  if (includeSemantic) {
    params.set("include_semantic", "true");
  }
  if (includeBenchmark) {
    params.set("include_benchmark", "true");
  }
  const suffix = params.size > 0 ? `?${params.toString()}` : "";
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    await apiFetch<{ status: string }>(`/api/v1/runtime/prewarm${suffix}`, {
      method: "POST",
      signal: controller.signal
    });
    return true;
  } catch {
    // Prewarm is best-effort only. The live flow should still work without it.
    return false;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function getEmbeddingManifest(): Promise<EmbeddingManifest> {
  try {
    return await apiFetch<EmbeddingManifest>("/api/v1/labs/embeddings/manifest");
  } catch {
    return {
      pointCount: 0,
      sourceCounts: {},
      histologyCounts: {},
      embeddingModel: "none",
      projectionMethod: "none",
      vectorStore: "unavailable"
    };
  }
}

export async function getEmbeddingPoints(sourceType?: "pubmed" | "esmo"): Promise<EmbeddingPoint[]> {
  const suffix = sourceType ? `?source_type=${sourceType}` : "";
  try {
    return await apiFetch<EmbeddingPoint[]>(`/api/v1/labs/embeddings/points${suffix}`);
  } catch {
    return [];
  }
}

export async function getEmbeddingNeighbors(pointId: string, limit = 8): Promise<EmbeddingNeighbor[]> {
  try {
    return await apiFetch<EmbeddingNeighbor[]>(`/api/v1/labs/embeddings/neighbors/${pointId}?limit=${limit}`);
  } catch {
    return [];
  }
}

export async function runEngineBenchmark(
  payload: EngineBenchmarkRequest,
  options?: { allowFallback?: boolean; timeoutMs?: number }
): Promise<EngineBenchmarkResult> {
  const allowFallback = options?.allowFallback ?? true;
  const timeoutMs = options?.timeoutMs ?? 30000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await apiFetch<EngineBenchmarkResult>("/api/v1/evals/compare", {
      method: "POST",
      body: JSON.stringify(payload),
      signal: controller.signal
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`Live benchmark timed out after ${Math.round(timeoutMs / 1000)}s.`);
    }
    if (!allowFallback) {
      throw error instanceof Error ? error : new Error("Live benchmark request failed.");
    }
    const usesFrozenPack = payload.packId === "frozen_pack";
    return {
      ...sampleEngineBenchmark,
      packId: usesFrozenPack ? "frozen-pack-canonical-v2" : sampleEngineBenchmark.packId,
      summary: {
        ...sampleEngineBenchmark.summary,
        packLabel: usesFrozenPack ? "Frozen Benchmark Pack" : sampleEngineBenchmark.summary.packLabel,
        headline: usesFrozenPack
          ? "Compare deterministic precision against hybrid semantic breadth on the frozen 15-case NSCLC pack."
          : sampleEngineBenchmark.summary.headline,
        recommendedTakeaway: usesFrozenPack
          ? "Deterministic remains the benchmark authority, while hybrid semantic is evaluated for measurable retrieval lift on the frozen pack."
          : sampleEngineBenchmark.summary.recommendedTakeaway
      },
      meta: {
        cached: true,
        cacheKey: "sample-benchmark-fallback",
        benchmarkVersion: "sample",
        pubmedBatchId: null,
        esmoBatchId: null,
        pubmedSemanticJobId: null,
        esmoSemanticJobId: null,
        sourceFingerprint: "sample-source-fingerprint",
        runtimeConfigFingerprint: "sample-runtime-config",
        vectorStore: null,
        embeddingModel: null
      },
      engines: sampleEngineBenchmark.engines.map((engine) => ({
        ...engine,
        retrievalMode: engine.engineKey === "hybrid_semantic" ? payload.retrievalMode : "hybrid",
        aggregate: {
          ...engine.aggregate,
          topicMatchRate: engine.aggregate.topicMatchRate ?? null,
          primaryLabelHitRate: engine.aggregate.primaryLabelHitRate ?? null,
          expectedLabelDistribution: engine.aggregate.expectedLabelDistribution ?? {},
          observedLabelDistribution: engine.aggregate.observedLabelDistribution ?? {},
          packCompleteness: engine.aggregate.packCompleteness ?? `${engine.aggregate.caseCount}/${engine.aggregate.caseCount} quantitative goldens present`,
          quantitativeGoldensComplete: engine.aggregate.quantitativeGoldensComplete ?? false
        },
        cases: engine.cases.map((caseResult) => ({
          ...caseResult,
          category: caseResult.category ?? "demo",
          clinicalQuestion: caseResult.clinicalQuestion ?? "Fallback benchmark case.",
          reference: caseResult.reference ?? {
            expectedPrimaryLabel: null,
            expectedGuidelineTopicId: null,
            expectedGuidelineTopicTitle: null,
            expectedEvidenceIds: [],
            expectedLabelByEvidenceId: {}
          },
          comparison: caseResult.comparison ?? {
            observedPrimaryLabel: caseResult.metrics?.observedPrimaryLabel ?? null,
            observedGuidelineTopicId: caseResult.metrics?.observedPrimaryTopicId ?? null,
            observedGuidelineTopicTitle: caseResult.metrics?.observedPrimaryTopicTitle ?? null,
            matchedExpectedEvidenceIds: [],
            missedExpectedEvidenceIds: [],
            unexpectedPromotedEvidenceIds: [],
            topicMatch: null,
            primaryLabelHit: null,
            why: "Fallback benchmark payload does not include canonical reference deltas.",
            sourceFingerprint: "sample-source-fingerprint",
            runtimeConfigFingerprint: "sample-runtime-config"
          },
          metrics: caseResult.metrics
            ? {
                ...caseResult.metrics,
                retrievalMode: engine.engineKey === "hybrid_semantic" ? payload.retrievalMode : "hybrid",
                observedPrimaryLabel: caseResult.metrics.observedPrimaryLabel ?? null,
                observedPrimaryTopicId: caseResult.metrics.observedPrimaryTopicId ?? null,
                observedPrimaryTopicTitle: caseResult.metrics.observedPrimaryTopicTitle ?? null
              }
            : null
        }))
      }))
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function getCachedEngineBenchmark(payload: EngineBenchmarkRequest): Promise<EngineBenchmarkResult | null> {
  try {
    return await apiFetch<EngineBenchmarkResult>("/api/v1/evals/compare/cached", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  } catch {
    return null;
  }
}
