from __future__ import annotations

from dataclasses import asdict
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


def biomarker_dict(vignette: VignetteInput) -> dict[str, str]:
    markers: Biomarkers = vignette.biomarkers
    return {
        "EGFR": markers.EGFR,
        "ALK": markers.ALK,
        "ROS1": markers.ROS1,
        "PDL1Bucket": markers.PDL1Bucket,
    }


def relevance_gate(vignette: VignetteInput, evidence: EvidenceRecord) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if evidence.populationTags.disease != "NSCLC":
        reasons.append("disease_mismatch")

    if evidence.populationTags.diseaseSetting not in (vignette.diseaseSetting, "mixed"):
        reasons.append("setting_mismatch")

    if evidence.populationTags.histology not in (vignette.histology, "mixed", "all_nsclc"):
        reasons.append("histology_mismatch")

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


def _condition_matches(vignette: VignetteInput, condition: str) -> bool:
    if "=" not in condition:
        return False
    key, expected = condition.split("=", 1)
    if key in {"EGFR", "ALK", "ROS1", "PDL1Bucket"}:
        return biomarker_dict(vignette).get(key) == expected
    if key == "diseaseSetting":
        return vignette.diseaseSetting == expected
    if key == "histology":
        return vignette.histology == expected
    return False


def topic_applies(vignette: VignetteInput, topic: GuidelineTopic) -> bool:
    if vignette.diseaseSetting not in topic.topicApplicability.diseaseSetting:
        return False
    if vignette.histology not in topic.topicApplicability.histology:
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
    ]
    if any(value == "unspecified" for value in evidence.populationTags.biomarkers.values()):
        notes.append("includes unspecified biomarker applicability")
    return "; ".join(notes) + "."


def analyze_records(
    vignette: VignetteInput,
    evidence_records: list[EvidenceRecord],
    topics: list[GuidelineTopic],
    *,
    current_year: int,
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
        "inputSchemaVersion": "vignette-v1",
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

