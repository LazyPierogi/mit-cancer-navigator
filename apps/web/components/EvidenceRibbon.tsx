type EvidenceItem = {
  rank: number;
  evidenceId: string;
  title: string;
  ersTotal: number;
  mappingLabel: string;
  mappedTopicTitle: string | null;
  applicabilityNote: string;
  ersBreakdown: {
    evidenceStrength: number;
    datasetRobustness: number;
    sourceCredibility: number;
    recency: number;
  };
};

const labelClassMap: Record<string, string> = {
  aligned: "tone-good",
  guideline_silent: "tone-muted",
  conflict: "tone-bad"
};

const labelDisplayMap: Record<string, string> = {
  aligned: "Aligned",
  guideline_silent: "Silent",
  conflict: "Conflict"
};

export function EvidenceRibbon({ items }: { items: EvidenceItem[] }) {
  return (
    <div className="ribbon">
      {items.map((item) => (
        <article className="ribbon-card" key={item.evidenceId}>
          <div className="ribbon-rail" />
          <div className="ribbon-rank">#{item.rank}</div>
          <div className="ribbon-body">
            <div className="eyebrow">{item.evidenceId}</div>
            <h3>{item.title}</h3>
            {item.mappedTopicTitle && (
              <p>
                <strong>Guideline topic:</strong> {item.mappedTopicTitle}
              </p>
            )}
            {!item.mappedTopicTitle && (
              <p className="muted">No guideline topic matched — labeled as silent.</p>
            )}
            <p className="muted">{item.applicabilityNote}</p>
            <div className="score-grid compact">
              <div>
                <span className="eyebrow">ERS Total</span>
                <strong>{item.ersTotal}</strong>
              </div>
              <div>
                <span className="eyebrow">Strength</span>
                <strong>{item.ersBreakdown.evidenceStrength}</strong>
              </div>
              <div>
                <span className="eyebrow">Robustness</span>
                <strong>{item.ersBreakdown.datasetRobustness}</strong>
              </div>
              <div>
                <span className="eyebrow">Credibility</span>
                <strong>{item.ersBreakdown.sourceCredibility}</strong>
              </div>
            </div>
          </div>
          <div className={`status-pill ${labelClassMap[item.mappingLabel] ?? "tone-muted"}`}>
            {labelDisplayMap[item.mappingLabel] ?? item.mappingLabel.replace(/_/g, " ")}
          </div>
        </article>
      ))}
    </div>
  );
}
