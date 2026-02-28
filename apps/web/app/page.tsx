import Link from "next/link";

import { EvidenceRibbon } from "@/components/EvidenceRibbon";
import { MetricGrid } from "@/components/MetricGrid";
import { PolicyStrip } from "@/components/PolicyStrip";
import { SectionCard } from "@/components/SectionCard";
import { benchmarkMetrics, policy, sampleRun } from "@/lib/sample-data";

export default function HomePage() {
  return (
    <>
      <div className="hero-grid">
        <section className="hero-card">
          <span className="eyebrow">Deterministic Evidence Triage Platform</span>
          <h1>Navigate NSCLC evidence with receipts, not vibes.</h1>
          <p>
            This scaffold frames the product as a governed clinical evidence atlas: structured vignette input,
            deterministic scoring, guideline mapping, benchmark-gated updates, and visible safety boundaries.
          </p>
          <div className="hero-actions">
            <Link className="cta-link" href="/workspace">
              Launch workspace
            </Link>
            <Link className="cta-link" href="/docs/method">
              Inspect methodology
            </Link>
          </div>
          <PolicyStrip
            rulesetVersion={sampleRun.rulesetVersion}
            corpusVersion={sampleRun.corpusVersion}
            uncertaintyFlags={sampleRun.uncertaintyFlags}
          />
        </section>
        <SectionCard eyebrow="Frozen Governance" title="Product boundaries are visible by design">
          <ul className="list-clean">
            {policy.safetyBoundaries.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard eyebrow="Evidence Ribbon" title="The core result view is an atlas, not a chatbot">
          <EvidenceRibbon items={sampleRun.topEvidence} />
        </SectionCard>
        <SectionCard eyebrow="Benchmark Targets" title="Evaluation remains a product surface, not an afterthought">
          <MetricGrid metrics={benchmarkMetrics} />
        </SectionCard>
      </div>
    </>
  );
}

