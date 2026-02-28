# ROADMAP.md

Roadmap for turning the current scaffold into a polished, benchmarked, presentation-ready MIT project.

## Status Legend

- `DONE`: implemented and verified in the repository
- `IN PROGRESS`: partially implemented, usable, but not yet production-complete
- `NEXT`: highest-priority remaining work
- `LATER`: valuable follow-up after the MVP loop is stable

## Where We Are Now

Current project state:

- We have a working full-stack scaffold.
- `web` and `api` run locally.
- Deterministic sample analysis works end-to-end.
- Runs and eval runs are persisted locally.
- The UI already expresses the intended Clinical Atlas / Signal Lab direction.
- The project is still using sample datasets and a local SQLite bootstrap DB for speed.

This means the foundation is real, but the project is **not yet clinically/data-complete**.

## Done

### Foundation

- `DONE` Repository scaffold created for:
  - `apps/web`
  - `apps/api`
  - `apps/worker`
  - `packages/design-tokens`
  - `datasets/`
  - `infra/compose`
- `DONE` Root workspace scripts added in [package.json](/Users/mario/Repo/mit-cancer-navigator/package.json)
- `DONE` Local infra definition added in [docker-compose.yml](/Users/mario/Repo/mit-cancer-navigator/infra/compose/docker-compose.yml)
- `DONE` Local dev instructions documented in [README.md](/Users/mario/Repo/mit-cancer-navigator/README.md)

### Backend API

- `DONE` FastAPI app bootstrapped in [main.py](/Users/mario/Repo/mit-cancer-navigator/apps/api/app/main.py)
- `DONE` Canonical schemas added for:
  - vignette input
  - run response
  - trace payload
  - governance policy
  - eval payload
- `DONE` Deterministic domain core implemented in [rules.py](/Users/mario/Repo/mit-cancer-navigator/apps/api/app/domain/rules.py)
  - clinical relevance gate
  - ERS scoring
  - topic matching
  - label mapping
  - uncertainty flags
- `DONE` Governance policy endpoint implemented
- `DONE` Evaluation endpoint implemented
- `DONE` Import/sync placeholder endpoints implemented

### Persistence

- `DONE` SQLAlchemy models added for:
  - `rulesets`
  - `safety_templates`
  - `policy_snapshots`
  - `update_records`
  - `guideline_topics`
  - `evidence_studies`
  - `analysis_runs`
  - `eval_runs`
- `DONE` Alembic initialized
- `DONE` Initial migration created and tested
- `DONE` API startup bootstrap seeds:
  - ruleset
  - safety template
  - policy snapshot
- `DONE` Analysis runs persist to DB
- `DONE` Eval runs persist to DB

### Frontend

- `DONE` Next.js app scaffolded
- `DONE` Visual shell and product direction implemented:
  - policy strip
  - evidence ribbon
  - metric cards
  - atlas-style landing page
- `DONE` Routes implemented for:
  - `/`
  - `/workspace`
  - `/runs/[runId]`
  - `/runs/[runId]/trace`
  - `/datasets`
  - `/labs/evals`
  - `/labs/evals/[evalRunId]`
  - `/labs/evals/[evalRunId]/cases/[caseId]`
  - `/labs/reviewer`
  - `/labs/embeddings`
  - `/docs/method`
  - `/docs/governance`
- `DONE` Workspace form now calls real API
- `DONE` Run detail page now renders persisted API data
- `DONE` Trace page now renders persisted API data
- `DONE` Production build passes

### Verification

- `DONE` Domain unit tests pass
- `DONE` Python syntax compile pass completed
- `DONE` `next build` passes
- `DONE` Smoke tests verified:
  - API health
  - governance endpoint
  - run creation
  - run retrieval
  - trace retrieval
  - eval run creation
  - web run page rendering
  - web trace page rendering

## In Progress

### Data Layer

- `IN PROGRESS` Sample datasets exist in:
  - [topics.sample.json](/Users/mario/Repo/mit-cancer-navigator/datasets/esmo/topics.sample.json)
  - [evidence.sample.json](/Users/mario/Repo/mit-cancer-navigator/datasets/pubmed/evidence.sample.json)
  - [frozen_pack.sample.json](/Users/mario/Repo/mit-cancer-navigator/datasets/vignettes/frozen_pack.sample.json)
- `IN PROGRESS` Canonical dataset shapes are established, but real ESMO and PubMed corpora are not loaded yet
- `IN PROGRESS` API defaults to SQLite for fast local boot, while intended long-term target remains PostgreSQL + pgvector

### Evaluation

- `IN PROGRESS` Evaluation route exists and persists results
- `IN PROGRESS` Current eval uses a scaffold sample pack, not the full frozen 15-vignette benchmark
- `IN PROGRESS` Reviewer pages exist as shell UI, but reviewer actions are not wired yet

### Explainability and Observability

- `IN PROGRESS` Trace payload exists and is shown in UI
- `IN PROGRESS` Observability is still lightweight and mostly app-native
- `IN PROGRESS` OpenTelemetry and richer run/update records are not fully surfaced yet

## Next

### 1. Load Real Project Data

Goal: replace all sample fixtures with real project inputs.

- `NEXT` Import curated ESMO excerpt/topic pack into canonical JSON format
- `NEXT` Import curated PubMed evidence into canonical JSON format
- `NEXT` Replace sample datasets in `datasets/` with real inputs
- `NEXT` Seed `guideline_topics` and `evidence_studies` from real data
- `NEXT` Verify that real data still produces deterministic outputs and clean trace payloads

