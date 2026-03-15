from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from .contracts import (
    AnalyzeRunResponse,
    Biomarkers,
    CitationRef,
    EvidenceRecord,
    GuidelineTopic,
    ManualReviewEvidenceItem,
    RunInfo,
    ScoreBreakdown,
    SecondaryReference,
    TopEvidenceItem,
    VignetteInput,
)


EVIDENCE_STRENGTH_SCORES = {
    "guideline": 35,
    "systematic_review": 35,
    "phase3_rct": 28,
    "phase2_rct": 20,
    "prospective_obs": 12,
    "retrospective": 8,
    "case_series": 6,
    "expert_opinion": 6,
    "unspecified": 6,
}

SOURCE_CREDIBILITY_SCORES = {
    "guideline_body": 25,
    "high_impact_journal": 20,
    "specialty_journal": 15,
    "preprint": 10,
    "industry_whitepaper": 5,
    None: 6,
}

MIN_STRUCTURED_FACETS_FOR_PRIMARY = 2
GENERIC_INTERVENTION_TAGS = {"therapy", "chemotherapy", "immunotherapy", "ici", "targeted"}

TAG_SYNONYMS = {
    "chemotherapy": {"chemotherapy", "chemo"},
    "chemo": {"chemotherapy", "chemo"},
    "platinum-doublet": {"platinum-doublet", "platinum_doublet", "chemotherapy", "chemo"},
    "platinum_doublet": {"platinum-doublet", "platinum_doublet", "chemotherapy", "chemo"},
    "chemo-ici": {"chemo-ici", "chemo_ici_combo", "immunotherapy-chemo-combo", "ici", "chemotherapy", "platinum-doublet"},
    "chemo_ici_combo": {"chemo-ici", "chemo_ici_combo", "immunotherapy-chemo-combo", "ici", "chemotherapy", "platinum-doublet"},
    "immunotherapy-chemo-combo": {"chemo-ici", "chemo_ici_combo", "immunotherapy-chemo-combo", "ici", "chemotherapy", "platinum-doublet"},
    "immunotherapy": {"immunotherapy", "ici"},
    "ici": {"immunotherapy", "ici"},
    "egfr-tki": {"egfr-tki", "egfr", "tki", "targeted"},
    "egfr-targeted": {"egfr-targeted", "egfr", "tki", "targeted"},
    "alk": {"alk", "targeted"},
    "ros1": {"ros1", "targeted"},
    "ret": {"ret", "targeted"},
    "ntrk": {"ntrk", "targeted"},
    "met": {"met", "targeted"},
    "her2": {"her2", "targeted"},
    "kras": {"kras", "targeted"},
    "kras-g12c": {"kras-g12c", "kras", "targeted"},
    "egfr-ex20ins": {"egfr-ex20ins", "egfr", "targeted"},
    "amivantamab": {"amivantamab", "targeted"},
    "atezolizumab": {"atezolizumab", "pdl1", "pd1", "ici", "immunotherapy-monotherapy"},
    "durvalumab": {"durvalumab", "pdl1", "pd1", "ici", "immunotherapy-monotherapy"},
    "cemiplimab": {"cemiplimab", "pd1", "ici", "immunotherapy-monotherapy"},
    "pembrolizumab": {"pembrolizumab", "pembro", "pd1", "ici", "immunotherapy-monotherapy"},
    "nivolumab": {"nivolumab", "nivo", "pd1", "ici"},
    "ipilimumab": {"ipilimumab", "ipi", "ctla4", "dual-ici"},
    "docetaxel": {"docetaxel", "single-agent-chemo", "single_agent_chemo", "taxane"},
}

FORBIDDEN_LANGUAGE = (
    "recommend treatment",
    "should receive",
    "prescribe",
    "approved for this patient",
)

PDL1_BUCKET_ORDER = {
    "lt1": 0,
    "1to49": 1,
    "ge50": 2,
    "any": 3,
    "unspecified": -1,
}

PERFORMANCE_STATUS_ORDER = {str(index): index for index in range(5)}


def biomarker_dict(vignette: VignetteInput) -> dict[str, str]:
    markers: Biomarkers = vignette.biomarkers
    return {
        "EGFR": markers.EGFR,
        "ALK": markers.ALK,
        "ROS1": markers.ROS1,
        "PDL1Bucket": markers.PDL1Bucket,
        "BRAF": markers.BRAF,
        "RET": markers.RET,
        "MET": markers.MET,
        "KRAS": markers.KRAS,
        "NTRK": markers.NTRK,
        "HER2": markers.HER2,
        "EGFRExon20ins": markers.EGFRExon20ins,
    }


