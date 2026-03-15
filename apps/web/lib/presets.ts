/**
 * Patient preset vignettes for demo presentations.
 *
 * Individual presets: quick-demo scenarios with distinct clinical profiles.
 * Golden vignettes: imported from the canonical frozen benchmark pack.
 */
import frozenPack from "@/lib/data/frozen_pack.sample.json";
import demoPresetsPack from "@/lib/data/demo_presets.curated.json";
import { VignetteInput } from "@/lib/contracts";

export type Preset = {
  id: string;
  name: string;
  detail: string;
  variant: "default" | "golden" | "custom";
  vignette: VignetteInput;
};

const baseBiomarkers: VignetteInput["biomarkers"] = {
  EGFR: "unspecified",
  ALK: "unspecified",
  ROS1: "unspecified",
  PDL1Bucket: "unspecified",
  BRAF: "unspecified",
  RET: "unspecified",
  MET: "unspecified",
  KRAS: "unspecified",
  NTRK: "unspecified",
  HER2: "unspecified",
  EGFRExon20ins: "unspecified"
};

const baseVignetteDefaults: Pick<
  VignetteInput,
  "diseaseStage" | "resectabilityStatus" | "treatmentContext" | "clinicalModifiers"
> = {
  diseaseStage: "stage_iv",
  resectabilityStatus: "not_applicable",
  treatmentContext: "treatment_naive",
  clinicalModifiers: {
    brainMetastases: "unspecified"
  }
};

const driverNegativeBiomarkers = {
  ...baseBiomarkers,
  EGFR: "no" as const,
  ALK: "no" as const,
  ROS1: "no" as const,
  BRAF: "no" as const,
  RET: "no" as const,
  MET: "no" as const,
  KRAS: "no" as const,
  NTRK: "no" as const,
  HER2: "no" as const,
  EGFRExon20ins: "no" as const
};

type DemoPresetCase = (typeof demoPresetsPack.cases)[number];
type FrozenPackCase = (typeof frozenPack.cases)[number];

export const individualPresets: Preset[] = (demoPresetsPack.cases as DemoPresetCase[]).map((item) => {
  const { biomarkers, ...restVignette } = item.vignette as VignetteInput;
  return {
    id: item.caseId,
    name: item.caseLabel,
    detail: item.detail,
    variant: "default",
    vignette: {
      ...baseVignetteDefaults,
      ...restVignette,
      biomarkers: {
        ...baseBiomarkers,
        ...driverNegativeBiomarkers,
        ...biomarkers
      }
    }
  };
});

export const goldenVignettes: Preset[] = (frozenPack.cases as FrozenPackCase[]).map((item) => ({
  id: item.caseId,
  name: item.caseLabel,
  detail: item.detail,
  variant: "golden",
  vignette: item.vignette as VignetteInput
}));
