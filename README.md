# Lung Cancer Treatment Navigator

Deterministic evidence triage platform for NSCLC vignette analysis, guideline mapping, and benchmark-gated iteration.

## Workspace

- `apps/web`: Next.js product surface and reviewer/lab UX
- `apps/api`: FastAPI API, deterministic domain logic, governance, evaluation
- `apps/worker`: async job skeleton for ingestion and benchmark processing
- `packages/design-tokens`: shared design tokens
- `datasets/`: curated ESMO, PubMed, and frozen vignette fixtures
- `infra/compose`: local infrastructure definitions

## Intended stack

- Web: Next.js + TypeScript
- API: FastAPI + Pydantic
- Worker: Dramatiq + Redis
- Data: PostgreSQL + pgvector
- Observability: OpenTelemetry + structured traces

## Local dev

This repository is scaffolded but dependencies are not installed by automation.

### Web

```bash
npm install
npm run dev:web
```

### API

```bash
uv sync --project apps/api
npm run migrate:api
uv run --project apps/api uvicorn app.main:app --reload
```

### Worker

```bash
uv sync --project apps/worker
uv run --project apps/worker python -m app.worker
```

## Notes

- The API defaults to a local SQLite bootstrap database at `apps/api/navigator.db` so the scaffold runs immediately.
- For the intended stack, set `DATABASE_URL` to PostgreSQL/pgvector and keep using the same Alembic workflow.
