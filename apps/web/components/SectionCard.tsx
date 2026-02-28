import { ReactNode } from "react";

export function SectionCard({
  eyebrow,
  title,
  children
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="section-card">
      <span className="eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  );
}

