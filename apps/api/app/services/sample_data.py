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
from app.repositories.corpus_store import corpus_store


ROOT = Path(__file__).resolve().parents[4]


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_first_available(paths: list[Path]):
    for path in paths:
        if path.exists():
            return _load_json(path)
    missing = ", ".join(str(path.relative_to(ROOT)) for path in paths)
    raise FileNotFoundError(f"No dataset found. Checked: {missing}")


def load_sample_topics() -> list[GuidelineTopic]:
    payload = corpus_store.get_guideline_topics() or _load_first_available(
        [
            ROOT / "datasets" / "esmo" / "topics.curated.json",
            ROOT / "datasets" / "esmo" / "topics.sample.json",
        ]
    )
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
    payload = corpus_store.get_evidence_studies() or _load_first_available(
        [
            ROOT / "datasets" / "pubmed" / "evidence.curated.json",
            ROOT / "datasets" / "pubmed" / "evidence.sample.json",
        ]
    )
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
    payload = _load_first_available(
        [
            ROOT / "datasets" / "vignettes" / "frozen_pack.curated.json",
            ROOT / "datasets" / "vignettes" / "frozen_pack.sample.json",
        ]
    )
    case = payload["cases"][0]["vignette"]
    return VignetteInput(
        cancerType=case["cancerType"],
        diseaseSetting=case["diseaseSetting"],
        histology=case["histology"],
        performanceStatus=case["performanceStatus"],
        biomarkers=Biomarkers(**case["biomarkers"]),
        lineOfTherapy=case.get("lineOfTherapy", "unspecified"),
    )


def load_frozen_pack() -> dict:
    return _load_first_available(
        [
            ROOT / "datasets" / "vignettes" / "frozen_pack.curated.json",
            ROOT / "datasets" / "vignettes" / "frozen_pack.sample.json",
        ]
    )
