type Metric = {
  label: string;
  value: string;
  detail: string;
};

export function MetricGrid({ metrics }: { metrics: Metric[] }) {
  return (
    <div className="metric-grid">
      {metrics.map((metric) => (
        <div className="metric-card" key={metric.label}>
          <span className="eyebrow">{metric.label}</span>
          <strong>{metric.value}</strong>
          <p>{metric.detail}</p>
        </div>
      ))}
    </div>
  );
}

