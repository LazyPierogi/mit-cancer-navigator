import Link from "next/link";

import { PolicyStrip } from "@/components/PolicyStrip";
import { WorkspaceForm } from "@/features/workspace/WorkspaceForm";
import { sampleRun } from "@/lib/sample-data";

export default function WorkspacePage() {
  return (
    <>
      <div className="page-grid">
        <section className="workspace-card">
          <span className="eyebrow">Structured Vignette Intake</span>
          <h1 className="page-title">Workspace</h1>
          <p>
            The MVP accepts structured inputs only. Missing fields become explicit uncertainty, never hidden
            inference.
          </p>
          <WorkspaceForm />
        </section>

        <section className="panel">
          <span className="eyebrow">Preview</span>
          <h2>First working flow</h2>
          <p>
            This form now posts to the real `POST /api/v1/runs` endpoint and redirects to the stored run detail page.
          </p>
          <PolicyStrip
            rulesetVersion={sampleRun.rulesetVersion}
            corpusVersion={sampleRun.corpusVersion}
            uncertaintyFlags={sampleRun.uncertaintyFlags}
          />
          <Link className="cta-link" href="/runs/run-demo-001">
            Open sample run
          </Link>
        </section>
      </div>
    </>
  );
}
