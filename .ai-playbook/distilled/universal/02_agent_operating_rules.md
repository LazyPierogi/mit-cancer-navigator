# Universal Rules: Agent Operating Model

## U-AO-01
- Rule: Use architect-first execution (spec before code).
- Rationale: High-speed generation without architecture produces brittle systems.
- Adoption signal: Implementation follows a written blueprint with explicit constraints.
- Failure signal: "Vibe coding" leads to fragmented patterns and debt.

## U-AO-02
- Rule: Prefer declarative goals with measurable success criteria.
- Rationale: Agents loop better toward outcomes than imperative micro-steps.
- Adoption signal: Prompts define what must be true when done.
- Failure signal: Agents complete steps but miss the real objective.

## U-AO-03
- Rule: Enforce plan -> execute -> verify loops.
- Rationale: Most agent mistakes are subtle conceptual errors, not syntax errors.
- Adoption signal: Each task includes a verification step and evidence.
- Failure signal: Completion claims without proof.

## U-AO-04
- Rule: Require a focused self-review pass in a fresh context.
- Rationale: Independent review catches overengineering and dead code.
- Adoption signal: A review pass is recorded before merge/hand-off.
- Failure signal: Unused abstractions and contradictory logic remain.

## U-AO-05
- Rule: Keep prompts constrained, structured, and facts-first.
- Rationale: Tight structure improves reproducibility across tools.
- Adoption signal: Stable sectioned output and minimal re-prompting.
- Failure signal: Drift, filler, and speculative output.

## U-AO-06
- Rule: Force clarification at ambiguity boundaries.
- Rationale: Agents tend to fill gaps with incorrect assumptions.
- Adoption signal: Unknowns are surfaced early as explicit assumptions/questions.
- Failure signal: Wrong architectural decisions made silently.

## U-AO-07
- Rule: Preserve orthogonality of changes.
- Rationale: Side-effect edits are a common agent failure mode.
- Adoption signal: Unrelated code/comments remain untouched.
- Failure signal: Task-specific changes include unrelated rewrites.

## U-AO-08
- Rule: Treat agent output as draft, not source of truth.
- Rationale: Reliability comes from verification discipline, not model confidence.
- Adoption signal: Human review + automated checks gate final acceptance.
- Failure signal: Production defects traced to unverified generated code.

## U-AO-09
- Rule: Keep `AGENTS.md` concise and use it as a navigation map with progressive disclosure.
- Rationale: Oversized instruction blobs dilute task-relevant context and become stale quickly. Agents work best with a small stable entry point that teaches them where to look next.
- Adoption signal: `AGENTS.md` points to versioned deeper docs with clear ownership; agents discover detail on demand.
- Failure signal: Large top-level instructions drift from code reality and confuse execution.

## U-AO-10
- Rule: Make repository-local docs, executable plans, and quality grades the system of record.
- Rationale: Agents can only reliably act on context that is discoverable, versioned, and queryable in-repo. Execution plans (active, completed, tech-debt tracker) and quality grades per domain/layer must be first-class versioned artifacts.
- Adoption signal: Key decisions, plans, quality grades, and constraints are committed alongside code; a recurring doc-gardening process scans for stale docs and opens fix-up PRs.
- Failure signal: Critical context remains trapped in chat threads, meetings, or private notes; documentation drifts from code without detection.

## U-AO-11
- Rule: When agents fail, improve harness capabilities before patching symptoms.
- Rationale: Throughput compounds when fixes are encoded as reusable tools, guards, or docs.
- Adoption signal: Recurrent failures trigger harness/tooling/doc updates, not repeated manual rescue.
- Failure signal: Teams repeatedly solve the same class of agent errors by hand.

## U-AO-12
- Rule: Push review and remediation loops toward agent-to-agent execution with explicit human escalation boundaries.
- Rationale: Human attention is the bottleneck; agents can iterate faster on deterministic checks.
- Adoption signal: Agents handle iterative review feedback and humans intervene for judgment/risk decisions.
- Failure signal: Humans spend most cycles on repetitive review chores that agents could resolve.

## U-AO-13
- Rule: Prefer short-lived PRs and fix-forward iteration when rollback and verification paths are strong.
- Rationale: In high-throughput systems, prolonged blocking on non-critical friction costs more than rapid corrective follow-ups.
- Adoption signal: Small PRs merge quickly with immediate corrective loops for non-critical issues.
- Failure signal: Work stalls in queue for long periods while low-risk issues block delivery.

## U-AO-14
- Rule: When documentation repeatedly fails to prevent errors, escalate the rule into code (lints, structural tests).
- Rationale: Mechanical enforcement compounds; documentation alone cannot keep a fully agent-generated codebase coherent.
- Adoption signal: Recurrent violations trigger new lint rules or structural tests with agent-friendly remediation messages.
- Failure signal: The same class of documentation-backed rule is violated sprint after sprint.

## U-AO-15
 - Rule: Accept agent output style variance unless style requirements are explicitly documented as invariants and mechanically enforced (formatter/lints/tests).
 - Rationale: Unwritten or unenforced style preferences consume scarce human attention and slow throughput. If style matters, encode it so agents can comply automatically.
 - Adoption signal: Reviews focus on correctness, maintainability, and legibility; style feedback is either (a) captured as an invariant and enforced mechanically, or (b) treated as non-blocking.
 - Failure signal: Agents are repeatedly blocked or reworked for cosmetic style-only concerns that are not encoded in tooling.

## U-AO-16
- Rule: Provide isolated, per-task work environments for agents when feasible.
- Rationale: Isolated instances (e.g., per-worktree app boots, ephemeral observability stacks) let agents reproduce, validate, and tear down without cross-task interference.
- Adoption signal: Agent runs operate on dedicated instances with task-scoped logs and state.
- Failure signal: Concurrent agent tasks corrupt shared state or produce non-reproducible results.
