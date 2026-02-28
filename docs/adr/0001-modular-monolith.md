# ADR 0001: Modular Monolith for MVP

## Status

Accepted

## Context

The project needs a polished UI, deterministic domain logic, benchmark gating, and strong auditability without the operational complexity of microservices.

## Decision

Use a modular monolith split across:

- `apps/web` for the product UI
- `apps/api` for API, domain services, governance, and evaluation
- `apps/worker` for async ingestion and benchmark jobs

## Consequences

- Faster team velocity and easier traceability
- One relational source of truth for runs, policies, and evaluation artifacts
- Simple future escape hatches for Qdrant or additional services if benchmarks justify them

