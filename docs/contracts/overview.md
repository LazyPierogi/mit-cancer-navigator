# Contracts Overview

The canonical contracts for the MVP are defined in:

- `apps/api/app/domain/contracts.py` for deterministic runtime models
- `apps/api/app/schemas/contracts.py` for API payload schemas
- `datasets/` sample fixtures for canonical import and evaluation shapes

The API and UI must preserve:

- structured vignette input only
- deterministic label vocabulary
- explicit uncertainty flags
- score breakdowns for all ranked evidence
- provenance versions for ruleset and corpus

