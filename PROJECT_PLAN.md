# Lung Cancer Treatment Navigator: Updated Stack and App Skeleton After Modeling, Evaluation, and Responsible AI Review

## Summary

The new documents make the plan **stronger and more specific**, not radically different. The previous direction still stands:

- **Frontend**: `Next.js` + `TypeScript`
- **Backend API**: `FastAPI` + `Pydantic`
- **Worker layer**: Python async jobs
- **Primary datastore**: `PostgreSQL + pgvector`
- **Cache/queue**: `Redis`
- **Architecture style**: **modular monolith**, not microservices
- **Decision engine**: **deterministic**, not generative
- **Product shape**: polished app + rigorous evaluation harness + explainability + observability

What changes now is that the plan becomes much more **spec-locked** in five areas:

1. **Exact vignette schema**
2. **Exact deterministic ERS and tie-break logic**
3. **Two-layer evaluation model**
4. **Responsible AI safety boundaries as frozen product rules**
5. **Non-regression/update policy as a first-class subsystem**

So: the architecture proposal is still good in spirit, but after reading the new docs, I would update it from “retrieval pipeline architecture” to a much more explicit **product platform architecture with frozen rulesets and evaluation governance baked in**.

## Verdict on the Current Architecture Proposal

### What still holds

- Structured vignette input only
- Separate evidence corpus and guideline corpus
- Deterministic ranking and mapping core
- Frozen vignette evaluation set
- Bounded LLM usage only for low-risk assistive tasks
- Explainability and citations as product requirements

### What must be tightened

The current proposal still under-specifies:

- the **canonical input schema**
- the **exact runtime decision contract**
- the **hard distinction between system-function and clinical-correctness evaluation**
- the **frozen safety boundaries**
- the **change-management policy**
- the **manual review touchpoints**

### Updated framing

Do not describe this app as:

> a retrieval pipeline that produces mapped evidence

Describe it as:

> a deterministic evidence triage platform with governed data imports, frozen rulesets, explicit safety boundaries, and benchmark-gated updates

That subtle shift matters a lot for both implementation and final presentation.

## Final Recommended Stack

| Layer | Choice | Decision |
| --- | --- | --- |
| Web app | `Next.js 15` + `TypeScript` | keep |
| Frontend data/state | `TanStack Query` + server actions only where useful | keep |
| Form system | `React Hook Form` + `Zod` | keep |
| Styling | CSS Modules + CSS variables + custom component styling | keep |
| Data viz | `visx` + `deck.gl` | keep |
| API | `FastAPI` + `Pydantic v2` | keep |
| Worker | `Dramatiq` + Redis | keep |
| Primary database | `PostgreSQL 16` + `pgvector` | keep |
| Retrieval | Postgres FTS + pgvector + RRF fusion | keep |
| ORM/data access | `SQLAlchemy 2` + Alembic | keep |
| Observability | `OpenTelemetry` + structured logs + metrics tables | keep |
| Evaluation harness | internal benchmark service + reviewer scoring workflow | strengthen |
| Governance | frozen templates/ruleset versioning/update records | add as explicit module |

## Why the Stack Still Makes Sense

The new docs actually reinforce the previous stack choice:

- The system needs **strong typed schemas**, which fits FastAPI/Pydantic perfectly.
- The evaluation framework requires **persistent, versioned run artifacts**, which strongly favors Postgres.
- The responsible AI policy requires **explicit frozen templates, auditability, and update records**, which are easier in a unified relational core.
- The student-team reality still favors **low operational complexity**.

So the recommendation remains:

**Use `Next.js + FastAPI + Postgres/pgvector + Redis`, with one app, one API, one worker, one DB.**

## Architecture Changes Required After the New Docs

### 1. Add a first-class `Ruleset` subsystem

The new modeling docs freeze deterministic logic much more explicitly than before.

Add a versioned ruleset layer containing:

- relevance gate rules
- ERS scoring tables
- tie-break rules
- threshold rules
- mapping rubric
- label logic
- safety language templates
- frozen vocabularies

This means runtime decisions are not just code behavior. They are also tied to a **named ruleset version**.

### 2. Add a first-class `Governance` subsystem

The responsible AI document is not just a policy memo. It implies product behavior.

Add governance as an actual application concern:

- safety boundaries
- frozen label vocabulary
- frozen scope
- frozen input schema
- frozen disclaimer templates
- update records
- hard-stop vs soft-review logic

