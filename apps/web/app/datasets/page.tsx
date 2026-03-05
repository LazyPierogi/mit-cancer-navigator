import Link from "next/link";

import { MetricGrid } from "@/components/MetricGrid";
import { getImportBatches, getImportSummary } from "@/lib/api";
import { ImportBatch, ImportSummary } from "@/lib/contracts";
import { datasets as fallbackDatasets } from "@/lib/sample-data";

function formatDate(value: string) {
  return new Date(value).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function sourceName(batch: ImportBatch) {
  return `${batch.datasetKind} (${batch.datasetShape})`;
}

function datasetLabel(kind: string) {
  if (kind === "esmo") {
    return "ESMO";
  }
  if (kind === "pubmed") {
    return "PubMed";
  }
  return kind;
}

async function loadImportBatches() {
  try {
    return await getImportBatches();
  } catch {
    return null;
  }
}

async function loadImportSummary() {
  try {
    return await getImportSummary();
  } catch {
    return null;
  }
}

function statusTone(status: string) {
  if (status === "completed") {
    return "tone-good";
  }
  if (status === "completed_with_warnings") {
    return "tone-warn";
  }
  if (status.includes("failed") || status.includes("blocked")) {
    return "tone-bad";
  }
  return "tone-muted";
}

function buildMetrics(summary: ImportSummary | null, batchCount: number) {
  return [
    {
      label: "Active Topics",
      value: String(summary?.activeTopics ?? 0),
      detail: "Guideline topics currently active in the runtime corpus"
    },
    {
      label: "Evidence Studies",
      value: String(summary?.activeEvidenceStudies ?? 0),
      detail: "Evidence records currently active in the runtime corpus"
    },
    {
      label: "Import Batches",
      value: String(summary?.importBatchCount ?? batchCount),
      detail: "Persisted import runs recorded in the local database"
    },
    {
      label: "Latest Batch",
      value: summary?.latestBatchStatus ?? "fallback",
      detail: summary?.latestBatchId ?? "No API-backed batch summary available"
    },
    {
      label: "Runtime Source",
      value: summary ? "DB imported" : "File fallback",
      detail: summary
        ? `Topics: ${summary.runtimeSources.topics.replaceAll("_", " ")} | Evidence: ${summary.runtimeSources.evidence.replaceAll("_", " ")}`
        : "API summary unavailable, so runtime source cannot be confirmed from the server"
    }
  ];
}

function renderDatasetCard(kind: string, summary: ImportSummary | null) {
  const batch = summary?.latestByKind[kind];
  const label = datasetLabel(kind);

  if (!batch) {
    return (
      <article className="dataset-card" key={kind}>
        <span className="eyebrow">{label}</span>
        <h2>No imported batch yet</h2>
        <p>This dataset is not yet represented in the persisted import ledger.</p>
      </article>
    );
  }

  return (
    <article className="dataset-card" key={kind}>
      <span className="eyebrow">{label}</span>
      <h2>{batch.status.replaceAll("_", " ")}</h2>
      <p>Latest persisted batch for this source family.</p>
      <div className="dataset-card-meta">
        <span className={`status-tag ${statusTone(batch.status)}`}>{batch.status.replaceAll("_", " ")}</span>
        <span>{formatDate(batch.createdAt)}</span>
      </div>
      <div className="score-grid compact">
        <div>
          <span className="muted">Imported</span>
          <strong>
            {batch.importedCount}/{batch.recordCount}
          </strong>
        </div>
        <div>
          <span className="muted">Warnings</span>
          <strong>{batch.warningCount}</strong>
        </div>
        <div>
          <span className="muted">Errors</span>
          <strong>{batch.errorCount}</strong>
        </div>
        <div>
          <span className="muted">Batch</span>
          <strong>{batch.batchId.slice(0, 12)}</strong>
        </div>
      </div>
    </article>
  );
}

export default async function DatasetsPage() {
  const importBatches = await loadImportBatches();
  const importSummary = await loadImportSummary();
  const hasRealData = importBatches !== null && importBatches.length > 0;
  const metrics = buildMetrics(importSummary, hasRealData ? importBatches.length : fallbackDatasets.length);

  return (
    <div className="content-grid">
      <section className="section-card">
        <span className="eyebrow">Corpus Provenance</span>
        <h1 className="page-title">Datasets and import batches</h1>
        <p>
          Hybrid import comes first: canonical ESMO pack, curated PubMed pack, and the frozen evaluation set.
          {hasRealData ? " Showing persisted import batches from the API." : " API batch data is unavailable, so this page is showing the local fallback view."}
        </p>
        <MetricGrid metrics={metrics} />
      </section>

      <section className="section-card">
        <span className="eyebrow">Latest By Dataset</span>
        <h2>Source-specific latest drops</h2>
        <p>Quick read on the newest persisted import for each source family we are currently running.</p>
        <div className="dataset-grid">
          {["esmo", "pubmed", "vignettes"].map((kind) => renderDatasetCard(kind, importSummary))}
        </div>
      </section>

      <section className="table-card">
        <span className="eyebrow">Batch Ledger</span>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Source</th>
              <th>Status</th>
              <th>Imported</th>
              <th>Issues</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {hasRealData
              ? importBatches.map((batch) => (
                <tr key={batch.batchId}>
                  <td>
                    <Link href={`/datasets/${batch.batchId}`}>{batch.batchId}</Link>
                  </td>
                  <td>{sourceName(batch)}</td>
                  <td>
                    <span className={`status-tag ${statusTone(batch.status)}`}>{batch.status.replaceAll("_", " ")}</span>
                  </td>
                  <td>
                    {batch.importedCount}/{batch.recordCount}
                  </td>
                  <td>
                    {batch.errorCount} errors / {batch.warningCount} warnings
                  </td>
                  <td>{formatDate(batch.createdAt)}</td>
                </tr>
              ))
              : fallbackDatasets.map((dataset) => (
                <tr key={dataset.id}>
                  <td>{dataset.id}</td>
                  <td>{dataset.source}</td>
                  <td>
                    <span className={`status-tag tone-muted`}>{dataset.status.replaceAll("_", " ")}</span>
                  </td>
                  <td>{dataset.records}</td>
                  <td>n/a</td>
                  <td>n/a</td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
