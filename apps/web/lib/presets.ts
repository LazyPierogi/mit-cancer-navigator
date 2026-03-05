/**
 * Patient preset vignettes for demo presentations.
 * 
 * Individual presets (1-3): Quick-demo scenarios with distinct clinical profiles.
 * Golden Vignettes: Full 15-case frozen evaluation set based on frozen_pack.curated.json template.
 */
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

/* ─── Individual Demo Presets ─── */

export const individualPresets: Preset[] = [
    {
        id: "preset-1",
        name: "Patient 1",
        detail: "Metastatic adeno · PD-L1 ≥50% · Driver-negative",
        variant: "default",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: {
                ...baseBiomarkers,
                EGFR: "no",
                ALK: "no",
                ROS1: "no",
                PDL1Bucket: "ge50"
            }
        }
    },
    {
        id: "preset-2",
        name: "Patient 2",
        detail: "Squamous · 2nd line · PD-L1 1–49%",
        variant: "default",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "squamous",
            lineOfTherapy: "second_line",
            performanceStatus: "1",
            biomarkers: {
                ...baseBiomarkers,
                EGFR: "no",
                ALK: "no",
                ROS1: "no",
                PDL1Bucket: "1to49"
            }
        }
    },
    {
        id: "preset-3",
        name: "Patient 3",
        detail: "Non-squamous · EGFR+ · 1st line",
        variant: "default",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "non_squamous",
            lineOfTherapy: "first_line",
            performanceStatus: "0",
            biomarkers: {
                ...baseBiomarkers,
                EGFR: "yes",
                ALK: "no",
                ROS1: "no",
                PDL1Bucket: "lt1"
            }
        }
    }
];

/* ─── Golden Vignettes (15 frozen evaluation cases) ─── */

export const goldenVignettes: Preset[] = [
    {
        id: "VIG-CURATED-001",
        name: "GV-001",
        detail: "SCC met · 1L · PD-L1≥50 · driver-neg",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "squamous",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", PDL1Bucket: "ge50" }
        }
    },
    {
        id: "VIG-CURATED-002",
        name: "GV-002",
        detail: "Adeno met · 1L · PD-L1≥50 · driver-neg",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", PDL1Bucket: "ge50" }
        }
    },
    {
        id: "VIG-CURATED-003",
        name: "GV-003",
        detail: "Adeno met · 1L · PD-L1 1–49 · driver-neg",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "first_line",
            performanceStatus: "0",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", PDL1Bucket: "1to49" }
        }
    },
    {
        id: "VIG-CURATED-004",
        name: "GV-004",
        detail: "Adeno met · 1L · PD-L1<1 · driver-neg",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", PDL1Bucket: "lt1" }
        }
    },
    {
        id: "VIG-CURATED-005",
        name: "GV-005",
        detail: "Adeno met · 1L · EGFR+ · PD-L1 unspec",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "yes", ALK: "no", ROS1: "no", PDL1Bucket: "unspecified" }
        }
    },
    {
        id: "VIG-CURATED-006",
        name: "GV-006",
        detail: "Adeno met · 1L · ALK+ · PD-L1 unspec",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "first_line",
            performanceStatus: "0",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "yes", ROS1: "no", PDL1Bucket: "unspecified" }
        }
    },
    {
        id: "VIG-CURATED-007",
        name: "GV-007",
        detail: "Adeno met · 1L · ROS1+ · PD-L1 unspec",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "yes", PDL1Bucket: "unspecified" }
        }
    },
    {
        id: "VIG-CURATED-008",
        name: "GV-008",
        detail: "Adeno met · 2L · PD-L1≥50 · driver-neg",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "second_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", PDL1Bucket: "ge50" }
        }
    },
    {
        id: "VIG-CURATED-009",
        name: "GV-009",
        detail: "SCC met · 2L · PD-L1 1–49 · driver-neg",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "squamous",
            lineOfTherapy: "second_line",
            performanceStatus: "2",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", PDL1Bucket: "1to49" }
        }
    },
    {
        id: "VIG-CURATED-010",
        name: "GV-010",
        detail: "Adeno met · 1L · BRAF+ · PD-L1 unspec",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", BRAF: "yes", PDL1Bucket: "unspecified" }
        }
    },
    {
        id: "VIG-CURATED-011",
        name: "GV-011",
        detail: "Non-SCC met · 1L · KRAS+ · PD-L1≥50",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "non_squamous",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", KRAS: "yes", PDL1Bucket: "ge50" }
        }
    },
    {
        id: "VIG-CURATED-012",
        name: "GV-012",
        detail: "Non-SCC met · 1L · MET+ · PD-L1<1",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "non_squamous",
            lineOfTherapy: "first_line",
            performanceStatus: "0",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", MET: "yes", PDL1Bucket: "lt1" }
        }
    },
    {
        id: "VIG-CURATED-013",
        name: "GV-013",
        detail: "Adeno locally adv · 1L · PD-L1≥50",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "locally_advanced",
            histology: "adenocarcinoma",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", PDL1Bucket: "ge50" }
        }
    },
    {
        id: "VIG-CURATED-014",
        name: "GV-014",
        detail: "Adeno met · later-line · driver-neg · PD-L1 unspec",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "adenocarcinoma",
            lineOfTherapy: "later_line",
            performanceStatus: "2",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", PDL1Bucket: "unspecified" }
        }
    },
    {
        id: "VIG-CURATED-015",
        name: "GV-015",
        detail: "SCC met · 1L · HER2+ · PD-L1 1–49",
        variant: "golden",
        vignette: {
            cancerType: "NSCLC",
            diseaseSetting: "metastatic",
            histology: "squamous",
            lineOfTherapy: "first_line",
            performanceStatus: "1",
            biomarkers: { ...baseBiomarkers, EGFR: "no", ALK: "no", ROS1: "no", HER2: "yes", PDL1Bucket: "1to49" }
        }
    }
];