### 3. Add a first-class `Reviewer Workflow`

The new evaluation docs repeatedly rely on human-in-the-loop review.

This means the product should explicitly support:

- scoring sheet export/view
- reviewer notes
- citation support verification
- subset clinical review status
- disagreement capture

It does not need a complex collaboration suite, but it does need review artifacts.

### 4. Tighten “confidence” semantics

In the previous plan I allowed a general `confidenceScore`. That now needs to be narrowed.

Do **not** present ML-style probabilistic confidence unless you truly compute it that way.

Use:

- `confidenceMode: "rule_coverage"` or `"deterministic_support"`
- `confidenceScore`: bounded explanatory score only if clearly defined
- explicit `uncertaintyFlags`

The product should emphasize **coverage and applicability**, not fake calibrated certainty.

### 5. De-emphasize any NLI/reranker ambiguity

The new docs make it very clear that labeling and scoring must be deterministic and auditable.

So the plan is now fully locked to:

- no runtime semantic classifier for final labels
- no stochastic reranker in default production path
- no natural-language “interpretation engine” for stance classification

## Canonical Input and Domain Contracts

These are now locked from the modeling docs.

### Canonical vignette input

```ts
type VignetteInput = {
  cancerType: "NSCLC"
  diseaseSetting: "early" | "locally_advanced" | "metastatic"
  histology: "adenocarcinoma" | "squamous"
  performanceStatus: "0" | "1" | "2" | "3" | "4"
  biomarkers: {
    EGFR: "yes" | "no"
    ALK: "yes" | "no"
    ROS1: "yes" | "no"
    PDL1Bucket: "lt1" | "1to49" | "ge50"
  }
}
```

### Canonical evidence record

```ts
type EvidenceRecord = {
  evidenceId: string
  title: string
  publicationYear: number | null
  evidenceType:
    | "guideline"
    | "systematic_review"
    | "phase3_rct"
    | "phase2_rct"
    | "prospective_obs"
    | "retrospective"
    | "case_series"
    | "expert_opinion"
  relevantN: number | null
  sourceCategory:
    | "guideline_body"
    | "high_impact_journal"
    | "specialty_journal"
    | "preprint"
    | "industry_whitepaper"
    | null
  populationTags: {
    disease: "NSCLC"
    diseaseSetting: "early" | "locally_advanced" | "metastatic" | "mixed"
    histology: "adenocarcinoma" | "squamous" | "mixed" | "all_nsclc"
    biomarkers: Record<string, string>
  }
  interventionTags: string[]
  outcomeTags: Array<"OS" | "PFS" | "response" | "toxicity" | "QoL" | string>
}
```

### Canonical guideline topic

```ts
type GuidelineTopic = {
  topicId: string
  topicTitle: string
  topicApplicability: {
    diseaseSetting: Array<"early" | "locally_advanced" | "metastatic">
    histology: Array<"adenocarcinoma" | "squamous">
    biomarkerConditions: string[]
  }
  topicInterventionTags: string[]
  guidelineStance: "recommend" | "conditional" | "do_not_recommend" | "not_covered"
  stanceNotes?: string
  prerequisites?: string[]
}
```

## Deterministic Runtime Logic

This is now frozen more precisely.

### Step 1: Clinical relevance gate

Eligible evidence must satisfy:

- disease match
- setting match or acceptable `mixed`
- histology match or `all_nsclc` or acceptable `mixed`
- biomarker compatibility
- unspecified biomarker applicability passes gate but gains no extra benefit later

If a record fails gate:

- it is excluded from ranking
- it can appear in `secondaryReferences`
- it must include explicit exclusion reason(s)

### Step 2: ERS-MVP scoring

ERS is now hard-coded for v1.

#### A. Evidence strength and methodology

- `guideline`: 20
- `systematic_review`: 18
- `phase3_rct`: 16
- `phase2_rct`: 13
- `prospective_obs`: 10
- `retrospective`: 6
- `case_series`: 2
- `expert_opinion`: 2

#### B. Dataset robustness

- `N >= 300`: 15
- `100-299`: 12
- `50-99`: 9
- `20-49`: 6
- `<20`: 3
- `null`: 6

#### C. Source credibility

- `guideline_body`: 15
- `high_impact_journal`: 12
- `specialty_journal`: 9
- `preprint`: 5
- `industry_whitepaper`: 2
- `null`: 6

