type PolicyStripProps = {
  rulesetVersion: string;
  corpusVersion: string;
  uncertaintyFlags: string[];
};

export function PolicyStrip({ rulesetVersion, corpusVersion, uncertaintyFlags }: PolicyStripProps) {
  return (
    <div className="policy-strip">
      <div>
        <span className="eyebrow">Ruleset</span>
        <strong>{rulesetVersion}</strong>
      </div>
      <div>
        <span className="eyebrow">Corpus</span>
        <strong>{corpusVersion}</strong>
      </div>
      <div>
        <span className="eyebrow">Scope</span>
        <strong>NSCLC treatment evidence only</strong>
      </div>
      <div>
        <span className="eyebrow">Uncertainty Flags</span>
        <strong>{uncertaintyFlags.length}</strong>
      </div>
    </div>
  );
}

