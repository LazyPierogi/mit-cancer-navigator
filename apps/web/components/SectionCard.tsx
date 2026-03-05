import { ReactNode } from "react";

export function SectionCard({
  eyebrow,
  title,
  variant = "default",
  children
}: {
  eyebrow: string;
  title: string;
  variant?: "default" | "highlight" | "subtle";
  children: ReactNode;
}) {
  const className = `section-card${variant !== "default" ? ` variant-${variant}` : ""}`;
  return (
    <section className={className}>
      <span className="eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  );
}
