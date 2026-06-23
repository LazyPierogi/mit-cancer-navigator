# Verification Matrix

Use the smallest verification tier that covers the changed contract. Prefer targeted proof over broad builds unless the blast radius justifies it.

## Tier 0: Docs Or Bootstrap Only

- Inspect the diff.
- Run lightweight formatting/text checks only when useful.

## Tier 1: Local UI Copy Or Style

- Read the owning component or page.
- Use one direct browser/DOM/visual proof when the visible result matters.
- Do not run broad builds unless the change touches shared route wiring or types.

## Tier 2: UI Behavior Or Route Contract

- Check the owning component/page and any helper it calls.
- Run a targeted type/build check when props, route params, or shared types change.
- Browser-verify the affected route when behavior is user-visible.

## Tier 3: API, Domain, Or Persistence Logic

- Run `npm run test:domain` or the nearest API unittest target.
- Add or adjust focused tests when changing behavior, contracts, or schema assumptions.
- Verify any user-facing API change through the owning route or service.

## Tier 4: Database, Supabase, Or External Integration

- Verify the live integration when credentials are available and the request concerns live state.
- For Supabase table exposure, check:
  - `pg_class.relrowsecurity` for every affected table.
  - `information_schema.role_table_grants` for `anon` and `authenticated`.
  - `has_table_privilege` for expected public role access.
- Run the nearest migration/test path locally when changing Alembic files.
- Inspect for lock or transaction issues if DDL hangs.

## Tier 5: Live Incident Or Security Alert

- Confirm the exact affected project/resource.
- Make the smallest live fix that closes the exposure.
- Re-query live state after the fix.
- Record durable repo changes if the issue can recur through migrations or bootstrap.

## Escalation Triggers

- A targeted proof fails unexpectedly.
- A database change touches public roles, RLS, grants, auth, or secrets.
- A change alters the backend-mediated access model.
- Live DDL is blocked by open transactions or long-running jobs.

## Do Not Escalate Just Because

- The repo is large.
- A small UI or docs change feels important.
- A previous session happened to run broader checks.
