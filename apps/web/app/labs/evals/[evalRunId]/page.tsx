import Link from "next/link";

import { MetricGrid } from "@/components/MetricGrid";
import { benchmarkMetrics } from "@/lib/sample-data";

export default function EvalRunPage() {
  return (
    <div className="content-grid">
      <section className="section-card">
        <span className="eyebrow">Benchmark Run</span>
        <h1 className="page-title">Eval run details</h1>
        <p>
          This view will combine confusion matrices, layer separation, and release-gating output for a specific
          benchmark run.
        </p>
        <MetricGrid metrics={benchmarkMetrics} />
      </section>
      <section className="panel">
        <span className="eyebrow">Case Drilldown</span>
        <p>Review edge cases one-by-one to preserve interpretability and clinical accountability.</p>
        <Link className="cta-link" href="/labs/evals/eval-sample-v1/cases/VIG-001">
          Open sample case review
        </Link>
      </section>
    </div>
  );
}
