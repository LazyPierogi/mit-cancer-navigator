# Data Team Guide: ESMO

This file is the canonical source of truth for the ESMO data structure used by this project.

Related references:
- Frozen snapshots kept next to dataset exports are provenance only, not the canonical contract.
- Validation and import workflows live alongside this file in `docs/data-team/`.

## Final design decision

We will **not** use a separate translation table as the main model.

We will use:
- one shared clinical fact model across patient input, PubMed, and ESMO
- one small logic layer inside each ESMO record when the guideline needs OR/group logic
- the Tag Dictionary / 3-layer ontology as semantic support, not as the primary matching bridge

Why:
- one source of truth is easier to maintain than a second translation file
- PubMed evidence and ESMO guidelines can be compared directly on the same clinical primitives
- guideline-only logic like `any driver positive` or `PD-L1 >=1%` still fits cleanly

## Rule number 1

One row = one specific clinical scenario.

Good example:
- "Metastatic squamous NSCLC, first line, PD-L1 >=50%, pembrolizumab monotherapy"

Bad example:
- "First- and second-line immunotherapy options in advanced squamous NSCLC"

If a row mixes multiple lines, settings, or eligibility rules, split it.

## Canonical ESMO JSON export shape

Top-level export:

```json
{
  "datasetName": "ESMO_Stage_IV_SqCC_Recommended_Treatments",
  "datasetVersion": "v2.0",
  "schemaVersion": "esmo-guideline-v2",
  "records": []
}
```

Each record must follow this schema:

```json
{
  "topicId": "SQCC_IV_01",
  "topicTitle": "Pembrolizumab monotherapy in PD-L1 >=50%",
  "diseaseSetting": "metastatic",
  "histology": "squamous",
  "lineOfTherapy": "first_line",
  "guidelineStance": "recommend",
  "topicInterventionTags": ["pd1", "ici", "immunotherapy-monotherapy"],
  "biomarkerRequirements": {
    "PDL1Bucket": ["ge50"]
  },
  "biomarkerLogic": {
    "anyPositive": [],
    "allNegative": ["EGFR", "ALK", "ROS1"],
    "notes": ""
  },
  "semanticNormalization": {
    "tagDictionaryVersion": "v1",
    "ontologyTags": {
      "layer1": [],
      "layer2": [],
      "layer3": []
    }
  },
  "sourceExcerptShort": "PS 0-2 and PD-L1 >=50% -> pembrolizumab [I, A]",
  "applicabilityNotes": "ECOG PS 0-2, no contraindication to immunotherapy."
}
```

## Allowed values

Please use exactly these values:

- `diseaseSetting`: `early`, `locally_advanced`, `metastatic`
- `histology`: `adenocarcinoma`, `squamous`, `non_squamous`, `all_nsclc`
- `lineOfTherapy`: `first_line`, `second_line`, `later_line`
- `guidelineStance`: `recommend`, `conditional`, `do_not_recommend`, `not_covered`
- `biomarkerRequirements.PDL1Bucket`: `lt1`, `1to49`, `ge50`, `any`, `unspecified`

Please do not invent variations such as:
- `1st line`
- `first-line`
- `advanced/metastatic`
- `non squamous`

Computers love boring consistency. Let's give them boring consistency.

## Biomarker model

### Shared primitives

PubMed evidence, patient facts, and ESMO guideline logic should all use the same biomarker names:

- `EGFR`
- `ALK`
- `ROS1`
- `BRAF`
- `RET`
- `MET`
- `KRAS`
- `NTRK`
- `HER2`
- `EGFRExon20ins`
- `PDL1Bucket`

### What goes in `biomarkerRequirements`

Use `biomarkerRequirements` for simple direct requirements that can be expressed as exact values.

Examples:

```json
{ "PDL1Bucket": ["ge50"] }
```

```json
{ "PDL1Bucket": ["1to49", "ge50"] }
```

```json
{ "PDL1Bucket": ["any"] }
```

Do **not** use comparison-style expressions such as:
- `PDL1Bucket>=1to49`
- `PDL1Bucket<ge50`

These are hard to read and easy to misunderstand. Exact bucket categories are the source of truth.

### What goes in `biomarkerLogic`

Use `biomarkerLogic` only when the guideline needs grouped or OR-style reasoning.

Allowed keys:
- `anyPositive`: list of genes where at least one must be positive
- `allNegative`: list of genes that must all be negative
- `notes`: optional short note when the logic needs human context

Example: any actionable driver positive

