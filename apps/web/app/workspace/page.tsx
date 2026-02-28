import Link from "next/link";

import { PolicyStrip } from "@/components/PolicyStrip";
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
          <form className="workspace-form">
            <label>
              Disease setting
              <select defaultValue="metastatic">
                <option>early</option>
                <option>locally_advanced</option>
                <option>metastatic</option>
              </select>
            </label>
            <label>
              Histology
              <select defaultValue="adenocarcinoma">
                <option>adenocarcinoma</option>
                <option>squamous</option>
              </select>
            </label>
            <label>
              Performance status
              <select defaultValue="1">
                <option>0</option>
                <option>1</option>
                <option>2</option>
                <option>3</option>
                <option>4</option>
              </select>
            </label>
            <label>
              PD-L1 bucket
              <select defaultValue="ge50">
                <option>lt1</option>
                <option>1to49</option>
                <option>ge50</option>
              </select>
            </label>
            <label>
              EGFR
              <select defaultValue="no">
                <option>yes</option>
                <option>no</option>
              </select>
            </label>
            <label>
              ALK
              <select defaultValue="no">
                <option>yes</option>
                <option>no</option>
              </select>
            </label>
            <label>
              ROS1
              <select defaultValue="no">
                <option>yes</option>
                <option>no</option>
              </select>
            </label>
            <div>
              <button type="button">Run deterministic analysis</button>
            </div>
          </form>
        </section>

        <section className="panel">
          <span className="eyebrow">Preview</span>
          <h2>First working flow</h2>
          <p>
            Next step after dependency install: wire this form to `POST /api/v1/runs` and route users to the result
            surface below.
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