def abstract_preview(abstract: str | None, *, word_limit: int = 20) -> str | None:
    if not abstract:
        return None
    words = abstract.split()
    preview = " ".join(words[:word_limit]).strip()
    return preview or None


def build_citation(record: EvidenceRecord) -> CitationRef:
    return CitationRef(
        sourceId=record.evidenceId,
        title=record.title,
        summary=abstract_preview(record.abstract),
        year=record.publicationYear,
    )


def histology_matches(candidate: str, expected: str) -> bool:
    if candidate == "unspecified" or expected == "unspecified":
        return True
    if candidate == expected:
        return True
    if candidate in {"mixed", "all_nsclc"} or expected in {"mixed", "all_nsclc"}:
        return True
    non_squamous_family = {"adenocarcinoma", "non_squamous"}
    return candidate in non_squamous_family and expected in non_squamous_family


def line_of_therapy_matches(candidate: str, expected: str) -> bool:
    if expected == "unspecified":
        return True
    return candidate in {expected, "mixed", "unspecified"}


def plain_context_matches(candidate: str, expected: str) -> bool:
    if expected in {"unspecified", "not_applicable"}:
        return True
    return candidate in {expected, "mixed", "unspecified"}


def relevance_gate(vignette: VignetteInput, evidence: EvidenceRecord) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if evidence.populationTags.disease != "NSCLC":
        reasons.append("disease_mismatch")

    if evidence.populationTags.diseaseSetting not in (vignette.diseaseSetting, "mixed", "unspecified"):
        reasons.append("setting_mismatch")

    if not histology_matches(evidence.populationTags.histology, vignette.histology):
        reasons.append("histology_mismatch")

    if not line_of_therapy_matches(evidence.populationTags.lineOfTherapy, vignette.lineOfTherapy):
        reasons.append("line_of_therapy_mismatch")

    if not plain_context_matches(evidence.populationTags.diseaseStage, vignette.diseaseStage):
        reasons.append("disease_stage_mismatch")

    if not plain_context_matches(evidence.populationTags.resectabilityStatus, vignette.resectabilityStatus):
        reasons.append("resectability_status_mismatch")

    if not plain_context_matches(evidence.populationTags.treatmentContext, vignette.treatmentContext):
        reasons.append("treatment_context_mismatch")

    if not plain_context_matches(evidence.populationTags.brainMetastases, vignette.clinicalModifiers.brainMetastases):
        reasons.append("brain_metastases_mismatch")

    for key, vignette_value in biomarker_dict(vignette).items():
        evidence_value = evidence.populationTags.biomarkers.get(key, "unspecified")
        if evidence_value not in ("unspecified", vignette_value):
            reasons.append(f"biomarker_mismatch:{key}")

    return (len(reasons) == 0, reasons)


def dataset_robustness_score(relevant_n: int | None) -> int:
    if relevant_n is None:
        return 6
    if relevant_n >= 300:
        return 25
    if relevant_n >= 100:
        return 18
    if relevant_n >= 50:
        return 12
    if relevant_n >= 20:
        return 8
    return 4


def recency_score(publication_year: int | None, current_year: int) -> int:
    if publication_year is None:
        return 0
    age = current_year - publication_year
    if age <= 1:
        return 15
    if age <= 5:
        return 12
    return 8


def compute_ers(evidence: EvidenceRecord, current_year: int) -> ScoreBreakdown:
    return ScoreBreakdown(
        evidenceStrength=EVIDENCE_STRENGTH_SCORES[evidence.evidenceType],
        datasetRobustness=dataset_robustness_score(evidence.relevantN),
        sourceCredibility=SOURCE_CREDIBILITY_SCORES[evidence.sourceCategory],
        recency=recency_score(evidence.publicationYear, current_year),
    )


def _subject_value(vignette: VignetteInput, key: str) -> str:
    if key in biomarker_dict(vignette):
        return biomarker_dict(vignette).get(key, "unspecified")
    if key == "diseaseSetting":
        return vignette.diseaseSetting
    if key == "histology":
        return vignette.histology
    if key == "lineOfTherapy":
        return vignette.lineOfTherapy
    if key == "diseaseStage":
        return vignette.diseaseStage
    if key == "resectabilityStatus":
        return vignette.resectabilityStatus
    if key == "treatmentContext":
        return vignette.treatmentContext
    if key == "brainMetastases":
        return vignette.clinicalModifiers.brainMetastases
    if key == "performanceStatus":
        return vignette.performanceStatus
    return "unspecified"