Definition of done:

- real ESMO topics visible through `/api/v1/catalog/topics`
- real PubMed evidence available to the analysis pipeline
- sample placeholder corpus no longer drives top evidence results

### 2. Build Real Import Pipelines

Goal: move from static fixture loading to reproducible ingest workflows.

- `NEXT` Implement ESMO import service
- `NEXT` Implement PubMed curated import service
- `NEXT` Persist import batch metadata and provenance
- `NEXT` Add import status pages and job output visibility
- `NEXT` Add deterministic normalization/tagging rules for imported records

Definition of done:

- importing data no longer requires manual file editing
- every imported record has provenance and batch identity

### 3. Complete Persistence Model

Goal: stop relying on sample file reads at runtime.

- `NEXT` Persist actual guideline topics and evidence studies to DB
- `NEXT` Read runtime analysis inputs from DB-backed repositories
- `NEXT` Add repository methods for:
  - topics
  - evidence corpus
  - review sheets
  - update records
- `NEXT` Add second migration for import batches and richer run artifacts
- `NEXT` Switch default local stack from SQLite-only demo mode toward PostgreSQL dev mode

Definition of done:

- analysis path can run from DB records without sample JSON dependency

### 4. Wire Datasets and Eval Lab to Real Data

Goal: make labs useful, not decorative.

- `NEXT` Connect `/datasets` to real import batch and corpus metadata
- `NEXT` Connect `/labs/evals` to persisted eval runs
- `NEXT` Connect `/labs/evals/[evalRunId]` to real benchmark outputs
- `NEXT` Connect `/labs/evals/[evalRunId]/cases/[caseId]` to case-level review data
- `NEXT` Connect `/labs/reviewer` to review queue state

Definition of done:

- lab views reflect real stored data, not placeholder arrays

### 5. Implement the Full Frozen Benchmark

Goal: match the evaluation framework from your project docs.

- `NEXT` Add the real 15-vignette pack
- `NEXT` Add reference relevance annotations
- `NEXT` Add reference mapping table
- `NEXT` Add reference citation expectations
- `NEXT` Compute:
  - recall
  - FN rate
  - FP rate
  - mapping error
  - citation error
  - deterministic fidelity
- `NEXT` Separate Layer 1 and Layer 2 reporting in both API and UI

Definition of done:

- benchmark outputs mirror the evaluation framing from your documents
- updates can be compared against a stable frozen pack

### 6. Reviewer Workflow

Goal: support the human-in-the-loop process described in the evaluation docs.

- `NEXT` Add reviewer decisions persistence
- `NEXT` Add citation validity toggles
- `NEXT` Add disagreement notes
- `NEXT` Add subset-review tracking
- `NEXT` Add scoring-sheet export format

Definition of done:

- reviewer screens are not just display pages; they support real review work

### 7. Responsible AI Enforcement in Product UX

Goal: make governance visible and enforceable everywhere.

- `NEXT` Attach safety footer copy from DB-backed templates
- `NEXT` Show uncertainty copy consistently on run pages
- `NEXT` Add methodology/governance copy sourced from policy data
- `NEXT` Add recommendation-language checks into release/test workflow
- `NEXT` Add update record creation for meaningful system changes

Definition of done:

- governance is enforced in runtime behavior, not just documented in markdown

## Later

### Retrieval and Search Upgrade

- `LATER` Add hybrid retrieval over persisted corpora
- `LATER` Add vector embeddings and nearest-neighbor search
- `LATER` Add UMAP or other projection snapshots for embedding lab
- `LATER` Consider pgvector-first production path before introducing Qdrant

### Product Polish

- `LATER` Animate the atlas surfaces more intentionally
- `LATER` Add richer evidence cluster views
- `LATER` Add source drill-down drawers
- `LATER` Add benchmark storytelling views for the final demo

### Observability

- `LATER` Add real OpenTelemetry traces
- `LATER` Add latency/error dashboards
- `LATER` Add update impact records and release-gating summaries

### Deployment

- `LATER` Add production-ready Docker setup for web + api + worker + postgres + redis
- `LATER` Add CI for tests, build, and migration checks
- `LATER` Add deployment docs and release checklist

## Recommended Execution Order

Follow this order to minimize thrash:

1. Real ESMO and PubMed data import
2. DB-backed runtime repositories
3. Full frozen benchmark implementation
4. Reviewer workflow persistence
5. Datasets and eval UI wiring
6. Governance enforcement polish
7. Embedding lab and observability panels
8. Deployment hardening

## Current Blocking Inputs

These are the main external inputs still needed from the project team:

- real curated ESMO topic/excerpt data
- real curated PubMed evidence data
- the frozen 15-vignette pack
- reference relevance annotations
- guideline mapping reference table
- citation validity reference expectations

## Definition of Project-Complete MVP

We should consider the MVP complete when all of the following are true:

- a real structured vignette can be submitted through the web app
- the API runs deterministic analysis against real ESMO and PubMed data
- the run result shows:
  - top evidence
  - exclusions
  - score breakdown
  - guideline mapping
  - uncertainty flags
  - safety footer
- the benchmark suite runs on the real frozen vignette pack
- reviewer workflow supports human validation
- governance rules are enforced in UX and API behavior
- the app is visually polished enough for final presentation
- local setup is reproducible for the full team

## Immediate Next Session Suggestion

If we continue right away, the highest-leverage next task is:

1. define the canonical real-data import shape for your incoming ESMO and PubMed extracts
2. wire those imports into DB-backed repositories
3. retire the sample JSON fixtures from the live analysis path
