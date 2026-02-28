import { EvidenceRibbon } from "@/components/EvidenceRibbon";
import { PolicyStrip } from "@/components/PolicyStrip";
import { SectionCard } from "@/components/SectionCard";
import { sampleRun } from "@/lib/sample-data";

export default function RunDetailPage() {
  return (
    <>
      <PolicyStrip
        rulesetVersion={sampleRun.rulesetVersion}
        corpusVersion={sampleRun.corpusVersion}
        uncertaintyFlags={sampleRun.uncertaintyFlags}
      />
      <div className="content-grid">
        <SectionCard eyebrow="Top Evidence" title="Evidence atlas">
          <EvidenceRibbon items={sampleRun.topEvidence} />
        </SectionCard>
        <SectionCard eyebrow="Secondary References" title="Transparent exclusions">
          <ul className="list-clean">
            {sampleRun.secondaryReferences.map((item) => (
              <li key={item.evidenceId}>
                <strong>{item.evidenceId}</strong>: {item.exclusionReasons.join(", ")}
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>
    </>
  );
}

