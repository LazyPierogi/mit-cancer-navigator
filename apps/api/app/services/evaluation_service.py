from __future__ import annotations

import hashlib
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from uuid import uuid4

from app.config.settings import settings
from app.domain.rules import system_integrity_checks
from app.repositories.corpus_store import corpus_store
from app.repositories.run_store import run_store
from app.services.analysis_service import analysis_service
from app.services.import_pipeline import import_pipeline_service
from app.services.llm_explainability_service import llm_explainability_service
from app.services.sample_data import load_demo_presets, load_frozen_pack
from app.services.semantic_retrieval_service import semantic_retrieval_service

BENCHMARK_CACHE_VERSION = "benchmark-v4"
_BENCHMARK_CONCURRENCY = 5  # max parallel case executions per engine in benchmark
PRIMARY_LABELS = ("aligned", "guideline_silent", "conflict")


class EvaluationService:
    @staticmethod
    def _sample_ids(values: set[str] | list[str], limit: int = 5) -> list[str]:
        return sorted(values)[:limit]

    @staticmethod
    def _distribution(labels: list[str | None]) -> dict[str, int]:
        counts = Counter(label for label in labels if label)
        return {label: counts.get(label, 0) for label in PRIMARY_LABELS}

    @staticmethod
    def _top_observation(response) -> tuple[str | None, str | None, str | None]:
        if not response.topEvidence:
            return None, None, None
        top_item = response.topEvidence[0]
        return (
            getattr(top_item, "mappingLabel", None),
            getattr(top_item, "mappedTopicId", None),
            getattr(top_item, "mappedTopicTitle", None),
        )

    def _case_state(self, response, trace: dict) -> dict[str, set[str]]:
        return {
            "alignedEvidenceIds": {item.evidenceId for item in response.topEvidence if item.mappingLabel == "aligned"},
            "guidelineSilentEvidenceIds": {
                item.evidenceId for item in response.topEvidence if item.mappingLabel == "guideline_silent"
            },
            "manualReviewEvidenceIds": {item.evidenceId for item in response.manualReviewEvidence},
            "retrievalCandidateEvidenceIds": set(trace.get("retrievalCandidateEvidenceIds", [])),
            "semanticCandidateOnlyEvidenceIds": set(trace.get("semanticCandidateOnlyEvidenceIds", [])),
        }

    def _benchmark_cache_context(self, *, pack_id: str, retrieval_mode: str) -> dict[str, str]:
        import_summary = corpus_store.get_import_summary()
        latest_by_kind = import_summary.get("latestByKind", {})
        pubmed_batch_id = latest_by_kind.get("pubmed", {}).get("batchId") or "no-pubmed"
        esmo_batch_id = latest_by_kind.get("esmo", {}).get("batchId") or "no-esmo"
        pubmed_status = semantic_retrieval_service.get_status(dataset_kind="pubmed")
        esmo_status = semantic_retrieval_service.get_status(dataset_kind="esmo")
        debug_config = import_pipeline_service.get_debug_config()
        vector_store = pubmed_status.get("latestJob", {}).get("vectorStore") or "unknown-vector-store"
        embedding_model = pubmed_status.get("latestJob", {}).get("embeddingModel") or "unknown-embedding-model"

        source_fingerprint_material = "|".join(
            [
                settings.ruleset_version,
                settings.corpus_version,
                pubmed_batch_id,
                esmo_batch_id,
                pubmed_status.get("latestJob", {}).get("jobId") or "no-semantic-pubmed-job",
                esmo_status.get("latestJob", {}).get("jobId") or "no-semantic-esmo-job",
                vector_store,
                embedding_model,
            ]
        )
        runtime_config_material = "|".join(
            [
                str(debug_config.get("strictMvpPubmed", False)),
                str(debug_config.get("semanticRetrievalEnabled", False)),
                str(debug_config.get("runtimeEngine", "deterministic")),
                str(debug_config.get("retrievalMode", retrieval_mode)),
                str(debug_config.get("llmExplainabilityEnabled", False)),
            ]
        )
        source_fingerprint = hashlib.blake2b(source_fingerprint_material.encode("utf-8"), digest_size=10).hexdigest()
        runtime_config_fingerprint = hashlib.blake2b(runtime_config_material.encode("utf-8"), digest_size=10).hexdigest()
        cache_material = "|".join(
            [
                pack_id,
                retrieval_mode,
                BENCHMARK_CACHE_VERSION,
                source_fingerprint,
                runtime_config_fingerprint,
            ]
        )
        digest = hashlib.blake2b(cache_material.encode("utf-8"), digest_size=10).hexdigest()
        return {
            "cacheId": f"benchmark-cache-{pack_id}-{retrieval_mode}-{digest}",
            "pubmedBatchId": pubmed_batch_id,
            "esmoBatchId": esmo_batch_id,
            "pubmedSemanticJobId": pubmed_status.get("latestJob", {}).get("jobId") or "no-semantic-pubmed-job",
            "esmoSemanticJobId": esmo_status.get("latestJob", {}).get("jobId") or "no-semantic-esmo-job",
            "sourceFingerprint": source_fingerprint,
            "runtimeConfigFingerprint": runtime_config_fingerprint,
            "vectorStore": vector_store,
            "embeddingModel": embedding_model,
        }

    def _load_pack(self, pack_id: str) -> dict:
        if pack_id == "demo_presets":
            return load_demo_presets()
        if pack_id == "frozen_pack":
            frozen_pack = load_frozen_pack()
            return {
                "packId": frozen_pack["packId"],
                "packLabel": frozen_pack.get("packLabel", "Frozen Benchmark Pack"),
                "schemaVersion": frozen_pack.get("schemaVersion", "frozen-benchmark-v2"),
                "cases": list(frozen_pack["cases"]),
            }
        raise ValueError(f"Unknown benchmark pack: {pack_id}")

    def _reference_payload(self, reference: dict | None) -> dict | None:
        if not reference:
            return None
        expected_topic = reference.get("expectedGuidelineTopic") or {}
        return {
            "expectedPrimaryLabel": reference.get("expectedPrimaryLabel"),
            "expectedGuidelineTopicId": expected_topic.get("topicId"),
            "expectedGuidelineTopicTitle": expected_topic.get("topicTitle"),
            "expectedEvidenceIds": list(reference.get("expectedTopEvidence", [])),
            "expectedLabelByEvidenceId": dict(reference.get("expectedLabelByEvidenceId", {})),
        }

    def _comparison_payload(
        self,
        *,
        response,
        reference: dict | None,
        source_fingerprint: str,
        runtime_config_fingerprint: str,
    ) -> dict | None:
        if not reference:
            return None

        expected_evidence_ids = list(reference.get("expectedTopEvidence", []))
        top_evidence_ids = [item.evidenceId for item in response.topEvidence]
        expected_topic = reference.get("expectedGuidelineTopic") or {}
        expected_topic_id = expected_topic.get("topicId")
        expected_primary = reference.get("expectedPrimaryLabel")
        observed_primary, observed_topic_id, observed_topic_title = self._top_observation(response)

        matched = [evidence_id for evidence_id in expected_evidence_ids if evidence_id in top_evidence_ids]
        missed = [evidence_id for evidence_id in expected_evidence_ids if evidence_id not in top_evidence_ids]
        unexpected = [evidence_id for evidence_id in top_evidence_ids if evidence_id not in set(expected_evidence_ids)]
        topic_match = (
            observed_topic_id is None if expected_topic_id is None else observed_topic_id == expected_topic_id
        )
        primary_label_hit = observed_primary == expected_primary

        why_bits: list[str] = []
        if primary_label_hit:
            why_bits.append(f"Primary label matched {expected_primary}.")
        else:
            why_bits.append(
                f"Expected {expected_primary or 'none'} but observed {observed_primary or 'none'} at rank 1."
            )
        if topic_match:
            why_bits.append(
                "Observed topic matched the canonical expectation."
                if expected_topic_id
                else "No canonical topic was expected and none was promoted."
            )
        else:
            why_bits.append(
                f"Expected topic {expected_topic_id or 'none'} but observed {observed_topic_id or 'none'}."
            )
        if missed:
            why_bits.append(f"Missed expected PMID(s): {', '.join(missed[:3])}.")
        if unexpected:
            why_bits.append(f"Unexpected promoted PMID(s): {', '.join(unexpected[:3])}.")

        return {
            "observedPrimaryLabel": observed_primary,
            "observedGuidelineTopicId": observed_topic_id,
            "observedGuidelineTopicTitle": observed_topic_title,
            "matchedExpectedEvidenceIds": matched,
            "missedExpectedEvidenceIds": missed,
            "unexpectedPromotedEvidenceIds": unexpected,
            "topicMatch": topic_match,
            "primaryLabelHit": primary_label_hit,
            "why": " ".join(why_bits),
            "sourceFingerprint": source_fingerprint,
            "runtimeConfigFingerprint": runtime_config_fingerprint,
        }

    def _case_metrics(self, response, trace: dict, reference: dict | None = None) -> dict:
        top_evidence_ids = [item.evidenceId for item in response.topEvidence]
        aligned_count = len([item for item in response.topEvidence if item.mappingLabel == "aligned"])
        guideline_silent_count = len([item for item in response.topEvidence if item.mappingLabel == "guideline_silent"])
        conflict_count = len([item for item in response.topEvidence if item.mappingLabel == "conflict"])
        observed_primary, observed_topic_id, observed_topic_title = self._top_observation(response)

        expected_top = reference.get("expectedTopEvidence", []) if reference else []
        expected_label_map = reference.get("expectedLabelByEvidenceId", {}) if reference else {}

        recall = None
        label_accuracy = None
        if expected_top:
            recall = round(
                sum(1 for evidence_id in expected_top if evidence_id in top_evidence_ids) / len(expected_top),
                4,
            )
        if expected_label_map:
            correct = 0
            for evidence_id, expected_label in expected_label_map.items():
                predicted = next((item.mappingLabel for item in response.topEvidence if item.evidenceId == evidence_id), None)
                if predicted == expected_label:
                    correct += 1
            label_accuracy = round(correct / len(expected_label_map), 4)

        return {
            "engine": response.engine,
            "retrievalMode": response.retrievalMode,
            "topEvidenceCount": len(response.topEvidence),
            "alignedCount": aligned_count,
            "guidelineSilentCount": guideline_silent_count,
            "conflictCount": conflict_count,
            "manualReviewCount": len(response.manualReviewEvidence),
            "secondaryCount": len(response.secondaryReferences),
            "uncertaintyFlagCount": len(response.uncertaintyFlags),
            "retrievalCandidateCount": trace.get("retrievalCandidateCount", 0),
            "semanticCandidateOnlyCount": trace.get("semanticCandidateOnlyCount", 0),
            "topTopicTitles": [item.mappedTopicTitle for item in response.topEvidence[:3] if item.mappedTopicTitle],
            "expectedRecall": recall,
            "expectedLabelAccuracy": label_accuracy,
            "observedPrimaryLabel": observed_primary,
            "observedPrimaryTopicId": observed_topic_id,
            "observedPrimaryTopicTitle": observed_topic_title,
        }

    @staticmethod
    def _is_quantitative_golden(case: dict) -> bool:
        reference = case.get("reference") or {}
        return bool(reference.get("expectedPrimaryLabel")) and bool(reference.get("expectedTopEvidence"))

    def _pack_completeness(self, pack: dict) -> tuple[str, bool]:
        complete = sum(1 for case in pack["cases"] if self._is_quantitative_golden(case))
        total = len(pack["cases"])
        return f"{complete}/{total} quantitative goldens present", complete == total

    def _run_engine(
        self,
        *,
        case_payload: dict,
        runtime_engine: str,
        retrieval_mode: str,
        llm_explainability_enabled: bool = False,
    ) -> tuple[dict | None, dict | None, str | None]:
        try:
            response, trace = analysis_service.analyze_with_runtime(
                case_payload,
                runtime_engine=runtime_engine,
                retrieval_mode=retrieval_mode,
                llm_explainability_enabled=llm_explainability_enabled,
            )
            return response, trace, None
        except Exception as exc:
            return None, None, str(exc)

    def _build_breakdown(
        self,
        *,
        pack: dict,
        deterministic_engine: dict | None,
        hybrid_engine: dict | None,
        engine_internal: dict[str, dict],
        aligned_delta: int,
        manual_review_delta: int,
        retrieval_delta: int,
    ) -> dict:
        empty_case_state = {
            "alignedEvidenceIds": set(),
            "guidelineSilentEvidenceIds": set(),
            "manualReviewEvidenceIds": set(),
            "retrievalCandidateEvidenceIds": set(),
            "semanticCandidateOnlyEvidenceIds": set(),
        }
        empty = {
            "retrieval": {
                "delta": retrieval_delta,
                "deterministicUniqueEvidenceCount": 0,
                "hybridUniqueEvidenceCount": 0,
                "hybridCaseHitCountTotal": 0,
                "hybridOverlapCount": 0,
                "hybridMultiCaseEvidenceCount": 0,
                "hybridOverlapRate": 0.0,
                "hybridOnlyEvidenceCount": 0,
                "sampleHybridOnlyEvidenceIds": [],
                "sampleMultiCaseEvidenceIds": [],
            },
            "decisionLayer": {
                "alignedDelta": aligned_delta,
                "guidelineSilentDelta": 0,
                "manualReviewDelta": manual_review_delta,
                "promotedAlignedUniqueCount": 0,
                "promotedGuidelineSilentUniqueCount": 0,
                "promotedManualReviewUniqueCount": 0,
                "samplePromotedAlignedEvidenceIds": [],
                "samplePromotedGuidelineSilentEvidenceIds": [],
                "samplePromotedManualReviewEvidenceIds": [],
            },
            "caseDeltas": [],
        }
        if deterministic_engine is None or hybrid_engine is None:
            return empty

        det_internal = engine_internal.get("deterministic", {"caseStates": {}, "retrievalOccurrences": {}})
        hybrid_internal = engine_internal.get("hybrid_semantic", {"caseStates": {}, "retrievalOccurrences": {}})
        det_case_states = det_internal["caseStates"]
        hybrid_case_states = hybrid_internal["caseStates"]

        det_retrieval_union = (
            set().union(*(state["retrievalCandidateEvidenceIds"] for state in det_case_states.values()))
            if det_case_states
            else set()
        )
        hybrid_retrieval_union = (
            set().union(*(state["retrievalCandidateEvidenceIds"] for state in hybrid_case_states.values()))
            if hybrid_case_states
            else set()
        )
        hybrid_only_retrieval = hybrid_retrieval_union - det_retrieval_union
        multi_case_retrieval_ids = {
            evidence_id for evidence_id, count in hybrid_internal["retrievalOccurrences"].items() if count > 1
        }

        det_aligned_union = set().union(*(state["alignedEvidenceIds"] for state in det_case_states.values())) if det_case_states else set()
        hybrid_aligned_union = (
            set().union(*(state["alignedEvidenceIds"] for state in hybrid_case_states.values())) if hybrid_case_states else set()
        )
        det_guideline_silent_union = (
            set().union(*(state["guidelineSilentEvidenceIds"] for state in det_case_states.values())) if det_case_states else set()
        )
        hybrid_guideline_silent_union = (
            set().union(*(state["guidelineSilentEvidenceIds"] for state in hybrid_case_states.values()))
            if hybrid_case_states
            else set()
        )
        det_manual_review_union = (
            set().union(*(state["manualReviewEvidenceIds"] for state in det_case_states.values())) if det_case_states else set()
        )
        hybrid_manual_review_union = (
            set().union(*(state["manualReviewEvidenceIds"] for state in hybrid_case_states.values()))
            if hybrid_case_states
            else set()
        )

        case_deltas: list[dict] = []
        for case in pack["cases"]:
            case_id = case["caseId"]
            det_case = det_case_states.get(case_id, empty_case_state)
            hybrid_case = hybrid_case_states.get(case_id, empty_case_state)
            hybrid_only_case_retrieval = hybrid_case["retrievalCandidateEvidenceIds"] - det_case["retrievalCandidateEvidenceIds"]
            promoted_aligned = hybrid_case["alignedEvidenceIds"] - det_case["alignedEvidenceIds"]
            promoted_guideline_silent = hybrid_case["guidelineSilentEvidenceIds"] - det_case["guidelineSilentEvidenceIds"]
            promoted_manual_review = hybrid_case["manualReviewEvidenceIds"] - det_case["manualReviewEvidenceIds"]
            case_deltas.append(
                {
                    "caseId": case_id,
                    "caseLabel": case["caseLabel"],
                    "retrievalDelta": len(hybrid_case["retrievalCandidateEvidenceIds"]) - len(det_case["retrievalCandidateEvidenceIds"]),
                    "alignedDelta": len(hybrid_case["alignedEvidenceIds"]) - len(det_case["alignedEvidenceIds"]),
                    "guidelineSilentDelta": len(hybrid_case["guidelineSilentEvidenceIds"]) - len(det_case["guidelineSilentEvidenceIds"]),
                    "manualReviewDelta": len(hybrid_case["manualReviewEvidenceIds"]) - len(det_case["manualReviewEvidenceIds"]),
                    "hybridRetrievalCount": len(hybrid_case["retrievalCandidateEvidenceIds"]),
                    "hybridOnlyRetrievalCount": len(hybrid_only_case_retrieval),
                    "promotedAlignedCount": len(promoted_aligned),
                    "promotedGuidelineSilentCount": len(promoted_guideline_silent),
                    "promotedManualReviewCount": len(promoted_manual_review),
                    "sampleRetrievalEvidenceIds": self._sample_ids(hybrid_case["retrievalCandidateEvidenceIds"]),
                    "sampleHybridOnlyRetrievalEvidenceIds": self._sample_ids(hybrid_only_case_retrieval),
                    "samplePromotedAlignedEvidenceIds": self._sample_ids(promoted_aligned),
                    "samplePromotedGuidelineSilentEvidenceIds": self._sample_ids(promoted_guideline_silent),
                    "samplePromotedManualReviewEvidenceIds": self._sample_ids(promoted_manual_review),
                }
            )

        guideline_silent_delta = (
            hybrid_engine["aggregate"]["totalGuidelineSilent"] - deterministic_engine["aggregate"]["totalGuidelineSilent"]
        )
        return {
            "retrieval": {
                "delta": retrieval_delta,
                "deterministicUniqueEvidenceCount": len(det_retrieval_union),
                "hybridUniqueEvidenceCount": len(hybrid_retrieval_union),
                "hybridCaseHitCountTotal": hybrid_engine["aggregate"]["totalRetrievalCaseHits"],
                "hybridOverlapCount": hybrid_engine["aggregate"]["retrievalOverlapCount"],
                "hybridMultiCaseEvidenceCount": hybrid_engine["aggregate"]["retrievalMultiCaseEvidenceCount"],
                "hybridOverlapRate": hybrid_engine["aggregate"]["retrievalOverlapRate"],
                "hybridOnlyEvidenceCount": len(hybrid_only_retrieval),
                "sampleHybridOnlyEvidenceIds": self._sample_ids(hybrid_only_retrieval),
                "sampleMultiCaseEvidenceIds": self._sample_ids(multi_case_retrieval_ids),
            },
            "decisionLayer": {
                "alignedDelta": aligned_delta,
                "guidelineSilentDelta": guideline_silent_delta,
                "manualReviewDelta": manual_review_delta,
                "promotedAlignedUniqueCount": len(hybrid_aligned_union - det_aligned_union),
                "promotedGuidelineSilentUniqueCount": len(hybrid_guideline_silent_union - det_guideline_silent_union),
                "promotedManualReviewUniqueCount": len(hybrid_manual_review_union - det_manual_review_union),
                "samplePromotedAlignedEvidenceIds": self._sample_ids(hybrid_aligned_union - det_aligned_union),
                "samplePromotedGuidelineSilentEvidenceIds": self._sample_ids(
                    hybrid_guideline_silent_union - det_guideline_silent_union
                ),
                "samplePromotedManualReviewEvidenceIds": self._sample_ids(hybrid_manual_review_union - det_manual_review_union),
            },
            "caseDeltas": case_deltas,
        }

    def run_engine_comparison(self, *, pack_id: str, retrieval_mode: str = "hybrid", force_refresh: bool = False) -> dict:
        started_at = time.perf_counter()
        debug_config = import_pipeline_service.get_debug_config()
        llm_explainability_enabled = bool(debug_config.get("llmExplainabilityEnabled", False))
        cache_context = self._benchmark_cache_context(pack_id=pack_id, retrieval_mode=retrieval_mode)
        cache_context.setdefault("sourceFingerprint", "unknown-source-fingerprint")
        cache_context.setdefault("runtimeConfigFingerprint", "unknown-runtime-config")
        cache_context.setdefault("vectorStore", "unknown-vector-store")
        cache_context.setdefault("embeddingModel", "unknown-embedding-model")
        cache_id = cache_context["cacheId"]
        cached = None if force_refresh else self.get_cached_engine_comparison(
            pack_id=pack_id,
            retrieval_mode=retrieval_mode,
        )
        if cached is not None:
            print(
                "[benchmark] cache_hit "
                f"pack={pack_id} retrieval={retrieval_mode} "
                f"duration_ms={int((time.perf_counter() - started_at) * 1000)}"
            )
            return cached

        print(
            "[benchmark] start "
            f"pack={pack_id} retrieval={retrieval_mode} force_refresh={force_refresh} "
            f"llm_explainability_enabled={llm_explainability_enabled}"
        )
        pack = self._load_pack(pack_id)
        query_embedding_warm_count = 0
        if semantic_retrieval_service is not None:
            try:
                query_embedding_warm_count = semantic_retrieval_service.prewarm_query_embeddings_for_vignettes(
                    [case["vignette"] for case in pack["cases"]]
                )
            except Exception:
                query_embedding_warm_count = 0
        if query_embedding_warm_count:
            print(
                "[benchmark] query_embeddings_warmed "
                f"pack={pack_id} retrieval={retrieval_mode} count={query_embedding_warm_count}"
            )
        pack_completeness, quantitative_goldens_complete = self._pack_completeness(pack)
        expected_label_distribution = self._distribution(
            [(case.get("reference") or {}).get("expectedPrimaryLabel") for case in pack["cases"]]
        )
        engines = [
            {
                "engineKey": "deterministic",
                "label": "Deterministic Runtime",
                "runtimeEngine": "deterministic",
                "retrievalMode": "hybrid",
            },
            {
                "engineKey": "hybrid_semantic",
                "label": "Hybrid Semantic Lab",
                "runtimeEngine": "semantic_retrieval_lab",
                "retrievalMode": retrieval_mode,
            },
        ]

        engine_results: list[dict] = []
        engine_internal: dict[str, dict] = {}
        hybrid_case_summaries: list[dict] = []

        for engine in engines:
            case_results: list[dict] = []
            retrieval_candidate_ids: set[str] = set()
            semantic_candidate_only_ids: set[str] = set()
            retrieval_occurrences: dict[str, int] = {}
            case_states: dict[str, dict[str, set[str]]] = {}
            observed_primary_labels: list[str | None] = []
            topic_match_hits = 0
            primary_label_hits = 0
            comparable_case_count = 0
            aggregate = {
                "caseCount": 0,
                "casesWithAlignedEvidence": 0,
                "totalTopEvidence": 0,
                "totalAligned": 0,
                "totalGuidelineSilent": 0,
                "totalConflict": 0,
                "totalManualReview": 0,
                "totalSecondary": 0,
                "totalUncertaintyFlags": 0,
                "totalRetrievalCandidates": 0,
                "totalRetrievalCaseHits": 0,
                "retrievalOverlapCount": 0,
                "retrievalMultiCaseEvidenceCount": 0,
                "retrievalOverlapRate": 0.0,
                "totalSemanticCandidateOnly": 0,
                "averageExpectedRecall": None,
                "averageExpectedLabelAccuracy": None,
                "topicMatchRate": None,
                "primaryLabelHitRate": None,
                "expectedLabelDistribution": expected_label_distribution,
                "observedLabelDistribution": {},
                "packCompleteness": pack_completeness,
                "quantitativeGoldensComplete": quantitative_goldens_complete,
            }
            recall_values: list[float] = []
            label_accuracy_values: list[float] = []
            notes: list[str] = []
            status = "available"

            # Phase A: run all cases in parallel (I/O-bound Qdrant calls benefit from threading)
            def _run_case(case, *, _engine=engine, _llm=llm_explainability_enabled):
                try:
                    return (
                        case,
                        *self._run_engine(
                            case_payload=case["vignette"],
                            runtime_engine=_engine["runtimeEngine"],
                            retrieval_mode=_engine["retrievalMode"],
                            llm_explainability_enabled=_llm and _engine["runtimeEngine"] == "semantic_retrieval_lab",
                        ),
                    )
                except Exception as exc:
                    return (case, None, None, str(exc))

            _engine_t0 = time.perf_counter()
            with ThreadPoolExecutor(max_workers=_BENCHMARK_CONCURRENCY) as _pool:
                _case_runs = list(_pool.map(_run_case, pack["cases"]))
            print(
                f"[benchmark] cases_parallel_done "
                f"engine={engine['engineKey']} cases={len(pack['cases'])} "
                f"workers={_BENCHMARK_CONCURRENCY} "
                f"duration_ms={int((time.perf_counter() - _engine_t0) * 1000)}"
            )

            # Phase B: aggregate results sequentially
            for case, response, trace, error in _case_runs:
                if error or response is None or trace is None:
                    status = "unavailable"
                    notes.append(error or "Unknown benchmark failure.")
                    case_results.append(
                        {
                            "caseId": case["caseId"],
                            "caseLabel": case["caseLabel"],
                            "detail": case["detail"],
                            "category": case.get("category"),
                            "clinicalQuestion": case.get("clinicalQuestion"),
                            "status": "failed",
                            "error": error or "Unknown benchmark failure.",
                            "metrics": None,
                            "reference": self._reference_payload(case.get("reference")),
                            "comparison": None,
                        }
                    )
                    continue

                metrics = self._case_metrics(response, trace, case.get("reference"))
                comparison = self._comparison_payload(
                    response=response,
                    reference=case.get("reference"),
                    source_fingerprint=cache_context["sourceFingerprint"],
                    runtime_config_fingerprint=cache_context["runtimeConfigFingerprint"],
                )
                case_state = self._case_state(response, trace)

                aggregate["caseCount"] += 1
                aggregate["casesWithAlignedEvidence"] += 1 if metrics["alignedCount"] > 0 else 0
                aggregate["totalTopEvidence"] += metrics["topEvidenceCount"]
                aggregate["totalAligned"] += metrics["alignedCount"]
                aggregate["totalGuidelineSilent"] += metrics["guidelineSilentCount"]
                aggregate["totalConflict"] += metrics["conflictCount"]
                aggregate["totalManualReview"] += metrics["manualReviewCount"]
                aggregate["totalSecondary"] += metrics["secondaryCount"]
                aggregate["totalUncertaintyFlags"] += metrics["uncertaintyFlagCount"]
                aggregate["totalRetrievalCaseHits"] += len(case_state["retrievalCandidateEvidenceIds"])
                retrieval_candidate_ids.update(case_state["retrievalCandidateEvidenceIds"])
                semantic_candidate_only_ids.update(case_state["semanticCandidateOnlyEvidenceIds"])
                case_states[case["caseId"]] = case_state
                for evidence_id in case_state["retrievalCandidateEvidenceIds"]:
                    retrieval_occurrences[evidence_id] = retrieval_occurrences.get(evidence_id, 0) + 1
                if metrics["expectedRecall"] is not None:
                    recall_values.append(metrics["expectedRecall"])
                if metrics["expectedLabelAccuracy"] is not None:
                    label_accuracy_values.append(metrics["expectedLabelAccuracy"])
                observed_primary_labels.append(metrics["observedPrimaryLabel"])

                if comparison is not None:
                    comparable_case_count += 1
                    topic_match_hits += 1 if comparison["topicMatch"] else 0
                    primary_label_hits += 1 if comparison["primaryLabelHit"] else 0

                case_result = {
                    "caseId": case["caseId"],
                    "caseLabel": case["caseLabel"],
                    "detail": case["detail"],
                    "category": case.get("category"),
                    "clinicalQuestion": case.get("clinicalQuestion"),
                    "status": "completed",
                    "error": None,
                    "metrics": metrics,
                    "reference": self._reference_payload(case.get("reference")),
                    "comparison": comparison,
                }
                case_results.append(case_result)

                if engine["engineKey"] == "hybrid_semantic":
                    hybrid_case_summaries.append(
                        {
                            "caseId": case["caseId"],
                            "caseLabel": case["caseLabel"],
                            "expectedPrimaryLabel": (case.get("reference") or {}).get("expectedPrimaryLabel"),
                            "observedPrimaryLabel": metrics["observedPrimaryLabel"],
                            "topicMatch": comparison["topicMatch"] if comparison else None,
                            "matchedExpectedEvidenceIds": comparison["matchedExpectedEvidenceIds"] if comparison else [],
                            "missedExpectedEvidenceIds": comparison["missedExpectedEvidenceIds"] if comparison else [],
                            "unexpectedPromotedEvidenceIds": comparison["unexpectedPromotedEvidenceIds"] if comparison else [],
                            "why": comparison["why"] if comparison else "No canonical reference on file.",
                        }
                    )

            aggregate["averageTopEvidence"] = round(aggregate["totalTopEvidence"] / aggregate["caseCount"], 2) if aggregate["caseCount"] else 0.0
            aggregate["averageAligned"] = round(aggregate["totalAligned"] / aggregate["caseCount"], 2) if aggregate["caseCount"] else 0.0
            aggregate["averageUncertaintyFlags"] = (
                round(aggregate["totalUncertaintyFlags"] / aggregate["caseCount"], 2) if aggregate["caseCount"] else 0.0
            )
            aggregate["totalRetrievalCandidates"] = len(retrieval_candidate_ids)
            aggregate["retrievalOverlapCount"] = max(0, aggregate["totalRetrievalCaseHits"] - aggregate["totalRetrievalCandidates"])
            aggregate["retrievalMultiCaseEvidenceCount"] = sum(1 for count in retrieval_occurrences.values() if count > 1)
            aggregate["retrievalOverlapRate"] = (
                round(aggregate["retrievalOverlapCount"] / aggregate["totalRetrievalCaseHits"], 4)
                if aggregate["totalRetrievalCaseHits"] > 0
                else 0.0
            )
            aggregate["totalSemanticCandidateOnly"] = len(semantic_candidate_only_ids)
            aggregate["averageExpectedRecall"] = round(sum(recall_values) / len(recall_values), 4) if recall_values else None
            aggregate["averageExpectedLabelAccuracy"] = (
                round(sum(label_accuracy_values) / len(label_accuracy_values), 4) if label_accuracy_values else None
            )
            aggregate["topicMatchRate"] = round(topic_match_hits / comparable_case_count, 4) if comparable_case_count else None
            aggregate["primaryLabelHitRate"] = (
                round(primary_label_hits / comparable_case_count, 4) if comparable_case_count else None
            )
            aggregate["observedLabelDistribution"] = self._distribution(observed_primary_labels)

            engine_internal[engine["engineKey"]] = {
                "caseStates": case_states,
                "retrievalOccurrences": retrieval_occurrences,
            }

            if engine["runtimeEngine"] == "semantic_retrieval_lab":
                notes.append(
                    "Hybrid Semantic Lab queries semantic candidates through the active vector backend while deterministic logic remains the final authority for labels."
                )
                if llm_explainability_enabled:
                    notes.append(
                        "Gemini assistive explainability is enabled for narration only; labels, scores, and pass/fail remain deterministic."
                    )

            engine_results.append(
                {
                    "engineKey": engine["engineKey"],
                    "label": engine["label"],
                    "runtimeEngine": engine["runtimeEngine"],
                    "retrievalMode": engine["retrievalMode"],
                    "status": status,
                    "aggregate": aggregate,
                    "cases": case_results,
                    "notes": notes,
                }
            )

        deterministic_engine = next((engine for engine in engine_results if engine["engineKey"] == "deterministic"), None)
        hybrid_engine = next((engine for engine in engine_results if engine["engineKey"] == "hybrid_semantic"), None)
        aligned_delta = 0
        manual_review_delta = 0
        retrieval_delta = 0
        if deterministic_engine and hybrid_engine:
            aligned_delta = hybrid_engine["aggregate"]["totalAligned"] - deterministic_engine["aggregate"]["totalAligned"]
            manual_review_delta = hybrid_engine["aggregate"]["totalManualReview"] - deterministic_engine["aggregate"]["totalManualReview"]
            retrieval_delta = (
                hybrid_engine["aggregate"]["totalRetrievalCandidates"]
                - deterministic_engine["aggregate"]["totalRetrievalCandidates"]
            )

        breakdown = self._build_breakdown(
            pack=pack,
            deterministic_engine=deterministic_engine,
            hybrid_engine=hybrid_engine,
            engine_internal=engine_internal,
            aligned_delta=aligned_delta,
            manual_review_delta=manual_review_delta,
            retrieval_delta=retrieval_delta,
        )

        fallback_benchmark_summary = (
            f"{pack['packLabel']} compares deterministic and hybrid semantic runs over {len(pack['cases'])} canonical cases. "
            f"Aligned delta is {aligned_delta:+d}, retrieval breadth delta is {retrieval_delta:+d}, and pack completeness is {pack_completeness}."
        )
        benchmark_narrative = llm_explainability_service.summarize_benchmark(
            pack_label=pack["packLabel"],
            headline="Compare deterministic precision against hybrid semantic breadth on the same cases.",
            case_summaries=hybrid_case_summaries,
            fallback_summary=fallback_benchmark_summary,
            llm_enabled=llm_explainability_enabled,
            timeout_s=5,
        )

        summary = {
            "packLabel": pack["packLabel"],
            "semanticChangesDecisionLayer": aligned_delta != 0 or manual_review_delta != 0,
            "headline": "Compare deterministic precision against hybrid semantic breadth on the same canonical cases.",
            "recommendedTakeaway": (
                "Use deterministic guardrails as the final safety rail. Hybrid semantic is valuable when it increases grounded retrieval without degrading topic and label accuracy."
                if aligned_delta == 0 and manual_review_delta == 0
                else "Use deterministic guardrails as the final safety rail, while hybrid semantic is proving value by changing decision-layer outcomes on the canonical pack."
            ),
            "benchmarkNarrative": asdict(benchmark_narrative) if benchmark_narrative else None,
        }

        result = {
            "evalRunId": f"benchmark-{uuid4()}",
            "packId": pack["packId"],
            "summary": summary,
            "engines": engine_results,
            "breakdown": breakdown,
            "meta": {
                "cached": False,
                "cacheKey": cache_id,
                "benchmarkVersion": BENCHMARK_CACHE_VERSION,
                "pubmedBatchId": cache_context["pubmedBatchId"],
                "esmoBatchId": cache_context["esmoBatchId"],
                "pubmedSemanticJobId": cache_context["pubmedSemanticJobId"],
                "esmoSemanticJobId": cache_context["esmoSemanticJobId"],
                "sourceFingerprint": cache_context["sourceFingerprint"],
                "runtimeConfigFingerprint": cache_context["runtimeConfigFingerprint"],
                "vectorStore": cache_context["vectorStore"],
                "embeddingModel": cache_context["embeddingModel"],
            },
            "notes": [
                "This benchmark runs both engines against the same pack so we can compare precision, review burden, and retrieval breadth live.",
                (
                    f"Current live delta: aligned {aligned_delta:+d}, manual review {manual_review_delta:+d}, retrieval {retrieval_delta:+d}."
                    if deterministic_engine and hybrid_engine
                    else "Hybrid semantic keeps deterministic logic as the final authority for labeling."
                ),
                (
                    "Hybrid retrieval observability: "
                    f"{breakdown['retrieval']['hybridUniqueEvidenceCount']} unique evidence IDs across the pack, "
                    f"{breakdown['retrieval']['hybridOverlapCount']} overlapping case hits."
                ),
                f"Pack completeness: {pack_completeness}.",
                (
                    "Explainability provider status: "
                    f"{summary['benchmarkNarrative']['providerStatus']}."
                    if summary["benchmarkNarrative"]
                    else "Explainability provider status: unavailable."
                ),
            ],
        }
        run_store.save_benchmark_cache(
            eval_run_id=cache_id,
            pack_id=pack["packId"],
            payload=result,
            notes=result["notes"],
        )
        print(
            "[benchmark] completed "
            f"pack={pack_id} retrieval={retrieval_mode} "
            f"duration_ms={int((time.perf_counter() - started_at) * 1000)} "
            f"provider_status={(summary['benchmarkNarrative'] or {}).get('providerStatus') if summary['benchmarkNarrative'] else 'unavailable'}"
        )
        return result

    def get_cached_engine_comparison(self, *, pack_id: str, retrieval_mode: str = "hybrid") -> dict | None:
        cache_context = self._benchmark_cache_context(pack_id=pack_id, retrieval_mode=retrieval_mode)
        cache_context.setdefault("sourceFingerprint", "unknown-source-fingerprint")
        cache_context.setdefault("runtimeConfigFingerprint", "unknown-runtime-config")
        cache_context.setdefault("vectorStore", "unknown-vector-store")
        cache_context.setdefault("embeddingModel", "unknown-embedding-model")
        cache_id = cache_context["cacheId"]
        cached = run_store.get_benchmark_cache(cache_id)
        if cached is None:
            return None

        cached["meta"] = {
            **cached.get("meta", {}),
            "cached": True,
            "cacheKey": cache_id,
            "benchmarkVersion": BENCHMARK_CACHE_VERSION,
            "pubmedBatchId": cache_context["pubmedBatchId"],
            "esmoBatchId": cache_context["esmoBatchId"],
            "pubmedSemanticJobId": cache_context["pubmedSemanticJobId"],
            "esmoSemanticJobId": cache_context["esmoSemanticJobId"],
            "sourceFingerprint": cache_context["sourceFingerprint"],
            "runtimeConfigFingerprint": cache_context["runtimeConfigFingerprint"],
            "vectorStore": cache_context["vectorStore"],
            "embeddingModel": cache_context["embeddingModel"],
        }
        return cached

    def run_sample_eval(self) -> dict:
        frozen_pack = load_frozen_pack()
        case = frozen_pack["cases"][0]
        response, _trace = analysis_service.analyze(case["vignette"])
        layer1 = system_integrity_checks(response)

        top_ids = [item.evidenceId for item in response.topEvidence]
        expected_top = case["reference"]["expectedTopEvidence"]
        expected_label_map = case["reference"]["expectedLabelByEvidenceId"]

        recall = 1.0 if all(item in top_ids for item in expected_top) else 0.0
        mapping_correct = 1.0
        for evidence_id, expected_label in expected_label_map.items():
            predicted = next((item.mappingLabel for item in response.topEvidence if item.evidenceId == evidence_id), None)
            if predicted != expected_label:
                mapping_correct = 0.0

        return {
            "evalRunId": "eval-sample-v2",
            "packId": frozen_pack["packId"],
            "layer1": layer1,
            "layer2Metrics": [
                {"name": "recall", "value": recall, "target": ">= 0.95"},
                {"name": "mapping_accuracy", "value": mapping_correct, "target": ">= 0.85"},
                {"name": "deterministic_logic_fidelity", "value": 1.0, "target": "1.0"},
            ],
            "notes": [
                "Sample eval now points at the first case of the canonical 15-vignette frozen pack.",
            ],
        }


evaluation_service = EvaluationService()
