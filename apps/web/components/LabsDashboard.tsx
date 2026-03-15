"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Binary,
  CheckCircle2,
  Database,
  FileSearch,
  FlaskConical,
  SlidersHorizontal,
  Sparkles,
  Workflow
} from "lucide-react";
import { STYLES } from "@/lib/theme";
import {
  getDatasetBrowser,
  getCachedEngineBenchmark,
  getEmbeddingManifest,
  getEmbeddingNeighbors,
  getEmbeddingPoints,
  getImportDebugConfig,
  getImportDebugLogs,
  getImportSummary,
  prewarmRuntime,
  runEngineBenchmark,
  getSemanticImportStatus,
  importDataset,
  importSemanticDataset,
  updateImportDebugConfig,
  validateDataset
} from "@/lib/api";
import type {
  DatasetBrowserResponse,
  EmbeddingManifest,
  EmbeddingNeighbor,
  EmbeddingPoint,
  EngineBenchmarkResult,
  ImportBatch,
  ImportDebugConfig,
  ImportDebugLogEntry,
  ImportSummary,
  SemanticImportStatus,
  ValidationReport
} from "@/lib/contracts";
import {
  DEFAULT_NAVIGATOR_DEBUG_PREFERENCES,
  readNavigatorDebugPreferences,
  subscribeNavigatorDebugPreferences,
  updateNavigatorDebugPreferences,
  type NavigatorDebugPreferences
} from "@/lib/debug-preferences";
import {
  clearCachedEmbeddingPoints,
  readCachedEmbeddingPoints,
  readLabsDashboardCache,
  writeCachedEmbeddingPoints,
  writeLabsDashboardCache,
} from "@/lib/labs-cache";
import { policy } from "@/lib/sample-data";

type VersionManifest = {
  productVersion: string;
  uiVersion: string;
  backendVersion: string;
  rulesetVersion: string;
  corpusVersion: string;
  releaseDate?: string;
  buildLabel: string;
  notes: string[];
};

type LabsDashboardProps = {
  versionManifest: VersionManifest;
};

type LabKey = "datasets" | "evaluation" | "embeddings" | "debug";
type EvaluationViewMode = "simple" | "detailed";

const labCards: Array<{
  id: LabKey;
  title: string;
  description: string;
  eyebrow: string;
  icon: typeof Database;
}> = [
  {
    id: "datasets",
    title: "Curated Datasets",
    description: "Live corpus health, batch counts, and whether runtime is using imported or fallback data.",
    eyebrow: "Operational",
    icon: Database
  },
  {
    id: "evaluation",
    title: "Evaluation Lab",
    description: "Frozen-vignette metrics, reviewer queue, and what we monitor before trusting the output.",
    eyebrow: "Quality",
    icon: FlaskConical
  },
  {
    id: "embeddings",
    title: "Embedding Atlas",
    description: "Projector-style map of semantic chunks, topic neighbors, and how PubMed and ESMO vectors cluster.",
    eyebrow: "Atlas",
    icon: Binary
  },
  {
    id: "debug",
    title: "Debug Console",
    description: "Working toggles for import strictness and UI controls that impact the active lab surface.",
    eyebrow: "Controls",
    icon: SlidersHorizontal
  }
];

const frozenLabelVocabulary = ["aligned", "guideline_silent", "conflict"];
const benchmarkPackOptions = [
  { value: "demo_presets", label: "Sample benchmark presets" },
  { value: "frozen_pack", label: "Frozen benchmark pack" }
] as const;

const evaluationViewOptions: Array<{
  value: EvaluationViewMode;
  label: string;
  description: string;
}> = [
  {
    value: "simple",
    label: "Simple",
    description: "Quick glance benchmark summary"
  },
  {
    value: "detailed",
    label: "Detailed",
    description: "Audit and debugging mode"
  }
];

function formatDelta(value: number, suffix = "") {
  if (value === 0) {
    return `0${suffix}`;
  }
  return `${value > 0 ? "+" : ""}${value}${suffix}`;
}

function metricTone(value: number) {
  if (value > 0) {
    return "text-[#2D5940]";
  }
  if (value < 0) {
    return "text-[#A63D2F]";
  }
  return "text-[#6B6B6B]";
}

