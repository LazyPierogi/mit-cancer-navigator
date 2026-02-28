import { policy } from "@/lib/sample-data";

export default function GovernancePage() {
  return (
    <div className="content-grid">
      <section className="section-card">
        <span className="eyebrow">Responsible AI</span>
        <h1 className="page-title">Governance policy</h1>
        <p>
          Safety boundaries are implemented as product behavior: fixed vocabularies, no recommendation language,
          explicit uncertainty, and frozen scope.
        </p>
        <ul className="list-clean">
          {policy.safetyBoundaries.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
      <section className="section-card">
        <span className="eyebrow">Release Gating</span>
        <h2>Hard stops and soft review</h2>
        <ul className="list-clean">
          {policy.hardStops.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
