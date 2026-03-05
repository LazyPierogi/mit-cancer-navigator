import Link from "next/link";

import { PolicyStrip } from "@/components/PolicyStrip";
import { WorkspaceForm } from "@/features/workspace/WorkspaceForm";
import { sampleRun } from "@/lib/sample-data";

export default function WorkspacePage() {
  return (
    <>
      <div className="step-indicator">
        <div className="step step-active">
          <span className="step-num">1</span>
          <span>Select profile</span>
        </div>
        <span className="step-divider" />
        <div className="step">
          <span className="step-num">2</span>
          <span>Run analysis</span>
        </div>
        <span className="step-divider" />
        <div className="step">
          <span className="step-num">3</span>
          <span>Review evidence</span>
        </div>
      </div>

      <div className="page-grid">
        <section className="workspace-card">
          <span className="eyebrow">Structured Vignette Intake</span>
          <h1 className="page-title">Workspace</h1>
          <p>
            Select a patient preset for quick demo, or configure fields manually.
            Missing fields become explicit uncertainty — never hidden inference.
          </p>
          <WorkspaceForm />
        </section>

        <section className="panel">
          <span className="eyebrow">How It Works</span>
          <h2>Evidence Navigation Flow</h2>
          <p>
            This form submits a structured vignette to the deterministic analysis engine.
            Results include ranked evidence, guideline alignment labels, and an explainability trace.
          </p>
          <PolicyStrip
            rulesetVersion={sampleRun.rulesetVersion}
            corpusVersion={sampleRun.corpusVersion}
            uncertaintyFlags={sampleRun.uncertaintyFlags}
          />
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 8 }}>
            <Link className="cta-link" href="/runs/run-demo-001">
              Open sample run
            </Link>
            <Link className="cta-link" href="/docs/method">
              Methodology
            </Link>
          </div>
        </section>
      </div>
    </>
  );
}
