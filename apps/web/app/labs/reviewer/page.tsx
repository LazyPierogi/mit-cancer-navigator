import { reviewerQueue } from "@/lib/sample-data";

export default function ReviewerPage() {
  return (
    <section className="table-card">
      <span className="eyebrow">Reviewer Workflow</span>
      <h1 className="page-title">Scoring queue</h1>
      <table>
        <thead>
          <tr>
            <th>Case</th>
            <th>Reviewer</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {reviewerQueue.map((item) => (
            <tr key={item.caseId}>
              <td>{item.caseId}</td>
              <td>{item.reviewer}</td>
              <td>{item.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

