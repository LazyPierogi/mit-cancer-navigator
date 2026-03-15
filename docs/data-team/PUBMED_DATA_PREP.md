# Data Team Guide: PubMed

This file is the canonical source of truth for the PubMed data structure used by this project.

Related references:
- ESMO sister contract: [`./ESMO_DATA_PREP.md`](./ESMO_DATA_PREP.md)
- Validation and import workflows live alongside this file in `docs/data-team/`.

## Why we are doing this

We want every PubMed record to tell the computer:

"What kind of study is this, which population is it about, and what exactly does it cover?"

The biggest quality trap here is mixing up:

- what the article merely mentions
- with who the study population actually is

Those are not the same thing. This is where data gets messy fastest.

## Rule number 1

Describe the study cohort, not just words found in the abstract.

If the abstract mentions `EGFR`, that does not automatically mean:

- the patients were `EGFR-positive`
- the study was about `EGFR-mutated NSCLC`

Please record only what truly describes the study population.

## Fields that must always be filled in

Each PubMed record should have:

- `pmid`
- `title`
- `publicationYear`
- `publicationType`
- `journalTitle`
- `evidenceType`
- `diseaseSetting`
- `histology`
- `lineOfTherapy`
- `biomarkers`
- `interventionTags`
- `outcomeTags`
- `relevantN`

## How to write values

Please use exactly these values:

- `diseaseSetting`: `early`, `locally_advanced`, `metastatic`, `mixed`, `unspecified`
- `histology`: `adenocarcinoma`, `squamous`, `non_squamous`, `all_nsclc`, `mixed`, `unspecified`
- `lineOfTherapy`: `first_line`, `second_line`, `later_line`, `mixed`, `unspecified`
- `evidenceType`: `guideline`, `systematic_review`, `phase3_rct`, `phase2_rct`, `prospective_obs`, `retrospective`, `case_series`, `expert_opinion`

Current MVP import policy:

- preferred values for active MVP drops: `phase3_rct`, `systematic_review`
- `phase2_rct` may still exist in the broader contract, but current strict MVP mode is optimized for `phase3_rct` and `systematic_review`

## How to write biomarkers

For every important biomarker, use exactly one of these three values:

- `yes`
- `no`
- `unspecified`

Useful keys:

- `EGFR`
- `ALK`
- `ROS1`
- `PDL1Bucket`
- `BRAF`
- `RET`
- `MET`
- `KRAS`
- `NTRK`
- `HER2`
- `EGFRExon20ins`

For `PDL1Bucket`, use only:

- `lt1`
- `1to49`
- `ge50`
- `any`
- `unspecified`

Please use one PD-L1 field only.

Do not send:
- `PDL1_ge50=yes`
- `PDL1_1to49=no`
- multiple PD-L1 flags in parallel

Send:
- `PDL1Bucket=ge50`
- `PDL1Bucket=1to49`
- `PDL1Bucket=lt1`
- `PDL1Bucket=any`
- `PDL1Bucket=unspecified`

## Very important biomarker rule

Use `yes` only when the study truly targets that population.

Good examples:

- the paper says `EGFR-mutated NSCLC` -> `EGFR=yes`
- the paper says `no sensitizing EGFR/ALK alterations` -> `EGFR=no`, `ALK=no`

Bad example:

- the abstract contains the word `EGFR`, so we mark `EGFR=yes`

That is exactly the kind of mistake we do not want to fix by hand anymore.

## How to write intervention tags

Intervention tags should say what was actually tested.

Good examples:

- `pd1`
- `pdl1`
- `ctla4`
- `dual-ici`
- `chemo-ici`
- `platinum-doublet`
- `egfr-tki`
- `egfr-targeted`
- `antiangiogenic`
- `docetaxel`
- `amivantamab`
- `lazertinib`

If a study compares two arms, include the main tested intervention and the most important therapy classes.

Export format rule:
- `interventionTags` should be a machine-readable list
- preferred CSV cell format: JSON array string, for example `["pd1","chemotherapy"]`

## How to write `relevantN`

Best option: give the number of patients relevant to the analyzed result.

If you only have the total study population, that is still OK.

If you do not know the number, use `null` or `unspecified`, but please do not guess.

## How to label study type

Please do not leave this for later inference from the title.

Good examples:

- randomized phase III -> `phase3_rct`
- randomized phase II -> `phase2_rct`
- systematic review / network meta-analysis -> `systematic_review`
- retrospective study -> `retrospective`

## Minimal example record

```json
{
  "pmid": "40118215",
  "title": "Cemiplimab Monotherapy for First-Line Treatment...",
  "publicationYear": 2025,
  "publicationType": "Randomized Controlled Trial",
  "journalTitle": "Journal of Thoracic Oncology",
  "evidenceType": "phase3_rct",
  "diseaseSetting": "metastatic",
  "histology": "all_nsclc",
  "lineOfTherapy": "first_line",
  "relevantN": 712,
  "biomarkers": {
    "EGFR": "no",
    "ALK": "no",
    "ROS1": "no",
    "PDL1Bucket": "ge50"
  },
  "interventionTags": ["pd1", "ici", "immunotherapy-monotherapy", "cemiplimab"],
  "outcomeTags": ["OS", "PFS", "ORR", "AE"]
}
```

## Most common mistakes

- a biomarker tag describes a text mention instead of the actual cohort
- `lineOfTherapy` is free text such as `previously untreated / first line-ish`
- `histology` is empty even though the study clearly says `squamous` or `non-squamous`
- `interventionTags` only says `chemotherapy` even though the study is really about something like `nivolumab + ipilimumab + chemotherapy`
- `evidenceType` is missing and has to be guessed later from the paper

## The quick self-check

Imagine a very organized five-year-old looking only at the spreadsheet columns.

If that five-year-old can answer:

- which patients the study is about
- which therapy line it belongs to
- what the main treatment type is
- what the evidence level is

then the record is ready.

If they still need to read the abstract to guess those things, the record is not ready yet.

## Current canonical note

This file is the current truth for PubMed data structure.

Importer behavior and validation workflows should stay aligned to this file.
