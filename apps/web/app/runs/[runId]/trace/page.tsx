import { MetricGrid } from "@/components/MetricGrid";

const traceMetrics = [
  { label: "Gate candidates", value: "48", detail: "All retrieved evidence before gating" },
  { label: "Eligible", value: "16", detail: "Pass clinical relevance gate" },
  { label: "Top evidence", value: "5", detail: "ERS >= 30" },
  { label: "Secondary", value: "11", detail: "Excluded or below threshold" }
];

export default function TracePage() {
  return (
    <section className="panel">
      <span className="eyebrow">Explainability Trace</span>
      <h1 className="page-title">Run trace</h1>
      <p>
        This screen is where we show gate candidate counts, threshold movements, and the audit trail for every
        deterministic decision.
      </p>
      <MetricGrid metrics={traceMetrics} />
    </section>
  );
}

