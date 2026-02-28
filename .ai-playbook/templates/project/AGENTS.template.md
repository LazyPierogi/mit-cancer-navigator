# AGENTS.md

## Mission
Build this project with explicit constraints, reversible changes, and evidence-first delivery.

## Universal Operating Rules
- Use architect-first workflow: scope, constraints, success criteria, then implementation.
- Enforce invariants, not implementations: constrain what must be true, allow freedom in how.
- Keep `AGENTS.md` short: use it as a map to deeper versioned docs with progressive disclosure.
- Keep changes small and reversible.
- Preserve orthogonality: do not change unrelated code.
- Validate all external input/output boundaries with typed schemas.
- Keep secrets/config out of code and validate env at startup.
- Use centralized design tokens/constants/storage keys.
- When failures repeat, improve harnesses (tooling/docs/lints), not one-off manual workarounds.
- When documentation repeatedly fails to prevent errors, escalate the rule into code (lints, structural tests).

## Agent Workflow
- Plan -> Execute -> Verify for every non-trivial task.
- Ask for clarification when assumptions affect architecture.
- Do not claim completion without validation evidence.
- Run a focused self-review for dead code, overengineering, and regressions.
- Keep repository docs/plans current in the same change so agents can reason from source of truth.
- Prefer short-lived PR loops and fast fix-forward iterations when rollback paths are clear.
- Push iterative review to agent-to-agent loops; escalate humans for judgment-critical decisions.
- Accept agent output style variance unless style requirements are documented as invariants and mechanically enforced (formatter/lints/tests).
- Use isolated per-task work environments when feasible (dedicated instances, task-scoped logs).
- For unfamiliar GitHub codebases, use DeepWiki MCP with GitHub tooling first to map architecture and verify implementation paths before coding.

## Quality Gates
- Functional checks for changed behavior.
- Regression checks for critical loops/flows.
- Cross-platform/surface checks where applicable.
- Agent-legible diagnostics where possible (UI snapshots, logs, metrics, traces).
- Docs/checklists updated when behavior or contracts change.
- Maintain quality grades per domain/layer; update with recurring cleanup passes.
- Custom lint error messages must include remediation instructions for agent context.

## Optional Pack Addons
Add one or more of the following if relevant:
- `templates/packs/web-app/AGENTS.addon.web-app.md`
- `templates/packs/mobile-app/AGENTS.addon.mobile-app.md`
- `templates/packs/game/AGENTS.addon.game.md`
- `templates/packs/fullstack-ai/AGENTS.addon.fullstack-ai.md`

## Optional Skills Bootstrap
- If skill bootstrap is enabled, select and install up to 6-7 skills aligned to the selected packs.
- Source repo: `https://github.com/sickn33/antigravity-awesome-skills`
- Source catalog: `https://github.com/sickn33/antigravity-awesome-skills/blob/main/CATALOG.md`
- Install project-specific skills into `./.codex/skills/` in this repository, not into the global IDE skills directory.