#### D. Recency

- `<= 3 years`: 10
- `4-6 years`: 6
- `7-10 years`: 3
- `> 10 years`: 0

### ERS total

```ts
ERS_MVP = A + B + C + D
```

### Tie-break order

1. higher A
2. newer year
3. larger N
4. otherwise keep both and cluster by topic

### Threshold

- `ERS >= 30` => `topEvidence`
- otherwise => `secondaryReference`

## Topic Mapping and Labeling Logic

### Topic match

For each ranked evidence item:

1. find applicable topics by vignette applicability
2. compare evidence `interventionTags` to `topicInterventionTags`
3. choose best overlap count
4. tie-break by more specific biomarker conditions
5. if none match => `guideline_silent`

### Label logic

- `aligned`
  - topic stance is `recommend` or `conditional`
  - evidence supports that intervention category
  - vignette and topic are applicable

- `conflict`
  - topic stance is `do_not_recommend`
  - evidence suggests benefit for that same intervention in applicable population

- `guideline_silent`
  - topic stance is `not_covered`
  - or no topic matched

### Important implementation choice

For MVP, “supports” remains conservative and deterministic:

- evidence passes gate
- intervention tags overlap
- evidence type is sufficiently supportive by rubric
- no free-form medical interpretation is introduced

## Important Public APIs and Types

### Main API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/runs` | analyze structured vignette |
| `GET` | `/api/v1/runs/{runId}` | fetch run result |
| `GET` | `/api/v1/runs/{runId}/trace` | fetch gate, scoring, mapping trace |
| `GET` | `/api/v1/runs/{runId}/review-sheet` | fetch reviewer-facing scoring artifact |
| `POST` | `/api/v1/import/esmo` | import guideline topic/snippet set |
| `POST` | `/api/v1/import/pubmed` | import curated PubMed evidence |
| `POST` | `/api/v1/sync/pubmed` | trigger sync job |
| `GET` | `/api/v1/jobs/{jobId}` | job status |
| `POST` | `/api/v1/evals/run` | run frozen benchmark |
| `GET` | `/api/v1/evals/{evalRunId}` | benchmark results |
| `GET` | `/api/v1/governance/policy` | current frozen safety and update policy |
| `GET` | `/api/v1/catalog/topics` | topic catalog list |

### Updated analyze response

```ts
type AnalyzeRunResponse = {
  run: {
    id: string
    status: "queued" | "running" | "completed" | "failed"
    rulesetVersion: string
    corpusVersion: string
    createdAt: string
    latencyMs?: number
  }
  topEvidence: Array<{
    rank: number
    evidenceId: string
    title: string
    publicationYear: number | null
    ersTotal: number
    ersBreakdown: {
      evidenceStrength: number
      datasetRobustness: number
      sourceCredibility: number
      recency: number
    }
    mappedTopicId: string | null
    mappedTopicTitle: string | null
    mappingLabel: "aligned" | "guideline_silent" | "conflict"
    applicabilityNote: string
    citations: CitationRef[]
  }>
  secondaryReferences: Array<{
    evidenceId: string
    exclusionReasons: string[]
  }>
  uncertaintyFlags: string[]
  safetyFooterKey: string
  traceId: string
}
```

## Governance and Responsible AI Module

This is now a formal product subsystem.

### Frozen safety boundaries

The product must never:

- diagnose
- prescribe
- replace clinician judgment
- claim exhaustive evidence coverage
- infer beyond provided inputs
- expand beyond NSCLC treatment evidence scope

### Product enforcement mechanisms

These must be implemented as code and content constraints:

- fixed output templates
- restricted label vocabulary
- fixed disclaimers
- explicit uncertainty language
- structured inputs only
- no free-text patient reasoning
- no recommendation language generation
- frozen scope guards in API/domain layer

### Visible UX locations

Safety boundaries must be visible in:

- results page footer
- methodology page
- import/eval documentation
- benchmark report headers

### Governance entities

Add these backend entities:

- `rulesets`
- `safety_templates`
- `update_records`
- `policy_snapshots`

## Evaluation Architecture

The new evaluation document makes this fully decision-complete.

### Layer 1: System integrity

Binary checks only:

- input accepted
- evidence retrieved
- exactly one valid label assigned

This layer does **not** judge clinical correctness.

