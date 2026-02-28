export default function MethodPage() {
  return (
    <section className="section-card">
      <span className="eyebrow">Transparent Method</span>
      <h1 className="page-title">Rules, scoring, and mapping</h1>
      <p>
        The methodology page is where we explain the clinical relevance gate, the exact ERS formula, deterministic
        tie-break rules, and why labels never come from a stochastic medical reasoning model.
      </p>
      <ul className="list-clean">
        <li>Structured vignette inputs only</li>
        <li>Clinical relevance gate before ranking</li>
        <li>ERS = evidence strength + robustness + credibility + recency</li>
        <li>Guideline label derived from topic match and stance rubric</li>
      </ul>
    </section>
  );
}

