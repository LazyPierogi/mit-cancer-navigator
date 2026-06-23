# MIT Cancer Navigator Agent Guide

## Project Intent

MIT Cancer Navigator is a research-oriented NSCLC evidence navigation and evaluation system. Preserve its responsible AI posture: deterministic guardrails, visible provenance, explicit uncertainty, and assistive LLM behavior only where it supports reviewer judgment.

## Work Lanes

- Classify each request as `micro-change`, `scoped-change`, or `complex-change` before tool use.
- Use Codebase Memory first for code ownership discovery in this indexed repo: project id `Users-mario-Repo-mit-cancer-navigator`.
- Keep changes narrow and reversible; do not refactor unrelated runtime, dataset, or UI surfaces.
- For Supabase or Postgres changes, treat the task as at least `scoped-change`; verify RLS/grants directly against the database when credentials are in scope.

## Architecture Map

- `apps/web`: Next.js reviewer and lab UI. It talks to the FastAPI API, not directly to Supabase Data API.
- `apps/api`: FastAPI app, SQLAlchemy models, Alembic migrations, deterministic engine, imports, semantic retrieval, and governance endpoints.
- `apps/api/alembic/versions`: database schema history. Security migrations should be idempotent where possible and safe for local non-Supabase Postgres.
- `datasets`: bundled proof-of-concept fixtures only; do not imply clinical or production completeness.
- `docs`: operating memory, codebase map, verification matrix, data-team import guidance, ADRs, and roadmap material.

## Security Rules

- All application tables in Supabase `public` must have Row-Level Security enabled.
- Public Supabase roles (`anon`, `authenticated`) must not receive table or sequence grants unless a future feature explicitly chooses Data API exposure and adds matching RLS policies.
- The current app contract is backend-mediated database access through SQLAlchemy. Do not add frontend Supabase client access without revisiting RLS policies and `docs/PROJECT_MEMORY.md`.
- Do not expose service-role keys, database URLs, or other secrets in docs, logs, screenshots, or examples.

## Verification

- Use `docs/VERIFICATION_MATRIX.md` to pick the smallest sufficient proof.
- For backend/domain changes, prefer `npm run test:domain` or the nearest `uv run --project apps/api python -m unittest ...` target.
- For database security changes, verify both catalog state (`relrowsecurity`) and role privileges (`has_table_privilege` or `information_schema.role_table_grants`).
- Do not claim a Supabase security issue is resolved until the live database state has been checked.

## Docs To Keep Current

- `docs/PROJECT_MEMORY.md`: durable decisions, especially safety, Supabase, and product posture.
- `docs/CODEBASE_MAP.md`: fastest jump targets for future agents.
- `docs/VERIFICATION_MATRIX.md`: blast-radius-based checks.
- `docs/STARTUP_CHECKLIST.md`: setup and release checklist.