def _compare_bucket(actual: str, expected: str, operator: str, order: dict[str, int]) -> bool:
    if actual not in order or expected not in order or actual == "unspecified":
        return False
    actual_value = order[actual]
    expected_value = order[expected]
    if operator == ">=":
        return actual_value >= expected_value
    if operator == "<=":
        return actual_value <= expected_value
    if operator == ">":
        return actual_value > expected_value
    if operator == "<":
        return actual_value < expected_value
    return False


def _condition_matches(vignette: VignetteInput, condition: str) -> bool:
    normalized = condition.strip()

    if normalized.startswith("any_positive(") and normalized.endswith(")"):
        keys = [item.strip() for item in normalized[len("any_positive(") : -1].split(",") if item.strip()]
        return any(_subject_value(vignette, key) == "yes" for key in keys)

    if normalized.startswith("all_negative(") and normalized.endswith(")"):
        keys = [item.strip() for item in normalized[len("all_negative(") : -1].split(",") if item.strip()]
        return all(_subject_value(vignette, key) == "no" for key in keys)

    if " in [" in normalized and normalized.endswith("]"):
        key, raw_values = normalized.split(" in [", 1)
        options = [item.strip() for item in raw_values[:-1].split(",") if item.strip()]
        actual = _subject_value(vignette, key.strip())
        return actual in options

    for operator in (">=", "<=", ">", "<"):
        if operator in normalized:
            key, expected = normalized.split(operator, 1)
            actual = _subject_value(vignette, key.strip())
            key = key.strip()
            expected = expected.strip()
            if key == "PDL1Bucket":
                return _compare_bucket(actual, expected, operator, PDL1_BUCKET_ORDER)
            if key == "performanceStatus":
                return _compare_bucket(actual, expected, operator, PERFORMANCE_STATUS_ORDER)
            return False

    if "=" in normalized:
        key, expected = normalized.split("=", 1)
        actual = _subject_value(vignette, key.strip())
        expected = expected.strip()
        if key.strip() == "histology":
            return histology_matches(actual, expected)
        return actual == expected

    return False


def _applicability_list_matches(value: str, allowed_values: list[str], *, kind: str) -> bool:
    if "unspecified" in allowed_values:
        return True
    if kind == "histology":
        return any(histology_matches(value, candidate) for candidate in allowed_values)
    return value in allowed_values


def _topic_performance_status_matches(vignette: VignetteInput, topic: GuidelineTopic) -> bool:
    searchable_text = " ".join(
        part for part in [topic.topicTitle.lower(), (topic.stanceNotes or "").lower(), " ".join(topic.prerequisites).lower()] if part
    )
    if "ps 3-4" in searchable_text or "ps3-4" in searchable_text:
        return vignette.performanceStatus in {"3", "4"}
    if "ps 0-2" in searchable_text or "ps0-2" in searchable_text:
        return vignette.performanceStatus in {"0", "1", "2"}
    if "ps 2" in searchable_text or "ps2" in searchable_text:
        return vignette.performanceStatus == "2"
    return True


def topic_applies(vignette: VignetteInput, topic: GuidelineTopic) -> bool:
    if not _applicability_list_matches(vignette.diseaseSetting, topic.topicApplicability.diseaseSetting, kind="plain"):
        return False
    if not _applicability_list_matches(vignette.histology, topic.topicApplicability.histology, kind="histology"):
        return False
    if not _applicability_list_matches(vignette.lineOfTherapy, topic.topicApplicability.lineOfTherapy, kind="plain"):
        return False
    if not _applicability_list_matches(vignette.diseaseStage, topic.topicApplicability.diseaseStage, kind="plain"):
        return False
    if not _applicability_list_matches(
        vignette.resectabilityStatus, topic.topicApplicability.resectabilityStatus, kind="plain"
    ):
        return False
    if not _applicability_list_matches(vignette.treatmentContext, topic.topicApplicability.treatmentContext, kind="plain"):
        return False
    if not _topic_performance_status_matches(vignette, topic):
        return False
    return all(_condition_matches(vignette, condition) for condition in topic.topicApplicability.biomarkerConditions)


def _normalized_tag_set(tags: list[str]) -> set[str]:
    normalized: set[str] = set()
    for raw_tag in tags:
        tag = raw_tag.lower()
        normalized.add(tag)
        normalized.update(TAG_SYNONYMS.get(tag, set()))
    return normalized


