# Project Memory

## Current Truth

- MIT Cancer Navigator is a research and evaluation app for NSCLC evidence navigation, not a clinical decision or prescribing system.
- The product posture is responsible AI: deterministic guardrails own safety-critical results; semantic retrieval and LLM hooks are assistive.
- The frontend talks to the FastAPI API. Supabase/Postgres is a backend persistence layer, not a public Data API contract.
- Bundled datasets are proof-of-concept fixtures and are not production-grade clinical data.

## Durable Decisions

- 2026-06-23: Supabase public application tables are private-by-default. RLS is enabled on all app tables in `public`, and `anon`/`authenticated` table/sequence grants are revoked unless a future feature explicitly designs Data API access with policies.
- 2026-06-23: Current table and sequence grants are closed. The MCP role could not change `supabase_admin` default privileges, so also review Supabase dashboard Data API/default grant settings before adding new platform-created tables.
- Use Alembic for application schema history. Security migrations should be idempotent and tolerate local Postgres setups where Supabase roles do not exist.
- Keep safety language explicit: this tool supports review and evidence navigation; it does not replace clinician judgment.

## Open Questions

- Whether any future public or authenticated Supabase Data API access is actually needed. If yes, define table-by-table policies before granting roles.
- Whether the API has lingering `idle in transaction` paths around import/list queries; the 2026-06-23 RLS fix found blocking idle transactions during DDL.
- Whether Supabase project-level defaults should be changed in the dashboard so future `supabase_admin`-owned tables do not receive public role grants.

## Maintenance Notes

- Update this file when product posture, database exposure, safety language, or integration ownership changes.
- Do not use this file as a changelog for local UI or implementation-only tweaks.
