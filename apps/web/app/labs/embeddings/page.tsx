export default function EmbeddingsPage() {
  return (
    <div className="content-grid">
      <section className="section-card">
        <span className="eyebrow">Embedding Lab</span>
        <h1 className="page-title">Projection view</h1>
        <p>
          The embedding explorer lives in the lab layer so it can help debug neighborhoods and impress the jury
          without pretending embeddings are the clinical decision engine.
        </p>
        <div className="embedding-stage" />
      </section>
      <section className="panel">
        <span className="eyebrow">Filters</span>
        <ul className="list-clean">
          <li>Corpus version</li>
          <li>Topic label</li>
          <li>Evidence type</li>
          <li>Year range</li>
        </ul>
      </section>
    </div>
  );
}

