# Startup Checklist

## Purpose

Use this checklist when preparing a local environment or a public-facing release candidate.

## Environment

- Confirm `Node.js`, `Python`, and `uv` versions match the repository requirements.
- Copy `.env.example` into a local untracked `.env` file when needed.
- Keep real credentials out of the repository and out of screenshots, logs, and shared examples.

## Before shipping a meaningful change

- Update `VERSION.json` and `apps/api/VERSION.json` when the repository metadata shown in the product should change.
- Verify `rulesetVersion`, `corpusVersion`, and `buildLabel` still describe the intended runtime state.
- Review `README.md`, `docs/PROJECT_PLAN.md`, and `docs/ROADMAP.md` if behavior or scope changed.

## Verification

Run the focused checks that match the change:

- `npm run test:domain`
- `uv run --project apps/api python -m unittest discover -s apps/api/tests -p 'test_*.py'`
- `npm --workspace apps/web run build`

If import logic changed, also validate the relevant dataset flow using the docs in `docs/data-team/`.

## Repository hygiene

- Remove presentation-only notes, local machine paths, and one-off operator instructions before publishing.
- Keep secrets and environment-specific values in local untracked files only.
- Prefer relative links in docs.
- Avoid committing generated local artifacts such as `.next`, `.venv`, logs, and local databases.

## Public release review

- Confirm the README reflects the current state of the project.
- Confirm the documentation that remains in `docs/` is useful to an external reader.
- Confirm sample data and fixtures are safe to publish.
- Confirm there is an explicit license decision before making the repository public.
