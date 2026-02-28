import Link from "next/link";

import { MetricGrid } from "@/components/MetricGrid";
import { benchmarkMetrics } from "@/lib/sample-data";

export default function EvalLabPage() {
  return (
    <div className="content-grid">
      <section className="section-card">
        <span className="eyebrow">Two-Layer Evaluation</span>
        <h1 className="page-title">Eval Lab</h1>
        <p>
          Layer 1 verifies system integrity. Layer 2 scores relevance, mapping, citation validity, and deterministic
          model fidelity without mixing those concerns.
        </p>
        <MetricGrid metrics={benchmarkMetrics} />
      </section>
      <section className="panel">
        <span className="eyebrow">Reviewer Flow</span>
        <h2>Human validation remains visible</h2>
        <p>Clinical correctness and citation validity still require lightweight human review artifacts.</p>
        <Link className="cta-link" href="/labs/reviewer">
          Open reviewer queue
        </Link>
      </section>
    </div>
  );
}

