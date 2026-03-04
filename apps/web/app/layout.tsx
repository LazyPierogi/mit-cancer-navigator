import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lung Cancer Treatment Navigator",
  description: "Clinical Atlas / Signal Lab for deterministic NSCLC evidence triage."
};

const navItems = [
  { href: "/", label: "Atlas" },
  { href: "/workspace", label: "Workspace" },
  { href: "/datasets", label: "Datasets" },
  { href: "/labs/evals", label: "Eval Lab" },
  { href: "/labs/embeddings", label: "Embedding Lab" },
  { href: "/labs/debug", label: "Debug Console" },
  { href: "/docs/governance", label: "Governance" }
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="site-header">
            <div>
              <p className="brand-kicker">Clinical Atlas / Signal Lab</p>
              <Link href="/" className="brand-title">
                Lung Cancer Treatment Navigator
              </Link>
            </div>
            <nav className="site-nav" aria-label="Primary">
              {navItems.map((item) => (
                <Link href={item.href} key={item.href}>
                  {item.label}
                </Link>
              ))}
            </nav>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