function formatRate(value?: number | null) {
  if (value === null || value === undefined) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function labelBadgeStyles(label?: string | null) {
  if (label === "aligned") {
    return "bg-[#E8F2EC] text-[#2D5940]";
  }
  if (label === "conflict") {
    return "bg-[#FBEAE5] text-[#A63D2F]";
  }
  if (label === "guideline_silent") {
    return "bg-[#F6E7C8] text-[#8A5A13]";
  }
  return "bg-[#F0EBE3] text-[#6B6B6B]";
}

function formatTimestamp(value?: string | null) {
  if (!value) {
    return "Unknown";
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(new Date(value));
}

function sourceLabel(source: "db_imported" | "file_fallback") {
  return source === "db_imported" ? "Imported DB" : "File fallback";
}

function isPubmedAppendOnlyDemoPath(datasetKind: "esmo" | "pubmed", datasetPath: string) {
  if (datasetKind !== "pubmed") {
    return false;
  }
  const normalized = datasetPath.trim().replaceAll("\\", "/").toLowerCase();
  return normalized.includes("/datasets/pubmed/demo/") || normalized.startsWith("datasets/pubmed/demo/");
}

function levelStyles(level: string) {
  if (level === "error") {
    return "text-[#A63D2F] bg-[#FBEAE5]";
  }
  if (level === "warning") {
    return "text-[#8A5A13] bg-[#F6E7C8]";
  }
  return "text-[#2D5940] bg-[#E8F2EC]";
}

function statusBadgeStyles(status: string) {
  if (status.includes("failed") || status.includes("error")) {
    return "bg-[#FBEAE5] text-[#A63D2F]";
  }
  if (status.includes("warning")) {
    return "bg-[#F6E7C8] text-[#8A5A13]";
  }
  return "bg-[#E8F2EC] text-[#2D5940]";
}

function compactMetricCardStyles(tone: "neutral" | "positive" | "warning" | "accent" = "neutral") {
  if (tone === "positive") {
    return "border-[#D5E5DB] bg-[#F6FBF8]";
  }
  if (tone === "warning") {
    return "border-[#E7D7B7] bg-[#FCF8F0]";
  }
  if (tone === "accent") {
    return "border-[#E9B7AC] bg-[#FFF5F1]";
  }
  return "border-[#EAE6DF]/70 bg-white";
}

function benchmarkRateAssessment(rate?: number | null) {
  if (rate === null || rate === undefined) {
    return "Waiting for benchmark data.";
  }
  if (rate >= 0.8) {
    return "Strong for this build.";
  }
  if (rate >= 0.5) {
    return "Mixed result for this build.";
  }
  return "Still low for this build.";
}

function benchmarkCaseCount(rate?: number | null, totalCases?: number | null) {
  if (rate === null || rate === undefined || !totalCases || totalCases <= 0) {
    return null;
  }
  return Math.round(rate * totalCases);
}

function formatRateOrZero(value?: number | null) {
  if (value === null || value === undefined) {
    return "0%";
  }
  return formatRate(value);
}

function EvidenceIdChips({ ids, emptyLabel = "No sampled IDs" }: { ids: string[]; emptyLabel?: string }) {
  if (ids.length === 0) {
    return <div className="text-xs text-[#8A867F]">{emptyLabel}</div>;
  }

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {ids.map((id) => (
        <span key={id} className="rounded-full border border-[#EAE6DF] bg-white px-2.5 py-1 text-[11px] font-semibold text-[#4F4A43]">
          {id}
        </span>
      ))}
    </div>
  );
}

function UnexpectedPromotedDisclosure({
  ids,
  hybridOnlyIds = [],
  emptyLabel = "No unexpected promotions"
}: {
  ids: string[];
  hybridOnlyIds?: string[];
  emptyLabel?: string;
}) {
  if (ids.length === 0) {
    return <div className="text-xs text-[#8A867F]">{emptyLabel}</div>;
  }

  const hybridOnlySet = new Set(hybridOnlyIds);
  const hybridOnlyCount = ids.filter((id) => hybridOnlySet.has(id)).length;

  return (
    <details className="mt-2 rounded-[16px] border border-[#EAE6DF]/70 bg-[#FCFBF8] px-3 py-3">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold text-[#2E2E2E]">
            Unexpected promoted PMID{ids.length === 1 ? "" : "s"}: {ids.length}
          </div>
          <div className="mt-1 text-[11px] leading-relaxed text-[#6B6B6B]">
            Promoted by this engine, but not included in the canonical expected PMID set for this vignette.
          </div>
        </div>
        {hybridOnlyCount > 0 ? (
          <span className="rounded-full bg-[#FBEAE5] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#A63D2F]">
            hybrid-only {hybridOnlyCount}
          </span>
        ) : null}
      </summary>
      <div className="mt-3 border-t border-[#EAE6DF]/70 pt-3">
        <p className="text-xs leading-relaxed text-[#6B6B6B]">
          A large count here does not automatically mean the engine is wrong. It can mean the gold set is intentionally sparse, the engine is surfacing extra grounded studies, or the promotion/ranking window needs calibration. Use matched and missed canonical PMID plus topic-match and primary-label-hit as the main fidelity signal.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {ids.map((id) => (
            <span
              key={id}
              className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
                hybridOnlySet.has(id)
                  ? "border-[#E9B7AC] bg-[#FBEAE5] text-[#A63D2F]"
                  : "border-[#EAE6DF] bg-white text-[#4F4A43]"
              }`}
            >
              {id}
            </span>
          ))}
        </div>
      </div>
    </details>
  );
}

function BuildNotesSection({ versionManifest }: { versionManifest: VersionManifest }) {
  return (
    <section className={`${STYLES.surface} ${STYLES.radiusCard} ${STYLES.shadow} border border-[#EAE6DF]/60 p-8`}>
      <div className="mb-6 flex items-start justify-between gap-6">
        <div>
          <div className="mb-3 flex items-center gap-3">
            <div className={`${STYLES.primaryBg} flex h-10 w-10 items-center justify-center rounded-xl text-white shadow-sm`}>
              <Workflow size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-[#2E2E2E]">Build Notes</h2>
              <p className="text-sm text-[#6B6B6B]">Version snapshot and release notes for the currently running demo build.</p>
            </div>
          </div>
        </div>
        <span className="rounded-lg bg-[#F6E7C8] px-3 py-1.5 text-xs font-bold uppercase tracking-widest text-[#8A5A13]">
          {versionManifest.buildLabel}
        </span>
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <div className="rounded-2xl border border-[#EAE6DF]/70 bg-[#F9F8F6] px-4 py-4">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#6B6B6B]">Product</div>
          <div className="text-lg font-black text-[#2E2E2E]">v{versionManifest.productVersion}</div>
        </div>
        <div className="rounded-2xl border border-[#EAE6DF]/70 bg-[#F9F8F6] px-4 py-4">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#6B6B6B]">UI</div>
          <div className="text-lg font-black text-[#2E2E2E]">v{versionManifest.uiVersion}</div>
        </div>
        <div className="rounded-2xl border border-[#EAE6DF]/70 bg-[#F9F8F6] px-4 py-4">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#6B6B6B]">Backend</div>
          <div className="text-lg font-black text-[#2E2E2E]">v{versionManifest.backendVersion}</div>
        </div>
        <div className="rounded-2xl border border-[#EAE6DF]/70 bg-[#F9F8F6] px-4 py-4">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#6B6B6B]">Ruleset</div>
          <div className="text-lg font-black text-[#2E2E2E]">{versionManifest.rulesetVersion}</div>
        </div>
        <div className="rounded-2xl border border-[#EAE6DF]/70 bg-[#F9F8F6] px-4 py-4">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#6B6B6B]">Corpus</div>
          <div className="text-lg font-black text-[#2E2E2E]">{versionManifest.corpusVersion}</div>
        </div>
        <div className="rounded-2xl border border-[#EAE6DF]/70 bg-[#F9F8F6] px-4 py-4">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#6B6B6B]">Released</div>
          <div className="text-lg font-black text-[#2E2E2E]">{versionManifest.releaseDate ?? "Unknown"}</div>
        </div>
      </div>

      <div className="rounded-[24px] border border-[#EAE6DF]/70 bg-[#FCFBF8] px-5 py-5">
        <div className="mb-3 text-[10px] font-bold uppercase tracking-widest text-[#6B6B6B]">Included in this build</div>
        <ul className="space-y-2">
          {versionManifest.notes.map((note) => (
            <li key={note} className="flex items-start gap-3 text-sm leading-relaxed text-[#2E2E2E]">
              <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[#C96557]" />
              <span>{note}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function ToggleRow({
  title,
  description,
  enabled,
  onToggle,
  disabled,
  badge
}: {
  title: string;
  description: string;
  enabled: boolean;
  onToggle?: () => void;
  disabled?: boolean;
  badge?: string;
}) {
  return (
    <div className={`flex items-start justify-between gap-4 rounded-[24px] border border-[#EAE6DF]/70 bg-[#FCFBF8] p-5`}>
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold text-[#2E2E2E]">{title}</h3>
          {badge ? (
            <span className="rounded-full bg-[#F0EBE3] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">
              {badge}
            </span>
          ) : null}
        </div>
        <p className="max-w-xl text-sm leading-relaxed text-[#6B6B6B]">{description}</p>
      </div>

      <button
        type="button"
        onClick={onToggle}
        disabled={disabled || !onToggle}
        aria-pressed={enabled}
        className={`relative h-11 w-20 shrink-0 rounded-full border transition-all ${
          enabled ? "border-[#C96557] bg-[#C96557]" : "border-[#EAE6DF] bg-white"
        } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
      >
        <span
          className={`absolute top-1.5 h-8 w-8 rounded-full bg-white shadow-[0_8px_24px_rgba(0,0,0,0.12)] transition-all ${
            enabled ? "left-[2.45rem]" : "left-1.5"
          }`}
        />
      </button>
    </div>
  );
}

function ReadOnlyStatusRow({
  title,
  value,
  tone = "neutral",
  badge
}: {
  title: string;
  value: string;
  tone?: "neutral" | "positive" | "warning";
  badge?: string;
}) {
  const toneStyles =
    tone === "positive"
      ? "bg-[#E8F2EC] text-[#2D5940]"
      : tone === "warning"
        ? "bg-[#F6E7C8] text-[#8A5A13]"
        : "bg-[#F0EBE3] text-[#6B6B6B]";

  return (
    <div className="flex items-start justify-between gap-4 rounded-[24px] border border-[#EAE6DF]/70 bg-[#FCFBF8] p-5">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold text-[#2E2E2E]">{title}</h3>
          {badge ? (
            <span className="rounded-full bg-[#F0EBE3] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">
              {badge}
            </span>
          ) : null}
        </div>
      </div>

      <span className={`rounded-full px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.16em] ${toneStyles}`}>{value}</span>
    </div>
  );
}

function DatasetsPanel({ importSummary }: { importSummary: ImportSummary | null }) {
  const pubmedSummary = importSummary?.latestByKind.pubmed;
  const esmoSummary = importSummary?.latestByKind.esmo;

  return (
    <div className="space-y-6">
      <div className="grid gap-5 md:grid-cols-4">
        <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6">
          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Active topics</div>
          <div className="mt-3 text-3xl font-black text-[#2E2E2E]">{importSummary?.activeTopics ?? "..."}</div>
        </div>
        <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6">
          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Evidence studies</div>
          <div className="mt-3 text-3xl font-black text-[#2E2E2E]">{importSummary?.activeEvidenceStudies ?? "..."}</div>
        </div>
        <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6">
          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Import batches</div>
          <div className="mt-3 text-3xl font-black text-[#2E2E2E]">{importSummary?.importBatchCount ?? "..."}</div>
        </div>
        <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6">
          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Runtime mode</div>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-full bg-[#E8F2EC] px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.14em] text-[#2D5940]">
              Topics: {sourceLabel(importSummary?.runtimeSources.topics ?? "file_fallback")}
            </span>
            <span className="rounded-full bg-[#FBEAE5] px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.14em] text-[#A63D2F]">
              Evidence: {sourceLabel(importSummary?.runtimeSources.evidence ?? "file_fallback")}
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Guideline catalog</div>
              <h3 className="mt-2 text-2xl font-black tracking-tight text-[#2E2E2E]">ESMO topic pack</h3>
            </div>
            <span className="rounded-full bg-[#E8F2EC] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-[#2D5940]">
              {esmoSummary?.status ?? "Loading"}
            </span>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-[24px] bg-[#F9F8F6] p-5">
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Latest batch</div>
              <div className="mt-2 text-sm font-semibold text-[#2E2E2E]">{esmoSummary?.batchId ?? "Pending"}</div>
            </div>
            <div className="rounded-[24px] bg-[#F9F8F6] p-5">
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Imported records</div>
              <div className="mt-2 text-sm font-semibold text-[#2E2E2E]">{esmoSummary?.importedCount ?? 0}</div>
            </div>
            <div className="rounded-[24px] bg-[#F9F8F6] p-5">
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Warnings</div>
              <div className="mt-2 text-sm font-semibold text-[#2E2E2E]">{esmoSummary?.warningCount ?? 0}</div>
            </div>
            <div className="rounded-[24px] bg-[#F9F8F6] p-5">
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Updated</div>
              <div className="mt-2 text-sm font-semibold text-[#2E2E2E]">{formatTimestamp(esmoSummary?.createdAt)}</div>
            </div>
          </div>
        </div>

        <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Evidence corpus</div>
              <h3 className="mt-2 text-2xl font-black tracking-tight text-[#2E2E2E]">Curated PubMed pack</h3>
            </div>
            <span className="rounded-full bg-[#F6E7C8] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-[#8A5A13]">
              {pubmedSummary?.status ?? "Loading"}
            </span>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-[24px] bg-[#F9F8F6] p-5">
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Latest batch</div>
              <div className="mt-2 text-sm font-semibold text-[#2E2E2E]">{pubmedSummary?.batchId ?? "Pending"}</div>
            </div>
            <div className="rounded-[24px] bg-[#F9F8F6] p-5">
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Imported records</div>
              <div className="mt-2 text-sm font-semibold text-[#2E2E2E]">{pubmedSummary?.importedCount ?? 0}</div>
            </div>
            <div className="rounded-[24px] bg-[#F9F8F6] p-5">
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Warnings</div>
              <div className="mt-2 text-sm font-semibold text-[#2E2E2E]">{pubmedSummary?.warningCount ?? 0}</div>
            </div>
            <div className="rounded-[24px] bg-[#F9F8F6] p-5">
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Updated</div>
              <div className="mt-2 text-sm font-semibold text-[#2E2E2E]">{formatTimestamp(pubmedSummary?.createdAt)}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
        <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Data discipline</div>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[24px] bg-[#F9F8F6] p-5 text-sm leading-relaxed text-[#2E2E2E]">
            We store disease setting, histology, therapy line, and biomarker buckets as explicit fields so cohort matching is not guesswork.
          </div>
          <div className="rounded-[24px] bg-[#F9F8F6] p-5 text-sm leading-relaxed text-[#2E2E2E]">
            Strict PubMed mode can block imports that drift outside the MVP evidence policy or arrive with weak study-type labeling.
          </div>
          <div className="rounded-[24px] bg-[#F9F8F6] p-5 text-sm leading-relaxed text-[#2E2E2E]">
            Runtime source badges let us prove whether the demo is reading imported records or only falling back to packaged fixtures.
          </div>
        </div>
      </div>
    </div>
  );
}

function EvaluationViewModeToggle({
  value,
  onChange
}: {
  value: EvaluationViewMode;
  onChange: (value: EvaluationViewMode) => void;
}) {
  return (
    <div className="inline-flex rounded-full border border-[#EAE6DF] bg-[#FCFBF8] p-1">
      {evaluationViewOptions.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`rounded-full px-4 py-2 text-left transition ${
              active ? "bg-[#201B1A] text-white shadow-[0_10px_24px_rgba(32,27,26,0.18)]" : "text-[#6B6B6B] hover:text-[#2E2E2E]"
            }`}
          >
            <div className="text-[10px] font-bold uppercase tracking-[0.18em]">{option.label}</div>
            <div className={`mt-1 text-[11px] ${active ? "text-white/78" : "text-[#8A867F]"}`}>{option.description}</div>
          </button>
        );
      })}
    </div>
  );
}

function EvaluationCompactMetric({
  label,
  value,
  detail,
  tone = "neutral"
}: {
  label: string;
  value: string;
  detail: string;
  tone?: "neutral" | "positive" | "warning" | "accent";
}) {
  return (
    <div className={`rounded-[24px] border p-5 ${compactMetricCardStyles(tone)}`}>
      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">{label}</div>
      <div className="mt-3 text-3xl font-black text-[#2E2E2E]">{value}</div>
      <div className="mt-2 text-sm leading-relaxed text-[#6B6B6B]">{detail}</div>
    </div>
  );
}

function EvaluationSimpleEngineTable({
  deterministic,
  hybrid
}: {
  deterministic: EngineBenchmarkResult["engines"][number] | null;
  hybrid: EngineBenchmarkResult["engines"][number] | null;
}) {
  const rows = [
    {
      key: "deterministic",
      label: "Deterministic",
      description: "This engine decides the final label and score.",
      engine: deterministic
    },
    {
      key: "semantic",
      label: "Semantic",
      description: "This engine finds more candidate studies, but does not override the final label.",
      engine: hybrid
    }
  ];

  return (
    <div className="overflow-hidden rounded-[28px] border border-[#EAE6DF]/70 bg-white">
      <div className="grid grid-cols-[1.3fr_repeat(3,minmax(0,1fr))] border-b border-[#EAE6DF]/70 bg-[#F9F8F6] px-5 py-4 text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">
        <div>Engine</div>
        <div>Aligned</div>
        <div>Needs review</div>
        <div>Extra studies found</div>
      </div>
      {rows.map((row) => (
        <div key={row.key} className="grid grid-cols-[1.3fr_repeat(3,minmax(0,1fr))] items-center border-b border-[#EAE6DF]/70 px-5 py-4 last:border-b-0">
          <div className="pr-4">
            <div className="mt-2 text-sm font-bold text-[#2E2E2E]">{row.label}</div>
            <div className="mt-1 max-w-[22rem] text-xs leading-relaxed text-[#6B6B6B]">{row.description}</div>
          </div>
          <div className="text-lg font-black text-[#2E2E2E]">{row.engine?.aggregate.totalAligned ?? 0}</div>
          <div className="text-lg font-black text-[#2E2E2E]">{row.engine?.aggregate.totalManualReview ?? 0}</div>
          <div className="text-lg font-black text-[#2E2E2E]">{row.engine?.aggregate.totalRetrievalCandidates ?? 0}</div>
        </div>
      ))}
    </div>
  );
}

function EvaluationPanel({
  benchmarkResult,
  selectedPackId,
  selectedRetrievalMode,
  evaluationViewMode,
  isRunningBenchmark,
  benchmarkError,
  onPackChange,
  onRetrievalModeChange,
  onEvaluationViewModeChange,
  onRunBenchmark
}: {
  benchmarkResult: EngineBenchmarkResult | null;
  selectedPackId: "demo_presets" | "frozen_pack";
  selectedRetrievalMode: "hybrid" | "dense_only";
  evaluationViewMode: EvaluationViewMode;
  isRunningBenchmark: boolean;
  benchmarkError: string | null;
  onPackChange: (value: "demo_presets" | "frozen_pack") => void;
  onRetrievalModeChange: (value: "hybrid" | "dense_only") => void;
  onEvaluationViewModeChange: (value: EvaluationViewMode) => void;
  onRunBenchmark: () => void;
}) {
  const deterministic = benchmarkResult?.engines.find((engine) => engine.engineKey === "deterministic") ?? null;
  const hybrid = benchmarkResult?.engines.find((engine) => engine.engineKey === "hybrid_semantic") ?? null;
  const alignedDelta = (hybrid?.aggregate.totalAligned ?? 0) - (deterministic?.aggregate.totalAligned ?? 0);
  const retrievalDelta =
    (hybrid?.aggregate.totalRetrievalCandidates ?? 0) - (deterministic?.aggregate.totalRetrievalCandidates ?? 0);
  const decisionLayerLabel = benchmarkResult?.summary.semanticChangesDecisionLayer ? "Shared" : "Deterministic only";
  const packCompleteness = hybrid?.aggregate.packCompleteness ?? deterministic?.aggregate.packCompleteness ?? "n/a";
  const topicMatchRate = hybrid?.aggregate.topicMatchRate ?? deterministic?.aggregate.topicMatchRate ?? null;
  const primaryLabelHitRate = hybrid?.aggregate.primaryLabelHitRate ?? deterministic?.aggregate.primaryLabelHitRate ?? null;
  const caseRows = benchmarkResult?.engines[0]?.cases ?? [];
  const breakdown = benchmarkResult?.breakdown ?? null;
  const retrievalBreakdown = breakdown?.retrieval ?? null;
  const decisionBreakdown = breakdown?.decisionLayer ?? null;
  const caseDeltaMap = new Map((breakdown?.caseDeltas ?? []).map((item) => [item.caseId, item]));
  const activePackLabel = benchmarkPackOptions.find((option) => option.value === selectedPackId)?.label ?? selectedPackId;
  const activeModeLabel = selectedRetrievalMode === "hybrid" ? "Hybrid dense + sparse" : "Dense only";
  const benchmarkCaseTotal = hybrid?.aggregate.caseCount ?? deterministic?.aggregate.caseCount ?? 0;
  const topicMatchCount = benchmarkCaseCount(topicMatchRate, benchmarkCaseTotal);
  const primaryLabelHitCount = benchmarkCaseCount(primaryLabelHitRate, benchmarkCaseTotal);
  const recallRate = hybrid?.aggregate.averageExpectedRecall ?? deterministic?.aggregate.averageExpectedRecall ?? null;
  const hasBenchmarkResult = benchmarkResult !== null;

  return (
    <div className="space-y-6">
      <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-3xl space-y-3">
            <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Evaluation Lab</div>
            <h3 className="text-2xl font-black tracking-tight text-[#2E2E2E]">
              {evaluationViewMode === "simple" ? "Benchmark essentials view" : "Full benchmark audit mode"}
            </h3>
            <p className="text-sm leading-relaxed text-[#6B6B6B]">
              {evaluationViewMode === "simple"
                ? "This view keeps only the benchmark signals a non-specialist can read quickly: whether the frozen pack still lands on the right topics and labels, and whether semantic retrieval adds measurable breadth."
                : "Detailed mode keeps the full benchmark surface for debugging: per-case truth comparisons, explainability breakdowns, label distributions, and runtime-level observability."}
            </p>
          </div>

          <div className="flex flex-col items-start gap-4 xl:items-end">
            <EvaluationViewModeToggle value={evaluationViewMode} onChange={onEvaluationViewModeChange} />
            <button
              type="button"
              onClick={onRunBenchmark}
              disabled={isRunningBenchmark}
              className="rounded-full bg-[#C96557] px-5 py-3 text-sm font-bold text-white shadow-[0_10px_24px_rgba(201,101,87,0.22)] transition hover:bg-[#B65446] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isRunningBenchmark ? "Running benchmark..." : "Run live benchmark"}
            </button>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <span className="rounded-full bg-[#F0EBE3] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">
            Pack: {activePackLabel}
          </span>
          <span className="rounded-full bg-[#F0EBE3] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">
            Retrieval: {activeModeLabel}
          </span>
          <span className="rounded-full bg-[#E8F2EC] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#2D5940]">
            Final labels come from deterministic
          </span>
          <span className="rounded-full bg-[#FFF5F1] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#A63D2F]">
            Semantic adds more studies
          </span>
        </div>

        {evaluationViewMode === "detailed" ? (
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Case pack</span>
              <select
                value={selectedPackId}
                onChange={(event) => onPackChange(event.target.value as "demo_presets" | "frozen_pack")}
                className="w-full rounded-2xl border border-[#EAE6DF] bg-white px-4 py-3 text-sm font-semibold text-[#2E2E2E] outline-none transition focus:border-[#C96557]"
              >
                {benchmarkPackOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Hybrid retrieval mode</span>
              <select
                value={selectedRetrievalMode}
                onChange={(event) => onRetrievalModeChange(event.target.value as "hybrid" | "dense_only")}
                className="w-full rounded-2xl border border-[#EAE6DF] bg-white px-4 py-3 text-sm font-semibold text-[#2E2E2E] outline-none transition focus:border-[#C96557]"
              >
                <option value="hybrid">Hybrid dense + sparse</option>
                <option value="dense_only">Dense only</option>
              </select>
            </label>
          </div>
        ) : null}

        {benchmarkError ? (
          <div className="mt-5 rounded-[20px] border border-[#E9B7AC] bg-[#FBEAE5] px-4 py-3 text-sm font-semibold text-[#8B3E2F]">
            {benchmarkError}
          </div>
        ) : null}
      </div>

      {evaluationViewMode === "simple" ? (
        <div className="space-y-6">
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            <EvaluationCompactMetric
              label="Pack completeness"
              value={packCompleteness !== "n/a" ? packCompleteness : "Pending"}
              detail={
                hasBenchmarkResult
                  ? `These are the same ${benchmarkCaseTotal || 15} frozen cases every time.`
                  : "Run live benchmark to confirm the frozen pack is complete and active."
              }
              tone="warning"
            />
            <EvaluationCompactMetric
              label="Exact guideline topic match"
              value={formatRateOrZero(topicMatchRate)}
              detail={
                topicMatchCount === null
                  ? "Run live benchmark to see how many cases land on the exact expected guideline topic."
                  : `${topicMatchCount} of ${benchmarkCaseTotal} cases landed on the exact expected guideline topic. Higher is better. ${benchmarkRateAssessment(topicMatchRate)}`
              }
              tone="positive"
            />
            <EvaluationCompactMetric
              label="First label correct"
              value={formatRateOrZero(primaryLabelHitRate)}
              detail={
                primaryLabelHitCount === null
                  ? "Run live benchmark to see how often the first label shown on screen matches the benchmark."
                  : `${primaryLabelHitCount} of ${benchmarkCaseTotal} cases showed the expected first label on screen. Higher is better. ${benchmarkRateAssessment(primaryLabelHitRate)}`
              }
              tone="positive"
            />
            <EvaluationCompactMetric
              label="Retrieval breadth delta"
              value={formatDelta(retrievalDelta)}
              detail={
                hasBenchmarkResult
                  ? "How many additional grounded studies semantic retrieval surfaced across the pack."
                  : "Run live benchmark to compare how many extra studies semantic retrieval finds."
              }
              tone="accent"
            />
            <EvaluationCompactMetric
              label="Aligned delta"
              value={formatDelta(alignedDelta)}
              detail={
                hasBenchmarkResult
                  ? "How many more evidence items ended up aligned after semantic retrieval fed candidates back into deterministic rules."
                  : "Run live benchmark to compare how many additional evidence items become aligned."
              }
              tone={alignedDelta > 0 ? "positive" : alignedDelta < 0 ? "warning" : "neutral"}
            />
            <EvaluationCompactMetric
              label="Recall rate"
              value={formatRateOrZero(recallRate)}
              detail={
                recallRate === null
                  ? "Run live benchmark to measure how many expected benchmark studies the system recovers. Higher recall means fewer false negatives."
                  : `On average, the system recovered ${formatRate(recallRate)} of the expected benchmark studies across the frozen pack. Higher is better because it means fewer false negatives. ${benchmarkRateAssessment(recallRate)}`
              }
              tone="positive"
            />
          </div>

          <div className="space-y-5">
            <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
              <div className="mb-4">
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Two-engine comparison</div>
                <h4 className="mt-2 text-2xl font-black tracking-tight text-[#2E2E2E]">Deterministic vs semantic on this benchmark</h4>
              </div>
              <p className="mb-5 text-sm leading-relaxed text-[#6B6B6B]">
                {hasBenchmarkResult
                  ? "Deterministic still decides the final label. Semantic helps us find more studies to evaluate and can improve aligned results when those studies survive deterministic rules."
                  : "Run live benchmark to compare the deterministic and semantic paths on the same frozen cases."}
              </p>
              <EvaluationSimpleEngineTable deterministic={deterministic} hybrid={hybrid} />
            </div>
          </div>

          <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Observability footer</div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">Result state</div>
                <div className="mt-2 text-sm font-bold text-[#2E2E2E]">
                  {hasBenchmarkResult ? (benchmarkResult?.meta.cached ? "Cached" : "Fresh") : "Not run yet"}
                </div>
              </div>
              <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">Source fingerprint</div>
                <div className="mt-2 break-all text-sm font-bold text-[#2E2E2E]">{benchmarkResult?.meta.sourceFingerprint ?? "pending"}</div>
              </div>
              <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">Runtime fingerprint</div>
                <div className="mt-2 break-all text-sm font-bold text-[#2E2E2E]">{benchmarkResult?.meta.runtimeConfigFingerprint ?? "pending"}</div>
              </div>
              <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">Vector stack</div>
                <div className="mt-2 text-sm font-bold text-[#2E2E2E]">
                  {benchmarkResult?.meta.vectorStore ?? "n/a"}
                  {benchmarkResult?.meta.embeddingModel ? ` · ${benchmarkResult.meta.embeddingModel}` : ""}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            <EvaluationCompactMetric
              label="Benchmark pack"
              value={benchmarkResult?.summary.packLabel ?? "Loading..."}
              detail={`Run the same cases through both engines and compare live. Current result is ${benchmarkResult?.meta.cached ? "cached" : "fresh"}.`}
            />
            <EvaluationCompactMetric
              label="Aligned delta"
              value={formatDelta(alignedDelta)}
              detail="Hybrid minus deterministic across the full pack."
              tone={alignedDelta > 0 ? "positive" : alignedDelta < 0 ? "warning" : "neutral"}
            />
            <EvaluationCompactMetric
              label="Retrieval breadth delta"
              value={formatDelta(retrievalDelta)}
              detail="Extra semantic candidates surfaced by the hybrid lab path."
              tone="accent"
            />
            <EvaluationCompactMetric
              label="Topic match rate"
              value={formatRate(topicMatchRate)}
              detail="Canonical topic hit rate on the active pack."
              tone="positive"
            />
            <EvaluationCompactMetric
              label="Primary label hit rate"
              value={formatRate(primaryLabelHitRate)}
              detail="Expected primary label vs observed rank-1 label."
              tone="positive"
            />
            <EvaluationCompactMetric
              label="Pack completeness"
              value={packCompleteness}
              detail={`${decisionLayerLabel}. Semantic stays assistive, not authoritative.`}
              tone="warning"
            />
          </div>

          <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
              <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">What we validate</div>
              <div className="space-y-4">
                <div className="rounded-[24px] bg-[#F9F8F6] p-5">
                  <h3 className="text-lg font-black text-[#2E2E2E]">Frozen clinical vignettes</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#6B6B6B]">
                    We compare the same patient pack through both runtimes so the benchmark stays grounded in a real A/B instead of an architecture-only claim.
                  </p>
                </div>
                <div className="rounded-[24px] bg-[#F9F8F6] p-5">
                  <h3 className="text-lg font-black text-[#2E2E2E]">Label vocabulary control</h3>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {policy.safetyBoundaries.slice(0, 3).map((item) => (
                      <span key={item} className="rounded-full border border-[#EAE6DF] bg-white px-3 py-1.5 text-[11px] font-semibold text-[#2E2E2E]">
                        {item}
                      </span>
                    ))}
                    {frozenLabelVocabulary.map((label) => (
                      <span key={label} className="rounded-full bg-[#E8F2EC] px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.16em] text-[#2D5940]">
                        {label}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="rounded-[24px] bg-[#F9F8F6] p-5">
                  <h3 className="text-lg font-black text-[#2E2E2E]">Architecture honesty</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#6B6B6B]">
                    Hybrid semantic can win on retrieval breadth today without pretending it already owns the final decision layer. That nuance is the point.
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
              <div className="mb-4">
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Operator guide</div>
                <h3 className="mt-2 text-2xl font-black tracking-tight text-[#2E2E2E]">Expected vs observed</h3>
              </div>

              <div className="space-y-4">
                <div className="rounded-[24px] bg-[#F9F8F6] p-5">
                  <h3 className="text-lg font-black text-[#2E2E2E]">Expected</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#6B6B6B]">
                    The canonical benchmark truth for a vignette: expected primary label, expected guideline topic, and the curated PMID set from the frozen pack. This is the reference we compare the runtime against.
                  </p>
                </div>

                <div className="rounded-[24px] bg-[#F9F8F6] p-5">
                  <h3 className="text-lg font-black text-[#2E2E2E]">Observed</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#6B6B6B]">
                    What the selected engine actually promoted at run time: the rank-1 label, topic, retrieval counts, manual-review burden, and promoted PMIDs after deterministic rules close the loop.
                  </p>
                </div>

                <div className="rounded-[24px] bg-[#F9F8F6] p-5">
                  <h3 className="text-lg font-black text-[#2E2E2E]">How to read the delta</h3>
                  <div className="mt-3 space-y-3 text-sm leading-relaxed text-[#6B6B6B]">
                    <p><span className="font-semibold text-[#2E2E2E]">Healthy:</span> canonical PMID matched, topic match = yes, primary label hit = yes. Unexpected PMIDs may still appear if the engine surfaced extra grounded studies beyond the minimal gold set.</p>
                    <p><span className="font-semibold text-[#2E2E2E]">Needs review:</span> canonical PMID missed but primary label still hits. That usually means the engine is landing in the right clinical neighborhood but ranking or promotion is broad.</p>
                    <p><span className="font-semibold text-[#2E2E2E]">Alarm:</span> primary label miss or topic mismatch on canonical cases, especially if paired with many missed expected PMIDs. That points to retrieval drift, mapping drift, or benchmark assumptions that need recalibration.</p>
                  </div>
                </div>

                <div className="rounded-[24px] border border-[#EAE6DF]/70 bg-[#FCFBF8] p-5">
                  <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Observability rules</div>
                  <div className="space-y-2 text-sm leading-relaxed text-[#2E2E2E]">
                    <p>Use <span className="font-semibold">topic match rate</span> and <span className="font-semibold">primary label hit rate</span> as the fast benchmark health signal.</p>
                    <p>Use <span className="font-semibold">matched vs missed canonical PMIDs</span> to decide whether this is ranking breadth or a real recall problem.</p>
                    <p>Use <span className="font-semibold">source fingerprint</span> and <span className="font-semibold">runtime fingerprint</span> to confirm which exact corpus and runtime config produced the result.</p>
                    <p>Use <span className="font-semibold">unexpected promoted PMIDs</span> as a calibration clue, not an automatic failure. If both deterministic and hybrid show many of them, the benchmark truth may be intentionally sparse or the promotion window may be too wide.</p>
                  </div>
                </div>

                <div className="rounded-[24px] border border-[#EAE6DF]/70 bg-[#FCFBF8] p-5">
                  <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Benchmark takeaway</div>
                  <p className="text-sm leading-relaxed text-[#2E2E2E]">
                    {benchmarkResult?.summary.recommendedTakeaway ??
                      "Deterministic stays in charge of labels; semantic earns its keep by finding more grounded candidates."}
                  </p>
                  {benchmarkResult?.summary.benchmarkNarrative ? (
                    <div className="mt-3 rounded-[18px] border border-[#EAE6DF]/70 bg-white px-4 py-3 text-sm leading-relaxed text-[#4F4A43]">
                      <div className="mb-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">
                        LLM narrative · {benchmarkResult.summary.benchmarkNarrative.providerStatus}
                      </div>
                      {benchmarkResult.summary.benchmarkNarrative.summary}
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Explainability breakdown</div>
                <h3 className="mt-2 text-2xl font-black tracking-tight text-[#2E2E2E]">Why the live delta moved</h3>
              </div>
              <span className="rounded-full bg-[#F0EBE3] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">
                union + overlap
              </span>
            </div>

            <div className="grid gap-5 xl:grid-cols-2">
              <div className="rounded-[24px] bg-[#F9F8F6] p-5">
                <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Retrieval observability</div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-[20px] bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Hybrid unique evidence</div>
                    <div className="mt-1 text-2xl font-black text-[#2E2E2E]">{retrievalBreakdown?.hybridUniqueEvidenceCount ?? 0}</div>
                  </div>
                  <div className="rounded-[20px] bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Case-hit overlap</div>
                    <div className="mt-1 text-2xl font-black text-[#2E2E2E]">{retrievalBreakdown?.hybridOverlapCount ?? 0}</div>
                    <div className="mt-1 text-xs text-[#6B6B6B]">
                      {formatDelta(Math.round((retrievalBreakdown?.hybridOverlapRate ?? 0) * 100), "%")} duplicated across cases
                    </div>
                  </div>
                  <div className="rounded-[20px] bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Hybrid case hits</div>
                    <div className="mt-1 text-2xl font-black text-[#2E2E2E]">{retrievalBreakdown?.hybridCaseHitCountTotal ?? 0}</div>
                  </div>
                  <div className="rounded-[20px] bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Multi-case evidence IDs</div>
                    <div className="mt-1 text-2xl font-black text-[#2E2E2E]">{retrievalBreakdown?.hybridMultiCaseEvidenceCount ?? 0}</div>
                  </div>
                </div>

                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div className="rounded-[20px] border border-[#EAE6DF]/70 bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Sample hybrid-only IDs</div>
                    <EvidenceIdChips ids={retrievalBreakdown?.sampleHybridOnlyEvidenceIds ?? []} />
                  </div>
                  <div className="rounded-[20px] border border-[#EAE6DF]/70 bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Sample overlapping IDs</div>
                    <EvidenceIdChips ids={retrievalBreakdown?.sampleMultiCaseEvidenceIds ?? []} emptyLabel="No multi-case overlap sampled" />
                  </div>
                </div>
              </div>

              <div className="rounded-[24px] bg-[#F9F8F6] p-5">
                <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Decision-layer movement</div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-[20px] bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Promoted aligned</div>
                    <div className={`mt-1 text-2xl font-black ${metricTone(decisionBreakdown?.alignedDelta ?? 0)}`}>
                      {decisionBreakdown?.promotedAlignedUniqueCount ?? 0}
                    </div>
                  </div>
                  <div className="rounded-[20px] bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Promoted silent</div>
                    <div className={`mt-1 text-2xl font-black ${metricTone(decisionBreakdown?.guidelineSilentDelta ?? 0)}`}>
                      {decisionBreakdown?.promotedGuidelineSilentUniqueCount ?? 0}
                    </div>
                  </div>
                  <div className="rounded-[20px] bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Promoted manual</div>
                    <div className={`mt-1 text-2xl font-black ${metricTone(decisionBreakdown?.manualReviewDelta ?? 0)}`}>
                      {decisionBreakdown?.promotedManualReviewUniqueCount ?? 0}
                    </div>
                  </div>
                </div>

                <div className="mt-4 grid gap-4">
                  <div className="rounded-[20px] border border-[#EAE6DF]/70 bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Sample promoted aligned IDs</div>
                    <EvidenceIdChips ids={decisionBreakdown?.samplePromotedAlignedEvidenceIds ?? []} />
                  </div>
                  <div className="rounded-[20px] border border-[#EAE6DF]/70 bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Sample promoted manual-review IDs</div>
                    <EvidenceIdChips ids={decisionBreakdown?.samplePromotedManualReviewEvidenceIds ?? []} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            {benchmarkResult?.engines.map((engine) => (
              <div key={engine.engineKey} className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">
                      {engine.runtimeEngine === "deterministic" ? "Current authority" : "Experimental challenger"}
                    </div>
                    <h3 className="mt-2 text-2xl font-black tracking-tight text-[#2E2E2E]">{engine.label}</h3>
                  </div>
                  <span
                    className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] ${
                      engine.status === "available" ? "bg-[#E8F2EC] text-[#2D5940]" : "bg-[#FBEAE5] text-[#A63D2F]"
                    }`}
                  >
                    {engine.status}
                  </span>
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Aligned</div>
                    <div className="mt-2 text-2xl font-black text-[#2E2E2E]">{engine.aggregate.totalAligned}</div>
                  </div>
                  <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Top evidence</div>
                    <div className="mt-2 text-2xl font-black text-[#2E2E2E]">{engine.aggregate.totalTopEvidence}</div>
                  </div>
                  <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Manual review</div>
                    <div className="mt-2 text-2xl font-black text-[#2E2E2E]">{engine.aggregate.totalManualReview}</div>
                  </div>
                  <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Retrieval candidates</div>
                    <div className="mt-2 text-2xl font-black text-[#2E2E2E]">{engine.aggregate.totalRetrievalCandidates}</div>
                  </div>
                  <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Topic match</div>
                    <div className="mt-2 text-2xl font-black text-[#2E2E2E]">{formatRate(engine.aggregate.topicMatchRate)}</div>
                  </div>
                  <div className="rounded-[20px] bg-[#F9F8F6] px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Primary label hit</div>
                    <div className="mt-2 text-2xl font-black text-[#2E2E2E]">{formatRate(engine.aggregate.primaryLabelHitRate)}</div>
                  </div>
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div className="rounded-[20px] border border-[#EAE6DF]/70 bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Expected label distribution</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(engine.aggregate.expectedLabelDistribution).map(([label, count]) => (
                        <span key={label} className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] ${labelBadgeStyles(label)}`}>
                          {label} {count}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[20px] border border-[#EAE6DF]/70 bg-white px-4 py-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Observed label distribution</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(engine.aggregate.observedLabelDistribution).map(([label, count]) => (
                        <span key={label} className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] ${labelBadgeStyles(label)}`}>
                          {label} {count}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  <div className="rounded-[18px] border border-[#EAE6DF]/70 bg-white px-4 py-3 text-sm text-[#6B6B6B]">
                    {engine.aggregate.packCompleteness}
                  </div>
                  {engine.notes.map((note) => (
                    <div key={note} className="rounded-[18px] bg-[#FCFBF8] px-4 py-3 text-sm leading-relaxed text-[#6B6B6B]">
                      {note}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Case-by-case comparison</div>
                <h3 className="mt-2 text-2xl font-black tracking-tight text-[#2E2E2E]">Where hybrid actually changes the live story</h3>
              </div>
              <span className="rounded-full bg-[#F0EBE3] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">
                {benchmarkResult?.evalRunId ?? "Pending"}
              </span>
            </div>

            <div className="space-y-4">
              <div className="rounded-[20px] border border-[#EAE6DF]/70 bg-white px-4 py-4 text-sm leading-relaxed text-[#6B6B6B]">
                <span className="font-semibold text-[#2E2E2E]">What &quot;unexpected promoted&quot; means:</span> these are PMIDs promoted into the engine&apos;s top evidence for a case, but not included in the canonical expected PMID set for that vignette. If you see many of them in both deterministic and hybrid, that usually means the gold set is intentionally selective or the promotion window is broad, not that semantic alone is hallucinating. The key signal is whether canonical PMIDs are matched or missed and whether the primary label and topic still hit.
              </div>
              {caseRows.map((caseRow) => {
                const detCase = deterministic?.cases.find((item) => item.caseId === caseRow.caseId) ?? null;
                const hybridCase = hybrid?.cases.find((item) => item.caseId === caseRow.caseId) ?? null;
                const caseDelta = caseDeltaMap.get(caseRow.caseId);
                const caseAlignedDelta =
                  (hybridCase?.metrics?.alignedCount ?? 0) - (detCase?.metrics?.alignedCount ?? 0);
                const caseRetrievalDelta =
                  (hybridCase?.metrics?.retrievalCandidateCount ?? 0) - (detCase?.metrics?.retrievalCandidateCount ?? 0);
                const deterministicUnexpectedIds = new Set(detCase?.comparison?.unexpectedPromotedEvidenceIds ?? []);

                return (
                  <div key={caseRow.caseId} className="rounded-[24px] border border-[#EAE6DF]/70 bg-[#FCFBF8] p-5">
                    <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">{caseRow.caseLabel}</div>
                          {caseRow.category ? (
                            <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">
                              {caseRow.category.replaceAll("_", " ")}
                            </span>
                          ) : null}
                        </div>
                        <h4 className="mt-1 text-lg font-black text-[#2E2E2E]">{caseRow.detail}</h4>
                        {caseRow.clinicalQuestion ? (
                          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-[#6B6B6B]">{caseRow.clinicalQuestion}</p>
                        ) : null}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] ${metricTone(caseAlignedDelta)}`}>
                          aligned {formatDelta(caseAlignedDelta)}
                        </span>
                        <span className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] ${metricTone(caseRetrievalDelta)}`}>
                          retrieval {formatDelta(caseRetrievalDelta)}
                        </span>
                      </div>
                    </div>

                    {caseDelta ? (
                      <div className="mb-4 grid gap-3 md:grid-cols-3">
                        <div className="rounded-[18px] bg-white px-4 py-3">
                          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Hybrid-only retrieval</div>
                          <div className="mt-1 text-lg font-black text-[#2E2E2E]">{caseDelta.hybridOnlyRetrievalCount}</div>
                        </div>
                        <div className="rounded-[18px] bg-white px-4 py-3">
                          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Promoted aligned</div>
                          <div className={`mt-1 text-lg font-black ${metricTone(caseDelta.promotedAlignedCount)}`}>{caseDelta.promotedAlignedCount}</div>
                        </div>
                        <div className="rounded-[18px] bg-white px-4 py-3">
                          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Promoted manual</div>
                          <div className={`mt-1 text-lg font-black ${metricTone(caseDelta.promotedManualReviewCount)}`}>{caseDelta.promotedManualReviewCount}</div>
                        </div>
                      </div>
                    ) : null}

                    <div className="grid gap-4 lg:grid-cols-2">
                      {[detCase, hybridCase].map((engineCase, index) => (
                        <div key={`${caseRow.caseId}-${index}`} className="rounded-[20px] bg-white p-4">
                          <div className="mb-3 flex items-center justify-between gap-3">
                            <div className="text-sm font-bold text-[#2E2E2E]">
                              {index === 0 ? "Deterministic Runtime" : "Hybrid Semantic Lab"}
                            </div>
                            <span className="rounded-full bg-[#F0EBE3] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">
                              {engineCase?.status ?? "unknown"}
                            </span>
                          </div>
                          {engineCase?.metrics ? (
                            <div className="space-y-3">
                              <div className="grid gap-3 md:grid-cols-2">
                                <div className="rounded-[16px] bg-[#F9F8F6] px-3 py-3">
                                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Expected</div>
                                  <div className="mt-2 flex flex-wrap gap-2">
                                    <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${labelBadgeStyles(engineCase.reference?.expectedPrimaryLabel)}`}>
                                      {engineCase.reference?.expectedPrimaryLabel ?? "none"}
                                    </span>
                                    <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-semibold text-[#4F4A43]">
                                      {engineCase.reference?.expectedGuidelineTopicId ?? "no topic"}
                                    </span>
                                  </div>
                                  <div className="mt-2 text-xs text-[#6B6B6B]">
                                    PMID: {engineCase.reference?.expectedEvidenceIds.join(", ") || "none"}
                                  </div>
                                </div>
                                <div className="rounded-[16px] bg-[#F9F8F6] px-3 py-3">
                                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Observed</div>
                                  <div className="mt-2 flex flex-wrap gap-2">
                                    <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${labelBadgeStyles(engineCase.comparison?.observedPrimaryLabel)}`}>
                                      {engineCase.comparison?.observedPrimaryLabel ?? "none"}
                                    </span>
                                    <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-semibold text-[#4F4A43]">
                                      {engineCase.comparison?.observedGuidelineTopicId ?? "no topic"}
                                    </span>
                                  </div>
                                  <div className="mt-2 text-xs text-[#6B6B6B]">
                                    retrieval {engineCase.metrics.retrievalCandidateCount} · manual {engineCase.metrics.manualReviewCount} · uncertainty {engineCase.metrics.uncertaintyFlagCount}
                                  </div>
                                </div>
                              </div>

                              <div className="grid gap-3 md:grid-cols-2">
                                <div className="rounded-[16px] border border-[#EAE6DF]/70 bg-white px-3 py-3">
                                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Delta</div>
                                  <div className="mt-2 text-xs leading-relaxed text-[#4F4A43]">
                                    Topic match: <span className="font-semibold">{engineCase.comparison?.topicMatch === null ? "n/a" : engineCase.comparison?.topicMatch ? "yes" : "no"}</span>
                                  </div>
                                  <div className="mt-1 text-xs leading-relaxed text-[#4F4A43]">
                                    Primary label hit: <span className="font-semibold">{engineCase.comparison?.primaryLabelHit === null ? "n/a" : engineCase.comparison?.primaryLabelHit ? "yes" : "no"}</span>
                                  </div>
                                  <div className="mt-2">
                                    <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">Matched PMID</div>
                                    <EvidenceIdChips ids={engineCase.comparison?.matchedExpectedEvidenceIds ?? []} emptyLabel="No canonical PMID match" />
                                  </div>
                                  <div className="mt-2">
                                    <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">Missed PMID</div>
                                    <EvidenceIdChips ids={engineCase.comparison?.missedExpectedEvidenceIds ?? []} emptyLabel="No missed PMID" />
                                  </div>
                                </div>
                                <div className="rounded-[16px] border border-[#EAE6DF]/70 bg-white px-3 py-3">
                                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Why</div>
                                  <p className="mt-2 text-sm leading-relaxed text-[#4F4A43]">
                                    {engineCase.comparison?.why ?? "No canonical comparison available."}
                                  </p>
                                  <div className="mt-3">
                                    <UnexpectedPromotedDisclosure
                                      ids={engineCase.comparison?.unexpectedPromotedEvidenceIds ?? []}
                                      hybridOnlyIds={
                                        index === 1
                                          ? (engineCase.comparison?.unexpectedPromotedEvidenceIds ?? []).filter((id) => !deterministicUnexpectedIds.has(id))
                                          : []
                                      }
                                    />
                                  </div>
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="text-sm text-[#8B3E2F]">{engineCase?.error ?? "Benchmark failed for this case."}</div>
                          )}
                        </div>
                      ))}
                    </div>

                    {caseDelta ? (
                      <div className="mt-4 grid gap-3 lg:grid-cols-3">
                        <div className="rounded-[18px] border border-[#EAE6DF]/70 bg-white px-4 py-3">
                          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Sample retrieval IDs</div>
                          <EvidenceIdChips ids={caseDelta.sampleRetrievalEvidenceIds} />
                        </div>
                        <div className="rounded-[18px] border border-[#EAE6DF]/70 bg-white px-4 py-3">
                          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Promoted aligned IDs</div>
                          <EvidenceIdChips ids={caseDelta.samplePromotedAlignedEvidenceIds} emptyLabel="No aligned promotions" />
                        </div>
                        <div className="rounded-[18px] border border-[#EAE6DF]/70 bg-white px-4 py-3">
                          <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">Promoted manual IDs</div>
                          <EvidenceIdChips ids={caseDelta.samplePromotedManualReviewEvidenceIds} emptyLabel="No manual-review promotions" />
                        </div>
                      </div>
                    ) : null}
                  </div>
                );
              })}

              {!benchmarkResult ? (
                <div className="rounded-[24px] bg-[#F9F8F6] p-5 text-sm text-[#6B6B6B]">Benchmark results will appear here after the first run.</div>
              ) : null}
            </div>

            <div className="mt-5 grid gap-3">
              {benchmarkResult?.notes.map((note) => (
                <div key={note} className="rounded-[18px] bg-[#F9F8F6] px-4 py-3 text-sm leading-relaxed text-[#6B6B6B]">
                  {note}
                </div>
              ))}
              {benchmarkResult?.meta ? (
                <div className="rounded-[18px] border border-[#EAE6DF]/70 bg-white px-4 py-3 text-sm text-[#6B6B6B]">
                  Source fingerprint: PubMed batch <span className="font-semibold text-[#2E2E2E]">{benchmarkResult.meta.pubmedBatchId ?? "none"}</span>, semantic job{" "}
                  <span className="font-semibold text-[#2E2E2E]">{benchmarkResult.meta.pubmedSemanticJobId ?? "none"}</span>, source hash{" "}
                  <span className="font-semibold text-[#2E2E2E]">{benchmarkResult.meta.sourceFingerprint}</span>, runtime hash{" "}
                  <span className="font-semibold text-[#2E2E2E]">{benchmarkResult.meta.runtimeConfigFingerprint}</span>.
                </div>
              ) : null}
              {benchmarkResult?.summary.headline ? (
                <div className="rounded-[18px] border border-[#EAE6DF]/70 bg-white px-4 py-3 text-sm font-semibold text-[#2E2E2E]">
                  {benchmarkResult.summary.headline}
                </div>
              ) : null}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function EmbeddingAtlasPanel({
  manifest,
  points,
  neighbors,
  selectedPointId,
  sourceFilter,
  onSelectPoint,
  onSourceFilterChange,
}: {
  manifest: EmbeddingManifest | null;
  points: EmbeddingPoint[];
  neighbors: EmbeddingNeighbor[];
  selectedPointId: string | null;
  sourceFilter: "all" | "pubmed" | "esmo";
  onSelectPoint: (pointId: string) => void;
  onSourceFilterChange: (value: "all" | "pubmed" | "esmo") => void;
}) {
  const selectedPoint = points.find((point) => point.pointId === selectedPointId) ?? points[0] ?? null;
  const displayPoints = [...points].sort((left, right) => {
    if (left.pointId === selectedPointId) {
      return 1;
    }
    if (right.pointId === selectedPointId) {
      return -1;
    }
    if (left.sourceType === right.sourceType) {
      return left.pointId.localeCompare(right.pointId);
    }
    return left.sourceType === "pubmed" ? -1 : 1;
  });

  return (
    <div className="space-y-6">
      <div className="grid gap-5 md:grid-cols-4">
        <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6">
          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Points</div>
          <div className="mt-3 text-3xl font-black text-[#2E2E2E]">{manifest?.pointCount ?? 0}</div>
        </div>
        <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6">
          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Vector store</div>
          <div className="mt-3 text-lg font-black text-[#2E2E2E]">{manifest?.vectorStore ?? "loading"}</div>
        </div>
        <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6">
          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Embedding model</div>
          <div className="mt-3 text-lg font-black text-[#2E2E2E]">{manifest?.embeddingModel ?? "loading"}</div>
        </div>
        <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6">
          <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Projection</div>
          <div className="mt-3 text-lg font-black text-[#2E2E2E]">{manifest?.projectionMethod ?? "loading"}</div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Embedding Atlas</div>
              <h3 className="mt-2 text-2xl font-black tracking-tight text-[#2E2E2E]">Projector-style chunk map</h3>
            </div>
            <select
              value={sourceFilter}
              onChange={(event) => onSourceFilterChange(event.target.value as "all" | "pubmed" | "esmo")}
              className="rounded-full border border-[#EAE6DF] bg-white px-4 py-2 text-[11px] font-bold uppercase tracking-[0.18em] text-[#2E2E2E] outline-none"
            >
              <option value="all">All sources</option>
              <option value="pubmed">PubMed</option>
              <option value="esmo">ESMO</option>
            </select>
          </div>

          <div className="relative h-[420px] overflow-hidden rounded-[28px] border border-[#EAE6DF]/80 bg-[#201B1A]">
            <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(to_right,rgba(255,255,255,0.12)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.12)_1px,transparent_1px)] [background-size:28px_28px]" />
            {displayPoints.map((point) => {
              const baseLeft = `${Math.min(Math.max(((point.x + 1.1) / 2.2) * 100, 4), 96)}%`;
              const baseTop = `${Math.min(Math.max(((point.y + 1.1) / 2.2) * 100, 6), 94)}%`;
              const isActive = selectedPoint?.pointId === point.pointId;
              const isEsmo = point.sourceType === "esmo";
              const shouldSeparateSources = sourceFilter === "all";
              const left = shouldSeparateSources && isEsmo ? `calc(${baseLeft} + 3px)` : baseLeft;
              const top = shouldSeparateSources && isEsmo ? `calc(${baseTop} - 3px)` : baseTop;
              const pointColor = isEsmo ? "bg-[#C96557]" : "bg-[#8AB0A6]";
              return (
                <button
                  key={point.pointId}
                  type="button"
                  onClick={() => onSelectPoint(point.pointId)}
                  className={`absolute h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full transition-transform ${
                    isEsmo
                      ? "border border-[#FFD4CC]/90 shadow-[0_8px_20px_rgba(201,101,87,0.20)]"
                      : "border border-white/50 opacity-80 shadow-[0_8px_24px_rgba(0,0,0,0.18)]"
                  } ${pointColor} ${isActive ? "scale-150" : "hover:scale-125"}`}
                  style={{ left, top, zIndex: isActive ? 30 : isEsmo ? 15 : 10 }}
                  title={point.title}
                />
              );
            })}
          </div>
        </div>

        <div className="space-y-5">
          <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
            <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Selected point</div>
            {selectedPoint ? (
              <div className="space-y-3">
                <h3 className="text-lg font-black text-[#2E2E2E]">{selectedPoint.title}</h3>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-[#F0EBE3] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">
                    {selectedPoint.sourceType}
                  </span>
                  <span className="rounded-full bg-[#E8F2EC] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-[#2D5940]">
                    {selectedPoint.histology}
                  </span>
                </div>
                <p className="text-sm leading-relaxed text-[#6B6B6B]">
                  {selectedPoint.sourceId} {selectedPoint.topicId ? `· ${selectedPoint.topicId}` : ""}
                </p>
              </div>
            ) : (
              <p className="text-sm leading-relaxed text-[#6B6B6B]">Import semantic corpora to populate the atlas.</p>
            )}
          </div>

          <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
            <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Nearest neighbors</div>
            <div className="space-y-3">
              {neighbors.map((neighbor) => (
                <div key={neighbor.pointId} className="rounded-[22px] bg-[#F9F8F6] p-4">
                  <div className="text-sm font-semibold text-[#2E2E2E]">{neighbor.title}</div>
                  <div className="mt-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">
                    {neighbor.sourceType} · similarity {neighbor.similarity.toFixed(3)}
                  </div>
                </div>
              ))}
              {neighbors.length === 0 ? (
                <div className="rounded-[22px] bg-[#F9F8F6] p-4 text-sm text-[#6B6B6B]">Select a point to inspect neighbors.</div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DebugConsolePanel({
  versionManifest,
  debugConfig,
  debugLogs,
  navigatorPreferences,
  datasetKind,
  datasetPath,
  datasetBrowser,
  validationReport,
  importResult,
  semanticStatus,
  isRunningDatasetAction,
  datasetActionError,
  onDatasetKindChange,
  onDatasetPathChange,
  onValidateDataset,
  onImportDataset,
  onAppendDataset,
  onImportSemanticDataset,
  onNavigatorPreferenceToggle,
  onStrictImportToggle,
  onSemanticRetrievalToggle,
  onLlmImportToggle,
  onLlmExplainabilityToggle,
  isSavingImportConfig
}: {
  versionManifest: VersionManifest;
  debugConfig: ImportDebugConfig;
  debugLogs: ImportDebugLogEntry[];
  navigatorPreferences: NavigatorDebugPreferences;
  datasetKind: "esmo" | "pubmed";
  datasetPath: string;
  datasetBrowser: DatasetBrowserResponse | null;
  validationReport: ValidationReport | null;
  importResult: ImportBatch | null;
  semanticStatus: SemanticImportStatus | null;
  isRunningDatasetAction: boolean;
  datasetActionError: string | null;
  onDatasetKindChange: (datasetKind: "esmo" | "pubmed") => void;
  onDatasetPathChange: (datasetPath: string) => void;
  onValidateDataset: () => void;
  onImportDataset: () => void;
  onAppendDataset: () => void;
  onImportSemanticDataset: () => void;
  onNavigatorPreferenceToggle: () => void;
  onStrictImportToggle: () => void;
  onSemanticRetrievalToggle: () => void;
  onLlmImportToggle: () => void;
  onLlmExplainabilityToggle: () => void;
  isSavingImportConfig: boolean;
}) {
  const appendOnlyDemoPath = isPubmedAppendOnlyDemoPath(datasetKind, datasetPath);

  return (
    <div className="space-y-6">
      <BuildNotesSection versionManifest={versionManifest} />

      <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-4">
          <ToggleRow
            title="Show Additional Clinical Modifiers"
            description="This controls the extra Patient Profile field in Navigator. Keep it off for the clean demo flow, or turn it on when you want the advanced input visible."
            enabled={navigatorPreferences.showClinicalModifiers}
            onToggle={onNavigatorPreferenceToggle}
            badge="Navigator UI"
          />
          <ToggleRow
            title="Strict MVP PubMed validation"
            description="When enabled, PubMed imports are blocked if they drift outside the MVP evidence policy or arrive with unresolved critical fields."
            enabled={debugConfig.strictMvpPubmed}
            onToggle={onStrictImportToggle}
            disabled={isSavingImportConfig}
            badge={isSavingImportConfig ? "Saving" : "Import pipeline"}
          />
          <ToggleRow
            title="Semantic Retrieval"
            description="Master switch for the live demo. Turning it on enables semantic retrieval and routes Navigator runs through the Semantic Retrieval Lab path."
            enabled={debugConfig.semanticRetrievalEnabled}
            onToggle={onSemanticRetrievalToggle}
            disabled={isSavingImportConfig}
            badge="Master switch"
          />
          <ReadOnlyStatusRow
            title="Runtime engine status"
            value={debugConfig.runtimeEngine === "semantic_retrieval_lab" ? "Semantic runtime" : "Deterministic runtime"}
            tone={debugConfig.runtimeEngine === "semantic_retrieval_lab" ? "positive" : "neutral"}
            badge="Read only"
          />
          <ReadOnlyStatusRow
            title="Semantic corpus status"
            value={debugConfig.semanticRetrievalEnabled ? `${debugConfig.retrievalMode} ready` : "Semantic path off"}
            tone={debugConfig.semanticRetrievalEnabled ? "positive" : "warning"}
            badge="Read only"
          />
          <ToggleRow
            title="LLM import assist"
            description="Allows non-authoritative semantic assistance during ingestion. Suggestions stay advisory and never overwrite deterministic normalization."
            enabled={debugConfig.llmImportAssistEnabled}
            onToggle={onLlmImportToggle}
            disabled={isSavingImportConfig}
            badge="Assistive"
          />
          <ToggleRow
            title="LLM explainability"
            description="Enables grounded explainability summaries sourced only from retrieved chunks. Final labels remain deterministic."
            enabled={debugConfig.llmExplainabilityEnabled}
            onToggle={onLlmExplainabilityToggle}
            disabled={isSavingImportConfig}
            badge="Grounded"
          />
          <div className="rounded-[24px] border border-[#EAE6DF]/70 bg-[#FCFBF8] p-5">
            <div className="mb-2 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">
              <CheckCircle2 size={14} />
              Live behavior now
            </div>
            <p className="text-sm leading-relaxed text-[#2E2E2E]">
              Patient Profile filters stage changes locally. The analysis only runs when the user presses <strong>Run Analysis</strong>. The live engine is currently{" "}
              <strong>{debugConfig.runtimeEngine === "semantic_retrieval_lab" ? "Semantic Retrieval Lab" : "Deterministic Runtime"}</strong>.
            </p>
          </div>
          <div className="rounded-[24px] border border-[#EAE6DF]/70 bg-[#FCFBF8] p-5">
            <div className="mb-4 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">
              <FileSearch size={14} />
              Dataset operations
            </div>
            <p className="mb-4 text-sm leading-relaxed text-[#6B6B6B]">
              These actions run against the backend you are currently viewing. Local UI talks to local API. Production UI talks to production API.
            </p>
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-[180px_1fr]">
                <label className="space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Dataset kind</span>
                  <select
                    value={datasetKind}
                    onChange={(event) => onDatasetKindChange(event.target.value as "esmo" | "pubmed")}
                    className="w-full rounded-2xl border border-[#EAE6DF] bg-white px-4 py-3 text-sm font-semibold text-[#2E2E2E] outline-none transition focus:border-[#C96557]"
                  >
                    <option value="esmo">ESMO</option>
                    <option value="pubmed">PubMed</option>
                  </select>
                </label>
                <label className="space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Dataset path</span>
                  <input
                    type="text"
                    value={datasetPath}
                    onChange={(event) => onDatasetPathChange(event.target.value)}
                    placeholder={datasetKind === "esmo" ? "datasets/esmo/v.5/your-file.json" : "datasets/pubmed/v.4/your-file.csv"}
                    className="w-full rounded-2xl border border-[#EAE6DF] bg-white px-4 py-3 text-sm font-semibold text-[#2E2E2E] outline-none transition focus:border-[#C96557]"
                  />
                </label>
              </div>

              {datasetKind === "esmo" ? (
                <div className="rounded-[20px] border border-[#EAE6DF]/70 bg-[#FCFBF8] px-4 py-3 text-sm text-[#6B6B6B]">
                  Recommended quick path: <span className="font-semibold text-[#2E2E2E]">datasets/esmo/v.5/ESMO_Stage_I-III_NSCLC_Treatment_Recommendations_v5_explicit_topicIds.json</span>
                </div>
              ) : null}

              {datasetBrowser ? (
                <label className="space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Quick pick from repo</span>
                  <select
                    value={datasetBrowser.entries.some((entry) => entry.path === datasetPath) ? datasetPath : ""}
                    onChange={(event) => onDatasetPathChange(event.target.value)}
                    className="w-full rounded-2xl border border-[#EAE6DF] bg-white px-4 py-3 text-sm font-semibold text-[#2E2E2E] outline-none transition focus:border-[#C96557]"
                  >
                    <option value="">Choose a folder or file under {datasetBrowser.rootPath}</option>
                    <optgroup label="Folders">
                      {datasetBrowser.entries
                        .filter((entry) => entry.kind === "folder")
                        .map((entry) => (
                          <option key={entry.path} value={entry.path}>
                            {entry.path} ({entry.fileCount} files)
                          </option>
                        ))}
                    </optgroup>
                    <optgroup label="Files">
                      {datasetBrowser.entries
                        .filter((entry) => entry.kind === "file")
                        .map((entry) => (
                          <option key={entry.path} value={entry.path}>
                            {entry.path}
                          </option>
                        ))}
                    </optgroup>
                  </select>
                </label>
              ) : null}

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={onValidateDataset}
                  disabled={isRunningDatasetAction}
                  className="rounded-full border border-[#EAE6DF] bg-white px-5 py-3 text-sm font-bold text-[#2E2E2E] transition hover:border-[#C96557] hover:text-[#A63D2F] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isRunningDatasetAction ? "Working..." : "Validate"}
                </button>
                <button
                  type="button"
                  onClick={onImportDataset}
                  disabled={isRunningDatasetAction || appendOnlyDemoPath}
                  className="rounded-full bg-[#C96557] px-5 py-3 text-sm font-bold text-white shadow-[0_10px_24px_rgba(201,101,87,0.22)] transition hover:bg-[#B65446] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isRunningDatasetAction ? "Working..." : "Replace Corpus"}
                </button>
                <button
                  type="button"
                  onClick={onAppendDataset}
                  disabled={isRunningDatasetAction}
                  className="rounded-full border border-[#C96557] bg-[#FFF5F1] px-5 py-3 text-sm font-bold text-[#A63D2F] transition hover:bg-[#FBEAE5] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isRunningDatasetAction ? "Working..." : datasetKind === "pubmed" ? "Append Delta" : "Append Corpus"}
                </button>
                {datasetKind === "pubmed" ? (
                  <div className="w-full rounded-[20px] border border-[#EAE6DF]/70 bg-[#FCFBF8] px-4 py-3 text-sm text-[#6B6B6B]">
                    {appendOnlyDemoPath
                      ? "This demo PubMed file is append-only. `Replace Corpus` is disabled on purpose so the live delta set cannot overwrite the full evidence base."
                      : "`Append Delta` keeps the current PubMed corpus intact, upserts only the selected records, and refreshes semantic/Qdrant artifacts just for that delta. `Replace Corpus` rewrites the active PubMed dataset."}
                  </div>
                ) : (
                  <div className="w-full rounded-[20px] border border-[#EAE6DF]/70 bg-[#FCFBF8] px-4 py-3 text-sm text-[#6B6B6B]">
                    <strong>`Replace Corpus`</strong> clears the active ESMO guideline set and loads only the selected file or folder.{" "}
                    <strong>`Append Corpus`</strong> merges the selected ESMO rows into the current corpus by `topicId`, so you can layer Stage I-III on top of metastatic or vice versa.
                  </div>
                )}
                {datasetKind === "pubmed" ? (
                  <button
                    type="button"
                    onClick={onImportSemanticDataset}
                    disabled={isRunningDatasetAction}
                    className="rounded-full bg-[#201B1A] px-5 py-3 text-sm font-bold text-white shadow-[0_10px_24px_rgba(32,27,26,0.22)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isRunningDatasetAction ? "Working..." : "Index Semantic Corpus"}
                  </button>
                ) : (
                <button
                  type="button"
                  onClick={onImportSemanticDataset}
                  disabled={isRunningDatasetAction}
                  className="rounded-full bg-[#201B1A] px-5 py-3 text-sm font-bold text-white shadow-[0_10px_24px_rgba(32,27,26,0.22)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isRunningDatasetAction ? "Working..." : "Index Semantic Corpus"}
                </button>
                )}
              </div>

              {datasetActionError ? (
                <div className="rounded-[20px] border border-[#E9B7AC] bg-[#FBEAE5] px-4 py-3 text-sm font-semibold text-[#8B3E2F]">
                  {datasetActionError}
                </div>
              ) : null}

              {validationReport ? (
                <div className="rounded-[24px] border border-[#EAE6DF]/70 bg-white p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Last validation</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{validationReport.path}</div>
                    </div>
                    <span className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] ${statusBadgeStyles(validationReport.errorCount ? "failed" : validationReport.warningCount ? "warning" : "completed")}`}>
                      {validationReport.errorCount ? "Blocking issues" : validationReport.warningCount ? "Warnings only" : "Clean"}
                    </span>
                  </div>
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-[18px] bg-[#F9F8F6] px-4 py-3">
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Shape</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{validationReport.datasetShape}</div>
                    </div>
                    <div className="rounded-[18px] bg-[#F9F8F6] px-4 py-3">
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Errors</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{validationReport.errorCount}</div>
                    </div>
                    <div className="rounded-[18px] bg-[#F9F8F6] px-4 py-3">
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Warnings</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{validationReport.warningCount}</div>
                    </div>
                  </div>
                  <div className="mt-4 space-y-2">
                    {validationReport.errors.slice(0, 6).map((issue, index) => (
                      <div key={`${issue.code}-${index}`} className="rounded-[18px] bg-[#FBEAE5] px-4 py-3 text-sm text-[#8B3E2F]">
                        <strong>{issue.code}</strong>: {issue.message}
                      </div>
                    ))}
                    {validationReport.warnings.slice(0, 6).map((issue, index) => (
                      <div key={`${issue.code}-${index}`} className="rounded-[18px] bg-[#F6E7C8] px-4 py-3 text-sm text-[#8A5A13]">
                        <strong>{issue.code}</strong>: {issue.message}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {importResult ? (
                <div className="rounded-[24px] border border-[#EAE6DF]/70 bg-white p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Last import</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{importResult.batchId}</div>
                    </div>
                    <span className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] ${statusBadgeStyles(importResult.status)}`}>
                      {importResult.status}
                    </span>
                  </div>
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-[18px] bg-[#F9F8F6] px-4 py-3">
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Records</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{importResult.importedCount} / {importResult.recordCount}</div>
                    </div>
                    <div className="rounded-[18px] bg-[#F9F8F6] px-4 py-3">
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Warnings</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{importResult.warningCount}</div>
                    </div>
                    <div className="rounded-[18px] bg-[#F9F8F6] px-4 py-3">
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Errors</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{importResult.errorCount}</div>
                    </div>
                  </div>
                </div>
              ) : null}

              {semanticStatus ? (
                <div className="rounded-[24px] border border-[#EAE6DF]/70 bg-white p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">Semantic corpus</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{semanticStatus.latestBatchId ?? "Not indexed yet"}</div>
                    </div>
                    <span className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] ${statusBadgeStyles(semanticStatus.latestStatus ?? "pending")}`}>
                      {semanticStatus.latestStatus ?? "pending"}
                    </span>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="rounded-[18px] bg-[#F9F8F6] px-4 py-3">
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Documents</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{semanticStatus.documentCount}</div>
                    </div>
                    <div className="rounded-[18px] bg-[#F9F8F6] px-4 py-3">
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6B6B6B]">Chunks</div>
                      <div className="mt-1 text-sm font-semibold text-[#2E2E2E]">{semanticStatus.chunkCount}</div>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
          <div className="mb-4 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">
            <Activity size={14} />
            Recent debug events
          </div>
          <div className="space-y-3">
            {debugLogs.map((entry) => (
              <div key={`${entry.timestamp}-${entry.event}`} className="rounded-[22px] bg-[#F9F8F6] p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${levelStyles(entry.level)}`}>
                    {entry.level}
                  </span>
                  <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">
                    {entry.datasetKind ?? "system"}
                  </span>
                  <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#6B6B6B]">
                    {formatTimestamp(entry.timestamp)}
                  </span>
                </div>
                <div className="text-sm font-semibold text-[#2E2E2E]">{entry.message}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.16em] text-[#6B6B6B]">{entry.event}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function LabsDashboard({ versionManifest }: LabsDashboardProps) {
  const initialLabsCache = readLabsDashboardCache();
  const [activeLab, setActiveLab] = useState<LabKey>("datasets");
  const [importSummary, setImportSummary] = useState<ImportSummary | null>(initialLabsCache.importSummary);
  const [debugConfig, setDebugConfig] = useState<ImportDebugConfig>({
    strictMvpPubmed: initialLabsCache.debugConfig?.strictMvpPubmed ?? false,
    runtimeEngine: initialLabsCache.debugConfig?.runtimeEngine ?? "deterministic",
    semanticRetrievalEnabled: initialLabsCache.debugConfig?.semanticRetrievalEnabled ?? false,
    retrievalMode: initialLabsCache.debugConfig?.retrievalMode ?? "hybrid",
    llmImportAssistEnabled: initialLabsCache.debugConfig?.llmImportAssistEnabled ?? false,
    llmExplainabilityEnabled: initialLabsCache.debugConfig?.llmExplainabilityEnabled ?? false
  });
  const [debugLogs, setDebugLogs] = useState<ImportDebugLogEntry[]>(initialLabsCache.debugLogs);
  const [datasetKind, setDatasetKind] = useState<"esmo" | "pubmed">("esmo");
  const [datasetPath, setDatasetPath] = useState("");
  const [datasetBrowser, setDatasetBrowser] = useState<DatasetBrowserResponse | null>(
    initialLabsCache.datasetBrowsers.esmo ?? null
  );
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [importResult, setImportResult] = useState<ImportBatch | null>(null);
  const [semanticStatus, setSemanticStatus] = useState<SemanticImportStatus | null>(
    initialLabsCache.semanticStatuses.esmo ?? null
  );
  const [embeddingManifest, setEmbeddingManifest] = useState<EmbeddingManifest | null>(initialLabsCache.embeddingManifest);
  const [embeddingPoints, setEmbeddingPoints] = useState<EmbeddingPoint[]>(readCachedEmbeddingPoints("all"));
  const [embeddingNeighbors, setEmbeddingNeighbors] = useState<EmbeddingNeighbor[]>([]);
  const [embeddingSourceFilter, setEmbeddingSourceFilter] = useState<"all" | "pubmed" | "esmo">("all");
  const [selectedPointId, setSelectedPointId] = useState<string | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<EngineBenchmarkResult | null>(
    initialLabsCache.benchmarkResults["frozen_pack:hybrid"] ?? null
  );
  const [benchmarkPackId, setBenchmarkPackId] = useState<"demo_presets" | "frozen_pack">("frozen_pack");
  const [benchmarkRetrievalMode, setBenchmarkRetrievalMode] = useState<"hybrid" | "dense_only">("hybrid");
  const [evaluationViewMode, setEvaluationViewMode] = useState<EvaluationViewMode>("simple");
  const [benchmarkError, setBenchmarkError] = useState<string | null>(null);
  const [datasetActionError, setDatasetActionError] = useState<string | null>(null);
  const [isRunningDatasetAction, setIsRunningDatasetAction] = useState(false);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);
  const [navigatorPreferences, setNavigatorPreferences] = useState<NavigatorDebugPreferences>(
    DEFAULT_NAVIGATOR_DEBUG_PREFERENCES
  );
  const [isSavingImportConfig, setIsSavingImportConfig] = useState(false);
  const benchmarkPrefetchKeyRef = useRef<string | null>(null);
  const benchmarkPrimerReadyRef = useRef(false);
  const benchmarkPrimerPromiseRef = useRef<Promise<boolean> | null>(null);

  async function ensureBenchmarkPrimer() {
    if (benchmarkPrimerReadyRef.current) {
      return true;
    }
    if (benchmarkPrimerPromiseRef.current) {
      return benchmarkPrimerPromiseRef.current;
    }
    const primerPromise = (async () => {
      try {
        void prewarmRuntime({
          includeSemantic: true,
          timeoutMs: 15000,
        });
        const primerResult = await runEngineBenchmark(
          { packId: "demo_presets", retrievalMode: "hybrid", forceRefresh: false },
          { allowFallback: false, timeoutMs: 45000 }
        );
        writeLabsDashboardCache({
          benchmarkResults: {
            ...readLabsDashboardCache().benchmarkResults,
            ["demo_presets:hybrid"]: primerResult,
          },
        });
        benchmarkPrimerReadyRef.current = true;
        return true;
      } catch {
        benchmarkPrimerReadyRef.current = false;
        return false;
      } finally {
        benchmarkPrimerPromiseRef.current = null;
      }
    })();
    benchmarkPrimerPromiseRef.current = primerPromise;
    return primerPromise;
  }

  async function loadBenchmark(
    packId: "demo_presets" | "frozen_pack",
    retrievalMode: "hybrid" | "dense_only",
    options?: { forceRefresh?: boolean }
  ) {
    setIsRunningBenchmark(true);
    setBenchmarkError(null);
    try {
      const result = await runEngineBenchmark(
        { packId, retrievalMode, forceRefresh: options?.forceRefresh ?? false },
        { allowFallback: false, timeoutMs: 90000 }
      );
      setBenchmarkResult(result);
      writeLabsDashboardCache({
        benchmarkResults: {
          ...readLabsDashboardCache().benchmarkResults,
          [`${packId}:${retrievalMode}`]: result,
        },
      });
    } catch (error) {
      setBenchmarkError(error instanceof Error ? error.message : "Benchmark failed.");
    } finally {
      setIsRunningBenchmark(false);
    }
  }

  async function loadCachedBenchmark(packId: "demo_presets" | "frozen_pack", retrievalMode: "hybrid" | "dense_only") {
    const result = await getCachedEngineBenchmark({ packId, retrievalMode, forceRefresh: false });
    if (result) {
      setBenchmarkError(null);
      benchmarkPrimerReadyRef.current = true;
      setBenchmarkResult(result);
      writeLabsDashboardCache({
        benchmarkResults: {
          ...readLabsDashboardCache().benchmarkResults,
          [`${packId}:${retrievalMode}`]: result,
        },
      });
      return;
    }
    if (packId === "frozen_pack" && retrievalMode === "hybrid") {
      void ensureBenchmarkPrimer();
      return;
    }
    void prewarmRuntime({ includeSemantic: true });
  }

  useEffect(() => {
    let mounted = true;

    async function loadLabData() {
      const [summary, config, logs, browser] = await Promise.all([
        getImportSummary(),
        getImportDebugConfig(),
        getImportDebugLogs(12),
        getDatasetBrowser("esmo"),
      ]);

      if (!mounted) {
        return;
      }

      setImportSummary(summary);
      setDebugConfig(config);
      setDebugLogs(logs);
      setDatasetBrowser(browser);
      writeLabsDashboardCache({
        importSummary: summary,
        debugConfig: config,
        debugLogs: logs,
        datasetBrowsers: { esmo: browser },
      });

      void (async () => {
        const initialSemanticStatus = await getSemanticImportStatus("esmo").catch(() => null);
        if (!mounted) {
          return;
        }
        setSemanticStatus(initialSemanticStatus);
        writeLabsDashboardCache({
          semanticStatuses: initialSemanticStatus ? { esmo: initialSemanticStatus } : {},
        });
      })();
    }

    setNavigatorPreferences(readNavigatorDebugPreferences());
    void loadLabData();

    const unsubscribe = subscribeNavigatorDebugPreferences((next) => {
      setNavigatorPreferences(next);
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, []);

  async function persistImportConfig(updates: Partial<ImportDebugConfig>) {
    setIsSavingImportConfig(true);
    const nextConfig = await updateImportDebugConfig({ ...debugConfig, ...updates });
    const nextLogs = await getImportDebugLogs(12);
    setDebugConfig(nextConfig);
    setDebugLogs(nextLogs);
    writeLabsDashboardCache({
      debugConfig: nextConfig,
      debugLogs: nextLogs,
    });
    setIsSavingImportConfig(false);
  }

  async function refreshOperationalData() {
    const [summary, logs] = await Promise.all([
      getImportSummary(),
      getImportDebugLogs(12),
    ]);
    setImportSummary(summary);
    setDebugLogs(logs);
    setBenchmarkResult(null);
    benchmarkPrefetchKeyRef.current = null;
    benchmarkPrimerReadyRef.current = false;
    benchmarkPrimerPromiseRef.current = null;
    setBenchmarkError("Benchmark invalidated by data change. Run live benchmark again.");
    clearCachedEmbeddingPoints();
    setEmbeddingPoints([]);
    setEmbeddingManifest(null);
    writeLabsDashboardCache({
      importSummary: summary,
      debugLogs: logs,
      embeddingManifest: null,
      benchmarkResults: {},
    });
    void prewarmRuntime({ includeSemantic: true });
    void (async () => {
      const status = await getSemanticImportStatus(datasetKind).catch(() => null);
      setSemanticStatus(status);
      writeLabsDashboardCache({
        semanticStatuses: status ? { [datasetKind]: status } : {},
      });
    })();

    if (activeLab === "embeddings") {
      void (async () => {
        const [manifest, points] = await Promise.all([
          getEmbeddingManifest().catch(() => null),
          getEmbeddingPoints(embeddingSourceFilter === "all" ? undefined : embeddingSourceFilter).catch(() => []),
        ]);
        setEmbeddingManifest(manifest);
        setEmbeddingPoints(points);
        writeLabsDashboardCache({ embeddingManifest: manifest });
        writeCachedEmbeddingPoints(embeddingSourceFilter, points);
      })();
    }
  }

  useEffect(() => {
    let mounted = true;

    async function loadBrowser() {
      try {
        const browser = await getDatasetBrowser(datasetKind);
        if (!mounted) {
          return;
        }
        setDatasetBrowser(browser);
        writeLabsDashboardCache({
          datasetBrowsers: { [datasetKind]: browser },
        });
        void (async () => {
          const status = await getSemanticImportStatus(datasetKind).catch(() => null);
          if (!mounted) {
            return;
          }
          setSemanticStatus(status);
          writeLabsDashboardCache({
            semanticStatuses: status ? { [datasetKind]: status } : {},
          });
        })();
      } catch {
        if (!mounted) {
          return;
        }
        setDatasetBrowser(null);
        setSemanticStatus(null);
      }
    }

    void loadBrowser();

    return () => {
      mounted = false;
    };
  }, [datasetKind]);

  async function handleValidateDataset() {
    setDatasetActionError(null);
    setIsRunningDatasetAction(true);
    try {
      const report = await validateDataset(datasetKind, datasetPath.trim() || undefined);
      setValidationReport(report);
      setImportResult(null);
      const logs = await getImportDebugLogs(12);
      setDebugLogs(logs);
    } catch (error) {
      setDatasetActionError(error instanceof Error ? error.message : "Validation failed.");
    } finally {
      setIsRunningDatasetAction(false);
    }
  }

  async function handleImportDataset() {
    setDatasetActionError(null);
    setIsRunningDatasetAction(true);
    try {
      const result = await importDataset(datasetKind, datasetPath.trim() || undefined);
      setImportResult(result);
      setValidationReport(result.validation);
      await refreshOperationalData();
    } catch (error) {
      setDatasetActionError(error instanceof Error ? error.message : "Import failed.");
    } finally {
      setIsRunningDatasetAction(false);
    }
  }

  async function handleAppendDataset() {
    setDatasetActionError(null);
    setIsRunningDatasetAction(true);
    try {
      const result = await importDataset(datasetKind, datasetPath.trim() || undefined, "append");
      setImportResult(result);
      setValidationReport(result.validation);
      await refreshOperationalData();
    } catch (error) {
      setDatasetActionError(error instanceof Error ? error.message : "Append failed.");
    } finally {
      setIsRunningDatasetAction(false);
    }
  }

  async function handleImportSemanticDataset() {
    setDatasetActionError(null);
    setIsRunningDatasetAction(true);
    try {
      const result = await importSemanticDataset(datasetKind, datasetPath.trim() || undefined);
      setSemanticStatus(result);
      await refreshOperationalData();
    } catch (error) {
      setDatasetActionError(error instanceof Error ? error.message : "Semantic import failed.");
    } finally {
      setIsRunningDatasetAction(false);
    }
  }

  useEffect(() => {
    let mounted = true;
    if (activeLab !== "embeddings") {
      return () => {
        mounted = false;
      };
    }

    async function loadManifest() {
      try {
        const manifest = await getEmbeddingManifest();
        if (mounted) {
          setEmbeddingManifest(manifest);
          writeLabsDashboardCache({ embeddingManifest: manifest });
        }
      } catch {
        if (mounted) {
          setEmbeddingManifest(null);
        }
      }
    }

    void loadManifest();

    return () => {
      mounted = false;
    };
  }, [activeLab]);

  useEffect(() => {
    let mounted = true;
    if (activeLab !== "embeddings") {
      return () => {
        mounted = false;
      };
    }

    async function loadPoints() {
      try {
        const cachedPoints = readCachedEmbeddingPoints(embeddingSourceFilter);
        if (mounted && cachedPoints.length > 0) {
          setEmbeddingPoints(cachedPoints);
          if (!selectedPointId && cachedPoints[0]) {
            setSelectedPointId(cachedPoints[0].pointId);
          }
        }
        const points = await getEmbeddingPoints(embeddingSourceFilter === "all" ? undefined : embeddingSourceFilter);
        if (!mounted) {
          return;
        }
        setEmbeddingPoints(points);
        writeCachedEmbeddingPoints(embeddingSourceFilter, points);
        if (!selectedPointId && points[0]) {
          setSelectedPointId(points[0].pointId);
        }
      } catch {
        if (mounted) {
          setEmbeddingPoints([]);
        }
      }
    }
    void loadPoints();
    return () => {
      mounted = false;
    };
  }, [activeLab, embeddingSourceFilter]);

  useEffect(() => {
    let mounted = true;
    if (activeLab !== "embeddings") {
      setEmbeddingNeighbors([]);
      return () => {
        mounted = false;
      };
    }

    async function loadNeighbors() {
      if (!selectedPointId) {
        setEmbeddingNeighbors([]);
        return;
      }
      try {
        const neighbors = await getEmbeddingNeighbors(selectedPointId, 8);
        if (mounted) {
          setEmbeddingNeighbors(neighbors);
        }
      } catch {
        if (mounted) {
          setEmbeddingNeighbors([]);
        }
      }
    }
    void loadNeighbors();
    return () => {
      mounted = false;
    };
  }, [activeLab, selectedPointId]);

  useEffect(() => {
    if (activeLab !== "evaluation" || benchmarkResult || isRunningBenchmark) {
      return;
    }
    const key = `${benchmarkPackId}:${benchmarkRetrievalMode}`;
    if (benchmarkPrefetchKeyRef.current === key) {
      return;
    }
    benchmarkPrefetchKeyRef.current = key;
    void loadCachedBenchmark(benchmarkPackId, benchmarkRetrievalMode);
  }, [activeLab, benchmarkPackId, benchmarkResult, benchmarkRetrievalMode, isRunningBenchmark]);

  function handleNavigatorPreferenceToggle() {
    const next = updateNavigatorDebugPreferences({
      showClinicalModifiers: !navigatorPreferences.showClinicalModifiers
    });
    setNavigatorPreferences(next);
  }

  async function handleRunBenchmark() {
    if (benchmarkPackId === "frozen_pack" && benchmarkRetrievalMode === "hybrid") {
      await ensureBenchmarkPrimer();
    }
    await loadBenchmark(benchmarkPackId, benchmarkRetrievalMode);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-10">
      <header className="border-b border-[#EAE6DF] pb-6">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-[#F0EBE3] px-4 py-2 text-[10px] font-bold uppercase tracking-[0.24em] text-[#6B6B6B]">
          <Sparkles size={14} />
          Signal Labs
        </div>
        <h1 className="text-4xl font-black tracking-tight text-[#2E2E2E]">Operational cockpit for labs and evaluation</h1>
        <p className="mt-3 max-w-3xl text-lg leading-relaxed text-[#6B6B6B]">
          This page focuses on corpus state, evaluation context, embeddings, and runtime controls without mixing them into the main product narrative.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {labCards.map((card) => {
          const Icon = card.icon;
          const isActive = activeLab === card.id;

          return (
            <button
              key={card.id}
              type="button"
              onClick={() => setActiveLab(card.id)}
              className={`${STYLES.surface} ${STYLES.radiusCard} ${STYLES.shadow} flex h-full flex-col border p-6 text-left transition-all ${
                isActive
                  ? "border-[#C96557] bg-[#FFF5F1] ring-2 ring-[#C96557]/25 shadow-[0_16px_40px_rgba(201,101,87,0.12),inset_0_0_0_1px_rgba(201,101,87,0.38)]"
                  : "border-[#EAE6DF]/60 hover:-translate-y-[2px] hover:shadow-[0_10px_30px_rgba(0,0,0,0.08)]"
              }`}
            >
              <div className="mb-5 flex min-h-12 items-start justify-between gap-4">
                <div className={`${STYLES.primaryBg} flex h-12 w-12 items-center justify-center rounded-xl text-white shadow-sm`}>
                  <Icon size={22} />
                </div>
                <span className="mt-2 inline-flex shrink-0 items-center self-start rounded-full bg-[#F0EBE3] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">
                  {card.eyebrow}
                </span>
              </div>
              <div className="min-h-[3.5rem]">
                <h3 className={`text-xl font-black leading-tight ${isActive ? "text-[#A63D2F]" : "text-[#2E2E2E]"}`}>{card.title}</h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-[#6B6B6B]">{card.description}</p>
            </button>
          );
        })}
      </section>

      <section>
        {activeLab === "datasets" ? <DatasetsPanel importSummary={importSummary} /> : null}
        {activeLab === "evaluation" ? (
          <EvaluationPanel
            benchmarkResult={benchmarkResult}
            selectedPackId={benchmarkPackId}
            selectedRetrievalMode={benchmarkRetrievalMode}
            evaluationViewMode={evaluationViewMode}
            isRunningBenchmark={isRunningBenchmark}
            benchmarkError={benchmarkError}
            onPackChange={setBenchmarkPackId}
            onRetrievalModeChange={setBenchmarkRetrievalMode}
            onEvaluationViewModeChange={setEvaluationViewMode}
            onRunBenchmark={handleRunBenchmark}
          />
        ) : null}
        {activeLab === "embeddings" ? (
          <EmbeddingAtlasPanel
            manifest={embeddingManifest}
            points={embeddingPoints}
            neighbors={embeddingNeighbors}
            selectedPointId={selectedPointId}
            sourceFilter={embeddingSourceFilter}
            onSelectPoint={setSelectedPointId}
            onSourceFilterChange={setEmbeddingSourceFilter}
          />
        ) : null}
        {activeLab === "debug" ? (
          <DebugConsolePanel
            versionManifest={versionManifest}
            debugConfig={debugConfig}
            debugLogs={debugLogs}
            navigatorPreferences={navigatorPreferences}
            datasetKind={datasetKind}
            datasetPath={datasetPath}
            datasetBrowser={datasetBrowser}
            validationReport={validationReport}
            importResult={importResult}
            semanticStatus={semanticStatus}
            isRunningDatasetAction={isRunningDatasetAction}
            datasetActionError={datasetActionError}
            onDatasetKindChange={setDatasetKind}
            onDatasetPathChange={setDatasetPath}
            onValidateDataset={handleValidateDataset}
            onImportDataset={handleImportDataset}
            onAppendDataset={handleAppendDataset}
            onImportSemanticDataset={handleImportSemanticDataset}
            onNavigatorPreferenceToggle={handleNavigatorPreferenceToggle}
            onStrictImportToggle={() => void persistImportConfig({ strictMvpPubmed: !debugConfig.strictMvpPubmed })}
            onSemanticRetrievalToggle={() =>
              void persistImportConfig(
                debugConfig.semanticRetrievalEnabled
                  ? {
                      semanticRetrievalEnabled: false,
                      runtimeEngine: "deterministic"
                    }
                  : {
                      semanticRetrievalEnabled: true,
                      runtimeEngine: "semantic_retrieval_lab"
                    }
              )
            }
            onLlmImportToggle={() => void persistImportConfig({ llmImportAssistEnabled: !debugConfig.llmImportAssistEnabled })}
            onLlmExplainabilityToggle={() =>
              void persistImportConfig({ llmExplainabilityEnabled: !debugConfig.llmExplainabilityEnabled })
            }
            isSavingImportConfig={isSavingImportConfig}
          />
        ) : null}
      </section>
    </div>
  );
}
