# Universal Rules: Architecture

## U-AR-01
- Rule: Keep composition shells thin and move business logic into domain modules.
- Rationale: Shell-heavy pages become unmaintainable and hard to test.
- Adoption signal: Route/view files orchestrate; services/hooks own behavior.
- Failure signal: Core logic duplicated across UI layers.

## U-AR-02
- Rule: Define explicit module boundaries and contracts.
- Rationale: Clear seams make refactors safer and integration predictable.
- Adoption signal: Core interfaces exist for AI, storage, and external clients.
- Failure signal: Tight coupling between UI, transport, and business rules.

## U-AR-03
- Rule: Design for split-ready evolution.
- Rationale: Features often start local and later require service extraction.
- Adoption signal: Shared packages/services can be moved without rewrites.
- Failure signal: Future backend extraction requires major redesign.

## U-AR-04
- Rule: Prefer local-first operation with explicit sync strategy.
- Rationale: Local responsiveness improves UX and resilience.
- Adoption signal: Core flow works offline or degraded.
- Failure signal: Basic workflows break without network access.

## U-AR-05
- Rule: Build fallback chains for brittle external dependencies.
- Rationale: AI providers, CV backends, and third-party APIs fail unpredictably.
- Adoption signal: Ordered fallback/backoff path and backend attribution exist.
- Failure signal: Single provider outage blocks core workflow.

## U-AR-06
- Rule: Separate stable runtime paths from tuning/debug infrastructure.
- Rationale: Tuning tools accelerate iteration but should not contaminate production behavior.
- Adoption signal: Debug paths are gated and isolated.
- Failure signal: Debug overrides leak into normal user flows.

## U-AR-07
- Rule: Align data model invariants across all execution surfaces.
- Rationale: Shared domain invariants prevent app/widget/client divergence.
- Adoption signal: One canonical model/engine is reused by multiple surfaces.
- Failure signal: Same input yields different outputs across entry points.

## U-AR-08
- Rule: Encode layer boundaries as mechanically enforced dependency rules with agent-friendly remediation messages.
- Rationale: Agents are faster and safer when allowed dependency directions are explicit and machine-checked. Custom lint error messages that include remediation instructions inject guidance directly into agent context.
- Adoption signal: Structural tests or custom lints fail builds on disallowed edges; error output explains the violation and suggests the correct path.
- Failure signal: Cross-layer shortcuts silently accumulate, or agents cannot self-correct because lint output is opaque.

## U-AR-09
- Rule: Route cross-cutting concerns through explicit provider interfaces.
- Rationale: A single integration seam keeps auth, telemetry, connectors, and feature flags legible and replaceable.
- Adoption signal: Cross-cutting access happens through approved provider contracts.
- Failure signal: Business code directly reaches into infra/service details across the codebase.

## U-AR-10
- Rule: Prefer boring, inspectable dependencies; reimplement small opaque primitives when needed.
- Rationale: Agent leverage drops when behavior is hidden behind unstable or opaque upstream abstractions.
- Adoption signal: Critical helpers are understandable in-repo with tests and instrumentation hooks.
- Failure signal: Delivery repeatedly stalls on third-party internals the team cannot inspect or control.

## U-AR-11
- Rule: Enforce invariants, not implementations: constrain what must be true and allow freedom in how.
- Rationale: Agents ship fast when boundaries are strict but implementation choices are unconstrained. Micromanaging implementations slows throughput without improving correctness.
- Adoption signal: Architecture rules define required outcomes (e.g., parse data at boundary) without mandating specific libraries or patterns.
- Failure signal: Agents are blocked or reworked because they chose a valid but non-preferred implementation path.
