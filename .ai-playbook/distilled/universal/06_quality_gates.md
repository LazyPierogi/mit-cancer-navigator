# Universal Rules: Quality Gates

## U-QG-01
- Rule: No completion claim without verification evidence.
- Rationale: Evidence-first closure prevents false positives.
- Adoption signal: Delivery notes include command/test/manual evidence.
- Failure signal: "Should work" closeouts reopen quickly.

## U-QG-02
- Rule: Protect critical loops with dedicated regression checks.
- Rationale: Interactive loops are high-risk for subtle regressions.
- Adoption signal: Physics/render/async loops have targeted test scenarios.
- Failure signal: Core interactions break after unrelated edits.

## U-QG-03
- Rule: Validate cross-surface parity for shared features.
- Rationale: App/web/widget/platform divergence creates hidden defects.
- Adoption signal: Feature behavior is checked across supported surfaces.
- Failure signal: One platform works while another silently fails.

## U-QG-04
- Rule: Verify environment and dependency compatibility before upgrades.
- Rationale: Version drift causes avoidable build/runtime failures.
- Adoption signal: Upgrade gates include compatibility checks and rollback notes.
- Failure signal: Emergency pin/revert cycles after upgrades.

## U-QG-05
- Rule: Keep a living checklist for release-critical flows.
- Rationale: Repeatable QA beats ad-hoc memory-based validation.
- Adoption signal: Checklist is updated and reused per release.
- Failure signal: Same classes of bugs reappear across milestones.

## U-QG-06
- Rule: Gate releases with explicit performance budgets on critical journeys.
- Rationale: Latency and responsiveness regressions often ship silently without thresholds.
- Adoption signal: Core journeys track agreed limits (for example, CWV/p95 latency/startup time) and compare before/after.
- Failure signal: Users report slowness before internal metrics detect regressions.

## U-QG-07
- Rule: Include security and secret-scan evidence in release verification.
- Rationale: Functional correctness alone does not protect production systems.
- Adoption signal: Release notes include dependency audit and secret-scan results.
- Failure signal: Security issues are discovered only after deployment.

## U-QG-08
- Rule: Verify clean-machine setup reproducibility for onboarding-critical projects.
- Rationale: Broken setup docs block scaling and incident recovery.
- Adoption signal: Setup steps are validated from scratch at defined milestones.
- Failure signal: New contributors cannot run project without tribal knowledge.

## U-QG-09
- Rule: Make UI state, logs, metrics, and traces directly legible to agents per task environment.
- Rationale: QA throughput improves when agents can reproduce behavior and inspect observability without human relay.
- Adoption signal: Agent runs can query browser state and task-scoped telemetry during verification.
- Failure signal: Humans must manually gather screenshots/logs/metrics for routine debugging loops.

## U-QG-10
- Rule: Run recurring garbage-collection passes that enforce golden principles and open targeted cleanup PRs, including doc-gardening for stale documentation.
- Rationale: Agent-generated repositories drift unless quality recovery is continuous and automated. Technical debt is a high-interest loan: pay it down continuously in small increments rather than letting it compound.
- Adoption signal: Scheduled cleanup tasks update quality grades, submit small refactor PRs, and scan for stale or obsolete docs that no longer reflect code behavior.
- Failure signal: Periodic manual cleanup weeks are required to remove growing "AI slop;" documentation quietly rots without detection.

## U-QG-11
- Rule: Maintain a quality grading document per domain or architectural layer, tracking gaps over time.
- Rationale: Without a persistent quality map, agents and humans cannot prioritize cleanup or detect regression trends.
- Adoption signal: A versioned quality grade file exists, is updated by recurring scans, and informs cleanup task prioritization.
- Failure signal: Quality perception is anecdotal; the same domains degrade repeatedly without visibility.
