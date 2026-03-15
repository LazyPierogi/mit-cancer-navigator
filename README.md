# Lung Cancer Treatment Navigator

Lung Cancer Treatment Navigator is a research-oriented evidence triage application for **non-small cell lung cancer (NSCLC)** case review.

It combines:

- a **deterministic analysis path** for ranking, labeling, and traceability
- an experimental **semantic retrieval lab** for chunk-level search and retrieval experiments
- benchmark and provenance surfaces for evaluating corpus and runtime changes

## Important scope note

This repository is **not** a clinical decision system and does **not** prescribe treatment.

The project is designed to help reviewers:

- capture a structured NSCLC vignette
- retrieve relevant evidence and guideline topics
- inspect scoring, exclusions, and provenance
- compare deterministic and semantic retrieval behavior in a controlled environment

## Repository layout

```text
apps/
  api/        FastAPI backend
  web/        Next.js frontend
  worker/     async worker scaffold

datasets/
  esmo/       guideline and topic fixtures
  pubmed/     evidence fixtures
  vignettes/  benchmark fixtures

docs/
  adr/        architecture decisions
  contracts/  contract notes
  data-team/  import and validation workflows

infra/
  compose/    local development services

packages/
  design-tokens/
```

## Stack

- **Frontend:** Next.js 15, React 19, TypeScript
- **Backend:** FastAPI, Pydantic, SQLAlchemy, Alembic
- **Worker:** Python async worker scaffold
- **Storage:** SQLite bootstrap mode locally, with PostgreSQL-oriented app structure
- **Search/Retrieval lab:** local hybrid retrieval today, adapter-friendly for external vector backends

## Current product shape

The repository currently includes two main runtime modes:

- **Deterministic Runtime**
  - structured vignette input
  - deterministic evidence scoring and labeling
  - explicit uncertainty and provenance metadata

- **Semantic Retrieval Lab**
  - raw-text chunk ingestion for PubMed and ESMO content
  - semantic and hybrid retrieval experiments
  - benchmark and explainability support surfaces

## Quick start

### Prerequisites

- Node.js 24+
- Python 3.11+
- `uv`
- Docker optional for local Postgres/Redis

### Install dependencies

```bash
npm install
uv sync --project apps/api
uv sync --project apps/worker
```

### Start the API

```bash
npm run migrate:api
npm run dev:api
```

API health endpoint:

- `http://127.0.0.1:8000/health`

### Start the web app

```bash
npm run dev:web
```

Web app:

- `http://127.0.0.1:3000`

### Optional local infrastructure

```bash
docker compose -f infra/compose/docker-compose.yml up -d
```

## Verification

### Backend tests

```bash
npm run test:domain
uv run --project apps/api python -m unittest discover -s apps/api/tests -p 'test_*.py'
```

### Frontend build

```bash
npm --workspace apps/web run build
```

## Datasets and imports

The repository includes sample and curated fixtures under `datasets/`.

For dataset validation and import workflows, see:

- `docs/data-team/VALIDATION_WORKFLOW.md`
- `docs/data-team/IMPORT_WORKFLOW.md`
- `docs/data-team/ESMO_DATA_PREP.md`
- `docs/data-team/PUBMED_DATA_PREP.md`

## Documentation

- `docs/adr/0001-modular-monolith.md`
- `docs/contracts/overview.md`
- `docs/PROJECT_PLAN.md`
- `docs/ROADMAP.md`
- `docs/STARTUP_CHECKLIST.md`

## Open-source release notes

This repository was cleaned up for public release:

- presentation-only materials were removed
- local machine paths and agent-bootstrap artifacts were removed from public-facing docs
- remaining documentation was narrowed to product, setup, contracts, and data workflows

## Suggested next public-repo steps

The repository is now much closer to open-source ready, but you should still choose explicitly:

- a `LICENSE`
- whether you want `CONTRIBUTING.md`
- whether you want `CODE_OF_CONDUCT.md`
- whether the published dataset fixtures are all legally and operationally safe to keep public
