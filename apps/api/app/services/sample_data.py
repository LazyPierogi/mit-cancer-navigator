from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

from app.domain.contracts import (
    Biomarkers,
    ClinicalModifiers,
    EvidenceRecord,
    GuidelineTopic,
    PopulationTags,
    TopicApplicability,
    VignetteInput,
)
from app.repositories.corpus_store import corpus_store
from app.services.import_pipeline import import_pipeline_service


ROOT = Path(__file__).resolve().parents[4]
API_ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_first_available(paths: list[Path]):
    for path in paths:
        if path.exists():
            return _load_json(path)
    missing = ", ".join(str(path.relative_to(ROOT)) for path in paths)
    raise FileNotFoundError(f"No dataset found. Checked: {missing}")


def _load_packaged_evidence_payload() -> list[dict]:
    return _load_first_available(
        [
            API_ROOT / "datasets" / "pubmed" / "evidence.curated.json",
            API_ROOT / "datasets" / "pubmed" / "evidence.sample.json",
            ROOT / "datasets" / "pubmed" / "evidence.curated.json",
            ROOT / "datasets" / "pubmed" / "evidence.sample.json",
        ]
    )


@lru_cache(maxsize=1)
def _load_packaged_evidence_payload_cached() -> tuple[dict, ...]:
    return tuple(_load_packaged_evidence_payload())


@lru_cache(maxsize=1)
def _load_packaged_evidence_by_id_cached() -> dict[str, dict]:
    return {item["evidenceId"]: item for item in _load_packaged_evidence_payload_cached()}


def _normalize_pubmed_row_to_enrichment(row: dict[str, object]) -> dict | None:
    pmid_raw = str(row.get("pmid", "") or row.get("evidenceId", "")).strip()
    pmid = pmid_raw.removeprefix("PMID-").strip()
    if not pmid:
        return None

    title = str(row.get("title", "")).strip() or None
    abstract = str(row.get("abstract", "")).strip() or None
    journal_title = str(row.get("journalTitle", "") or row.get("journal_title", "")).strip() or None
    publication_year_raw = row.get("publicationYear", row.get("pub_year"))
    try:
        publication_year = int(str(publication_year_raw).strip()) if str(publication_year_raw).strip() else None
    except ValueError:
        publication_year = None

    return {
        "evidenceId": f"PMID-{pmid}",
        "title": title,
        "abstract": abstract,
        "journalTitle": journal_title,
        "publicationYear": publication_year,
    }


def _iter_pubmed_dataset_files() -> list[Path]:
    candidates = [
        API_ROOT / "datasets" / "pubmed",
        ROOT / "datasets" / "pubmed",
    ]
    files: list[Path] = []
    seen: set[Path] = set()
    for base in candidates:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".json", ".csv", ".txt"}:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(resolved)
    return files


@lru_cache(maxsize=1)
def _build_pubmed_enrichment_index() -> dict[str, dict]:
    index: dict[str, dict] = {}
    for path in _iter_pubmed_dataset_files():
        suffix = path.suffix.lower()
        try:
            if suffix == ".json":
                payload = json.loads(path.read_text(encoding="utf-8"))
                rows = payload.get("records", payload) if isinstance(payload, dict) else payload
                if not isinstance(rows, list):
                    continue
            elif suffix in {".csv", ".txt"}:
                with path.open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
            else:
                continue
        except Exception:
            continue

        for raw_row in rows:
            if not isinstance(raw_row, dict):
                continue
            normalized = _normalize_pubmed_row_to_enrichment(raw_row)
            if normalized is None:
                continue
            evidence_id = normalized["evidenceId"]
            existing = index.get(evidence_id, {})
            index[evidence_id] = {
                "evidenceId": evidence_id,
                "title": existing.get("title") or normalized.get("title"),
                "abstract": existing.get("abstract") or normalized.get("abstract"),
                "journalTitle": existing.get("journalTitle") or normalized.get("journalTitle"),
                "publicationYear": existing.get("publicationYear") or normalized.get("publicationYear"),
            }
    return index


def load_sample_topics() -> list[GuidelineTopic]:
    esmo_batch_id, _pubmed_batch_id = _runtime_corpus_revision()
    return list(_load_sample_topics_cached(esmo_batch_id))


def load_sample_evidence() -> list[EvidenceRecord]:
    _esmo_batch_id, pubmed_batch_id = _runtime_corpus_revision()
    return list(_load_sample_evidence_cached(pubmed_batch_id))


def load_sample_evidence_by_id() -> dict[str, EvidenceRecord]:
    _esmo_batch_id, pubmed_batch_id = _runtime_corpus_revision()
    return dict(_load_sample_evidence_by_id_cached(pubmed_batch_id))


def _runtime_corpus_revision() -> tuple[str, str]:
    summary = corpus_store.get_import_summary()
    latest_by_kind = summary.get("latestByKind", {})
    return (
        latest_by_kind.get("esmo", {}).get("batchId") or "file_fallback",
        latest_by_kind.get("pubmed", {}).get("batchId") or "file_fallback",
    )


