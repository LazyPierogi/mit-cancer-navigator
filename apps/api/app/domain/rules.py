from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from .contracts import (
    AnalyzeRunResponse,
    Biomarkers,
    CitationRef,
    EvidenceRecord,
    GuidelineTopic,
    RunInfo,
    ScoreBreakdown,
    SecondaryReference,
    TopEvidenceItem,
    VignetteInput,
)


EVIDENCE_STRENGTH_SCORES = {
    "guideline": 20,
    "systematic_review": 18,
    "phase3_rct": 16,
    "phase2_rct": 13,
    "prospective_obs": 10,
    "retrospective": 6,
    "case_series": 2,
    "expert_opinion": 2,
}

SOURCE_CREDIBILITY_SCORES = {
    "guideline_body": 15,
    "high_impact_journal": 12,
    "specialty_journal": 9,
    "preprint": 5,
    "industry_whitepaper": 2,
    None: 6,
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


def histology_matches(candidate: str, expected: str) -> bool:
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


def relevance_gate(vignette: VignetteInput, evidence: EvidenceRecord) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if evidence.populationTags.disease != "NSCLC":
        reasons.append("disease_mismatch")

    if evidence.populationTags.diseaseSetting not in (vignette.diseaseSetting, "mixed"):
        reasons.append("setting_mismatch")

    if not histology_matches(evidence.populationTags.histology, vignette.histology):
        reasons.append("histology_mismatch")

    if not line_of_therapy_matches(evidence.populationTags.lineOfTherapy, vignette.lineOfTherapy):
        reasons.append("line_of_therapy_mismatch")

    for key, vignette_value in biomarker_dict(vignette).items():
        evidence_value = evidence.populationTags.biomarkers.get(key, "unspecified")
        if evidence_value not in ("unspecified", vignette_value):
            reasons.append(f"biomarker_mismatch:{key}")

    return (len(reasons) == 0, reasons)


def dataset_robustness_score(relevant_n: int | None) -> int:
    if relevant_n is None:
        return 6
    if relevant_n >= 300:
        return 15
    if relevant_n >= 100:
        return 12
    if relevant_n >= 50:
        return 9
    if relevant_n >= 20:
        return 6
    return 3


def recency_score(publication_year: int | None, current_year: int) -> int:
    if publication_year is None:
        return 0
    age = current_year - publication_year
    if age <= 3:
        return 10
    if age <= 6:
        return 6
    if age <= 10:
        return 3
    return 0


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


def topic_applies(vignette: VignetteInput, topic: GuidelineTopic) -> bool:
    if not _applicability_list_matches(vignette.diseaseSetting, topic.topicApplicability.diseaseSetting, kind="plain"):
        return False
    if not _applicability_list_matches(vignette.histology, topic.topicApplicability.histology, kind="histology"):
        return False
    if not _applicability_list_matches(vignette.lineOfTherapy, topic.topicApplicability.lineOfTherapy, kind="plain"):
        return False
    return all(_condition_matches(vignette, condition) for condition in topic.topicApplicability.biomarkerConditions)


def tag_overlap(evidence: EvidenceRecord, topic: GuidelineTopic) -> int:
    evidence_tags = {tag.lower() for tag in evidence.interventionTags}
    topic_tags = {tag.lower() for tag in topic.topicInterventionTags}
    return len(evidence_tags & topic_tags)


def choose_topic(vignette: VignetteInput, evidence: EvidenceRecord, topics: list[GuidelineTopic]) -> GuidelineTopic | None:
    candidates: list[tuple[int, int, GuidelineTopic]] = []
    for topic in topics:
        if not topic_applies(vignette, topic):
            continue
        overlap = tag_overlap(evidence, topic)
        if overlap == 0:
            continue
        specificity = len(topic.topicApplicability.biomarkerConditions)
        candidates.append((overlap, specificity, topic))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2].topicId))
    return candidates[0][2]


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


def applicability_note(vignette: VignetteInput, evidence: EvidenceRecord, gate_reasons: list[str]) -> str:
    if gate_reasons:
        return "Excluded because " + ", ".join(gate_reasons).replace("_", " ")

    notes = [
        f"Matches {vignette.diseaseSetting} setting",
        f"histology {vignette.histology}",
        f"line of therapy {vignette.lineOfTherapy}",
    ]
    if any(value == "unspecified" for value in evidence.populationTags.biomarkers.values()):
        notes.append("includes unspecified biomarker applicability")
    if evidence.populationTags.lineOfTherapy == "unspecified":
        notes.append("line of therapy unspecified in evidence record")
    return "; ".join(notes) + "."


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
) -> tuple[AnalyzeRunResponse, dict]:
    top_evidence: list[TopEvidenceItem] = []
    secondary: list[SecondaryReference] = []
    uncertainty_flags: list[str] = []
    trace_id = f"trace-{uuid4()}"

    eligible: list[tuple[EvidenceRecord, ScoreBreakdown, GuidelineTopic | None]] = []
    gate_candidate_count = len(evidence_records)

    for record in evidence_records:
        passed, reasons = relevance_gate(vignette, record)
        if not passed:
            secondary.append(SecondaryReference(evidenceId=record.evidenceId, exclusionReasons=reasons))
            continue

        breakdown = compute_ers(record, current_year)
        topic = choose_topic(vignette, record, topics)
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
                publicationYear=record.publicationYear,
                ersTotal=breakdown.total,
                ersBreakdown=breakdown,
                mappedTopicId=topic.topicId if topic else None,
                mappedTopicTitle=topic.topicTitle if topic else None,
                mappingLabel=label,
                applicabilityNote=applicability_note(vignette, record, []),
                citations=[CitationRef(sourceId=record.evidenceId, title=record.title, year=record.publicationYear)],
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
        topEvidence=top_evidence,
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
        "gateCandidateCount": gate_candidate_count,
        "eligibleCount": len(eligible),
        "topEvidenceCount": len(top_evidence),
        "secondaryCount": len(secondary),
        "uncertaintyFlags": response.uncertaintyFlags,
        "safetyFooterKey": safety_footer_key,
    }
    return response, trace


def system_integrity_checks(response: AnalyzeRunResponse) -> dict[str, bool]:
    return {
        "inputAccepted": True,
        "evidenceRetrieved": len(response.topEvidence) + len(response.secondaryReferences) > 0,
        "exactlyOneValidLabelAssigned": all(
            item.mappingLabel in {"aligned", "guideline_silent", "conflict"} for item in response.topEvidence
        ),
    }


def assert_safety_language(text: str) -> list[str]:
    return [phrase for phrase in FORBIDDEN_LANGUAGE if phrase in text.lower()]
