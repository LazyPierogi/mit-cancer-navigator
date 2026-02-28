# STARTUP_CHECKLIST.md

## 1) Base Installation
- [ ] Add universal rules from `.ai-playbook/distilled/universal/`.
- [ ] Select and add project-specific packs from `.ai-playbook/distilled/packs/`.
- [ ] Create `AGENTS.md` and `PROJECT_MEMORY.md` from templates.
- [ ] Run `SETUP_PROJECT_FIT_REVIEW.playbook.md` against real product docs to validate Skills + MCP fit.
- [ ] Keep MCP source-of-truth in `mcp.json`, then run `python3 scripts/update_windsurf_mcp.py` and click `Refresh` in Windsurf MCP settings.

## 2) Architecture and Contracts
- [ ] Define module boundaries and public interfaces.
- [ ] Define schema contracts for external inputs/outputs.
- [ ] Define fallback behavior for external dependencies.
- [ ] Define layer dependency directions and enforce mechanically (lints/structural tests).
- [ ] Ensure custom lint error messages include remediation instructions for agent context.

## 3) Security Baseline
- [ ] Validate env and secret handling.
- [ ] Define data minimization and logging redaction policy.
- [ ] Define permission and side-effect rollback strategy.

## 4) Delivery and Quality
- [ ] Define verification commands and manual QA checklist.
- [ ] Define regression checks for critical flows.
- [ ] Define performance budgets for critical user journeys.
- [ ] Define dependency audit and secret-scan checks in release flow.
- [ ] Define release/rollback path.
- [ ] Set up quality grading per domain/layer (initial baseline).
- [ ] Configure recurring garbage-collection and doc-gardening passes.
- [ ] Define execution plan structure (active plans, completed plans, tech-debt tracker).
- [ ] Set up isolated per-task agent work environments where feasible.

## 5) Distillation Hooks
- [ ] After milestone: capture `05_lessons_learnings_snapshot.md`.
- [ ] After failures: capture `06_failures_gotchas_snapshot.md`.
- [ ] Promote only reusable cross-project rules into `distilled/`.
