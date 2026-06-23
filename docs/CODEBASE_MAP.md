# Codebase Map

Use this as the low-token front door for the repo. Start here only when a task needs routing; do not treat it as required reading for obvious micro-changes.

## Discovery Seeds

- Codebase Memory project id: `Users-mario-Repo-mit-cancer-navigator`
- Find database bootstrap/schema: `search_graph(query="bootstrap database migration RLS")`
- Find API routes: `search_graph(query="FastAPI route imports runs evals catalog")`
- Find reviewer/labs UI: `search_graph(query="LabsDashboard reviewer page")`
- Find semantic runtime: `search_graph(query="semantic retrieval import batches document chunks projection points")`

## Main Surfaces

### Web App

- Route entries: `apps/web/app/page.tsx`, `apps/web/app/labs/page.tsx`, `apps/web/app/labs/reviewer/page.tsx`
- Main lab surface: `apps/web/components/LabsDashboard.tsx`
- Shared UI components: `apps/web/components/`
- Use for reviewer flows, lab imports UI, benchmark display, and visible product copy.

### API

- App entry: `apps/api/app/main.py`
- Routes: `apps/api/app/api/routes/`
- Settings: `apps/api/app/config/settings.py`
- Use for request contracts, domain endpoints, import jobs, evals, and runtime configuration.

### Persistence

- SQLAlchemy models: `apps/api/app/repositories/models.py`
- DB engine/session: `apps/api/app/repositories/db.py`
- Runtime bootstrap: `apps/api/app/repositories/bootstrap.py`
- Alembic migrations: `apps/api/alembic/versions/`
- Use for schema, Supabase/Postgres security, RLS posture, and persistence behavior.

### Data And Imports

- Dataset fixtures: `datasets/`
- Import/data-team docs: `docs/data-team/`
- Import routes: `apps/api/app/api/routes/imports.py`
- Use for ESMO/PubMed ingest, validation, semantic corpus setup, and benchmark fixtures.

## Verification Pointers

- Domain/API unit suite: `npm run test:domain`
- API test command: `uv run --project apps/api python -m unittest discover -s apps/api/tests -p 'test_*.py'`
- Web build: `npm --workspace apps/web run build`
- Database security proof: query `pg_class.relrowsecurity` and `information_schema.role_table_grants` or `has_table_privilege`.

## Maintenance

- Update this file when a route, service, schema owner, integration touchpoint, or best discovery query changes.
- Keep entries as jump targets, not architecture prose.
