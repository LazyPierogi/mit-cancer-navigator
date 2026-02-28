"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { createRun } from "@/lib/api";
import { VignetteInput } from "@/lib/contracts";

const initialPayload: VignetteInput = {
  cancerType: "NSCLC",
  diseaseSetting: "metastatic",
  histology: "adenocarcinoma",
  performanceStatus: "1",
  biomarkers: {
    EGFR: "no",
    ALK: "no",
    ROS1: "no",
    PDL1Bucket: "ge50"
  }
};

export function WorkspaceForm() {
  const router = useRouter();
  const [payload, setPayload] = useState<VignetteInput>(initialPayload);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function updateField<K extends keyof VignetteInput>(key: K, value: VignetteInput[K]) {
    setPayload((current) => ({ ...current, [key]: value }));
  }

  function updateBiomarker(key: keyof VignetteInput["biomarkers"], value: "yes" | "no" | "lt1" | "1to49" | "ge50") {
    setPayload((current) => ({
      ...current,
      biomarkers: {
        ...current.biomarkers,
        [key]: value
      }
    }));
  }

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    startTransition(async () => {
      try {
        const response = await createRun(payload);
        router.push(`/runs/${response.run.id}`);
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Run creation failed.");
      }
    });
  }

  return (
    <form className="workspace-form" onSubmit={onSubmit}>
      <label>
        Disease setting
        <select
          value={payload.diseaseSetting}
          onChange={(event) => updateField("diseaseSetting", event.target.value as VignetteInput["diseaseSetting"])}
        >
          <option value="early">early</option>
          <option value="locally_advanced">locally_advanced</option>
          <option value="metastatic">metastatic</option>
        </select>
      </label>
      <label>
        Histology
        <select value={payload.histology} onChange={(event) => updateField("histology", event.target.value as VignetteInput["histology"])}>
          <option value="adenocarcinoma">adenocarcinoma</option>
          <option value="squamous">squamous</option>
        </select>
      </label>
      <label>
        Performance status
        <select
          value={payload.performanceStatus}
          onChange={(event) => updateField("performanceStatus", event.target.value as VignetteInput["performanceStatus"])}
        >
          <option value="0">0</option>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
        </select>
      </label>
      <label>
        PD-L1 bucket
        <select value={payload.biomarkers.PDL1Bucket} onChange={(event) => updateBiomarker("PDL1Bucket", event.target.value as "lt1" | "1to49" | "ge50")}>
          <option value="lt1">lt1</option>
          <option value="1to49">1to49</option>
          <option value="ge50">ge50</option>
        </select>
      </label>
      <label>
        EGFR
        <select value={payload.biomarkers.EGFR} onChange={(event) => updateBiomarker("EGFR", event.target.value as "yes" | "no")}>
          <option value="yes">yes</option>
          <option value="no">no</option>
        </select>
      </label>
      <label>
        ALK
        <select value={payload.biomarkers.ALK} onChange={(event) => updateBiomarker("ALK", event.target.value as "yes" | "no")}>
          <option value="yes">yes</option>
          <option value="no">no</option>
        </select>
      </label>
      <label>
        ROS1
        <select value={payload.biomarkers.ROS1} onChange={(event) => updateBiomarker("ROS1", event.target.value as "yes" | "no")}>
          <option value="yes">yes</option>
          <option value="no">no</option>
        </select>
      </label>
      <div className="form-actions">
        <button type="submit" disabled={isPending}>
          {isPending ? "Running analysis..." : "Run deterministic analysis"}
        </button>
        {error ? <p className="form-error">{error}</p> : null}
      </div>
    </form>
  );
}

