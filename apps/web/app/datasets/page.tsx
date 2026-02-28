import { datasets } from "@/lib/sample-data";

export default function DatasetsPage() {
  return (
    <section className="table-card">
      <span className="eyebrow">Corpus Provenance</span>
      <h1 className="page-title">Datasets and import batches</h1>
      <p>Hybrid import comes first: canonical ESMO pack, curated PubMed pack, and the frozen evaluation set.</p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Source</th>
            <th>Status</th>
            <th>Records</th>
          </tr>
        </thead>
        <tbody>
          {datasets.map((dataset) => (
            <tr key={dataset.id}>
              <td>{dataset.id}</td>
              <td>{dataset.source}</td>
              <td>{dataset.status}</td>
              <td>{dataset.records}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