def tag_overlap(evidence: EvidenceRecord, topic: GuidelineTopic) -> int:
    evidence_tags = _normalized_tag_set(evidence.interventionTags)
    topic_tags = _normalized_tag_set(topic.topicInterventionTags)
    return len(evidence_tags & topic_tags)


def has_meaningful_tag_match(evidence: EvidenceRecord, topic: GuidelineTopic) -> bool:
    evidence_tags = _normalized_tag_set(evidence.interventionTags)
    topic_tags = _normalized_tag_set(topic.topicInterventionTags)
    overlap = evidence_tags & topic_tags
    return any(tag not in GENERIC_INTERVENTION_TAGS for tag in overlap)


def structured_facets_count(evidence: EvidenceRecord) -> int:
    facets = 0
    if evidence.populationTags.diseaseSetting != "unspecified":
        facets += 1
    if evidence.populationTags.histology != "unspecified":
        facets += 1
    if evidence.populationTags.lineOfTherapy != "unspecified":
        facets += 1
    if evidence.populationTags.diseaseStage != "unspecified":
        facets += 1
    if evidence.populationTags.resectabilityStatus not in {"unspecified", "not_applicable"}:
        facets += 1
    if evidence.populationTags.treatmentContext != "unspecified":
        facets += 1
    if any(value != "unspecified" for value in evidence.populationTags.biomarkers.values()):
        facets += 1
    return facets


def choose_topic(vignette: VignetteInput, evidence: EvidenceRecord, topics: list[GuidelineTopic]) -> GuidelineTopic | None:
    candidates: list[tuple[int, int, GuidelineTopic]] = []
    for topic in topics:
        if not topic_applies(vignette, topic):
            continue
        overlap = tag_overlap(evidence, topic)
        if overlap == 0:
            continue
        if not has_meaningful_tag_match(evidence, topic):
            continue
        specificity = len(topic.topicApplicability.biomarkerConditions)
        candidates.append((overlap, specificity, topic))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2].topicId))
    return candidates[0][2]


def semantic_hint_topic(
    vignette: VignetteInput,
    evidence: EvidenceRecord,
    topics_by_id: dict[str, GuidelineTopic],
    semantic_topic_hints: dict[str, str] | None,
) -> GuidelineTopic | None:
    if not semantic_topic_hints:
        return None
    topic_id = semantic_topic_hints.get(evidence.evidenceId)
    if not topic_id:
        return None
    topic = topics_by_id.get(topic_id)
    if topic is None or not topic_applies(vignette, topic):
        return None
    return topic


def mapping_label(evidence: EvidenceRecord, topic: GuidelineTopic | None) -> str:
    if topic is None:
        return "guideline_silent"
    if topic.guidelineStance == "not_covered":
        return "guideline_silent"
    if topic.guidelineStance == "do_not_recommend":
        return "conflict"
    if evidence.evidenceType in {"guideline", "systematic_review", "phase3_rct", "phase2_rct"}:
        return "aligned"
    return "guideline_silent"


def applicability_note(
    vignette: VignetteInput,
    evidence: EvidenceRecord,
    gate_reasons: list[str],
    *,
    extra_notes: list[str] | None = None,
) -> str:
    if gate_reasons:
        return "Excluded because " + ", ".join(gate_reasons).replace("_", " ")

    notes = [
        f"Matches {vignette.diseaseSetting} setting",
        f"histology {vignette.histology}",
        f"line of therapy {vignette.lineOfTherapy}",
    ]
    if vignette.diseaseStage != "unspecified":
        notes.append(f"disease stage {vignette.diseaseStage}")
    if vignette.resectabilityStatus not in {"unspecified", "not_applicable"}:
        notes.append(f"resectability {vignette.resectabilityStatus}")
    if vignette.treatmentContext != "unspecified":
        notes.append(f"treatment context {vignette.treatmentContext}")
    if vignette.clinicalModifiers.brainMetastases != "unspecified":
        notes.append(f"brain metastases {vignette.clinicalModifiers.brainMetastases}")
    if any(value == "unspecified" for value in evidence.populationTags.biomarkers.values()):
        notes.append("includes unspecified biomarker applicability")
    if evidence.populationTags.lineOfTherapy == "unspecified":
        notes.append("line of therapy unspecified in evidence record")
    if structured_facets_count(evidence) < MIN_STRUCTURED_FACETS_FOR_PRIMARY:
        notes.append("structured cohort metadata is too sparse for primary ranking")
    if extra_notes:
        notes.extend(extra_notes)
    return "; ".join(notes) + "."


