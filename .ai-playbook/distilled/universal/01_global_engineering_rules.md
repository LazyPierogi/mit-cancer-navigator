# Universal Rules: Global Engineering

## U-GE-01
- Rule: Start each feature with explicit success criteria, non-goals, and failure conditions.
- Rationale: Agents move fast but assume too much when intent is underspecified.
- Adoption signal: Tasks begin with concrete acceptance checks and scope boundaries.
- Failure signal: Rework caused by "not what I meant" outcomes.

## U-GE-02
- Rule: Prefer small, reversible changes over broad rewrites.
- Rationale: Small deltas reduce blast radius and speed up recovery.
- Adoption signal: Most changes touch limited files and include rollback paths.
- Failure signal: One fix causes unrelated regressions.

## U-GE-03
- Rule: Keep modules atomized and responsibility-focused.
- Rationale: Thin modules simplify testing, review, and reuse.
- Adoption signal: UI shells compose modules; domain logic lives outside route/view files.
- Failure signal: Large multi-purpose files become bottlenecks.

## U-GE-04
- Rule: Maintain single sources of truth for tokens, constants, and storage keys.
- Rationale: Centralized definitions prevent drift across surfaces.
- Adoption signal: Shared token/constant files are referenced by all consumers.
- Failure signal: Magic values and duplicate keys spread across components.

## U-GE-05
- Rule: Validate boundaries with typed schemas.
- Rationale: Schema checks catch malformed data before it corrupts state.
- Adoption signal: Inbound/outbound payloads are schema-validated.
- Failure signal: Silent field drops or runtime shape mismatches.

## U-GE-06
- Rule: Protect async pipelines against stale writes and race conditions.
- Rationale: UI and AI workflows often resolve out of order.
- Adoption signal: Request guards, correlation IDs, and idempotent updates are present.
- Failure signal: Flicker, stale overwrites, and non-deterministic UI state.

## U-GE-07
- Rule: Isolate experiments from stable production paths.
- Rationale: Experimental code frequently introduces hidden latency and instability.
- Adoption signal: Experiments run in separate branches or optional modules.
- Failure signal: Core critical path regresses after exploratory changes.

## U-GE-08
- Rule: Keep docs and code synchronized in the same change.
- Rationale: Fast-moving AI workflows lose context without durable documentation.
- Adoption signal: Key plans, runbooks, and checklists update with behavior changes.
- Failure signal: Team decisions exist only in chat history.

## U-GE-09
- Rule: Keep local development environments reproducible from a clean machine.
- Rationale: Setup drift causes onboarding friction and non-reproducible failures.
- Adoption signal: Version prerequisites, setup steps, and env templates are documented and verifiable.
- Failure signal: "Works on my machine" blocks handoff and release readiness.
