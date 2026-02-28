# Distilled Rule Source Map

This map links distilled rule groups to intake evidence.

## Universal rules evidence

| Distilled area | Primary evidence files |
|---|---|
| Global engineering | `intake/zaslony.com/05_lessons_learnings_snapshot.md`, `intake/subscription tracker app/05_lessons_learnings_snapshot.md`, `intake/water tracker app/05_lessons_learnings_snapshot.md`, `intake/unity game project/05_lessons_learnings_snapshot.md` |
| Agent operating model | `intake/zaslony.com/01_agents_snapshot.md`, `intake/water tracker app/01_agents_snapshot.md`, `intake/interactive website/06_failures_gotchas_snapshot.md`, `intake/social media pipeline advice posts/01_agents_snapshot.md` |
| Architecture | `intake/zaslony.com/02_architecture_snapshot.md`, `intake/mesh communication app/02_architecture_snapshot.mfd`, `intake/subscription tracker app/02_architecture_snapshot.md`, `intake/unity game project/02_architecture_snapshot.md` |
| AI product and LLM engineering | `intake/Document extraction and dahboard/05_lessons_learnings_snapshot.md`, `intake/Document extraction and dahboard/06_failures_gotchas_snapshot.md`, `intake/curtain configurator/05_lessons_learnings_snapshot.md`, `intake/zaslony.com/05_lessons_learnings_snapshot.md` |
| Security baseline | `intake/Document extraction and dahboard/06_failures_gotchas_snapshot.md`, `intake/water tracker app/06_failures_gotchas_snapshot.md`, `intake/mesh communication app/06_failures_gotchas_snapshot.mfd`, `intake/zaslony.com/06_failures_gotchas_snapshot.md` |
| Quality gates | `intake/interactive website/06_failures_gotchas_snapshot.md`, `intake/unity game project/06_failures_gotchas_snapshot.md`, `intake/zaslony.com/06_failures_gotchas_snapshot.md`, `intake/water tracker app/06_failures_gotchas_snapshot.md` |

## Canonical external source overlays

| Distilled area | Canonical source files | Specific rules |
|---|---|---|
| Agent operating model (v0.2 overlay) | `intake/PDF intake/Harness engineering_ leveraging Codex in an agent-first world _ OpenAI.pdf` ([openai.com/index/harness-engineering](https://openai.com/index/harness-engineering/), published 2026-02-11) | U-AO-09 (progressive disclosure), U-AO-10 (exec plans, quality grades, doc-gardening), U-AO-11, U-AO-12, U-AO-13, U-AO-14 (escalate docs→code), U-AO-15 (style variance), U-AO-16 (isolated environments) |
| Architecture (v0.2 overlay) | same | U-AR-08 (remediation messages), U-AR-09, U-AR-10, U-AR-11 (invariants not implementations) |
| Quality gates (v0.2 overlay) | same | U-QG-09, U-QG-10 (doc-gardening, continuous debt paydown), U-QG-11 (quality grading) |

## Pack evidence

| Pack | Primary evidence files |
|---|---|
| Web app | `intake/zaslony.com/02_architecture_snapshot.md`, `intake/zaslony.com/06_failures_gotchas_snapshot.md`, `intake/interactive website/06_failures_gotchas_snapshot.md`, `intake/Document extraction and dahboard/02_architecture_snapshot.md` |
| Mobile app | `intake/water tracker app/02_architecture_snapshot.md`, `intake/water tracker app/06_failures_gotchas_snapshot.md`, `intake/subscription tracker app/06_failures_gotchas_snapshot.md`, `intake/mesh communication app/02_architecture_snapshot.mfd` |
| Game | `intake/unity game project/02_architecture_snapshot.md`, `intake/unity game project/05_lessons_learnings_snapshot.md`, `intake/unity game project/06_failures_gotchas_snapshot.md`, `intake/interactive website/05_lessons_learnings_snapshot.md` |
| Fullstack AI | `intake/zaslony.com/02_architecture_snapshot.md`, `intake/Document extraction and dahboard/05_lessons_learnings_snapshot.md`, `intake/Document extraction and dahboard/06_failures_gotchas_snapshot.md`, `intake/social media pipeline advice posts/05_lessons_learnings_snapshot.md` |

## Notes
- This map references source files, not line-level citations.
- The distilled docs intentionally remove project-specific implementation details.
