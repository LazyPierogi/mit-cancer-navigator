# Setup Project-Fit Review (Skills + MCP)

Purpose: verify that the bootstrapped skills and MCP servers are correct for this specific product/repository, then propose targeted changes.

## Baseline snapshot from bootstrap
- Selected packs: none
- MCP mode(s): skip
- Skill install mode: yes
- Project skills directory: /Users/mario/repo/mit-cancer-navigator/.codex/skills
- Selected skills: ai-agents-architect api-security-best-practices api-security-testing appdeploy application-performance-performance-optimization architect-review architecture
- Installed skills: ai-agents-architect api-security-best-practices api-security-testing appdeploy application-performance-performance-optimization architect-review architecture
- Generated MCP files: none

## Required input before review
- [x] Product description or requirements file path in this repository (preferred)
- [ ] If no file exists, pasted project description text
- [x] Stack and architecture evidence (README, package manifests, service docs, ADRs)

## Review procedure (agent must execute)
1. Read AGENTS.md, PROJECT_MEMORY.md, STARTUP_CHECKLIST.md, and .ai-playbook/INSTALLATION_SUMMARY.md.
2. Read the product requirements and architecture docs.
3. Build a capability map for this project (UI, backend, infra, AI/LLM, mobile/game, testing, security, deployment, observability).
4. Compare required capabilities vs installed skills.
5. Compare required integrations vs configured MCP servers.
6. Decide for each gap:
   - Install now (safe and available)
   - Defer with exact install instructions
   - Reject as unnecessary (with rationale)
7. Use recommendation sources only when a gap exists:
   - Skills catalog: https://github.com/sickn33/antigravity-awesome-skills/blob/main/CATALOG.md
   - MCP catalog: https://github.com/punkpeye/awesome-mcp-servers
8. Produce a short execution report and update the decision table below.

## Decision table (fill during review)
| Area | Needed capability | Current skill/MCP | Decision (keep/add/remove/defer) | Evidence |
| --- | --- | --- | --- | --- |
| Product architecture | Architect-first workflow for a new full-stack AI product | `senior-fullstack` | add | MVP still has no chosen implementation stack, so setup and scaffolding guidance is needed before coding starts |
| AI retrieval design | RAG and evaluation patterns for evidence retrieval, rerank, citations, and regression | `llm-app-patterns` | add | Architecture proposal defines retrieval collections, rerank, citations, and bounded LLM use |
| Agent/tooling safety | Bounded agent usage for low-risk tasks like query expansion and future orchestration | `ai-agents-architect` | keep | Project description explicitly limits LLMs to bounded tasks and demands deterministic control |
| Backend/API design | Typed contracts for structured vignette input, retrieval APIs, and deterministic output | `backend-architect` | add | MVP requires UI/API output and schema-validated boundaries |
| Security/privacy | High-stakes safeguards for clinical data minimization, auditability, and secret/env policy | `security-auditor` | add | Clinical context and auditability requirements make security review mandatory |
| Performance and evaluation | Latency and scoring-harness optimization for retrieval and ranking loops | `application-performance-performance-optimization` | keep | Proposal defines retrieval, rerank, timeout, cache, and benchmark-style metrics |
| API hardening | API security guidance | `api-security-best-practices` | keep | Structured intake and external integrations will require API boundary hygiene once implementation starts |
| Missing bootstrap skill | `api-security-testing` selected in summary but not present in repo-local/global catalog | none | defer | Skill was declared by bootstrap, but no matching local/global skill artifact is available to install from disk |
| Missing bootstrap skill | `appdeploy` selected in summary but not present in repo-local/global catalog | none | defer | Deployment workflow is not yet chosen and no matching skill artifact is available locally |
| Missing bootstrap skill | `architect-review` selected in summary but not present in repo-local/global catalog | none | defer | Current need is setup/scaffolding, not formal architecture review automation, and the artifact is unavailable |
| Missing bootstrap skill | `architecture` selected in summary but not present in repo-local/global catalog | none | defer | The bootstrap reference does not match an installable local/global skill artifact |
| MCP tooling | Runnable MCP servers for active development | `mcp.json` with empty `mcpServers` | keep | Repo contains documentation/bootstrap only; project runtime dependencies like PubMed and Qdrant are application integrations, not current MCP requirements |

## Completion gate
- [x] All required capabilities are mapped to at least one skill or explicit manual workflow.
- [x] MCP configuration matches required integrations/tools for this project.
- [x] Missing items are either installed or have exact step-by-step install instructions.
- [x] Open decisions requiring human judgment are listed explicitly.

## Open decisions requiring human judgment
- Choose the first implementation stack for the MVP surface and API layer (for example Next.js + Python worker, or Python-first backend with a thin web UI).
- Decide whether PubMed tagging stays rule-based or introduces lightweight NLP assistance.
- Decide how much manual curation is acceptable for the ESMO topic catalog and stance mapping.

## Execution report
- What was merged:
  - Real project evidence from `docs/Lung Cancer Treatment Navigator (project description).pdf` and `docs/Lung Cancer Treatment Navigator (architecture proposal).md`.
  - Repo-local skills were aligned with actual project needs by adding `backend-architect`, `llm-app-patterns`, `security-auditor`, and `senior-fullstack`.
- What was skipped and why:
  - MCP servers were intentionally left empty because current repository work does not require runnable MCP tooling yet.
  - Pack add-ons were not applied because this repo does not yet contain a chosen implementation surface that would justify `web-app`, `mobile-app`, `game`, or `fullstack-ai` template merge.
- Skills/MCP validation results:
  - Keep: `ai-agents-architect`, `api-security-best-practices`, `application-performance-performance-optimization`.
  - Added locally: `backend-architect`, `llm-app-patterns`, `security-auditor`, `senior-fullstack`.
  - Deferred: `api-security-testing`, `appdeploy`, `architect-review`, `architecture` because matching artifacts are not available locally and are not blocking current bootstrap.
  - MCP: `mcp.json` remains the source of truth and currently requires no runnable server entries.
- Open decisions requiring human input:
  - Final runtime stack.
  - Guideline tagging strategy.
  - Manual labeling depth for evaluation data.
