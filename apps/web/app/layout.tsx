import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lung Cancer Treatment Navigator",
  description: "Clinical Atlas / Signal Lab for deterministic NSCLC evidence triage."
};

const primaryNav = [
  { href: "/", label: "Atlas" },
  { href: "/workspace", label: "Workspace" },
  { href: "/datasets", label: "Datasets" },
  { href: "/docs/governance", label: "Governance" }
];

const labsNav = [
  { href: "/labs/evals", label: "Eval Lab" },
  { href: "/labs/embeddings", label: "Embedding Lab" },
  { href: "/labs/debug", label: "Debug Console" }
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <div className="shell">
          <header className="site-header">
            <Link href="/" className="brand-lockup">
              <div>
                <p className="brand-kicker">Clinical Atlas · Signal Lab</p>
                <span className="brand-title">Lung Cancer Treatment Navigator</span>
              </div>
            </Link>
            <nav className="site-nav" aria-label="Primary">
              {primaryNav.map((item) => (
                <Link href={item.href} key={item.href}>
                  {item.label}
                </Link>
              ))}
              <div className="nav-group">
                <button className="nav-group-trigger" type="button">
                  Labs
                </button>
                <div className="nav-group-menu">
                  {labsNav.map((item) => (
                    <Link href={item.href} key={item.href}>
                      {item.label}
                    </Link>
                  ))}
                </div>
              </div>
            </nav>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
