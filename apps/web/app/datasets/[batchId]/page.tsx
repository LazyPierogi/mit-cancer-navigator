import Link from "next/link";

import { MetricGrid } from "@/components/MetricGrid";
import { SectionCard } from "@/components/SectionCard";
import { getImportBatch } from "@/lib/api";

function formatDate(value: string) {
  return new Date(value).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export default async function ImportBatchDetailPage({ params }: { params: Promise<{ batchId: string }> }) {
  const { batchId } = await params;
  const batch = await getImportBatch(batchId);

  const metrics = [
    { label: "Status", value: batch.status, detail: `${batch.datasetKind} ${batch.datasetShape}` },
    { label: "Imported", value: `${batch.importedCount}/${batch.recordCount}`, detail: "Imported records / validated records" },
    { label: "Errors", value: String(batch.errorCount), detail: "Validation errors recorded for this batch" },
    { label: "Warnings", value: String(batch.warningCount), detail: "Validation warnings recorded for this batch" }
  ];

  return (
    <div className="content-grid">
      <section className="section-card">
        <span className="eyebrow">Import Batch</span>
        <h1 className="page-title">{batch.batchId}</h1>
        <p>
          Source: <strong>{batch.sourcePath}</strong>
        </p>
        <p>Created: {formatDate(batch.createdAt)}</p>
        <MetricGrid metrics={metrics} />
        <Link className="cta-link" href="/datasets">
          Back to datasets
        </Link>
      </section>

      <SectionCard eyebrow="Validation" title="Summary">
        <ul className="list-clean">
          <li>
            <strong>Dataset kind:</strong> {batch.validation.datasetKind}
          </li>
          <li>
            <strong>Dataset shape:</strong> {batch.validation.datasetShape}
          </li>
          <li>
            <strong>Validated path:</strong> {batch.validation.path}
          </li>
          {batch.validation.info.map((line) => (
            <li key={line}>{line}</li>
          ))}
          {batch.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Errors" title="Blocking issues">
        {batch.validation.errors.length ? (
          <ul className="list-clean">
            {batch.validation.errors.map((issue, index) => (
              <li key={`${issue.code}-${issue.record_id ?? "global"}-${index}`}>
                <strong>{issue.code}</strong>
                {issue.record_id ? ` (${issue.record_id})` : ""}: {issue.message}
              </li>
            ))}
          </ul>
        ) : (
          <p>No blocking validation errors were recorded for this batch.</p>
        )}
      </SectionCard>

      <SectionCard eyebrow="Warnings" title="Things to review">
        {batch.validation.warnings.length ? (
          <ul className="list-clean">
            {batch.validation.warnings.map((issue, index) => (
              <li key={`${issue.code}-${issue.record_id ?? "global"}-${index}`}>
                <strong>{issue.code}</strong>
                {issue.record_id ? ` (${issue.record_id})` : ""}: {issue.message}
              </li>
            ))}
          </ul>
        ) : (
          <p>No validation warnings were recorded for this batch.</p>
        )}
      </SectionCard>
    </div>
  );
}
