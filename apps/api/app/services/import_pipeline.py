from __future__ import annotations

import csv
import json
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.repositories.corpus_store import corpus_store
from app.repositories.bootstrap import bootstrap_database


ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class ImportPipelineService:
    DEFAULT_PATHS = {
        "esmo": ROOT / "datasets" / "esmo" / "topics.curated.json",
        "pubmed": ROOT / "datasets" / "pubmed" / "evidence.curated.json",
    }

    RAW_PREVIEW_PATHS = {
        "esmo": ROOT / "datasets" / "esmo" / "ESMO_Stage_IV_SqCC_10_Recommended_Treatments_NORMALIZED_v0.3.1_3layer.json",
        "pubmed": ROOT / "datasets" / "pubmed" / "Test11.txt",
    }
    PUBMED_V2_REQUIRED_FIELDS = {
        "pmid",
        "title",
        "abstract",
        "publicationYear",
        "publicationType",
        "journalTitle",
        "evidenceType",
        "diseaseSetting",
        "histology",
        "lineOfTherapy",
        "biomarkers",
        "interventionTags",
        "outcomeTags",
        "relevantN",
    }
    PUBMED_EVIDENCE_TYPE_ALIASES = {
        "randomized control trial": "phase3_rct",
        "randomized controlled trial": "phase3_rct",
        "systematic review": "systematic_review",
    }
    PUBMED_EVIDENCE_TYPES = {
        "guideline",
        "systematic_review",
        "phase3_rct",
        "phase2_rct",
        "prospective_obs",
        "retrospective",
        "case_series",
        "expert_opinion",
    }
    PUBMED_DISEASE_SETTING_ALLOWED = {"early", "locally_advanced", "metastatic", "mixed", "unspecified"}
    PUBMED_HISTOLOGY_ALLOWED = {"adenocarcinoma", "squamous", "non_squamous", "all_nsclc", "mixed", "unspecified"}
    PUBMED_LINE_ALLOWED = {"first_line", "second_line", "later_line", "mixed", "unspecified"}
    PUBMED_BIOMARKER_ALLOWED = {"yes", "no", "unspecified"}
    PUBMED_BIOMARKER_KEYS = {
        "EGFR",
        "ALK",
        "ROS1",
        "BRAF",
        "RET",
        "MET",
        "KRAS",
        "NTRK",
        "HER2",
        "EGFRExon20ins",
    }

    def __init__(self) -> None:
        self._debug_config: dict[str, bool] = {"strictMvpPubmed": False}
        self._debug_logs: deque[dict] = deque(maxlen=300)

    def import_dataset(self, *, dataset_kind: str, path: str | None = None) -> dict:
        from scripts.validate_data_drop import validate_dataset

        bootstrap_database()
        source_path = Path(path).expanduser().resolve() if path else self.DEFAULT_PATHS[dataset_kind].resolve()
        strict_mvp = dataset_kind == "pubmed" and self._debug_config["strictMvpPubmed"]
        self._add_debug_log(
            level="info",
            event="import_started",
            dataset_kind=dataset_kind,
            path=str(source_path),
            message="Import requested.",
            details={"strictMvpPubmed": strict_mvp},
        )
        report = validate_dataset(source_path, dataset_kind, strict_mvp_pubmed=strict_mvp)
        report_dict = report.to_dict()
        batch_id = f"import-{dataset_kind}-{uuid4()}"

        if report.error_count:
            notes = ["Validation failed. Dataset was not imported."]
            corpus_store.save_import_batch(
                batch_id=batch_id,
                dataset_kind=dataset_kind,
                dataset_shape=report.dataset_shape,
                source_path=str(source_path),
                status="failed_validation",
                record_count=self._record_count(report_dict),
                imported_count=0,
                error_count=report.error_count,
                warning_count=report.warning_count,
                validation_payload=report_dict,
                notes=notes,
            )
            self._add_debug_log(
                level="error",
                event="import_failed_validation",
                dataset_kind=dataset_kind,
                path=str(source_path),
                message="Validation failed. Dataset not imported.",
                details={
                    "batchId": batch_id,
                    "errorCount": report.error_count,
                    "warningCount": report.warning_count,
                    "strictMvpPubmed": strict_mvp,
                },
            )
            return corpus_store.get_import_batch(batch_id) or {}

        try:
            normalized_records = self._normalize(dataset_kind=dataset_kind, source_path=source_path, dataset_shape=report.dataset_shape)
        except ValueError as exc:
            notes = [str(exc)]
            corpus_store.save_import_batch(
                batch_id=batch_id,
                dataset_kind=dataset_kind,
                dataset_shape=report.dataset_shape,
                source_path=str(source_path),
                status="normalization_blocked",
                record_count=self._record_count(report_dict),
                imported_count=0,
                error_count=report.error_count,
                warning_count=report.warning_count,
                validation_payload=report_dict,
                notes=notes,
            )
            self._add_debug_log(
                level="error",
                event="import_normalization_blocked",
                dataset_kind=dataset_kind,
                path=str(source_path),
                message=str(exc),
                details={
                    "batchId": batch_id,
                    "errorCount": report.error_count,
                    "warningCount": report.warning_count,
                    "strictMvpPubmed": strict_mvp,
                },
            )
            return corpus_store.get_import_batch(batch_id) or {}

        imported_count = self._ingest(dataset_kind=dataset_kind, batch_id=batch_id, records=normalized_records)
        notes = ["Imported successfully."] if not report.warning_count else ["Imported with validation warnings."]
        status = "completed" if not report.warning_count else "completed_with_warnings"
        corpus_store.save_import_batch(
            batch_id=batch_id,
            dataset_kind=dataset_kind,
            dataset_shape=report.dataset_shape,
            source_path=str(source_path),
            status=status,
            record_count=len(normalized_records),
            imported_count=imported_count,
            error_count=report.error_count,
            warning_count=report.warning_count,
            validation_payload=report_dict,
            notes=notes,
        )
        self._add_debug_log(
            level="warning" if report.warning_count else "info",
            event="import_completed",
            dataset_kind=dataset_kind,
            path=str(source_path),
            message="Import completed.",
            details={
                "batchId": batch_id,
                "status": status,
                "recordCount": len(normalized_records),
                "importedCount": imported_count,
                "errorCount": report.error_count,
                "warningCount": report.warning_count,
                "strictMvpPubmed": strict_mvp,
            },
        )
        return corpus_store.get_import_batch(batch_id) or {}

    def get_import_batch(self, batch_id: str) -> dict | None:
        return corpus_store.get_import_batch(batch_id)

    def list_import_batches(self) -> list[dict]:
        bootstrap_database()
        return corpus_store.list_import_batches()

    def get_import_summary(self) -> dict:
        bootstrap_database()
        return corpus_store.get_import_summary()

    def get_debug_config(self) -> dict:
        return dict(self._debug_config)

    def update_debug_config(self, *, strict_mvp_pubmed: bool) -> dict:
        self._debug_config["strictMvpPubmed"] = strict_mvp_pubmed
        self._add_debug_log(
            level="info",
            event="debug_config_updated",
            dataset_kind=None,
            path=None,
            message="Import debug config updated.",
            details={"strictMvpPubmed": strict_mvp_pubmed},
        )
        return self.get_debug_config()

    def get_debug_logs(self, *, limit: int = 80) -> list[dict]:
        clamped = max(1, min(limit, 300))
        return list(self._debug_logs)[-clamped:][::-1]

    def _normalize(self, *, dataset_kind: str, source_path: Path, dataset_shape: str) -> list[dict]:
        from scripts.build_curated_preview import build_evidence, build_topics

        if dataset_shape == "canonical":
            return json.loads(source_path.read_text(encoding="utf-8"))

        if dataset_kind == "pubmed" and source_path.suffix.lower() in {".csv", ".txt"}:
            with source_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            if rows and self.PUBMED_V2_REQUIRED_FIELDS.issubset(set(rows[0].keys())):
                return [self._normalize_pubmed_v2_row(row) for row in rows]

        expected_raw_path = self.RAW_PREVIEW_PATHS[dataset_kind].resolve()
        if source_path != expected_raw_path:
            raise ValueError(
                "Raw normalization is only configured for the current preview source files. "
                "For new external drops, ask Data Team to deliver the canonical format first."
            )

        if dataset_kind == "esmo":
            return build_topics()
        if dataset_kind == "pubmed":
            return build_evidence()
        raise ValueError(f"Unknown dataset kind `{dataset_kind}`.")

    def _ingest(self, *, dataset_kind: str, batch_id: str, records: list[dict]) -> int:
        if dataset_kind == "esmo":
            return corpus_store.replace_guideline_topics(batch_id=batch_id, topics=records)
        if dataset_kind == "pubmed":
            return corpus_store.replace_evidence_studies(batch_id=batch_id, evidence_records=records)
        raise ValueError(f"Unknown dataset kind `{dataset_kind}`.")

    def _normalize_pubmed_v2_row(self, row: dict[str, str]) -> dict:
        pmid = row["pmid"].strip()
        evidence_type = self._normalize_evidence_type(row.get("evidenceType", ""), publication_type=row.get("publicationType", ""))

        disease_setting = self._normalize_enum_value(
            row.get("diseaseSetting", ""), allowed=self.PUBMED_DISEASE_SETTING_ALLOWED, fallback="unspecified"
        )
        histology = self._normalize_enum_value(row.get("histology", ""), allowed=self.PUBMED_HISTOLOGY_ALLOWED, fallback="unspecified")
        line_of_therapy = self._normalize_enum_value(row.get("lineOfTherapy", ""), allowed=self.PUBMED_LINE_ALLOWED, fallback="unspecified")
        biomarkers = self._normalize_biomarkers(row.get("biomarkers", ""))

        return {
            "evidenceId": f"PMID-{pmid}",
            "title": row.get("title", "").strip(),
            "publicationYear": self._parse_int(row.get("publicationYear", "")),
            "evidenceType": evidence_type,
            "relevantN": self._parse_int(row.get("relevantN", "")),
            "sourceCategory": self._infer_source_category(row.get("journalTitle", "")),
            "populationTags": {
                "disease": "NSCLC",
                "diseaseSetting": disease_setting,
                "histology": histology,
                "lineOfTherapy": line_of_therapy,
                "biomarkers": biomarkers,
            },
            "interventionTags": self._parse_list_cell(row.get("interventionTags", "")),
            "outcomeTags": self._parse_list_cell(row.get("outcomeTags", "")),
        }

    def _add_debug_log(
        self,
        *,
        level: str,
        event: str,
        dataset_kind: str | None,
        path: str | None,
        message: str,
        details: dict | None = None,
    ) -> None:
        self._debug_logs.append(
            {
                "timestamp": datetime.now(timezone.utc),
                "level": level,
                "event": event,
                "datasetKind": dataset_kind,
                "path": path,
                "message": message,
                "details": details or {},
            }
        )

    @staticmethod
    def _record_count(report_dict: dict) -> int:
        info_lines = report_dict.get("info", [])
        for line in info_lines:
            if line.startswith("Validated ") and line.endswith(" records."):
                raw_number = line.removeprefix("Validated ").removesuffix(" records.")
                if raw_number.isdigit():
                    return int(raw_number)
        return 0

    def _normalize_evidence_type(self, raw_value: str, *, publication_type: str) -> str:
        normalized = self._normalize_token(raw_value)
        if normalized in self.PUBMED_EVIDENCE_TYPES:
            return normalized
        mapped = self.PUBMED_EVIDENCE_TYPE_ALIASES.get(raw_value.strip().lower())
        if mapped is not None:
            return mapped
        # Last-resort fallback only for importer resilience.
        publication_mapped = self.PUBMED_EVIDENCE_TYPE_ALIASES.get(publication_type.strip().lower())
        return publication_mapped or "prospective_obs"

    @staticmethod
    def _normalize_token(value: str) -> str:
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        while "__" in normalized:
            normalized = normalized.replace("__", "_")
        return normalized

    def _normalize_enum_value(self, value: str, *, allowed: set[str], fallback: str) -> str:
        raw = value.strip()
        if not raw:
            return fallback
        if "," in raw:
            return "mixed" if "mixed" in allowed else fallback
        normalized = self._normalize_token(raw)
        return normalized if normalized in allowed else fallback

    @staticmethod
    def _parse_int(value: str) -> int | None:
        cleaned = value.strip()
        if cleaned in {"", "unspecified", "null"}:
            return None
        return int(cleaned) if cleaned.isdigit() else None

    def _parse_list_cell(self, value: str) -> list[str]:
        raw = value.strip()
        if not raw:
            return []
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip() and str(item).strip() != "unspecified"]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in raw.split(",") if item.strip() and item.strip() != "unspecified"]

    def _parse_biomarkers_cell(self, value: str) -> dict[str, str]:
        raw = value.strip()
        if not raw:
            return {}
        if raw.startswith("{") and raw.endswith("}"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return {str(key).strip(): str(item).strip() for key, item in parsed.items()}
            except json.JSONDecodeError:
                return {}
        if "=" not in raw:
            return {}
        payload: dict[str, str] = {}
        for chunk in raw.split(","):
            part = chunk.strip()
            if not part or "=" not in part:
                continue
            key, item = part.split("=", 1)
            payload[key.strip()] = item.strip()
        return payload

    def _normalize_biomarkers(self, value: str) -> dict[str, str]:
        parsed = self._parse_biomarkers_cell(value)
        normalized: dict[str, str] = {key: "unspecified" for key in self.PUBMED_BIOMARKER_KEYS}
        normalized["PDL1Bucket"] = "unspecified"

        pdl1_flags: dict[str, str] = {}
        for key, raw_item in parsed.items():
            item = self._normalize_token(raw_item)
            if key == "PDL1Bucket":
                if item in {"lt1", "1to49", "ge50"}:
                    normalized["PDL1Bucket"] = item
                elif item in {"any", "unspecified"}:
                    normalized["PDL1Bucket"] = "unspecified"
                continue

            if key in {"PDL1_ge50", "PDL1_1to49", "PDL1_lt1", "PDL1_any"}:
                pdl1_flags[key] = item
                continue

            if key in self.PUBMED_BIOMARKER_KEYS and item in self.PUBMED_BIOMARKER_ALLOWED:
                normalized[key] = item

        if pdl1_flags:
            if pdl1_flags.get("PDL1_ge50") == "yes":
                normalized["PDL1Bucket"] = "ge50"
            elif pdl1_flags.get("PDL1_1to49") == "yes":
                normalized["PDL1Bucket"] = "1to49"
            elif pdl1_flags.get("PDL1_lt1") == "yes":
                normalized["PDL1Bucket"] = "lt1"
            elif pdl1_flags.get("PDL1_any") == "yes":
                normalized["PDL1Bucket"] = "unspecified"

        return normalized

    @staticmethod
    def _infer_source_category(journal_title: str) -> str:
        normalized = journal_title.strip().lower()
        high_impact_titles = {
            "bmj (clinical research ed.)",
            "nature medicine",
            "journal of thoracic oncology : official publication of the international association for the study of lung cancer",
        }
        return "high_impact_journal" if normalized in high_impact_titles else "specialty_journal"


import_pipeline_service = ImportPipelineService()
