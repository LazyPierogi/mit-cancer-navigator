"use client";

import { useEffect, useState, useTransition } from "react";

import { getImportDebugConfig, getImportDebugLogs, updateImportDebugConfig } from "@/lib/api";
import { ImportDebugConfig, ImportDebugLogEntry } from "@/lib/contracts";

function formatDate(value: string) {
  return new Date(value).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
}

function logTone(level: string) {
  if (level === "error") {
    return "tone-bad";
  }
  if (level === "warning") {
    return "tone-warn";
  }
  return "tone-muted";
}

export default function DebugConsolePage() {
  const [config, setConfig] = useState<ImportDebugConfig>({ strictMvpPubmed: false });
  const [logs, setLogs] = useState<ImportDebugLogEntry[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  async function refresh() {
    try {
      const [nextConfig, nextLogs] = await Promise.all([getImportDebugConfig(), getImportDebugLogs(120)]);
      setConfig(nextConfig);
      setLogs(nextLogs);
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to load debug console state.");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function onToggleStrict() {
    startTransition(async () => {
      try {
        const updated = await updateImportDebugConfig({ strictMvpPubmed: !config.strictMvpPubmed });
        setConfig(updated);
        const nextLogs = await getImportDebugLogs(120);
        setLogs(nextLogs);
        setErrorMessage(null);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "Failed to update strict mode.");
      }
    });
  }

  return (
    <div className="content-grid">
      <section className="section-card">
        <span className="eyebrow">Import Guardrails</span>
        <h1 className="page-title">Debug Console</h1>
        <p>Toggle strict PubMed MVP validation and inspect recent import pipeline events without leaving the app.</p>
        <div className="debug-actions">
          <button type="button" onClick={onToggleStrict} disabled={isPending}>
            {config.strictMvpPubmed ? "Disable strict MVP mode" : "Enable strict MVP mode"}
          </button>
          <span className={`status-tag ${config.strictMvpPubmed ? "tone-good" : "tone-muted"}`}>
            strictMvpPubmed: {String(config.strictMvpPubmed)}
          </span>
          <button type="button" className="debug-secondary" onClick={() => startTransition(refresh)} disabled={isPending}>
            Refresh logs
          </button>
        </div>
        {errorMessage ? <p className="form-error">{errorMessage}</p> : null}
      </section>

      <section className="table-card">
        <span className="eyebrow">Recent Events</span>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Level</th>
              <th>Event</th>
              <th>Dataset</th>
              <th>Message</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((entry) => (
              <tr key={`${entry.timestamp}-${entry.event}-${entry.message}`}>
                <td>{formatDate(entry.timestamp)}</td>
                <td>
                  <span className={`status-tag ${logTone(entry.level)}`}>{entry.level}</span>
                </td>
                <td>{entry.event}</td>
                <td>{entry.datasetKind ?? "n/a"}</td>
                <td>{entry.message}</td>
                <td className="debug-log-details">
                  {entry.path ? <div>{entry.path}</div> : null}
                  {Object.keys(entry.details).length ? <pre>{JSON.stringify(entry.details, null, 2)}</pre> : "n/a"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
