"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { createRun } from "@/lib/api";
import { VignetteInput } from "@/lib/contracts";

const initialPayload: VignetteInput = {
  cancerType: "NSCLC",
  diseaseSetting: "metastatic",
  histology: "adenocarcinoma",
  lineOfTherapy: "first_line",
  performanceStatus: "1",
  biomarkers: {
    EGFR: "no",
    ALK: "no",
    ROS1: "no",
    PDL1Bucket: "ge50",
    BRAF: "unspecified",
    RET: "unspecified",
    MET: "unspecified",
    KRAS: "unspecified",
    NTRK: "unspecified",
    HER2: "unspecified",
    EGFRExon20ins: "unspecified"
  }
};

const biomarkerOptions = ["yes", "no", "unspecified"] as const;
const pdl1Options = ["lt1", "1to49", "ge50", "unspecified"] as const;
const advancedBiomarkers = ["BRAF", "RET", "MET", "KRAS", "NTRK", "HER2", "EGFRExon20ins"] as const;

export function WorkspaceForm() {
  const router = useRouter();
  const [payload, setPayload] = useState<VignetteInput>(initialPayload);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function updateField<K extends keyof VignetteInput>(key: K, value: VignetteInput[K]) {
    setPayload((current) => ({ ...current, [key]: value }));
  }

  function updateBiomarker<K extends keyof VignetteInput["biomarkers"]>(key: K, value: VignetteInput["biomarkers"][K]) {
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
          <option value="non_squamous">non_squamous</option>
          <option value="squamous">squamous</option>
        </select>
      </label>
      <label>
        Line of therapy
        <select
          value={payload.lineOfTherapy}
          onChange={(event) => updateField("lineOfTherapy", event.target.value as VignetteInput["lineOfTherapy"])}
        >
          <option value="first_line">first_line</option>
          <option value="second_line">second_line</option>
          <option value="later_line">later_line</option>
          <option value="mixed">mixed</option>
          <option value="unspecified">unspecified</option>
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
        <select
          value={payload.biomarkers.PDL1Bucket}
          onChange={(event) => updateBiomarker("PDL1Bucket", event.target.value as VignetteInput["biomarkers"]["PDL1Bucket"])}
        >
          {pdl1Options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <label>
        EGFR
        <select value={payload.biomarkers.EGFR} onChange={(event) => updateBiomarker("EGFR", event.target.value as VignetteInput["biomarkers"]["EGFR"])}>
          {biomarkerOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <label>
        ALK
        <select value={payload.biomarkers.ALK} onChange={(event) => updateBiomarker("ALK", event.target.value as VignetteInput["biomarkers"]["ALK"])}>
          {biomarkerOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <label>
        ROS1
        <select value={payload.biomarkers.ROS1} onChange={(event) => updateBiomarker("ROS1", event.target.value as VignetteInput["biomarkers"]["ROS1"])}>
          {biomarkerOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      {advancedBiomarkers.map((marker) => (
        <label key={marker}>
          {marker}
          <select
            value={payload.biomarkers[marker]}
            onChange={(event) => updateBiomarker(marker, event.target.value as VignetteInput["biomarkers"][typeof marker])}
          >
            {biomarkerOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      ))}
      <div className="form-actions">
        <button type="submit" disabled={isPending}>
          {isPending ? "Running analysis..." : "Run deterministic analysis"}
        </button>
        {error ? <p className="form-error">{error}</p> : null}
      </div>
    </form>
  );
}
