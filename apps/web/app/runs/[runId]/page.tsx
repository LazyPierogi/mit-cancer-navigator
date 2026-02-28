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
      <PolicyStrip
        rulesetVersion={run.run.rulesetVersion}
        corpusVersion={run.run.corpusVersion}
        uncertaintyFlags={run.uncertaintyFlags}
      />
      <div className="content-grid">
        <SectionCard eyebrow="Top Evidence" title="Evidence atlas">
          <EvidenceRibbon items={run.topEvidence} />
        </SectionCard>
        <SectionCard eyebrow="Secondary References" title="Transparent exclusions">
          <ul className="list-clean">
            {run.secondaryReferences.map((item) => (
              <li key={item.evidenceId}>
                <strong>{item.evidenceId}</strong>: {item.exclusionReasons.join(", ")}
              </li>
            ))}
          </ul>
          <Link className="cta-link" href={`/runs/${runId}/trace`}>
            Inspect explainability trace
          </Link>
        </SectionCard>
      </div>
    </>
  );
}
