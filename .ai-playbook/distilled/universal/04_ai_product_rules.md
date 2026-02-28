# Universal Rules: AI Product and LLM Engineering

## U-AI-01
- Rule: Prefer the simplest architecture that satisfies the quality target.
- Rationale: Over-designed AI stacks add latency, cost, and failure points.
- Adoption signal: Full-context LLM is used before introducing retrieval complexity.
- Failure signal: Premature RAG/agent orchestration without measurable gain.

## U-AI-02
- Rule: Enforce structured output with schema validation.
- Rationale: Unstructured parsing is brittle and unsafe.
- Adoption signal: JSON mode/function schema + validation at boundaries.
- Failure signal: Regex parsing or silent field mismatch.

## U-AI-03
- Rule: Use semantic task prompts, not keyword matching.
- Rationale: Semantic prompts generalize better across languages and formats.
- Adoption signal: Prompting describes concepts and constraints.
- Failure signal: Extraction fails on translation/synonym changes.

## U-AI-04
- Rule: Require confidence and source-grounding signals when outputs drive decisions.
- Rationale: Trust increases when users can verify claims quickly.
- Adoption signal: Confidence tiers, citations, or trace links are surfaced in UI.
- Failure signal: High-stakes outputs cannot be audited by users.

## U-AI-05
- Rule: Track tokens, latency, and cost per request.
- Rationale: Cost and response time become product constraints at scale.
- Adoption signal: Cost/latency telemetry is visible in logs or diagnostics.
- Failure signal: Spend and latency surprises appear late.

## U-AI-06
- Rule: Add model/provider fallback strategy for core paths.
- Rationale: Availability and quality vary by provider and model revision.
- Adoption signal: Ordered fallback with explicit backend labeling.
- Failure signal: Core AI feature is all-or-nothing.

## U-AI-07
- Rule: Keep benchmark harnesses for AI quality-sensitive features.
- Rationale: Prompt/model changes need objective regression checks.
- Adoption signal: Repeatable benchmark scripts and target thresholds exist.
- Failure signal: Quality discussions rely on anecdotal testing only.

## U-AI-08
- Rule: Bound agent autonomy with explicit iteration limits and escalation paths.
- Rationale: Unbounded loops and silent retries create cost spikes and hidden failure states.
- Adoption signal: Agent flows define max steps/retries and clear handoff to human or fallback flow.
- Failure signal: Agents loop, stall, or incur runaway token/tool costs.

## U-AI-09
- Rule: Treat retrieval and tool outputs as untrusted input and apply guardrails.
- Rationale: Prompt-injection and tool-response poisoning can subvert downstream decisions.
- Adoption signal: Retrieved/tool content is validated, scoped, and filtered before model/action use.
- Failure signal: External content can directly alter system instructions or privileged behavior.