### Layer 2: Clinical and logical correctness

Separate domains:

1. relevance correctness
2. mapping correctness
3. citation correctness
4. deterministic logic correctness

### Explicit rule

Do not mix Layer 1 failures with Layer 2 metrics.

If Layer 1 fails, the case is excluded from clinical evaluation reporting and flagged as a system failure.

## Evaluation Data Model

Add these entities:

- `frozen_vignette_packs`
- `vignette_cases`
- `reference_relevance_annotations`
- `reference_mapping_table`
- `reference_citation_expectations`
- `eval_runs`
- `eval_case_results`
- `review_decisions`

## Metrics and Benchmark Outputs

### Relevance metrics

- recall
- false negative rate
- false positive rate
- precision
- F1
- misclassification rate

### Mapping metrics

- overall mapping error
- 3x3 confusion matrix
- per-class error rates for:
  - aligned
  - guideline_silent
  - conflict

### Citation metrics

- citation error rate
- missing citation rate
- misleading citation rate

### Deterministic fidelity metrics

- gate accuracy
- ERS calculation accuracy
- threshold accuracy
- ranking invariance accuracy
- label logic fidelity

### Locked targets

- relevance recall: `>= 95%`
- FN rate: `<= 5%`
- FP rate: `<= 10-15%`
- mapping error: `<= 10-15%`
- citation error: `<= 10-15%`
- deterministic logic fidelity: `100%`

## New Reviewer Workflow Requirements

Because the docs explicitly require human validation, the app should support a lightweight reviewer flow.

### Reviewer features

- per-case scoring sheet view
- reference vs predicted comparison
- citation review toggle: valid / invalid
- notes field for disagreement rationale
- subset-review tagging by expert reviewer
- exportable eval pack PDF/CSV later

### Reviewer routes

| Route | Purpose |
| --- | --- |
| `/labs/evals` | evaluation overview |
| `/labs/evals/[evalRunId]` | run results with confusion matrices |
| `/labs/evals/[evalRunId]/cases/[caseId]` | per-case review screen |
| `/labs/reviewer` | scoring queue / subset review tracker |

## Updated Frontend Product Structure

### Primary routes

| Route | Purpose |
| --- | --- |
| `/` | entry and project framing |
| `/workspace` | vignette input |
| `/runs/[runId]` | main results page |
| `/runs/[runId]/trace` | explainability and rule trace |
| `/datasets` | import batches, provenance, corpus versions |
| `/labs/evals` | benchmark and review |
| `/labs/embeddings` | projector-like exploration |
| `/docs/method` | transparent rules, safety, and evaluation method |
| `/docs/governance` | responsible AI boundaries and update policy |

### UX priority order

1. core vignette workflow
2. explainability panels
3. benchmark views
4. provenance/import pages
5. embeddings lab

The embeddings explorer remains a lab, not the main experience.

## Visual Direction

The visual direction still stands.

### Aesthetic

**Clinical Atlas / Signal Lab**

### New nuance after the Responsible AI doc

The UI needs to balance:

- high craft
- scientific seriousness
- non-authoritative tone

So the tone should feel:

- precise
- calm
- legible
- instrument-like
- not flashy in the clinical workflow

The “nerd panels” should absolutely exist, but the primary workflow should still feel trustworthy rather than performatively futuristic.

### Memorable visual anchor

Keep the **Evidence Ribbon**, but add a second anchor:

**Policy Strip**: a narrow, persistent visual band that surfaces:

- ruleset version
- corpus version
- uncertainty flags
- safety scope

This subtly communicates rigor without bloating the interface.

## Data Import Plan

### Chosen strategy

**Hybrid import first**

### v1 import stages

1. import canonical ESMO excerpt/topic pack
2. import curated PubMed evidence pack
3. normalize to canonical schemas
4. run deterministic tag extraction
5. review failures/null defaults
6. embed text for retrieval
7. snapshot corpus version

### Important decision

Even though the evidence schema allows `guideline` as `evidenceType`, the v1 product should keep:

- **evidence corpus** = curated PubMed-derived records
- **guideline corpus** = curated ESMO topic/snippet set

If guideline-like evidence records appear later, they should be flagged as a separate corpus source, not silently mixed into top evidence ranking.

## Observability Changes

The new docs imply a stronger audit trail.

### Required observability fields per run

