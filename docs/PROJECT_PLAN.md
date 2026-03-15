# Project Plan

Last updated: 2026-03-15

## Done

- Ship a working web and API pair for the main review and lab surfaces.
- Persist runs, evaluation artifacts, and import-oriented state in the backend.
- Support deterministic evidence scoring and labeling for structured NSCLC vignettes.
- Support semantic corpus ingestion and retrieval experiments for PubMed and ESMO content.
- Package repository-local datasets so the stack can be exercised without private infrastructure.

## In progress

- Keep import validation logic aligned across local scripts and production-facing application code.
- Continue tightening public documentation around accepted dataset formats and operating assumptions.
- Reduce duplication between runtime fallback logic and local maintenance scripts.

## Next

- Add stronger regression coverage for dataset validation and import normalization.
- Clarify which semantic and vector-backend paths are experimental versus recommended.
- Harden contributor-facing setup and verification guidance.
- Decide which collaboration and governance files should accompany the public repository.
