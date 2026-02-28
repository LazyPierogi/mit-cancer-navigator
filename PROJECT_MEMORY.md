# PROJECT_MEMORY.md

## Project Identity
- Name: Lung Cancer Treatment Navigator
- Goal: Build a defensible MVP that retrieves NSCLC evidence, ranks it deterministically, maps it to ESMO guideline topics, and labels findings as aligned, guideline-silent, or conflict.
- Primary users: Oncology teams and reviewers validating evidence-to-guideline mapping for NSCLC scenarios.
- Project type: Full-stack AI-assisted clinical evidence triage tool with deterministic decision logic.

## Scope and Constraints
- In-scope outcomes:
  - Structured patient vignette intake for NSCLC.
  - PubMed-based evidence retrieval focused on systematic reviews and RCTs.
  - Deterministic evidence ranking and guideline topic mapping.
  - Auditable output with citations, confidence signals, and label traceability.
  - Frozen-vignette regression workflow for non-regression checks.
- Non-goals:
  - Free-text clinical input in the MVP.
  - Generative medical advice or autonomous treatment recommendations.
  - Local hospital policy/compliance modeling in the MVP.
- Success criteria:
  - Evidence recall target >= 95% on the frozen 15-vignette evaluation set.
  - Mapping error rate <= 10-15%.
  - Rule audit fidelity at 100% for deterministic ranking and labeling logic.
  - Citation error rate <= 10-15%.
- Reliability/performance expectations:
  - Deterministic outputs for identical inputs.
  - Exactly one valid label per evidence cluster.
  - Bounded retrieval, rerank, and timeout behavior for UI/API responses.
- Security/privacy constraints:
  - Accept only structured vignette fields required for ranking and mapping.
  - Keep secrets and runtime config out of source code and validate env at startup.
  - Treat all retrieved evidence and tool outputs as untrusted input.
  - Redact sensitive patient details from logs and diagnostics.

## Technical Baseline
- Runtime and framework:
  - Application stack not chosen yet.
  - Architecture direction suggests a UI/API surface on top of a retrieval + deterministic ranking pipeline.
- Core modules and boundaries:
  - Structured vignette intake and validation boundary.
  - Query builder and normalization layer.
  - Evidence retrieval pipeline for PubMed-derived corpus.
  - Guideline retrieval pipeline for curated ESMO topic catalog.
  - Deterministic ranking, pairing, and labeling engine.
  - Output formatter for UI/API responses with citations and justification.
- External integrations:
  - PubMed API for evidence metadata and abstracts.
  - Qdrant for evidence and guideline collections.
  - Curated ESMO-derived topic catalog and guideline stance metadata.
- Data and persistence model:
  - Frozen synthetic vignette dataset for evaluation.
  - Evidence chunks and guideline snippets stored as retrieval collections with metadata.
  - Deterministic labels and scoring outputs preserved for audit and regression comparison.

## Decision Log
- Decision: Scope MVP to NSCLC evidence navigation rather than broad oncology support.
  - Context: Milestone feedback flagged data volume, evaluation complexity, and local bias.
  - Alternatives considered: Broad oncology assistant, local-compliance navigator.
  - Choice rationale: Narrow scope makes evaluation, data preparation, and product value more tractable.
  - Risks: Scope may still hide complexity in tagging and guideline curation.
  - Rollback plan: Expand only after frozen-vignette evaluation is stable.
- Decision: Use deterministic rule-based ranking and labeling instead of generative medical reasoning.
  - Context: The project needs auditable, binary-checkable outputs.
  - Alternatives considered: Fully generative advisor, hybrid reasoning-heavy LLM flow.
  - Choice rationale: Deterministic logic supports traceability, safety, and non-regression testing.
  - Risks: Rules may underspecify edge cases and require manual curation.
  - Rollback plan: Introduce bounded LLM support only for low-risk tasks such as query expansion or tagging assistance.
- Decision: Keep MCP configuration in repo but leave runnable MCP servers empty for now.
  - Context: Current repository contains documentation/bootstrap only; no active implementation workflow depends on MCP.
  - Alternatives considered: Add generic MCP servers preemptively.
  - Choice rationale: Avoid tool sprawl until the implementation stack and active dev workflows are chosen.
  - Risks: Future contributors may assume MCP is already configured for runtime work.
  - Rollback plan: Add concrete server entries to `mcp.json` when a real coding workflow requires them.

## Quality Grades
- Product definition: B (2026-02-28, MVP scope and evaluation targets are clear, but implementation stack is still open).
- Retrieval/ranking architecture: B- (2026-02-28, pipeline shape is defined, but contracts and schemas are not yet codified).
- Security/privacy baseline: C+ (2026-02-28, rules are identified, but env validation, redaction, and permission handling are not yet implemented).
- Delivery harness: C (2026-02-28, checklist exists, but no runnable tests or CI flow are present in repo).
- Update cadence: Reassess at each milestone and after the first implementation scaffold lands.

## Execution Plans
- Active plans:
  - Bootstrap fit review and setup alignment from [SETUP_PROJECT_FIT_REVIEW.playbook.md](/Users/mario/Repo/mit-cancer-navigator/SETUP_PROJECT_FIT_REVIEW.playbook.md).
  - Choose implementation stack and codify module contracts before writing the app scaffold.
- Completed plans:
  - Universal playbook bootstrap installation completed on 2026-02-28.
- Tech-debt tracker:
  - Missing typed schemas for vignette input, evidence metadata, guideline topics, and output labels.
  - Missing release, rollback, and dependency-audit workflow.
  - Missing automated regression harness for the 15 frozen vignettes.

## Validation Baseline
- Required automated checks:
  - Schema validation for structured vignette input and output payloads.
  - Deterministic scoring/ranking invariance tests.
  - Frozen-vignette regression suite.
  - Citation presence and traceability checks.
- Required manual checks:
  - Review of guideline topic catalog quality and stance tagging.
  - Spot-check of evidence relevance gating for histology/biomarker mismatches.
  - Clinical sanity review for aligned/silent/conflict labels on evaluation vignettes.
- Cross-surface checks:
  - API/output parity for citations and labels.
  - Desktop/mobile UI review once a product surface exists.
  - Timeout/fallback behavior when retrieval returns sparse evidence.

## Distillation Notes
- Reusable lessons:
  - Narrowing medical AI scope early increases auditability and delivery speed.
  - Deterministic cores need explicit benchmark datasets from day one.
- Repeated failures:
  - Bootstrap metadata can drift from actual repo-local skill installation if not verified after install.
- Candidate rules to promote:
  - Treat bootstrap summaries as provisional until repo-local assets are enumerated from disk.
  - For high-stakes AI products, do not accept free-text input in MVP unless the evaluation harness already exists.

## Optional Pack Addons
Add one or more of the following if relevant:
- `templates/packs/web-app/PROJECT_MEMORY.addon.web-app.md`
- `templates/packs/mobile-app/PROJECT_MEMORY.addon.mobile-app.md`
- `templates/packs/game/PROJECT_MEMORY.addon.game.md`
- `templates/packs/fullstack-ai/PROJECT_MEMORY.addon.fullstack-ai.md`
