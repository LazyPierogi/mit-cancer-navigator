"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { PresetSelector } from "@/components/PresetSelector";
import { createRun } from "@/lib/api";
import { VignetteInput } from "@/lib/contracts";
import { Preset, individualPresets, goldenVignettes } from "@/lib/presets";

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
const secondaryBiomarkers = ["BRAF", "RET", "MET", "KRAS", "NTRK", "HER2", "EGFRExon20ins"] as const;

export function WorkspaceForm() {
  const router = useRouter();
  const [payload, setPayload] = useState<VignetteInput>(initialPayload);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [activePresetId, setActivePresetId] = useState<string | null>("preset-1");
  const [showGolden, setShowGolden] = useState(false);
  const [showSecondary, setShowSecondary] = useState(false);

  function updateField<K extends keyof VignetteInput>(key: K, value: VignetteInput[K]) {
    setActivePresetId(null);
    setPayload((current) => ({ ...current, [key]: value }));
  }

  function updateBiomarker<K extends keyof VignetteInput["biomarkers"]>(key: K, value: VignetteInput["biomarkers"][K]) {
    setActivePresetId(null);
    setPayload((current) => ({
      ...current,
      biomarkers: {
        ...current.biomarkers,
        [key]: value
      }
    }));
  }

  function handlePresetSelect(preset: Preset) {
    if (preset.id === "__custom__") {
      setActivePresetId(null);
      return;
    }
    setActivePresetId(preset.id);
    setPayload(preset.vignette);

    /* Auto-expand secondary if any secondary biomarker is set */
    const secondaryKeys = ["BRAF", "RET", "MET", "KRAS", "NTRK", "HER2", "EGFRExon20ins"] as const;
    const hasSecondary = secondaryKeys.some(
      (k) => preset.vignette.biomarkers[k] !== "unspecified"
    );
    if (hasSecondary) {
      setShowSecondary(true);
    }
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
    <>
      <PresetSelector
        presets={individualPresets}
        goldenVignettes={goldenVignettes}
        activePresetId={activePresetId}
        onSelect={handlePresetSelect}
        showGolden={showGolden}
        onToggleGolden={() => setShowGolden(!showGolden)}
      />

      <form className="workspace-form" onSubmit={onSubmit}>
        {/* Section 1: Clinical Profile */}
        <fieldset className="form-section">
          <div className="form-section-header">
            <span className="form-section-title">Clinical Profile</span>
          </div>
          <div className="form-fields fields-4col">
            <label>
              Disease setting
              <select
                value={payload.diseaseSetting}
                onChange={(e) => updateField("diseaseSetting", e.target.value as VignetteInput["diseaseSetting"])}
              >
                <option value="early">Early</option>
                <option value="locally_advanced">Locally advanced</option>
                <option value="metastatic">Metastatic</option>
              </select>
            </label>
            <label>
              Histology
              <select
                value={payload.histology}
                onChange={(e) => updateField("histology", e.target.value as VignetteInput["histology"])}
              >
                <option value="adenocarcinoma">Adenocarcinoma</option>
                <option value="non_squamous">Non-squamous</option>
                <option value="squamous">Squamous</option>
              </select>
            </label>
            <label>
              Line of therapy
              <select
                value={payload.lineOfTherapy}
                onChange={(e) => updateField("lineOfTherapy", e.target.value as VignetteInput["lineOfTherapy"])}
              >
                <option value="first_line">1st line</option>
                <option value="second_line">2nd line</option>
                <option value="later_line">Later line</option>
                <option value="mixed">Mixed</option>
                <option value="unspecified">Unspecified</option>
              </select>
            </label>
            <label>
              ECOG PS
              <select
                value={payload.performanceStatus}
                onChange={(e) => updateField("performanceStatus", e.target.value as VignetteInput["performanceStatus"])}
              >
                <option value="0">0</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
              </select>
            </label>
          </div>
        </fieldset>

        {/* Section 2: Primary Biomarkers */}
        <fieldset className="form-section">
          <div className="form-section-header">
            <span className="form-section-title">Primary Biomarkers</span>
          </div>
          <div className="form-fields fields-4col">
            <label>
              PD-L1
              <select
                value={payload.biomarkers.PDL1Bucket}
                onChange={(e) => updateBiomarker("PDL1Bucket", e.target.value as VignetteInput["biomarkers"]["PDL1Bucket"])}
              >
                {pdl1Options.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt === "lt1" ? "<1%" : opt === "1to49" ? "1–49%" : opt === "ge50" ? "≥50%" : "Unspecified"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              EGFR
              <select
                value={payload.biomarkers.EGFR}
                onChange={(e) => updateBiomarker("EGFR", e.target.value as VignetteInput["biomarkers"]["EGFR"])}
              >
                {biomarkerOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt === "yes" ? "Positive" : opt === "no" ? "Negative" : "Unspecified"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              ALK
              <select
                value={payload.biomarkers.ALK}
                onChange={(e) => updateBiomarker("ALK", e.target.value as VignetteInput["biomarkers"]["ALK"])}
              >
                {biomarkerOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt === "yes" ? "Positive" : opt === "no" ? "Negative" : "Unspecified"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              ROS1
              <select
                value={payload.biomarkers.ROS1}
                onChange={(e) => updateBiomarker("ROS1", e.target.value as VignetteInput["biomarkers"]["ROS1"])}
              >
                {biomarkerOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt === "yes" ? "Positive" : opt === "no" ? "Negative" : "Unspecified"}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </fieldset>

        {/* Section 3: Secondary Biomarkers (collapsible) */}
        <fieldset className="form-section">
          <div className="form-section-header">
            <span className="form-section-title">Secondary Biomarkers</span>
            <button
              type="button"
              className="form-section-toggle"
              onClick={() => setShowSecondary(!showSecondary)}
            >
              {showSecondary ? "Collapse" : `Expand (${secondaryBiomarkers.length} markers)`}
            </button>
          </div>
          {showSecondary && (
            <div className="form-fields fields-4col">
              {secondaryBiomarkers.map((marker) => (
                <label key={marker}>
                  {marker}
                  <select
                    value={payload.biomarkers[marker]}
                    onChange={(e) => updateBiomarker(marker, e.target.value as VignetteInput["biomarkers"][typeof marker])}
                  >
                    {biomarkerOptions.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt === "yes" ? "Positive" : opt === "no" ? "Negative" : "Unspecified"}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          )}
          {!showSecondary && (
            <p className="muted" style={{ margin: "4px 0 0", fontSize: "0.78rem" }}>
              All set to &quot;unspecified&quot; — expand to configure BRAF, RET, MET, KRAS, NTRK, HER2, EGFRExon20ins
            </p>
          )}
        </fieldset>

        {/* Submit */}
        <div className="form-actions">
          <button type="submit" disabled={isPending}>
            {isPending ? "Running analysis…" : "Run deterministic analysis"}
          </button>
          {activePresetId && (
            <span className="muted" style={{ fontSize: "0.78rem" }}>
              Using preset: {individualPresets.find(p => p.id === activePresetId)?.name
                || goldenVignettes.find(p => p.id === activePresetId)?.name
                || activePresetId}
            </span>
          )}
          {error ? <p className="form-error">{error}</p> : null}
        </div>
      </form>
    </>
  );
}
