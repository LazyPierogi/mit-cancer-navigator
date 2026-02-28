# Distilled Ruleset

This folder stores reusable cross-project rules only.

## Structure
- `universal/`: rules that should apply to almost every project.
- `packs/`: optional rule packs by project type.
- `mcp/`: MCP baseline catalog and recommendation policy.
- `traceability/`: evidence map from intake sources to distilled rules.

## Distillation standard
A rule is promoted only when it appears in multiple projects or is a clearly universal engineering principle.

Each rule is expressed as:
- Rule
- Rationale
- Adoption signal
- Failure signal

## Scope boundaries
- Do not place project-specific names or one-off implementation details in this folder.
- Keep project-specific facts in `intake/` only.