```json
{
  "anyPositive": ["EGFR", "ALK", "ROS1", "BRAF", "RET", "MET", "KRAS", "NTRK", "HER2", "EGFRExon20ins"],
  "allNegative": [],
  "notes": "Use when any actionable oncogenic driver is present."
}
```

Example: driver-negative immunotherapy scenario

```json
{
  "anyPositive": [],
  "allNegative": ["EGFR", "ALK", "ROS1"],
  "notes": ""
}
```

If a topic is about driver-positive disease, do not mention that only in free text. Add it in `biomarkerLogic`.

## Intervention tags and ontology tags

We keep two layers on purpose:

- operational layer: `topicInterventionTags` used directly by the app
- normalized semantic layer: `semanticNormalization.ontologyTags` backed by the Tag Dictionary / 3-layer ontology

Decision:
- do not skip the Tag Dictionary
- do not make the app depend only on the ontology either

Both should exist in the final data contract.

Good `topicInterventionTags` examples:
- `pd1`
- `pdl1`
- `ctla4`
- `dual-ici`
- `chemo-ici`
- `platinum-doublet`
- `antiangiogenic`
- `docetaxel`
- `targeted`

Do not put full sentences into tags.

## What to do with performance status or frailty

If the guideline depends on `PS 2`, frailty, or similar conditions:

- put it in `applicabilityNotes`
- keep the main structured clinical scenario otherwise clean

Example:
- `applicabilityNotes`: `Use for PS 2 patients with PD-L1 <50%.`

## Minimal example records

PD-L1 >=50% monotherapy:

```json
{
  "topicId": "SQCC_IV_01",
  "topicTitle": "Pembrolizumab monotherapy in PD-L1 >=50%",
  "diseaseSetting": "metastatic",
  "histology": "squamous",
  "lineOfTherapy": "first_line",
  "guidelineStance": "recommend",
  "topicInterventionTags": ["pd1", "ici", "immunotherapy-monotherapy"],
  "biomarkerRequirements": {
    "PDL1Bucket": ["ge50"]
  },
  "biomarkerLogic": {
    "anyPositive": [],
    "allNegative": ["EGFR", "ALK", "ROS1"],
    "notes": ""
  },
  "semanticNormalization": {
    "tagDictionaryVersion": "v1",
    "ontologyTags": {
      "layer1": ["immunotherapy"],
      "layer2": ["pd1"],
      "layer3": ["pembrolizumab"]
    }
  },
  "sourceExcerptShort": "PS 0-2 and PD-L1 >=50% -> pembrolizumab [I, A]",
  "applicabilityNotes": "ECOG PS 0-2, no contraindication to immunotherapy."
}
```

Driver-positive targeted therapy:

```json
{
  "topicId": "SQCC_IV_10",
  "topicTitle": "Targeted therapy for oncogenic driver-positive tumors",
  "diseaseSetting": "metastatic",
  "histology": "squamous",
  "lineOfTherapy": "first_line",
  "guidelineStance": "recommend",
  "topicInterventionTags": ["targeted"],
  "biomarkerRequirements": {
    "PDL1Bucket": ["unspecified"]
  },
  "biomarkerLogic": {
    "anyPositive": ["EGFR", "ALK", "ROS1", "BRAF", "RET", "MET", "KRAS", "NTRK", "HER2", "EGFRExon20ins"],
    "allNegative": [],
    "notes": "Use when any actionable oncogenic driver is present."
  },
  "semanticNormalization": {
    "tagDictionaryVersion": "v1",
    "ontologyTags": {
      "layer1": ["targeted-therapy"],
      "layer2": ["driver-matched-therapy"],
      "layer3": ["molecularly-directed-treatment"]
    }
  },
  "sourceExcerptShort": "Molecular test positive -> targeted therapy",
  "applicabilityNotes": "Never/light smokers, long-time ex-smokers, or age <50 years with positive molecular test."
}
```

## Most common mistakes

- One record describes multiple therapy lines at once
- A biomarker appears only in the text description, not in `biomarkerRequirements` or `biomarkerLogic`
- `histology` is free text
- `topicInterventionTags` contains sentences instead of tags
- Different eligibility rules are mixed into one row

## Quick self-check

Before you send the dataset, ask one simple question:

"Can someone who knows nothing about this specific row reconstruct from the fields alone who it is for and what the guideline says?"

If the answer is no, the record is still not structured enough.

## Current canonical note

This file is the current truth for ESMO data structure.

If you find another ESMO prep file next to a dataset export, treat that file as a historical snapshot only unless it explicitly says otherwise.