def manual_review_note(vignette: VignetteInput, evidence: EvidenceRecord, *, extra_notes: list[str] | None = None) -> str:
    base_note = applicability_note(vignette, evidence, [], extra_notes=extra_notes)
    return (
        "Evidence type could not be reliably determined from structured source metadata. "
        "This item is shown for clinician review only and is excluded from the primary ERS ranking. "
        + base_note
    )


def analyze_records(
    vignette: VignetteInput,
    evidence_records: list[EvidenceRecord],
    topics: list[GuidelineTopic],
    *,
    current_year: int,
    input_schema_version: str,
    ruleset_version: str,
    corpus_version: str,
    safety_footer_key: str,
    semantic_evidence_scores: dict[str, float] | None = None,
    semantic_topic_hints: dict[str, str] | None = None,
    semantic_rescue_ids: set[str] | None = None,
) -> tuple[AnalyzeRunResponse, dict]:
    top_evidence: list[TopEvidenceItem] = []
    manual_review_evidence: list[ManualReviewEvidenceItem] = []
    secondary: list[SecondaryReference] = []
    uncertainty_flags: list[str] = []
    trace_id = f"trace-{uuid4()}"
    topics_by_id = {topic.topicId: topic for topic in topics}
    semantic_evidence_scores = semantic_evidence_scores or {}
    semantic_topic_hints = semantic_topic_hints or {}
    semantic_rescue_ids = semantic_rescue_ids or set()

    eligible: list[tuple[EvidenceRecord, ScoreBreakdown, GuidelineTopic | None]] = []
    gate_candidate_count = len(evidence_records)

    for record in evidence_records:
        passed, reasons = relevance_gate(vignette, record)
        if not passed:
            secondary.append(SecondaryReference(evidenceId=record.evidenceId, exclusionReasons=reasons))
            continue

        is_sparse = structured_facets_count(record) < MIN_STRUCTURED_FACETS_FOR_PRIMARY
        semantic_score = semantic_evidence_scores.get(record.evidenceId, 0.0)
        is_semantically_rescued = record.evidenceId in semantic_rescue_ids

        if is_sparse and not is_semantically_rescued:
            secondary.append(
                SecondaryReference(
                    evidenceId=record.evidenceId,
                    exclusionReasons=[
                        f"insufficient_structured_cohort_metadata:{structured_facets_count(record)}_of_{MIN_STRUCTURED_FACETS_FOR_PRIMARY}"
                    ],
                )
            )
            uncertainty_flags.append(f"sparse_structured_metadata:{record.evidenceId}")
            continue
        if is_sparse and is_semantically_rescued:
            uncertainty_flags.append(f"semantic_rescue_sparse_metadata:{record.evidenceId}")

        topic = choose_topic(vignette, record, topics)
        semantic_hint = None
        if topic is None:
            semantic_hint = semantic_hint_topic(vignette, record, topics_by_id, semantic_topic_hints)
            if semantic_hint is not None:
                topic = semantic_hint
                uncertainty_flags.append(f"semantic_topic_hint_used:{record.evidenceId}:{semantic_hint.topicId}")

        extra_notes: list[str] = []
        if is_semantically_rescued:
            extra_notes.append(f"semantic retrieval rescued sparse cohort metadata (score {semantic_score:.3f})")
        if semantic_hint is not None:
            extra_notes.append(f"semantic guideline hint mapped this evidence to {semantic_hint.topicId}")

        if record.evidenceType == "unspecified":
            label = mapping_label(record, topic)
            potential_conflict = label == "conflict"
            if potential_conflict:
                extra_notes.append("possible conflict with a matched do-not-recommend guideline topic")
            manual_review_evidence.append(
                ManualReviewEvidenceItem(
                    evidenceId=record.evidenceId,
                    title=record.title,
                    abstract=record.abstract,
                    journalTitle=record.journalTitle,
                    publicationYear=record.publicationYear,
                    classificationStatus="manual_review_required",
                    manualReviewReason="evidence_type_unspecified",
                    mappedTopicId=topic.topicId if topic else None,
                    mappedTopicTitle=topic.topicTitle if topic else None,
                    mappingLabel=label,
                    potentialConflict=potential_conflict,
                    applicabilityNote=manual_review_note(vignette, record, extra_notes=extra_notes),
                    citations=[build_citation(record)],
                )
            )
            uncertainty_flags.append(f"manual_review_required:evidence_type_unspecified:{record.evidenceId}")
            if potential_conflict:
                uncertainty_flags.append(f"manual_review_potential_conflict:{record.evidenceId}")
            continue

        breakdown = compute_ers(record, current_year)
        eligible.append((record, breakdown, topic))

        if topic is None:
            uncertainty_flags.append(f"no_guideline_topic_match:{record.evidenceId}")
        if any(value == "unspecified" for value in record.populationTags.biomarkers.values()):
            uncertainty_flags.append(f"unspecified_biomarker_applicability:{record.evidenceId}")

        if breakdown.total < 30:
            secondary.append(
                SecondaryReference(
                    evidenceId=record.evidenceId,
                    exclusionReasons=[f"below_top_evidence_threshold:{breakdown.total}"],
                )
            )

    eligible.sort(
        key=lambda item: (
            -item[1].total,
            -item[1].evidenceStrength,
            -(item[0].publicationYear or 0),
            -(item[0].relevantN or 0),
            item[0].evidenceId,
        )
    )

    rank = 1
    for record, breakdown, topic in eligible:
        if breakdown.total < 30:
            continue
        label = mapping_label(record, topic)
        top_evidence.append(
            TopEvidenceItem(
                rank=rank,
                evidenceId=record.evidenceId,
                title=record.title,
                abstract=record.abstract,
                journalTitle=record.journalTitle,
                publicationYear=record.publicationYear,
                ersTotal=breakdown.total,
                ersBreakdown=breakdown,
                mappedTopicId=topic.topicId if topic else None,
                mappedTopicTitle=topic.topicTitle if topic else None,
                mappingLabel=label,
                applicabilityNote=applicability_note(
                    vignette,
                    record,
                    [],
                    extra_notes=[
                        note
                        for note in [
                            (
                                f"semantic retrieval rescued sparse cohort metadata (score {semantic_evidence_scores.get(record.evidenceId, 0.0):.3f})"
                                if record.evidenceId in semantic_rescue_ids
                                else None
                            ),
                            (
                                f"semantic guideline hint mapped this evidence to {semantic_topic_hints.get(record.evidenceId)}"
                                if topic is not None and semantic_topic_hints.get(record.evidenceId) == topic.topicId
                                else None
                            ),
                        ]
                        if note is not None
                    ],
                ),
                citations=[build_citation(record)],
            )
        )
        rank += 1

    run = RunInfo(
        id=f"run-{uuid4()}",
        status="completed",
        rulesetVersion=ruleset_version,
        corpusVersion=corpus_version,
        createdAt=datetime.utcnow(),
        latencyMs=42,
    )

    response = AnalyzeRunResponse(
        run=run,
        engine="deterministic",
        retrievalMode="hybrid",
        vectorStore="deterministic_only",
        embeddingModel="none",
        chunkingStrategyVersion="none",
        topEvidence=top_evidence,
        manualReviewEvidence=manual_review_evidence,
        secondaryReferences=secondary,
        uncertaintyFlags=sorted(set(uncertainty_flags)),
        safetyFooterKey=safety_footer_key,
        traceId=trace_id,
    )
    trace = {
        "traceId": trace_id,
        "runId": run.id,
        "inputSchemaVersion": input_schema_version,
        "rulesetVersion": ruleset_version,
        "corpusVersion": corpus_version,
        "engine": "deterministic",
        "retrievalMode": "hybrid",
        "vectorStore": "deterministic_only",
        "embeddingModel": "none",
        "chunkingStrategyVersion": "none",
        "gateCandidateCount": gate_candidate_count,
        "eligibleCount": len(eligible),
        "topEvidenceCount": len(top_evidence),
        "manualReviewCount": len(manual_review_evidence),
        "secondaryCount": len(secondary),
        "uncertaintyFlags": response.uncertaintyFlags,
        "safetyFooterKey": safety_footer_key,
        "retrievalCandidateCount": 0,
        "semanticCandidateOnlyCount": 0,
    }
    return response, trace


def system_integrity_checks(response: AnalyzeRunResponse) -> dict[str, bool]:
    return {
        "inputAccepted": True,
        "evidenceRetrieved": len(response.topEvidence) + len(response.manualReviewEvidence) + len(response.secondaryReferences) > 0,
        "exactlyOneValidLabelAssigned": all(
            item.mappingLabel in {"aligned", "guideline_silent", "conflict"} for item in response.topEvidence
        ),
    }


def assert_safety_language(text: str) -> list[str]:
    return [phrase for phrase in FORBIDDEN_LANGUAGE if phrase in text.lower()]
