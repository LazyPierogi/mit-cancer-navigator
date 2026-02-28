from __future__ import annotations

import json
from pathlib import Path

from app.domain.contracts import (
    Biomarkers,
    EvidenceRecord,
    GuidelineTopic,
    PopulationTags,
    TopicApplicability,
    VignetteInput,
)


ROOT = Path(__file__).resolve().parents[4]


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_sample_topics() -> list[GuidelineTopic]:
    payload = _load_json(ROOT / "datasets" / "esmo" / "topics.sample.json")
    return [
        GuidelineTopic(
            topicId=item["topicId"],
            topicTitle=item["topicTitle"],
            topicApplicability=TopicApplicability(**item["topicApplicability"]),
            topicInterventionTags=item["topicInterventionTags"],
            guidelineStance=item["guidelineStance"],
            stanceNotes=item.get("stanceNotes"),
            prerequisites=item.get("prerequisites", []),
        )
        for item in payload
    ]


def load_sample_evidence() -> list[EvidenceRecord]:
    payload = _load_json(ROOT / "datasets" / "pubmed" / "evidence.sample.json")
    return [
        EvidenceRecord(
            evidenceId=item["evidenceId"],
            title=item["title"],
            publicationYear=item["publicationYear"],
            evidenceType=item["evidenceType"],
            relevantN=item["relevantN"],
            sourceCategory=item.get("sourceCategory"),
            populationTags=PopulationTags(**item["populationTags"]),
            interventionTags=item["interventionTags"],
            outcomeTags=item["outcomeTags"],
        )
        for item in payload
    ]


def load_sample_vignette() -> VignetteInput:
    payload = _load_json(ROOT / "datasets" / "vignettes" / "frozen_pack.sample.json")
    case = payload["cases"][0]["vignette"]
    return VignetteInput(
        cancerType=case["cancerType"],
        diseaseSetting=case["diseaseSetting"],
        histology=case["histology"],
        performanceStatus=case["performanceStatus"],
        biomarkers=Biomarkers(**case["biomarkers"]),
    )


def load_frozen_pack() -> dict:
    return _load_json(ROOT / "datasets" / "vignettes" / "frozen_pack.sample.json")

