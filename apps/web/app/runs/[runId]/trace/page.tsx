import { MetricGrid } from "@/components/MetricGrid";
import { SectionCard } from "@/components/SectionCard";
import { getRunTrace } from "@/lib/api";

export default async function TracePage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const trace = await getRunTrace(runId);

  const funnelSteps = [
    {
      label: "Gate candidates",
      value: String(trace.gateCandidateCount),
      detail: "Total evidence retrieved from corpus before any filtering"
    },
    {
      label: "Clinically eligible",
      value: String(trace.eligibleCount),
      detail: "Passed clinical relevance gate (histology, setting, biomarker match)"
    },
    {
      label: "Top evidence",
      value: String(trace.topEvidenceCount),
      detail: "Evidence Relevance Score (ERS) ≥ 30, included in results"
    },
    {
      label: "Excluded",
      value: String(trace.secondaryCount),
      detail: "Below threshold or failed gating — reasons logged per item"
    }
  ];

  return (
    <>
      <section className="panel">
        <span className="eyebrow">Explainability Trace</span>
        <h1 className="page-title">Decision audit trail</h1>
        <p>
          Every deterministic decision is traceable. This trace shows exactly how evidence was
          filtered, ranked, and labeled — from initial retrieval through final output.
          Nothing is hidden, nothing is inferred beyond the provided inputs.
        </p>
      </section>

      <div className="content-grid" style={{ marginTop: "var(--space-3)" }}>
        <SectionCard eyebrow="Evidence Funnel" title="How evidence was filtered">
          <p>
            Evidence flows through a deterministic pipeline: retrieve → gate → score → rank.
            Each step narrows the set using explicit, auditable rules.
          </p>
          <MetricGrid metrics={funnelSteps} />
        </SectionCard>

        <SectionCard eyebrow="Run Metadata" title="Reproducibility parameters" variant="highlight">
          <p>
            These parameters fully determine the analysis output.
            Given identical inputs and these exact versions, the result is always the same.
          </p>
          <ul className="list-clean">
            <li>
              <span className="muted">Trace ID</span><br />
              <strong>{trace.traceId}</strong>
            </li>
            <li>
              <span className="muted">Ruleset version</span><br />
              <strong>{trace.rulesetVersion}</strong>
            </li>
            <li>
              <span className="muted">Corpus version</span><br />
              <strong>{trace.corpusVersion}</strong>
            </li>
            <li>
              <span className="muted">Input schema</span><br />
              <strong>{trace.inputSchemaVersion}</strong>
            </li>
            <li>
              <span className="muted">Safety footer</span><br />
              <strong>{trace.safetyFooterKey}</strong>
            </li>
          </ul>
        </SectionCard>
      </div>

      {trace.uncertaintyFlags.length > 0 && (
        <SectionCard
          eyebrow="Uncertainty flags"
          title="What the system is not confident about"
          variant="subtle"
        >
          <p>
            These flags indicate where the analysis encountered ambiguity or missing data.
            They are automatically generated — not manually curated — to ensure honest reporting.
          </p>
          <ul className="list-clean">
            {trace.uncertaintyFlags.map((flag) => (
              <li key={flag}>
                {flag.replace(/_/g, " ").replace(/:/g, ": ")}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}
    </>
  );
}
