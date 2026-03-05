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
          <span className="eyebrow">Evidence Triage for NSCLC</span>
          <h1>Navigate treatment evidence with clarity.</h1>
          <p>
            Enter a structured clinical profile. Receive ranked evidence from peer-reviewed
            sources, mapped against treatment guidelines. Every decision is traceable,
            every exclusion is logged, every uncertainty is disclosed.
          </p>
          <div className="hero-actions">
            <Link className="cta-link" href="/workspace">
              Open workspace
            </Link>
            <Link className="cta-link" href="/docs/method">
              Read the methodology
            </Link>
          </div>
          <PolicyStrip
            rulesetVersion={sampleRun.rulesetVersion}
            corpusVersion={sampleRun.corpusVersion}
            uncertaintyFlags={sampleRun.uncertaintyFlags}
          />
        </section>
        <SectionCard eyebrow="Safety boundaries" title="What the system will not do">
          <ul className="list-clean">
            {policy.safetyBoundaries.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard eyebrow="Example result" title="Evidence ribbon — the core output">
          <p>
            Each run produces a ranked list of evidence. Items are scored deterministically
            and labeled against clinical guidelines (aligned, silent, or in conflict).
          </p>
          <EvidenceRibbon items={sampleRun.topEvidence} />
        </SectionCard>
        <SectionCard eyebrow="Evaluation targets" title="How we measure quality" variant="highlight">
          <p>
            These metrics are evaluated against a frozen set of clinical vignettes.
            Results are reproducible and version-pinned.
          </p>
          <MetricGrid metrics={benchmarkMetrics} />
        </SectionCard>
      </div>
    </>
  );
}
