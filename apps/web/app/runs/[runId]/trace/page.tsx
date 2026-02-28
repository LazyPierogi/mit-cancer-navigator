import { MetricGrid } from "@/components/MetricGrid";
import { getRunTrace } from "@/lib/api";

export default async function TracePage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const trace = await getRunTrace(runId);
  const traceMetrics = [
    { label: "Gate candidates", value: String(trace.gateCandidateCount), detail: "All retrieved evidence before gating" },
    { label: "Eligible", value: String(trace.eligibleCount), detail: "Pass clinical relevance gate" },
    { label: "Top evidence", value: String(trace.topEvidenceCount), detail: "ERS >= 30" },
    { label: "Secondary", value: String(trace.secondaryCount), detail: "Excluded or below threshold" }
  ];

  return (
    <section className="panel">
      <span className="eyebrow">Explainability Trace</span>
      <h1 className="page-title">Run trace</h1>
      <p>
        This screen is where we show gate candidate counts, threshold movements, and the audit trail for every
        deterministic decision.
      </p>
      <MetricGrid metrics={traceMetrics} />
      <ul className="list-clean">
        {trace.uncertaintyFlags.map((flag) => (
          <li key={flag}>{flag}</li>
        ))}
      </ul>
    </section>
  );
}
