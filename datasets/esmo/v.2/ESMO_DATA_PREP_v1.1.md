# Data Team Guide: ESMO

## Why we are doing this

We want every ESMO row to tell the computer one simple thing:

"Which patient scenario does this guideline topic apply to, and which
treatment option does it describe?"

If one row mixes several scenarios together, we have to split it by hand
later. That gets messy very fast.

## Rule number 1

One row = one specific clinical scenario.

Good example:

-   "Metastatic squamous NSCLC, first line, PD-L1 \>=50%,
    driver-negative, pembrolizumab monotherapy"

Bad example:

-   "First- and second-line immunotherapy options in advanced squamous
    NSCLC"

These are actually different rules. They should not live in one row.

## Fields that must always be filled in

Each ESMO record should have:

-   `topicId`
-   `topicTitle`
-   `diseaseSetting`
-   `histology`
-   `lineOfTherapy`
-   `guidelineStance`
-   `topicInterventionTags`
-   `biomarkerConditions`
-   `sourceExcerptShort`
-   `applicabilityNotes`

## How to write values

Please use exactly these values:

-   `diseaseSetting`: `early`, `locally_advanced`, `metastatic`
-   `histology`: `adenocarcinoma`, `squamous`, `non_squamous`,
    `all_nsclc`
-   `lineOfTherapy`: `first_line`, `second_line`, `later_line`
-   `guidelineStance`: `recommend`, `conditional`, `do_not_recommend`,
    `not_covered`

Please do not invent variations such as:

-   `1st line`
-   `first-line`
-   `advanced/metastatic`
-   `non squamous`

Computers love boring consistency. Let's give them boring consistency.

## How to write biomarkers

Best practice: keep them in a separate list of rules.

Good examples:

-   `all_negative(EGFR,ALK,ROS1)`
-   `PDL1Bucket>=ge50`
-   `PDL1Bucket>=1to49`
-   `PDL1Bucket<ge50`
-   `any_positive(EGFR,ALK,ROS1,BRAF,RET,MET,EGFRExon20ins,KRAS,NTRK,HER2)`

If a topic is about driver-positive disease, please do not mention that
only in the description. Add it as a structured rule too.

## How to write intervention tags

Tags should be short and specific.

Good examples:

-   `pd1`
-   `pdl1`
-   `ctla4`
-   `dual-ici`
-   `chemo-ici`
-   `platinum-doublet`
-   `egfr-targeted`
-   `antiangiogenic`
-   `docetaxel`

Do not put full sentences into tags.

Bad example:

-   `recommended for fit patients with high PD-L1`

That is a note, not a tag.

## What to do with performance status or frailty

If the guideline depends on `PS 2`, frailty, or a similar condition:

-   put it in `applicabilityNotes`
-   and also in a simple helper field if you have one

Example:

-   `applicabilityNotes`: `Use for PS 2 patients with PD-L1 <50%.`

This matters because these conditions change the meaning of the
recommendation.

## Minimal example record

``` json
{
  "topicId": "SQCC_IV_01",
  "topicTitle": "Pembrolizumab monotherapy in PD-L1 >=50%",
  "diseaseSetting": "metastatic",
  "histology": "squamous",
  "lineOfTherapy": "first_line",
  "guidelineStance": "recommend",
  "topicInterventionTags": ["pd1", "ici", "immunotherapy-monotherapy"],
  "biomarkerConditions": ["all_negative(EGFR,ALK,ROS1)", "PDL1Bucket>=ge50"],
  "sourceExcerptShort": "PS 0-2 and PD-L1 >=50% -> pembrolizumab [I, A]",
  "applicabilityNotes": "ECOG PS 0-2, no contraindication to immunotherapy."
}
```

## Most common mistakes

-   One record describes multiple therapy lines at once
-   A biomarker appears only in the text description, not in the
    structured field
-   `histology` is free text
-   `topicInterventionTags` contains sentences instead of tags
-   `guidelineStance` is described in plain language instead of one of
    the agreed tokens

## The quick self-check

Before you send the dataset, ask one simple question:

"Can someone who knows nothing about this specific record reconstruct
from the fields alone who it is for and what the guideline says?"

If the answer is no, the record is still not structured enough.

------------------------------------------------------------------------

# Versioning

## Version 1.1

Changes: - Added structured biomarker rule `PDL1Any`. - Clarified that
PD-L1 must always be represented in `biomarkerConditions` if mentioned
in text. - Disallowed leaving PD-L1 unstructured when guideline states
"regardless of PD-L1".

### New Allowed Biomarker Token

-   `PDL1Any`

Use `PDL1Any` when the guideline explicitly states that the
recommendation applies regardless of PD-L1 level.

Example:

-   Text: "Use for PS 0--1 regardless of PD-L1 expression."
-   Structured: `biomarkerConditions`: \["PDL1Any"\]

Do not omit PD-L1 from `biomarkerConditions` if it appears in
`topicTitle`, `sourceExcerptShort`, or `applicabilityNotes`.
