from __future__ import annotations

import json
import re
import time
from dataclasses import asdict
from urllib import error as urllib_error
from urllib import request as urllib_request

from app.config.settings import settings
from app.domain.contracts import (
    EvidenceExplainability,
    EvidenceExplainabilitySourceAnchor,
    EvidenceExplainabilityStudySummary,
    ExplainabilitySummary,
    SemanticEvidenceItem,
    SemanticGuidelineCandidate,
    UncertaintyFlagsExplainability,
    VignetteInput,
)


SEMANTIC_PROMPT_VERSION = "gemini-grounded-v1"
BENCHMARK_PROMPT_VERSION = "gemini-benchmark-v1"
EVIDENCE_PROMPT_VERSION = "gemini-evidence-v2"
UNCERTAINTY_FLAGS_PROMPT_VERSION = "gemini-uncertainty-flags-v1"


class LlmExplainabilityService:
    _OPENROUTER_TOOLTIP_SCHEMA = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "whyFlagsExist": {"type": "string"},
            "whatItMeans": {"type": "string"},
            "flags": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["summary", "whyFlagsExist", "whatItMeans", "flags"],
    }

    @staticmethod
    def _humanize_uncertainty_flag(flag: str) -> str:
        code, _, source_id = flag.partition(":")
        code_label = code.replace("_", " ").strip() or "unspecified uncertainty trigger"
        if source_id:
            return f"{code_label} ({source_id})"
        return code_label

    def _fallback_uncertainty_flags_explainability(
        self,
        *,
        uncertainty_flags: list[str],
        engine: str,
        top_evidence_count: int,
        manual_review_count: int,
        provider_status: str,
        validation_status: str,
        latency_ms: int | None = None,
    ) -> UncertaintyFlagsExplainability:
        flag_count = len(uncertainty_flags)
        if flag_count == 0:
            summary = (
                f"No uncertainty flags were raised in this {engine.replace('_', ' ')} run, which means the promoted evidence "
                "did not trip the current ambiguity heuristics."
            )
            why_flags_exist = (
                "These flags exist as guardrails for edge cases where the structured evidence is thin, ambiguous, or partially specified. "
                "They are meant to surface caution, not to silently change ranking logic."
            )
            what_it_means = (
                "Zero flags is a cleaner run, but it is not a guarantee of clinical correctness. It only means the current run did not trigger "
                "the uncertainty checks that we expose to the operator."
            )
        else:
            preview = ", ".join(self._humanize_uncertainty_flag(flag) for flag in uncertainty_flags[:3])
            summary = (
                f"This run raised {flag_count} uncertainty flag{'s' if flag_count != 1 else ''}, signaling that some promoted or reviewed evidence "
                f"still carries ambiguity the UI should surface explicitly. Current examples: {preview}."
            )
            why_flags_exist = (
                "The flags exist so the system can admit when structured evidence is incomplete, coarse, or mismatched to the patient context. "
                f"They help explain why a run with {top_evidence_count} top-evidence items and {manual_review_count} manual-review items may still require human judgment."
            )
            what_it_means = (
                "A flag is a caution signal, not a verdict. It tells the reviewer that something about applicability, evidence typing, or structured context "
                "needs extra scrutiny before anyone treats the surfaced studies as cleanly interpretable support."
            )

        return UncertaintyFlagsExplainability(
            summary=summary,
            whyFlagsExist=why_flags_exist,
            whatItMeans=what_it_means,
            flags=uncertainty_flags,
            grounded=True,
            providerStatus=provider_status,
            provider=(settings.llm_provider.strip() or None) if settings.llm_provider.strip().lower() != "disabled" else None,
            model=settings.llm_model.strip() or None,
            promptVersion=UNCERTAINTY_FLAGS_PROMPT_VERSION if provider_status == "llm_grounded" else "local-uncertainty-flags-v1",
            latencyMs=latency_ms,
            validationStatus=validation_status,
        )

    @staticmethod
    def _validate_uncertainty_flags_payload(*, result: dict, allowed_flags: set[str]) -> UncertaintyFlagsExplainability:
        summary = str(result.get("summary", "")).strip()
        why_flags_exist = str(result.get("whyFlagsExist", "")).strip()
        what_it_means = str(result.get("whatItMeans", "")).strip()
        if not all((summary, why_flags_exist, what_it_means)):
            raise ValueError("Gemini uncertainty-flags payload is incomplete.")

        raw_flags = result.get("flags", [])
        if not isinstance(raw_flags, list):
            raise ValueError("Gemini uncertainty-flags payload must include a flags array.")
        flags = [str(item).strip() for item in raw_flags if str(item).strip()]
        if flags and not set(flags).issubset(allowed_flags):
            raise ValueError("Gemini uncertainty-flags payload cited flags outside the run.")

        return UncertaintyFlagsExplainability(
            summary=summary,
            whyFlagsExist=why_flags_exist,
            whatItMeans=what_it_means,
            flags=flags,
            grounded=True,
            providerStatus="llm_grounded",
            validationStatus="passed",
            promptVersion=UNCERTAINTY_FLAGS_PROMPT_VERSION,
        )

    def _is_configured(self) -> bool:
        return (
            settings.llm_provider.strip().lower() != "disabled"
            and bool(settings.llm_api_key)
            and bool(settings.llm_model.strip())
        )

    def _fallback(
        self,
        *,
        summary: str,
        grounded: bool,
        source_chunk_ids: list[str],
        source_ids: list[str],
        provider_status: str,
        prompt_version: str,
        validation_status: str,
        latency_ms: int | None = None,
    ) -> ExplainabilitySummary:
        return ExplainabilitySummary(
            summary=summary,
            grounded=grounded,
            sourceChunkIds=source_chunk_ids,
            providerStatus=provider_status,
            provider=(settings.llm_provider.strip() or None) if settings.llm_provider.strip().lower() != "disabled" else None,
            model=settings.llm_model.strip() or None,
            promptVersion=prompt_version,
            latencyMs=latency_ms,
            validationStatus=validation_status,
            sourceIds=source_ids,
        )

    def _gemini_json(self, *, prompt: str, timeout_s: int = 30) -> tuple[dict, int]:
        model = settings.llm_model.strip()
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={settings.llm_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        }
        request = urllib_request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        started_at = time.perf_counter()
        try:
            with urllib_request.urlopen(request, timeout=timeout_s) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini request failed with {exc.code}: {details}") from exc
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return body, latency_ms

    def _openrouter_json(self, *, prompt: str, schema_name: str, schema: dict, timeout_s: int = 30) -> tuple[dict, int]:
        payload = {
            "model": settings.llm_model.strip(),
            "messages": [
                {
                    "role": "system",
                    "content": "Return only valid JSON matching the supplied schema.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
            "provider": {
                "require_parameters": True,
            },
        }
        request = urllib_request.Request(
            url="https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://mit-cancer-navigator-api.vercel.app",
                "X-Title": "MIT Cancer Navigator",
            },
        )
        started_at = time.perf_counter()
        try:
            with urllib_request.urlopen(request, timeout=timeout_s) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter request failed with {exc.code}: {details}") from exc
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return body, latency_ms

    @staticmethod
    def _extract_json_candidate(payload: dict) -> dict:
        candidates = payload.get("candidates", [])
        if not candidates:
            raise ValueError("No Gemini candidates returned.")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(str(part.get("text", "")) for part in parts)
        if not text.strip():
            raise ValueError("Gemini returned empty content.")
        result = json.loads(text)
        if not isinstance(result, dict):
            raise ValueError("Gemini JSON payload must be an object.")
        return result

    @staticmethod
    def _extract_openrouter_json_candidate(payload: dict) -> dict:
        choices = payload.get("choices", [])
        if not choices:
            raise ValueError("No OpenRouter choices returned.")
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            text = "".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
        else:
            text = str(content)
        if not text.strip():
            raise ValueError("OpenRouter returned empty content.")
        result = json.loads(text)
        if not isinstance(result, dict):
            raise ValueError("OpenRouter JSON payload must be an object.")
        return result

    @staticmethod
    def _validate_grounded_payload(
        *,
        result: dict,
        allowed_chunk_ids: set[str],
        allowed_source_ids: set[str],
    ) -> tuple[str, list[str], list[str]]:
        summary = str(result.get("summary", "")).strip()
        if not summary:
            raise ValueError("Gemini summary is empty.")
        chunk_ids = [str(item) for item in result.get("sourceChunkIds", []) if str(item)]
        source_ids = [str(item) for item in result.get("sourceIds", []) if str(item)]
        if chunk_ids and not set(chunk_ids).issubset(allowed_chunk_ids):
            raise ValueError("Gemini cited chunk IDs outside retrieved evidence.")
        if source_ids and not set(source_ids).issubset(allowed_source_ids):
            raise ValueError("Gemini cited source IDs outside retrieved evidence.")
        return summary, chunk_ids, source_ids

    @staticmethod
    def _split_sentences(text: str | None) -> list[str]:
        if not text:
            return []
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []
        return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", normalized) if sentence.strip()]

    @staticmethod
    def _truncate_text(text: str, limit: int) -> str:
        normalized = re.sub(r"\s+", " ", text).strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 3].rstrip() + "..."

    def _abstract_sections(self, abstract: str | None) -> tuple[str, str, str]:
        sentences = self._split_sentences(abstract)
        if not sentences:
            return (
                "Study objective not explicitly available in the imported abstract.",
                "No structured outcome signal was extracted from the imported abstract.",
                "Takeaway falls back to the scored metadata and label context for this evidence.",
            )

        objective = next(
            (
                sentence
                for sentence in sentences
                if any(keyword in sentence.lower() for keyword in ("objective", "aim", "purpose", "background", "methods"))
            ),
            sentences[0],
        )
        signal = next(
            (
                sentence
                for sentence in sentences
                if any(
                    keyword in sentence.lower()
                    for keyword in ("result", "results", "improved", "benefit", "significant", "response", "survival", "progression")
                )
            ),
            sentences[min(1, len(sentences) - 1)],
        )
        takeaway = next(
            (
                sentence
                for sentence in sentences
                if any(keyword in sentence.lower() for keyword in ("conclusion", "conclusions", "suggest", "support", "indicate"))
            ),
            sentences[-1],
        )
        return (
            self._truncate_text(objective, 220),
            self._truncate_text(signal, 220),
            self._truncate_text(takeaway, 220),
        )

    def _fallback_source_anchors(self, *, abstract: str | None, citations: list[dict]) -> list[EvidenceExplainabilitySourceAnchor]:
        sentences = self._split_sentences(abstract)
        snippets = sentences[:3]
        anchors: list[EvidenceExplainabilitySourceAnchor] = []
        if citations:
            primary = citations[0]
            for snippet in snippets:
                anchors.append(
                    EvidenceExplainabilitySourceAnchor(
                        sourceId=str(primary.get("sourceId", "")).strip(),
                        title=str(primary.get("title", "")).strip() or "Source",
                        snippet=self._truncate_text(snippet, 220),
                        year=primary.get("year"),
                    )
                )
        if anchors:
            return anchors

        for citation in citations[:3]:
            snippet = str(citation.get("summary", "")).strip()
            if not snippet:
                continue
            anchors.append(
                EvidenceExplainabilitySourceAnchor(
                    sourceId=str(citation.get("sourceId", "")).strip(),
                    title=str(citation.get("title", "")).strip() or "Source",
                    snippet=self._truncate_text(snippet, 220),
                    year=citation.get("year"),
                )
            )
        return anchors

    @staticmethod
    def _score_rationale(
        *,
        ers_total: int,
        ers_breakdown: dict,
        mapping_label: str,
        mapped_topic_title: str | None,
        applicability_note: str,
    ) -> str:
        topic_fragment = f" and maps to {mapped_topic_title}" if mapped_topic_title else ""
        return (
            f"ERS {ers_total}/100 comes from evidence strength {ers_breakdown.get('evidenceStrength', 0)}/35, "
            f"dataset robustness {ers_breakdown.get('datasetRobustness', 0)}/25, "
            f"source credibility {ers_breakdown.get('sourceCredibility', 0)}/25, and recency {ers_breakdown.get('recency', 0)}/15. "
            f"This evidence is labeled {mapping_label.replace('_', ' ')}{topic_fragment}. {applicability_note}"
        )

    def _fallback_evidence_explainability(
        self,
        *,
        evidence_id: str,
        abstract: str | None,
        citations: list[dict],
        ers_total: int,
        ers_breakdown: dict,
        mapping_label: str,
        mapped_topic_title: str | None,
        applicability_note: str,
        provider_status: str,
        validation_status: str,
        grounded: bool = True,
        latency_ms: int | None = None,
    ) -> EvidenceExplainability:
        objective, signal, takeaway = self._abstract_sections(abstract)
        anchors = self._fallback_source_anchors(abstract=abstract, citations=citations)
        source_ids = [anchor.sourceId for anchor in anchors if anchor.sourceId]
        return EvidenceExplainability(
            evidenceId=evidence_id,
            scoreRationale=self._score_rationale(
                ers_total=ers_total,
                ers_breakdown=ers_breakdown,
                mapping_label=mapping_label,
                mapped_topic_title=mapped_topic_title,
                applicability_note=applicability_note,
            ),
            studySummary=EvidenceExplainabilityStudySummary(
                objective=objective,
                signal=signal,
                takeaway=takeaway,
            ),
            sourceAnchors=anchors,
            grounded=grounded,
            providerStatus=provider_status,
            provider=(settings.llm_provider.strip() or None) if settings.llm_provider.strip().lower() != "disabled" else None,
            model=settings.llm_model.strip() or None,
            promptVersion=EVIDENCE_PROMPT_VERSION if provider_status == "llm_grounded" else "local-evidence-v1",
            latencyMs=latency_ms,
            validationStatus=validation_status,
            sourceIds=list(dict.fromkeys(source_ids)),
        )

    @staticmethod
    def _validate_evidence_payload(*, result: dict, evidence_id: str, allowed_source_ids: set[str]) -> EvidenceExplainability:
        payload_evidence_id = str(result.get("evidenceId", "")).strip()
        if payload_evidence_id != evidence_id:
            raise ValueError("Gemini returned explainability for an unexpected evidence ID.")

        score_rationale = str(result.get("scoreRationale", "")).strip()
        if not score_rationale:
            raise ValueError("Gemini score rationale is empty.")

        study_summary = result.get("studySummary")
        if not isinstance(study_summary, dict):
            raise ValueError("Gemini study summary must be an object.")
        objective = str(study_summary.get("objective", "")).strip()
        signal = str(study_summary.get("signal", "")).strip()
        takeaway = str(study_summary.get("takeaway", "")).strip()
        if not all((objective, signal, takeaway)):
            raise ValueError("Gemini study summary is incomplete.")

        anchors_payload = result.get("sourceAnchors", [])
        if not isinstance(anchors_payload, list):
            raise ValueError("Gemini sourceAnchors must be a list.")

        anchors: list[EvidenceExplainabilitySourceAnchor] = []
        source_ids: list[str] = []
        for anchor in anchors_payload[:3]:
            if not isinstance(anchor, dict):
                raise ValueError("Gemini sourceAnchor must be an object.")
            source_id = str(anchor.get("sourceId", "")).strip()
            title = str(anchor.get("title", "")).strip()
            snippet = str(anchor.get("snippet", "")).strip()
            if not source_id or not title or not snippet:
                raise ValueError("Gemini sourceAnchor is incomplete.")
            if source_id not in allowed_source_ids:
                raise ValueError("Gemini cited source IDs outside retrieved evidence.")
            year_raw = anchor.get("year")
            year = int(year_raw) if isinstance(year_raw, int) else None
            anchors.append(
                EvidenceExplainabilitySourceAnchor(
                    sourceId=source_id,
                    title=title,
                    snippet=snippet,
                    year=year,
                )
            )
            source_ids.append(source_id)

        if not anchors:
            raise ValueError("Gemini must return at least one source anchor.")

        return EvidenceExplainability(
            evidenceId=evidence_id,
            scoreRationale=score_rationale,
            studySummary=EvidenceExplainabilityStudySummary(
                objective=objective,
                signal=signal,
                takeaway=takeaway,
            ),
            sourceAnchors=anchors,
            grounded=True,
            sourceIds=list(dict.fromkeys(source_ids)),
            promptVersion=EVIDENCE_PROMPT_VERSION,
            providerStatus="llm_grounded",
            validationStatus="passed",
        )

    def summarize_semantic_case(
        self,
        *,
        vignette: VignetteInput,
        semantic_evidence: list[SemanticEvidenceItem],
        semantic_candidates: list[SemanticGuidelineCandidate],
        fallback_summary: str,
    ) -> ExplainabilitySummary:
        source_chunk_ids = [item.chunkId for item in semantic_evidence[:3]]
        source_ids = list(dict.fromkeys(item.sourceId for item in semantic_evidence[:5]))
        if not self._is_configured():
            return self._fallback(
                summary=fallback_summary,
                grounded=bool(semantic_evidence),
                source_chunk_ids=source_chunk_ids,
                source_ids=source_ids,
                provider_status="provider_unconfigured",
                prompt_version=SEMANTIC_PROMPT_VERSION,
                validation_status="not_attempted",
            )

        provider = settings.llm_provider.strip().lower()
        if provider != "gemini":
            return self._fallback(
                summary=fallback_summary,
                grounded=bool(semantic_evidence),
                source_chunk_ids=source_chunk_ids,
                source_ids=source_ids,
                provider_status="provider_unsupported",
                prompt_version=SEMANTIC_PROMPT_VERSION,
                validation_status="not_attempted",
            )

        prompt = (
            "You are a grounded explainability assistant for a clinical evidence benchmark.\n"
            "Use only the retrieved chunks and candidate topics below.\n"
            "Do not invent citations, treatment claims, or labels.\n"
            "Return strict JSON with keys summary, sourceChunkIds, sourceIds.\n\n"
            f"Vignette: {json.dumps(asdict(vignette), ensure_ascii=True, sort_keys=True)}\n"
            f"Semantic evidence: {json.dumps([asdict(item) for item in semantic_evidence[:5]], ensure_ascii=True)}\n"
            f"Semantic candidates: {json.dumps([asdict(item) for item in semantic_candidates[:3]], ensure_ascii=True)}\n"
            "Write 2 concise sentences explaining what the semantic retrieval clustered around and the leading guideline direction.\n"
            "All cited sourceChunkIds/sourceIds must be drawn from the provided evidence only."
        )

        try:
            raw_payload, latency_ms = self._gemini_json(prompt=prompt)
            result = self._extract_json_candidate(raw_payload)
            summary, chunk_ids, validated_source_ids = self._validate_grounded_payload(
                result=result,
                allowed_chunk_ids={item.chunkId for item in semantic_evidence},
                allowed_source_ids={item.sourceId for item in semantic_evidence},
            )
            return self._fallback(
                summary=summary,
                grounded=True,
                source_chunk_ids=chunk_ids or source_chunk_ids,
                source_ids=validated_source_ids or source_ids,
                provider_status="llm_grounded",
                prompt_version=SEMANTIC_PROMPT_VERSION,
                validation_status="passed",
                latency_ms=latency_ms,
            )
        except Exception:
            return self._fallback(
                summary=fallback_summary,
                grounded=bool(semantic_evidence),
                source_chunk_ids=source_chunk_ids,
                source_ids=source_ids,
                provider_status="provider_error",
                prompt_version=SEMANTIC_PROMPT_VERSION,
                validation_status="failed",
            )

    def summarize_benchmark(
        self,
        *,
        pack_label: str,
        headline: str,
        case_summaries: list[dict],
        fallback_summary: str,
        llm_enabled: bool,
        timeout_s: int = 5,
    ) -> ExplainabilitySummary | None:
        if not llm_enabled:
            return self._fallback(
                summary=fallback_summary,
                grounded=True,
                source_chunk_ids=[],
                source_ids=[],
                provider_status="llm_disabled",
                prompt_version=BENCHMARK_PROMPT_VERSION,
                validation_status="not_attempted",
            )

        if not self._is_configured():
            return self._fallback(
                summary=fallback_summary,
                grounded=True,
                source_chunk_ids=[],
                source_ids=[],
                provider_status="provider_unconfigured",
                prompt_version=BENCHMARK_PROMPT_VERSION,
                validation_status="not_attempted",
            )

        provider = settings.llm_provider.strip().lower()
        if provider != "gemini":
            return self._fallback(
                summary=fallback_summary,
                grounded=True,
                source_chunk_ids=[],
                source_ids=[],
                provider_status="provider_unsupported",
                prompt_version=BENCHMARK_PROMPT_VERSION,
                validation_status="not_attempted",
            )

        prompt = (
            "You are a grounded benchmark narrator.\n"
            "Use only the structured benchmark facts below.\n"
            "Return strict JSON with keys summary, sourceChunkIds, sourceIds.\n"
            "summary must be 2 concise sentences about what changed and why it matters.\n"
            "sourceChunkIds and sourceIds must be empty arrays because this is run-level narration.\n\n"
            f"Pack: {pack_label}\n"
            f"Headline: {headline}\n"
            f"Case summaries: {json.dumps(case_summaries[:6], ensure_ascii=True)}"
        )

        try:
            raw_payload, latency_ms = self._gemini_json(prompt=prompt, timeout_s=timeout_s)
            result = self._extract_json_candidate(raw_payload)
            summary, chunk_ids, source_ids = self._validate_grounded_payload(
                result=result,
                allowed_chunk_ids=set(),
                allowed_source_ids=set(),
            )
            return self._fallback(
                summary=summary,
                grounded=True,
                source_chunk_ids=chunk_ids,
                source_ids=source_ids,
                provider_status="llm_grounded",
                prompt_version=BENCHMARK_PROMPT_VERSION,
                validation_status="passed",
                latency_ms=latency_ms,
            )
        except Exception:
            return self._fallback(
                summary=fallback_summary,
                grounded=True,
                source_chunk_ids=[],
                source_ids=[],
                provider_status="provider_error",
                prompt_version=BENCHMARK_PROMPT_VERSION,
                validation_status="failed",
            )

    def summarize_evidence_item(
        self,
        *,
        evidence_id: str,
        title: str,
        abstract: str | None,
        journal_title: str | None,
        publication_year: int | None,
        ers_total: int,
        ers_breakdown: dict,
        mapping_label: str,
        mapped_topic_title: str | None,
        applicability_note: str,
        citations: list[dict],
        llm_enabled: bool,
    ) -> EvidenceExplainability:
        fallback = self._fallback_evidence_explainability(
            evidence_id=evidence_id,
            abstract=abstract,
            citations=citations,
            ers_total=ers_total,
            ers_breakdown=ers_breakdown,
            mapping_label=mapping_label,
            mapped_topic_title=mapped_topic_title,
            applicability_note=applicability_note,
            provider_status="grounded_local" if llm_enabled else "llm_disabled",
            validation_status="not_attempted",
        )
        if not llm_enabled:
            return fallback

        if not self._is_configured():
            return self._fallback_evidence_explainability(
                evidence_id=evidence_id,
                abstract=abstract,
                citations=citations,
                ers_total=ers_total,
                ers_breakdown=ers_breakdown,
                mapping_label=mapping_label,
                mapped_topic_title=mapped_topic_title,
                applicability_note=applicability_note,
                provider_status="provider_unconfigured",
                validation_status="not_attempted",
            )

        provider = settings.llm_provider.strip().lower()
        if provider != "gemini":
            return self._fallback_evidence_explainability(
                evidence_id=evidence_id,
                abstract=abstract,
                citations=citations,
                ers_total=ers_total,
                ers_breakdown=ers_breakdown,
                mapping_label=mapping_label,
                mapped_topic_title=mapped_topic_title,
                applicability_note=applicability_note,
                provider_status="provider_unsupported",
                validation_status="not_attempted",
            )

        prompt = (
            "You are a grounded evidence explainability assistant for a clinical ranking UI.\n"
            "Use only the evidence metadata and citations below.\n"
            "Do not invent treatment claims, labels, recommendations, or sources.\n"
            "Return strict JSON with keys evidenceId, scoreRationale, studySummary, sourceAnchors.\n"
            "studySummary must contain objective, signal, takeaway.\n"
            "sourceAnchors must be 1 to 3 objects with sourceId, title, snippet, year.\n\n"
            f"Evidence ID: {evidence_id}\n"
            f"Title: {title}\n"
            f"Journal: {journal_title or 'Unknown'}\n"
            f"Publication year: {publication_year}\n"
            f"Abstract: {abstract or 'Unavailable'}\n"
            f"ERS total: {ers_total}\n"
            f"ERS breakdown: {json.dumps(ers_breakdown, ensure_ascii=True, sort_keys=True)}\n"
            f"Mapping label: {mapping_label}\n"
            f"Mapped topic title: {mapped_topic_title or 'None'}\n"
            f"Applicability note: {applicability_note}\n"
            f"Citations: {json.dumps(citations[:3], ensure_ascii=True)}\n"
            "scoreRationale must explain the assigned ERS using the provided breakdown and label context only.\n"
            "Write 4 concise sentences in plain English: one sentence each for Evidence Strength, Dataset Robustness, Source Credibility, and Recency.\n"
            "Each sentence must name the metric and explain why that subscore makes sense from the supplied metadata.\n"
            "If the metadata does not support a detail such as trial size, randomization, or journal prestige, do not mention it.\n"
            "Use the title, abstract, journal, year, citations, and applicability note to justify the score without inventing hidden scoring rules.\n"
            "studySummary must condense the study into UI-friendly Objective, Signal, and Takeaway lines.\n"
            "Every sourceAnchor sourceId must come from the provided citations only."
        )

        try:
            raw_payload, latency_ms = self._gemini_json(prompt=prompt)
            result = self._extract_json_candidate(raw_payload)
            explainability = self._validate_evidence_payload(
                result=result,
                evidence_id=evidence_id,
                allowed_source_ids={str(citation.get("sourceId", "")).strip() for citation in citations if str(citation.get("sourceId", "")).strip()},
            )
            explainability.provider = settings.llm_provider.strip() or None
            explainability.model = settings.llm_model.strip() or None
            explainability.latencyMs = latency_ms
            return explainability
        except Exception:
            return self._fallback_evidence_explainability(
                evidence_id=evidence_id,
                abstract=abstract,
                citations=citations,
                ers_total=ers_total,
                ers_breakdown=ers_breakdown,
                mapping_label=mapping_label,
                mapped_topic_title=mapped_topic_title,
                applicability_note=applicability_note,
                provider_status="provider_error",
                validation_status="failed",
            )

    def summarize_uncertainty_flags(
        self,
        *,
        uncertainty_flags: list[str],
        engine: str,
        top_evidence_count: int,
        manual_review_count: int,
        llm_enabled: bool,
    ) -> UncertaintyFlagsExplainability:
        fallback = self._fallback_uncertainty_flags_explainability(
            uncertainty_flags=uncertainty_flags,
            engine=engine,
            top_evidence_count=top_evidence_count,
            manual_review_count=manual_review_count,
            provider_status="grounded_local" if llm_enabled else "llm_disabled",
            validation_status="not_attempted",
        )
        if not llm_enabled:
            return fallback

        if not self._is_configured():
            return self._fallback_uncertainty_flags_explainability(
                uncertainty_flags=uncertainty_flags,
                engine=engine,
                top_evidence_count=top_evidence_count,
                manual_review_count=manual_review_count,
                provider_status="provider_unconfigured",
                validation_status="not_attempted",
            )

        provider = settings.llm_provider.strip().lower()
        if provider not in {"gemini", "openrouter"}:
            return self._fallback_uncertainty_flags_explainability(
                uncertainty_flags=uncertainty_flags,
                engine=engine,
                top_evidence_count=top_evidence_count,
                manual_review_count=manual_review_count,
                provider_status="provider_unsupported",
                validation_status="not_attempted",
            )

        prompt = (
            "You are a grounded UI explainability assistant for a clinical evidence triage tool.\n"
            "Use only the structured run facts below.\n"
            "Do not invent clinical claims, recommendations, or hidden scoring rules.\n"
            "Return strict JSON with keys summary, whyFlagsExist, whatItMeans, flags.\n"
            "Write plain-English copy for a wide hover tooltip.\n"
            "summary should explain what uncertainty flags are doing in this run.\n"
            "whyFlagsExist should explain why the product surfaces them at all.\n"
            "whatItMeans should explain how the operator should interpret them without overstating risk.\n"
            "flags must echo only the provided uncertainty flags.\n\n"
            f"Runtime engine: {engine}\n"
            f"Top evidence count: {top_evidence_count}\n"
            f"Manual review count: {manual_review_count}\n"
            f"Uncertainty flags: {json.dumps(uncertainty_flags, ensure_ascii=True)}\n"
            "Do not mention any source or fact that is not present in the supplied run metadata."
        )

        try:
            if provider == "openrouter":
                raw_payload, latency_ms = self._openrouter_json(
                    prompt=prompt,
                    schema_name="uncertainty_flags_explainability",
                    schema=self._OPENROUTER_TOOLTIP_SCHEMA,
                )
                result = self._extract_openrouter_json_candidate(raw_payload)
            else:
                raw_payload, latency_ms = self._gemini_json(prompt=prompt)
                result = self._extract_json_candidate(raw_payload)
            explainability = self._validate_uncertainty_flags_payload(
                result=result,
                allowed_flags=set(uncertainty_flags),
            )
            explainability.provider = settings.llm_provider.strip() or None
            explainability.model = settings.llm_model.strip() or None
            explainability.latencyMs = latency_ms
            if not explainability.flags:
                explainability.flags = list(uncertainty_flags)
            return explainability
        except Exception:
            return self._fallback_uncertainty_flags_explainability(
                uncertainty_flags=uncertainty_flags,
                engine=engine,
                top_evidence_count=top_evidence_count,
                manual_review_count=manual_review_count,
                provider_status="provider_error",
                validation_status="failed",
            )


llm_explainability_service = LlmExplainabilityService()