@lru_cache(maxsize=4)
def _load_runtime_topics_payload_cached(esmo_batch_id: str) -> tuple[dict, ...]:
    latest_batch = corpus_store.get_latest_import_batch(dataset_kind="esmo")
    if latest_batch is not None:
        source_path = latest_batch.get("sourcePath")
        if isinstance(source_path, str) and source_path:
            try:
                payload = import_pipeline_service.load_normalized_records_from_source(
                    dataset_kind="esmo",
                    source_path=source_path,
                )
                return tuple(sorted(payload, key=lambda item: item["topicId"]))
            except Exception:
                pass

    payload = corpus_store.get_guideline_topics() or _load_first_available(
        [
            API_ROOT / "datasets" / "esmo" / "topics.curated.json",
            API_ROOT / "datasets" / "esmo" / "topics.sample.json",
            ROOT / "datasets" / "esmo" / "topics.curated.json",
            ROOT / "datasets" / "esmo" / "topics.sample.json",
        ]
    )
    return tuple(sorted(payload, key=lambda item: item["topicId"]))


@lru_cache(maxsize=4)
def _load_runtime_evidence_payload_cached(pubmed_batch_id: str) -> tuple[dict, ...]:
    latest_batch = corpus_store.get_latest_import_batch(dataset_kind="pubmed")
    if latest_batch is not None:
        source_path = latest_batch.get("sourcePath")
        if isinstance(source_path, str) and source_path:
            try:
                payload = import_pipeline_service.load_normalized_records_from_source(
                    dataset_kind="pubmed",
                    source_path=source_path,
                )
                return tuple(sorted(payload, key=lambda item: item["evidenceId"]))
            except Exception:
                pass

    payload = corpus_store.get_evidence_studies() or list(_load_packaged_evidence_payload_cached())
    return tuple(sorted(payload, key=lambda item: item["evidenceId"]))


def _load_runtime_topics_payload() -> list[dict]:
    esmo_batch_id, _pubmed_batch_id = _runtime_corpus_revision()
    return list(_load_runtime_topics_payload_cached(esmo_batch_id))


def _load_runtime_evidence_payload() -> list[dict]:
    _esmo_batch_id, pubmed_batch_id = _runtime_corpus_revision()
    return list(_load_runtime_evidence_payload_cached(pubmed_batch_id))


@lru_cache(maxsize=4)
def _load_sample_topics_cached(esmo_batch_id: str) -> tuple[GuidelineTopic, ...]:
    payload = _load_runtime_topics_payload_cached(esmo_batch_id)
    return tuple(
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
    )


@lru_cache(maxsize=4)
def _load_sample_evidence_cached(pubmed_batch_id: str) -> tuple[EvidenceRecord, ...]:
    payload = _load_runtime_evidence_payload_cached(pubmed_batch_id)
    packaged_by_id = _load_packaged_evidence_by_id_cached()
    enrichment_by_id: dict[str, dict] | None = None
    records: list[EvidenceRecord] = []

    for item in payload:
        evidence_id = item["evidenceId"]
        packaged_item = packaged_by_id.get(evidence_id, {})

        title = item.get("title") or packaged_item.get("title")
        abstract = item.get("abstract") or packaged_item.get("abstract")
        journal_title = item.get("journalTitle") or packaged_item.get("journalTitle")
        publication_year = item.get("publicationYear") or packaged_item.get("publicationYear")

        if not title or abstract is None or journal_title is None or publication_year is None:
            if enrichment_by_id is None:
                enrichment_by_id = _build_pubmed_enrichment_index()
            enrichment_item = enrichment_by_id.get(evidence_id, {})
            title = title or enrichment_item.get("title")
            abstract = abstract or enrichment_item.get("abstract")
            journal_title = journal_title or enrichment_item.get("journalTitle")
            publication_year = publication_year or enrichment_item.get("publicationYear")

        records.append(
            EvidenceRecord(
                evidenceId=evidence_id,
                title=title or evidence_id,
                abstract=abstract,
                journalTitle=journal_title,
                publicationYear=publication_year,
                evidenceType=item["evidenceType"],
                relevantN=item["relevantN"],
                sourceCategory=item.get("sourceCategory"),
                populationTags=PopulationTags(**item["populationTags"]),
                interventionTags=item["interventionTags"],
                outcomeTags=item["outcomeTags"],
            )
        )

    return tuple(records)


@lru_cache(maxsize=4)
def _load_sample_evidence_by_id_cached(pubmed_batch_id: str) -> dict[str, EvidenceRecord]:
    return {record.evidenceId: record for record in _load_sample_evidence_cached(pubmed_batch_id)}


def load_sample_vignette() -> VignetteInput:
    payload = _load_first_available(
        [
            API_ROOT / "datasets" / "vignettes" / "frozen_pack.curated.json",
            API_ROOT / "datasets" / "vignettes" / "frozen_pack.sample.json",
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
        diseaseStage=case.get("diseaseStage", "unspecified"),
        resectabilityStatus=case.get("resectabilityStatus", "not_applicable"),
        treatmentContext=case.get("treatmentContext", "unspecified"),
        clinicalModifiers=ClinicalModifiers(**case.get("clinicalModifiers", {})),
    )


def load_frozen_pack() -> dict:
    return _load_first_available(
        [
            API_ROOT / "datasets" / "vignettes" / "frozen_pack.curated.json",
            API_ROOT / "datasets" / "vignettes" / "frozen_pack.sample.json",
            ROOT / "datasets" / "vignettes" / "frozen_pack.curated.json",
            ROOT / "datasets" / "vignettes" / "frozen_pack.sample.json",
        ]
    )


def load_demo_presets() -> dict:
    return _load_first_available(
        [
            API_ROOT / "datasets" / "vignettes" / "demo_presets.curated.json",
            ROOT / "datasets" / "vignettes" / "demo_presets.curated.json",
        ]
    )
