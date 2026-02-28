export default function EvalCasePage() {
  return (
    <section className="workspace-card">
      <span className="eyebrow">Case Review</span>
      <h1 className="page-title">Per-case scoring sheet</h1>
      <p>
        This route is reserved for predicted vs reference comparisons, citation validity toggles, and disagreement
        notes.
      </p>
      <ul className="list-clean">
        <li>Reference relevant evidence list</li>
        <li>Predicted top evidence list</li>
        <li>Mapping label comparison</li>
        <li>Citation validity decision</li>
      </ul>
    </section>
  );
}

