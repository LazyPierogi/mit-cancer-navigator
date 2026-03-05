import Link from "next/link";

import { EvidenceRibbon } from "@/components/EvidenceRibbon";
import { PolicyStrip } from "@/components/PolicyStrip";
import { SectionCard } from "@/components/SectionCard";
import { getRun } from "@/lib/api";

export default async function RunDetailPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const run = await getRun(runId);

  return (
    <>
      {/* Step indicator — user knows where they are in the flow */}
      <div className="step-indicator">
        <div className="step">
          <span className="step-num">1</span>
          <span>Select profile</span>
        </div>
        <span className="step-divider" />
        <div className="step">
          <span className="step-num">2</span>
          <span>Run analysis</span>
        </div>
        <span className="step-divider" />
        <div className="step step-active">
          <span className="step-num">3</span>
          <span>Review evidence</span>
        </div>
      </div>

      <PolicyStrip
        rulesetVersion={run.run.rulesetVersion}
        corpusVersion={run.run.corpusVersion}
        uncertaintyFlags={run.uncertaintyFlags}
      />

      <div className="content-grid">
        <SectionCard eyebrow="Top Evidence" title="Ranked evidence atlas">
          <p>
            Evidence retrieved and ranked deterministically using the Evidence Relevance Score (ERS).
            Each item is mapped to a guideline topic and labeled as aligned, silent, or in conflict.
          </p>
          <EvidenceRibbon items={run.topEvidence} />
        </SectionCard>

        <div>
          <SectionCard eyebrow="Exclusion Transparency" title="Why some evidence was excluded" variant="subtle">
            <p>
              These references were retrieved but did not meet the clinical relevance gate
              or scored below the ERS threshold. Each exclusion reason is recorded and traceable.
            </p>
            <ul className="list-clean">
              {run.secondaryReferences.map((item) => (
                <li key={item.evidenceId}>
                  <strong>{item.evidenceId}</strong>
                  <br />
                  <span className="muted">{item.exclusionReasons.map(r => r.replace(/_/g, " ").replace(/:/g, ": ")).join(" · ")}</span>
                </li>
              ))}
            </ul>
          </SectionCard>

          {run.uncertaintyFlags.length > 0 && (
            <SectionCard eyebrow="Uncertainty Disclosure" title="Known limitations of this run" variant="highlight">
              <p>
                The system explicitly flags any uncertainty in the analysis.
                These are not errors — they are honest disclosures about where the evidence may be incomplete.
              </p>
              <ul className="list-clean">
                {run.uncertaintyFlags.map((flag) => (
                  <li key={flag}>
                    <span className="muted">{flag.replace(/_/g, " ").replace(/:/g, ": ")}</span>
                  </li>
                ))}
              </ul>
            </SectionCard>
          )}

          <div style={{ marginTop: "var(--space-2)" }}>
            <Link className="cta-link" href={`/runs/${runId}/trace`}>
              Inspect full explainability trace →
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