- `runId`
- `traceId`
- `rulesetVersion`
- `corpusVersion`
- `inputSchemaVersion`
- gate candidate counts
- threshold counts
- label distribution
- uncertainty flags emitted
- safety template version used

### Update records

Every meaningful update should produce:

- changed component
- reason for change
- before/after benchmark summary
- hard-stop violations
- soft-review flags
- reviewer notes if applicable

This should be visible in `/docs/governance` or `/labs/evals`.

## Non-Regression Policy as Product Logic

This is now explicit.

### Hard stops

Block default rollout if update introduces:

- recommendation language
- new approval/allowance claims
- increased misclassification errors beyond defined threshold
- removed uncertainty disclosures

### Soft review

Allow with documentation if update causes:

- relevance shifts
- mapping shifts
- new evidence additions without prior-context loss

### Versioned change gates

Each release candidate must be evaluated against:

- frozen vignette pack
- frozen ruleset
- frozen safety templates
- frozen label vocabulary

## Delivery Phases

### Phase 1: Foundation

- scaffold `web`, `api`, `worker`
- define canonical schemas from the new docs
- implement ruleset and governance models
- set up Postgres, pgvector, Redis
- add env validation and tracing

### Phase 2: Corpus and Rules

- implement ESMO topic/snippet import
- implement PubMed curated import
- implement deterministic tag normalization
- implement ruleset versioning
- implement safety template system

### Phase 3: Analysis Engine

- implement clinical relevance gate
- implement ERS scoring
- implement tie-break rules
- implement topic mapping
- implement label logic
- persist artifacts and traces

### Phase 4: Evaluation and Governance

- implement frozen vignette pack storage
- implement reference tables
- implement confusion matrix generation
- implement reviewer workflow
- implement update record generation
- implement hard-stop checks

### Phase 5: Product UX

- build structured vignette workspace
- build results page with evidence ribbon
- build trace panels
- build policy strip
- build datasets/provenance view
- build eval lab and reviewer screens

### Phase 6: Labs and Polish

- build embeddings explorer
- add advanced stats panels
- optimize latency and DX
- harden visual identity
- produce final demo narrative

## Tests and Acceptance Criteria

### Domain tests

- gate logic handles mixed/all/unspecified correctly
- ERS values exactly match rubric for all fixture cases
- tie-break behavior matches spec
- threshold behavior matches spec
- label logic matches stance rubric

### Evaluation tests

- Layer 1 checks are reported separately from Layer 2
- relevance confusion matrix is correct
- mapping confusion matrix is correct
- citation validity metrics are correct
- abstentions are tracked separately where needed

### Governance tests

- forbidden recommendation phrases never appear
- frozen label vocabulary cannot drift
- missing-input uncertainty messaging always appears when required
- scope enforcement rejects non-NSCLC usage

### Frontend tests

- required vignette fields are enforced
- results page always shows score breakdown and applicability note
- safety footer always renders
- policy strip always displays ruleset/corpus version
- reviewer flows allow case-by-case validation

### Acceptance criteria

- runtime outputs are deterministic for fixed inputs
- every top evidence record includes ERS breakdown + mapping + citation
- every excluded record includes reason
- benchmark suite produces separate Layer 1 and Layer 2 reporting
- hard-stop policy can block release candidate status
- main workflow remains visually polished and understandable

## Explicit Assumptions and Defaults

- single-team internal MVP, not public clinical deployment
- no PHI in first release
- ESMO inputs arrive as curated excerpts/topic pack, not raw guideline PDFs in v1 runtime
- PubMed inputs arrive first as curated import, with live sync added later
- LLM assistance is optional and non-authoritative
- embeddings are used for retrieval and lab visualization, not for final clinical judgment
- reviewer scoring is lightweight and internal, not a complex enterprise review system

## Final Recommendation

The current plan does **not** need a major rewrite, but it **does need to be upgraded from “good architecture” to “governed implementation spec.”**

The most important updates are:

- freeze the canonical schemas from the modeling docs
- freeze the exact ERS and mapping rubric
- add ruleset and governance as first-class modules
- implement two-layer evaluation exactly as specified
- make reviewer workflow and update records part of the product
- keep the rich UX, but place rigor and explainability above visual spectacle in the core workflow

So the stack remains the same, but the product architecture becomes sharper, safer, and much more defensible. That’s a very good evolution for a serious MIT final project.
