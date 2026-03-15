import type {
  DatasetBrowserResponse,
  EmbeddingManifest,
  EmbeddingPoint,
  EngineBenchmarkResult,
  ImportDebugConfig,
  ImportDebugLogEntry,
  ImportSummary,
  SemanticImportStatus,
} from "@/lib/contracts";

type DatasetKind = "esmo" | "pubmed";
type EmbeddingFilter = "all" | "pubmed" | "esmo";

type LabsDashboardCache = {
  updatedAt: number;
  importSummary: ImportSummary | null;
  debugConfig: ImportDebugConfig | null;
  debugLogs: ImportDebugLogEntry[];
  datasetBrowsers: Partial<Record<DatasetKind, DatasetBrowserResponse>>;
  semanticStatuses: Partial<Record<DatasetKind, SemanticImportStatus>>;
  embeddingManifest: EmbeddingManifest | null;
  benchmarkResults: Record<string, EngineBenchmarkResult>;
};

const STORAGE_KEY = "labs-dashboard-cache-v1";
const MAX_CACHE_AGE_MS = 5 * 60 * 1000;

let memorySnapshot: LabsDashboardCache | null = null;
const embeddingPointsByFilter: Partial<Record<EmbeddingFilter, EmbeddingPoint[]>> = {};

function emptyCache(): LabsDashboardCache {
  return {
    updatedAt: 0,
    importSummary: null,
    debugConfig: null,
    debugLogs: [],
    datasetBrowsers: {},
    semanticStatuses: {},
    embeddingManifest: null,
    benchmarkResults: {},
  };
}

function mergeCache(
  current: LabsDashboardCache,
  updates: Partial<Omit<LabsDashboardCache, "updatedAt">>,
): LabsDashboardCache {
  return {
    updatedAt: Date.now(),
    importSummary: updates.importSummary === undefined ? current.importSummary : updates.importSummary,
    debugConfig: updates.debugConfig === undefined ? current.debugConfig : updates.debugConfig,
    debugLogs: updates.debugLogs === undefined ? current.debugLogs : updates.debugLogs,
    datasetBrowsers: {
      ...current.datasetBrowsers,
      ...(updates.datasetBrowsers ?? {}),
    },
    semanticStatuses: {
      ...current.semanticStatuses,
      ...(updates.semanticStatuses ?? {}),
    },
    embeddingManifest: updates.embeddingManifest === undefined ? current.embeddingManifest : updates.embeddingManifest,
    benchmarkResults: updates.benchmarkResults === undefined ? current.benchmarkResults : updates.benchmarkResults,
  };
}

function readSessionSnapshot(): LabsDashboardCache | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as LabsDashboardCache;
    if (!parsed.updatedAt || Date.now() - parsed.updatedAt > MAX_CACHE_AGE_MS) {
      window.sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function persistSnapshot(snapshot: LabsDashboardCache): void {
  memorySnapshot = snapshot;
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } catch {
    // Ignore quota and serialization failures. Memory cache is still useful for this session.
  }
}

export function readLabsDashboardCache(): LabsDashboardCache {
  if (memorySnapshot) {
    return memorySnapshot;
  }

  const sessionSnapshot = readSessionSnapshot();
  if (sessionSnapshot) {
    memorySnapshot = sessionSnapshot;
    return sessionSnapshot;
  }

  const initial = emptyCache();
  memorySnapshot = initial;
  return initial;
}

export function writeLabsDashboardCache(
  updates: Partial<Omit<LabsDashboardCache, "updatedAt">>,
): LabsDashboardCache {
  const next = mergeCache(readLabsDashboardCache(), updates);
  persistSnapshot(next);
  return next;
}

export function readCachedEmbeddingPoints(filter: EmbeddingFilter): EmbeddingPoint[] {
  return embeddingPointsByFilter[filter] ? [...(embeddingPointsByFilter[filter] ?? [])] : [];
}

export function writeCachedEmbeddingPoints(filter: EmbeddingFilter, points: EmbeddingPoint[]): void {
  embeddingPointsByFilter[filter] = [...points];
}

export function clearCachedEmbeddingPoints(): void {
  for (const filter of Object.keys(embeddingPointsByFilter) as EmbeddingFilter[]) {
    delete embeddingPointsByFilter[filter];
  }
}
