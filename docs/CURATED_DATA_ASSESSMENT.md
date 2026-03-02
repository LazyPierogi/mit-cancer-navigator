# Curated Data Assessment

Date: 2026-03-02

## Sources reviewed

- `datasets/esmo/ESMO_Stage_IV_SqCC_10_Recommended_Treatments_NORMALIZED_v0.3.1_3layer.json`
- `datasets/esmo/nsclc_tag_dictionary_v0.4_3layer_expanded.json`
- `datasets/esmo/pubmed_to_nsclc_3layer_translation_table_v1.1.csv`
- `datasets/pubmed/Test11.txt`

## What is usable right now

- The ESMO file contains 10 structurally consistent rows.
- The PubMed file contains 9 rows, not 10.
- Titles, years, publication types, and most abstracts are present and machine-readable.
- The app can already consume a best-effort canonical preview pack derived from these files.

## What was fixed in the preview ingest

- Added `scripts/build_curated_preview.py` to convert the raw ESMO and PubMed files into canonical app datasets.
- Generated:
  - `datasets/esmo/topics.curated.json`
  - `datasets/pubmed/evidence.curated.json`
  - `datasets/vignettes/frozen_pack.curated.json`
- Updated the API sample-data loader to prefer curated preview files and fall back to legacy sample files.
- Extended the app contract with:
  - `lineOfTherapy`
  - richer biomarker support
  - range and OR-style applicability rules
- Corrected clearly wrong PubMed biomarker semantics in the preview pack.
  - Example: records that said `EGFR_tag=positive` because the abstract mentioned EGFR are mapped to `EGFR=no` or `EGFR=yes` only when the study population supports that interpretation.
- Normalized PubMed fields into the current domain contract:
  - `evidenceType`
  - `sourceCategory`
  - `relevantN`
  - `populationTags`
  - `interventionTags`
- Converted the ESMO rows into canonical `GuidelineTopic` objects with explicit `prerequisites` so we do not lose all source nuance.

## Remaining limitations after the v2 schema upgrade

These data now work well enough for a credible preview corpus, but there are still a few things to tighten before calling the import production-grade.

1. Performance-status and frailty logic are still only partially represented.
   Example: ESMO topics that depend on `PS 2` or frailty are preserved in notes/prerequisites, but not yet fully enforced in ranking.

2. PubMed still needs cleaner study-intent annotation.
   A toxicity-management trial and an efficacy trial can both look "relevant" unless the source row says clearly what kind of evidence it is for treatment selection.

3. Some cohorts are still broad in the source.
   `mixed`, `all_nsclc`, and `unspecified` are safe for preview, but they lower precision for final ranking.

4. The raw delivery should stop mixing entity mention detection with cohort eligibility.
   Mentioning `EGFR` in an abstract is not the same as studying an `EGFR-mutated` population.

## Verification

Preview run on the curated pack:

- vignette: metastatic squamous NSCLC, PS 1, EGFR/ALK/ROS1 negative, PD-L1 `ge50`
- eligible evidence: 2 / 9
- top evidence:
  - `PMID-40118215` -> `SQCC_IV_01`
  - `PMID-40446626` -> `SQCC_IV_04`

Evaluation result on the curated preview pack:

- recall: `1.0`
- mapping_accuracy: `1.0`
- deterministic_logic_fidelity: `1.0`

## Recommended next step

Promote the preview ingest into a real import pipeline after adding:

- explicit performance-status/frailty rules where ESMO requires them
- cleaner PubMed study-intent labels
- stable Data Team delivery templates for ESMO and PubMed
- a larger frozen benchmark pack than the current single preview case
