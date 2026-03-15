from __future__ import annotations

import csv
import json
import re
import sys
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.repositories.corpus_store import corpus_store
from app.repositories.bootstrap import bootstrap_database

try:
    from app.repositories.semantic_store import semantic_store
except Exception:
    semantic_store = None

try:
    from app.services.semantic_retrieval_service import semantic_retrieval_service
except Exception:
    semantic_retrieval_service = None


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass(slots=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    record_id: str | None = None


@dataclass(slots=True)
class ValidationReport:
    dataset_kind: str
    dataset_shape: str
    path: str
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def add(self, severity: str, code: str, message: str, record_id: str | None = None) -> None:
        issue = ValidationIssue(severity=severity, code=code, message=message, record_id=record_id)
        if severity == "error":
            self.errors.append(issue)
        else:
            self.warnings.append(issue)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "datasetKind": self.dataset_kind,
            "datasetShape": self.dataset_shape,
            "path": self.path,
            "errorCount": self.error_count,
            "warningCount": self.warning_count,
            "info": self.info,
            "errors": [asdict(issue) for issue in self.errors],
            "warnings": [asdict(issue) for issue in self.warnings],
        }


class ImportPipelineService:
    DEFAULT_DATASET_FILENAMES = {
        "esmo": "topics.curated.json",
        "pubmed": "evidence.curated.json",
    }
    LOGICAL_DATASET_ROOTS = {
        "esmo": Path("datasets") / "esmo",
        "pubmed": Path("datasets") / "pubmed",
    }
    DATASET_ROOT_CANDIDATES = {
        "esmo": (
            PACKAGE_ROOT / "datasets" / "esmo",
            REPO_ROOT / "datasets" / "esmo",
        ),
        "pubmed": (
            PACKAGE_ROOT / "datasets" / "pubmed",
            REPO_ROOT / "datasets" / "pubmed",
        ),
    }
    SUPPORTED_IMPORT_SUFFIXES = {
        "esmo": {".json"},
        "pubmed": {".csv", ".txt", ".json"},
    }

    RAW_PREVIEW_PATHS = {
        "esmo": REPO_ROOT / "datasets" / "esmo" / "ESMO_Stage_IV_SqCC_10_Recommended_Treatments_NORMALIZED_v0.3.1_3layer.json",
        "pubmed": REPO_ROOT / "datasets" / "pubmed" / "Test11.txt",
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
    PUBMED_RAW_REQUIRED_FIELDS = {
        "pmid",
        "title",
        "abstract",
        "pub_year",
        "publication_type",
        "journal_title",
        "sample_size_total",
        "disease_setting_tag",
        "line_of_therapy_tag",
        "histology_tag",
        "EGFR_tag",
        "ALK_tag",
        "ROS1_tag",
        "PDL1_rule_tag",
        "intervention_tags",
        "outcome_tags",
        "notes",
    }
    PUBMED_EVIDENCE_TYPE_ALIASES = {
        "randomized control trial": "phase3_rct",
        "randomized controlled trial": "phase3_rct",
        "systematic review": "systematic_review",
        "undefined": "unspecified",
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
        "unspecified",
    }
    PUBMED_DISEASE_SETTING_ALLOWED = {"early", "locally_advanced", "metastatic", "mixed", "unspecified"}
    PUBMED_DISEASE_SETTING_ALIASES = {"early_stage": "early"}
    PUBMED_HISTOLOGY_ALLOWED = {"adenocarcinoma", "squamous", "non_squamous", "all_nsclc", "mixed", "unspecified"}
    PUBMED_LINE_ALLOWED = {"first_line", "second_line", "later_line", "adjuvant", "consolidation", "mixed", "unspecified"}
    PUBMED_DISEASE_STAGE_ALLOWED = {"stage_i", "stage_ii", "stage_iii", "stage_iv", "mixed", "unspecified"}
    PUBMED_RESECTABILITY_ALLOWED = {"resected", "unresectable", "not_applicable", "unspecified"}
    PUBMED_TREATMENT_CONTEXT_ALLOWED = {
        "treatment_naive",
        "post_platinum_chemotherapy",
        "post_egfr_tki",
        "post_chemo_immunotherapy",
        "post_chemoradiation",
        "post_surgery",
        "unspecified",
    }
    PUBMED_BIOMARKER_ALLOWED = {"yes", "no", "unspecified"}
    PUBMED_RAW_PDL1_BUCKETS = {"lt1", "1to49", "ge50", "any", "unspecified"}
    PUBMED_RAW_BIOMARKER_RED_FLAGS = {"positive", "negative"}
    PUBMED_RAW_PDL1_FLAG_KEYS = {"PDL1_ge50", "PDL1_1to49", "PDL1_lt1", "PDL1_any"}
    PUBMED_RAW_PDL1_FREE_TEXT_THRESHOLD = 80
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
    ESMO_LINE_OF_THERAPY_ALIASES = {"first_line_maintenance": "first_line"}
    ESMO_CANONICAL_REQUIRED_FIELDS = {
        "topicId",
        "topicTitle",
        "topicApplicability",
        "topicInterventionTags",
        "guidelineStance",
    }
    ESMO_EXTERNAL_V2_REQUIRED_FIELDS = {
        "topicId",
        "topicTitle",
        "diseaseSetting",
        "histology",
        "lineOfTherapy",
        "guidelineStance",
        "topicInterventionTags",
        "biomarkerRequirements",
        "biomarkerLogic",
        "semanticNormalization",
        "sourceExcerptShort",
        "applicabilityNotes",
    }
    PUBMED_CANONICAL_REQUIRED_FIELDS = {
        "evidenceId",
        "title",
        "publicationYear",
        "evidenceType",
        "populationTags",
        "interventionTags",
        "outcomeTags",
    }

    def __init__(self) -> None:
        self._debug_config: dict[str, object] = {
            "strictMvpPubmed": False,
            "runtimeEngine": "deterministic",
            "semanticRetrievalEnabled": False,
            "retrievalMode": "hybrid",
            "llmImportAssistEnabled": False,
            "llmExplainabilityEnabled": False,
        }
        self._debug_logs: deque[dict] = deque(maxlen=300)

    def import_dataset(self, *, dataset_kind: str, path: str | None = None, mode: str = "replace") -> dict:
        bootstrap_database()
        if mode not in {"replace", "append"}:
            raise ValueError(f"Unknown import mode: {mode}")
        source_path = self._resolve_source_path(dataset_kind=dataset_kind, path=path)
        batch_id = f"import-{dataset_kind}-{uuid4()}"
        if dataset_kind == "pubmed" and mode == "replace" and self._is_pubmed_append_only_source(source_path):
            report_dict = {
                "datasetKind": dataset_kind,
                "datasetShape": "append_only_demo",
                "path": str(source_path),
                "errorCount": 1,
                "warningCount": 0,
                "info": ["Demo PubMed delta files are append-only."],
                "errors": [
                    {
                        "severity": "error",
                        "code": "append_only_demo_path",
                        "message": "This PubMed demo file is append-only. Use Append Delta instead of Import.",
                        "record_id": None,
                    }
                ],
                "warnings": [],
            }
            notes = ["Import blocked. Demo PubMed delta files are append-only; use Append Delta instead."]
            corpus_store.save_import_batch(
                batch_id=batch_id,
                dataset_kind=dataset_kind,
                dataset_shape=report_dict["datasetShape"],
                source_path=str(source_path),
                status="unsafe_mode_blocked",
                record_count=0,
                imported_count=0,
                error_count=report_dict["errorCount"],
                warning_count=report_dict["warningCount"],
                validation_payload=report_dict,
                notes=notes,
            )
            self._add_debug_log(
                level="error",
                event="import_blocked_unsafe_mode",
                dataset_kind=dataset_kind,
                path=str(source_path),
                message="Import blocked for append-only PubMed demo file.",
                details={"batchId": batch_id, "mode": mode},
            )
            return corpus_store.get_import_batch(batch_id) or {}
        source_files = self._collect_source_files(dataset_kind=dataset_kind, source_path=source_path)
        strict_mvp = dataset_kind == "pubmed" and self._debug_config["strictMvpPubmed"]
        self._add_debug_log(
            level="info",
            event="import_started",
            dataset_kind=dataset_kind,
            path=str(source_path),
            message="Import requested.",
            details={"strictMvpPubmed": strict_mvp, "sourceFileCount": len(source_files), "mode": mode},
        )
        reports = [self._validate_dataset_file(file_path, dataset_kind, strict_mvp_pubmed=strict_mvp) for file_path in source_files]
        report_dict = self._merge_validation_reports(dataset_kind=dataset_kind, source_path=source_path, reports=reports)

        if report_dict["errorCount"]:
            notes = ["Validation failed. Dataset was not imported."]
            corpus_store.save_import_batch(
                batch_id=batch_id,
                dataset_kind=dataset_kind,
                dataset_shape=report_dict["datasetShape"],
                source_path=str(source_path),
                status="failed_validation",
                record_count=self._record_count(report_dict),
                imported_count=0,
                error_count=report_dict["errorCount"],
                warning_count=report_dict["warningCount"],
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
                    "errorCount": report_dict["errorCount"],
                    "warningCount": report_dict["warningCount"],
                    "strictMvpPubmed": strict_mvp,
                    "sourceFileCount": len(source_files),
                },
            )
            return corpus_store.get_import_batch(batch_id) or {}

        try:
            normalized_records: list[dict] = []
            for file_path, report in zip(source_files, reports, strict=False):
                normalized_records.extend(
                    self._normalize(dataset_kind=dataset_kind, source_path=file_path, dataset_shape=report.dataset_shape)
                )
        except ValueError as exc:
            notes = [str(exc)]
            corpus_store.save_import_batch(
                batch_id=batch_id,
                dataset_kind=dataset_kind,
                dataset_shape=report_dict["datasetShape"],
                source_path=str(source_path),
                status="normalization_blocked",
                record_count=self._record_count(report_dict),
                imported_count=0,
                error_count=report_dict["errorCount"],
                warning_count=report_dict["warningCount"],
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
                    "errorCount": report_dict["errorCount"],
                    "warningCount": report_dict["warningCount"],
                    "strictMvpPubmed": strict_mvp,
                    "sourceFileCount": len(source_files),
                },
            )
            return corpus_store.get_import_batch(batch_id) or {}

        ingest_result = self._ingest(dataset_kind=dataset_kind, batch_id=batch_id, records=normalized_records, mode=mode)
        imported_count = ingest_result["processedCount"]
        action_verb = self._import_action_verb(dataset_kind=dataset_kind, mode=mode)
        notes = [f"{action_verb} successfully."]
        if report_dict["warningCount"]:
            notes = [f"{action_verb} with validation warnings."]
        if mode == "append":
            if dataset_kind == "pubmed":
                notes.append(
                    f"PubMed delta applied: {ingest_result['addedCount']} added, {ingest_result['updatedCount']} updated."
                )
                if semantic_retrieval_service is not None and self._debug_config.get("semanticRetrievalEnabled", False):
                    try:
                        semantic_result = semantic_retrieval_service.import_runtime_records_delta(
                            dataset_kind=dataset_kind,
                            records=normalized_records,
                            retrieval_mode=str(self._debug_config.get("retrievalMode", "hybrid")),
                            import_batch_id=batch_id,
                        )
                        notes.append(
                            "Semantic runtime delta refreshed: "
                            f"{semantic_result.get('documentCount', 0)} docs / {semantic_result.get('chunkCount', 0)} chunks."
                        )
                    except Exception as exc:
                        notes.append(f"Semantic runtime delta refresh failed after append. Reason: {exc}")
            else:
                notes.append(
                    f"ESMO corpus merged by topicId: {ingest_result['addedCount']} added, {ingest_result['updatedCount']} updated."
                )
                if semantic_retrieval_service is not None and self._debug_config.get("semanticRetrievalEnabled", False):
                    try:
                        semantic_result = semantic_retrieval_service.import_runtime_dataset(
                            dataset_kind=dataset_kind,
                            retrieval_mode=str(self._debug_config.get("retrievalMode", "hybrid")),
                        )
                        notes.append(
                            "Semantic runtime fully refreshed after append: "
                            f"{semantic_result.get('documentCount', 0)} docs / {semantic_result.get('chunkCount', 0)} chunks."
                        )
                    except Exception as exc:
                        notes.append(f"Semantic runtime full refresh failed after append. Reason: {exc}")
        elif semantic_retrieval_service is not None and self._debug_config.get("semanticRetrievalEnabled", False):
            try:
                semantic_result = semantic_retrieval_service.import_runtime_dataset(
                    dataset_kind=dataset_kind,
                    retrieval_mode=str(self._debug_config.get("retrievalMode", "hybrid")),
                )
                notes.append(
                    "Semantic runtime fully refreshed after replace: "
                    f"{semantic_result.get('documentCount', 0)} docs / {semantic_result.get('chunkCount', 0)} chunks."
                )
            except Exception as exc:
                notes.append(f"Semantic runtime full refresh failed after replace. Reason: {exc}")
        status = "completed" if not report_dict["warningCount"] else "completed_with_warnings"
        corpus_store.save_import_batch(
            batch_id=batch_id,
            dataset_kind=dataset_kind,
            dataset_shape=report_dict["datasetShape"],
            source_path=str(source_path),
            status=status,
            record_count=len(normalized_records),
            imported_count=imported_count,
            error_count=report_dict["errorCount"],
            warning_count=report_dict["warningCount"],
            validation_payload=report_dict,
            notes=notes,
        )
        self._add_debug_log(
            level="warning" if report_dict["warningCount"] else "info",
            event="import_completed",
            dataset_kind=dataset_kind,
            path=str(source_path),
            message="Import completed.",
            details={
                "batchId": batch_id,
                "status": status,
                "recordCount": len(normalized_records),
                "importedCount": imported_count,
                "errorCount": report_dict["errorCount"],
                "warningCount": report_dict["warningCount"],
                "strictMvpPubmed": strict_mvp,
                "sourceFileCount": len(source_files),
                "mode": mode,
            },
        )
        return corpus_store.get_import_batch(batch_id) or {}

    def validate_dataset(self, *, dataset_kind: str, path: str | None = None) -> dict:
        source_path = self._resolve_source_path(dataset_kind=dataset_kind, path=path)
        source_files = self._collect_source_files(dataset_kind=dataset_kind, source_path=source_path)
        strict_mvp = dataset_kind == "pubmed" and self._debug_config["strictMvpPubmed"]
        reports = [self._validate_dataset_file(file_path, dataset_kind, strict_mvp_pubmed=strict_mvp) for file_path in source_files]
        report = self._merge_validation_reports(dataset_kind=dataset_kind, source_path=source_path, reports=reports)
        self._add_debug_log(
            level="warning" if report["warningCount"] else "info",
            event="validation_completed" if not report["errorCount"] else "validation_failed",
            dataset_kind=dataset_kind,
            path=str(source_path),
            message="Validation completed." if not report["errorCount"] else "Validation found blocking issues.",
            details={
                "errorCount": report["errorCount"],
                "warningCount": report["warningCount"],
                "strictMvpPubmed": strict_mvp,
                "sourceFileCount": len(source_files),
            },
        )
        return report

    def list_dataset_entries(self, *, dataset_kind: str) -> dict:
        suffixes = self.SUPPORTED_IMPORT_SUFFIXES[dataset_kind]
        logical_root = self.LOGICAL_DATASET_ROOTS[dataset_kind]
        file_paths: set[Path] = set()

        for root in self._existing_dataset_roots(dataset_kind):
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                relative_parts = path.relative_to(root).parts
                if any(part.startswith(".") for part in relative_parts):
                    continue
                if path.suffix.lower() not in suffixes:
                    continue
                file_paths.add(logical_root / Path(*relative_parts))

        file_entries = [{"path": str(path), "kind": "file", "fileCount": 1} for path in sorted(file_paths)]

        directory_counts: dict[Path, int] = {}
        for file_path in file_paths:
            current = file_path.parent
            while current != logical_root.parent and current != file_path:
                if current == logical_root:
                    break
                directory_counts[current] = directory_counts.get(current, 0) + 1
                current = current.parent

        directory_entries = [
            {"path": str(path), "kind": "folder", "fileCount": count}
            for path, count in sorted(directory_counts.items(), key=lambda item: item[0])
        ]

        return {"datasetKind": dataset_kind, "rootPath": str(logical_root), "entries": directory_entries + file_entries}

    def get_import_batch(self, batch_id: str) -> dict | None:
        return corpus_store.get_import_batch(batch_id)

    def list_import_batches(self) -> list[dict]:
        bootstrap_database()
        return corpus_store.list_import_batches()

    def get_import_summary(self) -> dict:
        bootstrap_database()
        summary = corpus_store.get_import_summary()
        if summary.get("activeTopics", 0) == 0:
            summary["activeTopics"] = self._count_records_from_packaged_dataset("esmo")
        if summary.get("activeEvidenceStudies", 0) == 0:
            summary["activeEvidenceStudies"] = self._count_records_from_packaged_dataset("pubmed")
        if semantic_store is not None:
            summary.update(semantic_store.get_summary())
        else:
            summary.update({"semanticDocuments": 0, "semanticChunks": 0, "semanticCollections": {}})
        return summary

    def get_debug_config(self) -> dict:
        return dict(self._debug_config)

    def update_debug_config(
        self,
        *,
        strict_mvp_pubmed: bool,
        runtime_engine: str = "deterministic",
        semantic_retrieval_enabled: bool = False,
        retrieval_mode: str = "hybrid",
        llm_import_assist_enabled: bool = False,
        llm_explainability_enabled: bool = False,
    ) -> dict:
        self._debug_config["strictMvpPubmed"] = strict_mvp_pubmed
        self._debug_config["runtimeEngine"] = runtime_engine
        self._debug_config["semanticRetrievalEnabled"] = semantic_retrieval_enabled
        self._debug_config["retrievalMode"] = retrieval_mode
        self._debug_config["llmImportAssistEnabled"] = llm_import_assist_enabled
        self._debug_config["llmExplainabilityEnabled"] = llm_explainability_enabled
        self._add_debug_log(
            level="info",
            event="debug_config_updated",
            dataset_kind=None,
            path=None,
            message="Import debug config updated.",
            details=self.get_debug_config(),
        )
        return self.get_debug_config()

    def resolve_saved_source_path(self, *, dataset_kind: str, source_path: str) -> Path:
        candidate = Path(source_path)
        if candidate.exists():
            return candidate

        normalized = source_path.replace("\\", "/")
        marker = "/datasets/"
        if marker in normalized:
            relative = Path(normalized.split(marker, 1)[1])
            for base in (PACKAGE_ROOT / "datasets", REPO_ROOT / "datasets"):
                resolved = (base / relative).resolve()
                if resolved.exists():
                    return resolved

        logical_root = self.LOGICAL_DATASET_ROOTS[dataset_kind]
        logical_marker = f"{logical_root.as_posix()}/"
        if logical_marker in normalized:
            relative = Path(normalized.split(logical_marker, 1)[1])
            for base in self._existing_dataset_roots(dataset_kind):
                resolved = (base / relative).resolve()
                if resolved.exists():
                    return resolved

        return candidate

    def load_normalized_records_from_source(self, *, dataset_kind: str, source_path: str | None = None) -> list[dict]:
        resolved_source = (
            self.resolve_saved_source_path(dataset_kind=dataset_kind, source_path=source_path)
            if source_path
            else self._resolve_source_path(dataset_kind=dataset_kind, path=None)
        )
        source_files = self._collect_source_files(dataset_kind=dataset_kind, source_path=resolved_source)
        strict_mvp = dataset_kind == "pubmed" and bool(self._debug_config["strictMvpPubmed"])
        normalized_records: list[dict] = []

        for file_path in source_files:
            report = self._validate_dataset_file(file_path, dataset_kind, strict_mvp_pubmed=strict_mvp)
            normalized_records.extend(
                self._normalize(dataset_kind=dataset_kind, source_path=file_path, dataset_shape=report.dataset_shape)
            )

        return normalized_records

    def get_debug_logs(self, *, limit: int = 80) -> list[dict]:
        clamped = max(1, min(limit, 300))
        return list(self._debug_logs)[-clamped:][::-1]

    def import_semantic_dataset(self, *, dataset_kind: str, path: str | None = None) -> dict:
        if semantic_retrieval_service is None:
            raise RuntimeError("Semantic Retrieval Lab dependencies are unavailable in this deployment.")
        retrieval_mode = str(self._debug_config.get("retrievalMode", "hybrid"))
        if path is None:
            result = semantic_retrieval_service.import_runtime_dataset(
                dataset_kind=dataset_kind,
                retrieval_mode=retrieval_mode,
            )
            source_path_label = f"runtime:{dataset_kind}:current_imported_corpus"
        else:
            source_path = self._resolve_source_path(dataset_kind=dataset_kind, path=path)
            result = semantic_retrieval_service.import_dataset(
                dataset_kind=dataset_kind,
                source_path=str(source_path),
                retrieval_mode=retrieval_mode,
            )
            source_path_label = str(source_path)
        self._add_debug_log(
            level="info",
            event="semantic_import_completed",
            dataset_kind=dataset_kind,
            path=source_path_label,
            message="Semantic Retrieval Lab corpus refreshed.",
            details={"retrievalMode": retrieval_mode, "status": result.get("latestStatus"), "chunkCount": result.get("chunkCount")},
        )
        return result

    def get_semantic_status(self, *, dataset_kind: str) -> dict:
        if semantic_retrieval_service is None:
            return {
                "datasetKind": dataset_kind,
                "latestBatchId": None,
                "latestStatus": "unavailable",
                "documentCount": 0,
                "chunkCount": 0,
                "latestJob": None,
            }
        return semantic_retrieval_service.get_status(dataset_kind=dataset_kind)

    def _normalize(self, *, dataset_kind: str, source_path: Path, dataset_shape: str) -> list[dict]:
        if dataset_kind == "esmo" and dataset_shape == "external_v2":
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            rows = payload["records"] if isinstance(payload, dict) else payload
            return [self._normalize_esmo_v2_record(row) for row in rows]

        if dataset_shape == "canonical":
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            return payload["records"] if isinstance(payload, dict) and isinstance(payload.get("records"), list) else payload

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

        from scripts.build_curated_preview import build_evidence, build_topics

        if dataset_kind == "esmo":
            return build_topics()
        if dataset_kind == "pubmed":
            return build_evidence()
        raise ValueError(f"Unknown dataset kind `{dataset_kind}`.")

    def _ingest(self, *, dataset_kind: str, batch_id: str, records: list[dict], mode: str = "replace") -> dict[str, int]:
        if dataset_kind == "esmo":
            if mode == "replace":
                processed = corpus_store.replace_guideline_topics(batch_id=batch_id, topics=records)
                return {"processedCount": processed, "addedCount": processed, "updatedCount": 0}
            return corpus_store.merge_guideline_topics(batch_id=batch_id, topics=records)
        if dataset_kind == "pubmed":
            if mode == "append":
                return corpus_store.append_evidence_studies(batch_id=batch_id, evidence_records=records)
            processed = corpus_store.replace_evidence_studies(batch_id=batch_id, evidence_records=records)
            return {"processedCount": processed, "addedCount": processed, "updatedCount": 0}
        raise ValueError(f"Unknown dataset kind `{dataset_kind}`.")

    @staticmethod
    def _import_action_verb(*, dataset_kind: str, mode: str) -> str:
        if mode == "append":
            return "Merged" if dataset_kind == "esmo" else "Appended"
        return "Imported"

    def _normalize_pubmed_v2_row(self, row: dict[str, str]) -> dict:
        pmid = row["pmid"].strip()
        evidence_type = self._normalize_evidence_type(row.get("evidenceType", ""), publication_type=row.get("publicationType", ""))
        pubmed_text = self._normalize_pubmed_context_text(row)
        intervention_tags = self._parse_list_cell(row.get("interventionTags", ""))

        disease_setting = self._normalize_enum_value(
            row.get("diseaseSetting", ""), allowed=self.PUBMED_DISEASE_SETTING_ALLOWED, fallback="unspecified"
        )
        histology = self._normalize_enum_value(row.get("histology", ""), allowed=self.PUBMED_HISTOLOGY_ALLOWED, fallback="unspecified")
        line_of_therapy = self._normalize_enum_value(row.get("lineOfTherapy", ""), allowed=self.PUBMED_LINE_ALLOWED, fallback="unspecified")
        disease_stage = self._normalize_enum_value(
            row.get("diseaseStage", ""), allowed=self.PUBMED_DISEASE_STAGE_ALLOWED, fallback="unspecified"
        )
        resectability_status = self._normalize_enum_value(
            row.get("resectabilityStatus", ""), allowed=self.PUBMED_RESECTABILITY_ALLOWED, fallback="unspecified"
        )
        treatment_context = self._normalize_enum_value(
            row.get("treatmentContext", ""), allowed=self.PUBMED_TREATMENT_CONTEXT_ALLOWED, fallback="unspecified"
        )
        biomarkers = self._normalize_biomarkers(row.get("biomarkers", ""))
        line_of_therapy = self._infer_pubmed_line_of_therapy(
            line_of_therapy=line_of_therapy,
            pubmed_text=pubmed_text,
            intervention_tags=intervention_tags,
        )
        disease_stage = self._infer_pubmed_disease_stage(disease_stage=disease_stage, pubmed_text=pubmed_text)
        resectability_status = self._infer_pubmed_resectability(
            resectability_status=resectability_status,
            pubmed_text=pubmed_text,
            line_of_therapy=line_of_therapy,
        )
        treatment_context = self._infer_pubmed_treatment_context(
            treatment_context=treatment_context,
            pubmed_text=pubmed_text,
            line_of_therapy=line_of_therapy,
        )
        disease_setting = self._infer_pubmed_disease_setting(
            disease_setting=disease_setting,
            disease_stage=disease_stage,
            pubmed_text=pubmed_text,
            line_of_therapy=line_of_therapy,
        )

        return {
            "evidenceId": f"PMID-{pmid}",
            "title": row.get("title", "").strip(),
            "abstract": row.get("abstract", "").strip() or None,
            "journalTitle": row.get("journalTitle", "").strip() or None,
            "publicationYear": self._parse_int(row.get("publicationYear", "")),
            "evidenceType": evidence_type,
            "relevantN": self._parse_int(row.get("relevantN", "")),
            "sourceCategory": self._infer_source_category(row.get("journalTitle", "")),
            "populationTags": {
                "disease": "NSCLC",
                "diseaseSetting": disease_setting,
                "histology": histology,
                "lineOfTherapy": line_of_therapy,
                "diseaseStage": disease_stage,
                "resectabilityStatus": resectability_status,
                "treatmentContext": treatment_context,
                "biomarkers": biomarkers,
            },
            "interventionTags": intervention_tags,
            "outcomeTags": self._parse_list_cell(row.get("outcomeTags", "")),
        }

    def _normalize_esmo_v2_record(self, row: dict[str, object]) -> dict:
        disease_setting = self._normalize_token(str(row.get("diseaseSetting", ""))) or "unspecified"
        histology = self._normalize_token(str(row.get("histology", ""))) or "unspecified"
        line_of_therapy_raw = self._normalize_token(str(row.get("lineOfTherapy", ""))) or "unspecified"
        line_of_therapy = self.ESMO_LINE_OF_THERAPY_ALIASES.get(line_of_therapy_raw, line_of_therapy_raw)

        biomarker_requirements = row.get("biomarkerRequirements", {}) if isinstance(row.get("biomarkerRequirements"), dict) else {}
        biomarker_logic = row.get("biomarkerLogic", {}) if isinstance(row.get("biomarkerLogic"), dict) else {}

        biomarker_conditions: list[str] = []
        pdl1_values = biomarker_requirements.get("PDL1Bucket", [])
        if isinstance(pdl1_values, list):
            normalized_pdl1 = [self._normalize_token(str(value)) for value in pdl1_values if str(value).strip()]
            normalized_pdl1 = [value for value in normalized_pdl1 if value not in {"unspecified", "any"}]
            if len(normalized_pdl1) == 1:
                biomarker_conditions.append(f"PDL1Bucket={normalized_pdl1[0]}")
            elif len(normalized_pdl1) > 1:
                biomarker_conditions.append(f"PDL1Bucket in [{','.join(normalized_pdl1)}]")

        any_positive = biomarker_logic.get("anyPositive", [])
        if isinstance(any_positive, list) and any_positive:
            biomarker_conditions.append(f"any_positive({','.join(str(value).strip() for value in any_positive if str(value).strip())})")

        all_negative = biomarker_logic.get("allNegative", [])
        if isinstance(all_negative, list) and all_negative:
            biomarker_conditions.append(f"all_negative({','.join(str(value).strip() for value in all_negative if str(value).strip())})")

        notes = biomarker_logic.get("notes", "")
        stance_notes = str(notes).strip() if isinstance(notes, str) and str(notes).strip() else None
        topic_text = self._normalize_esmo_context_text(row)
        topic_title = str(row.get("topicTitle", "")).strip().lower()
        inferred_line_of_therapy = self._infer_esmo_line_of_therapy(
            line_of_therapy=line_of_therapy,
            topic_text=topic_text,
            intervention_tags=row.get("topicInterventionTags", []),
        )
        disease_stage = self._explicit_or_inferred_esmo_list(
            raw_value=row.get("diseaseStage"),
            allowed=self.PUBMED_DISEASE_STAGE_ALLOWED - {"mixed"},
            inferred=self._infer_esmo_disease_stages(
                topic_id=str(row.get("topicId", "")).strip(),
                topic_title=topic_title,
                topic_text=topic_text,
            ),
        )
        resectability_status = self._explicit_or_inferred_esmo_list(
            raw_value=row.get("resectabilityStatus"),
            allowed=self.PUBMED_RESECTABILITY_ALLOWED,
            inferred=self._infer_esmo_resectability(
                topic_text=topic_text,
                line_of_therapy=inferred_line_of_therapy,
            ),
        )
        treatment_context = self._explicit_or_inferred_esmo_list(
            raw_value=row.get("treatmentContext"),
            allowed=self.PUBMED_TREATMENT_CONTEXT_ALLOWED,
            inferred=self._infer_esmo_treatment_context(
                topic_text=topic_text,
                line_of_therapy=inferred_line_of_therapy,
            ),
        )
        disease_settings = self._explicit_or_inferred_esmo_list(
            raw_value=row.get("diseaseSettingList"),
            allowed=self.PUBMED_DISEASE_SETTING_ALLOWED - {"mixed", "unspecified"},
            inferred=self._infer_esmo_disease_settings(
                disease_setting=disease_setting,
                disease_stage=disease_stage,
                line_of_therapy=inferred_line_of_therapy,
                resectability_status=resectability_status,
                topic_text=topic_text,
            ),
        )

        return {
            "topicId": str(row.get("topicId", "")).strip(),
            "topicTitle": str(row.get("topicTitle", "")).strip(),
            "topicApplicability": {
                "diseaseSetting": disease_settings,
                "histology": [histology],
                "lineOfTherapy": [inferred_line_of_therapy],
                "diseaseStage": disease_stage,
                "resectabilityStatus": resectability_status,
                "treatmentContext": treatment_context,
                "biomarkerConditions": biomarker_conditions,
            },
            "topicInterventionTags": [str(tag).strip() for tag in row.get("topicInterventionTags", []) if str(tag).strip()],
            "guidelineStance": str(row.get("guidelineStance", "")).strip(),
            "stanceNotes": stance_notes,
            "prerequisites": [],
        }

    def _normalize_esmo_context_text(self, row: dict[str, object]) -> str:
        parts = [
            str(row.get("topicTitle", "")).strip(),
            str(row.get("sourceExcerptShort", "")).strip(),
            str(row.get("applicabilityNotes", "")).strip(),
            " ".join(str(tag).strip() for tag in row.get("topicInterventionTags", []) if str(tag).strip()),
        ]
        normalized = " ".join(part for part in parts if part).lower()
        return normalized.replace("≥", ">=").replace("–", "-").replace("‑", "-")

    def _normalize_pubmed_context_text(self, row: dict[str, str]) -> str:
        parts = [
            row.get("title", "").strip(),
            row.get("abstract", "").strip(),
            row.get("journalTitle", "").strip(),
            row.get("interventionTags", "").strip(),
            row.get("outcomeTags", "").strip(),
        ]
        normalized = " ".join(part for part in parts if part).lower()
        return normalized.replace("≥", ">=").replace("–", "-").replace("‑", "-")

    def _infer_pubmed_line_of_therapy(self, *, line_of_therapy: str, pubmed_text: str, intervention_tags: list[str]) -> str:
        if line_of_therapy != "unspecified":
            return line_of_therapy
        tag_text = " ".join(tag.lower() for tag in intervention_tags)
        searchable = f"{pubmed_text} {tag_text}"
        if "adjuvant" in searchable:
            return "adjuvant"
        if "consolidation" in searchable or "after chemoradiotherapy" in searchable or "after chemoradiation" in searchable:
            return "consolidation"
        return "unspecified"

    def _infer_pubmed_disease_stage(self, *, disease_stage: str, pubmed_text: str) -> str:
        if disease_stage != "unspecified":
            return disease_stage
        if re.search(r"\bstage\s+iv\b", pubmed_text):
            return "stage_iv"
        if re.search(r"\bstage\s+iii(?:a|b|c)?\b", pubmed_text) or re.search(r"\biii(?:a|b|c)?\b", pubmed_text):
            return "stage_iii"
        if re.search(r"\bstage\s+ii(?!i)(?:a|b|c)?\b", pubmed_text) or re.search(r"\bii(?!i)(?:a|b|c)?\b", pubmed_text):
            return "stage_ii"
        if re.search(r"\bstage\s+i(?:a|b|c)?\b", pubmed_text) or re.search(r"\bib\b", pubmed_text):
            return "stage_i"
        return "unspecified"

    def _infer_pubmed_resectability(self, *, resectability_status: str, pubmed_text: str, line_of_therapy: str) -> str:
        if resectability_status != "unspecified":
            return resectability_status
        if "unresectable" in pubmed_text:
            return "unresectable"
        if line_of_therapy == "adjuvant" or any(
            phrase in pubmed_text
            for phrase in ("resected", "postoperative", "after surgery", "post surgery", "curative resection")
        ):
            return "resected"
        return "unspecified"

    def _infer_pubmed_treatment_context(self, *, treatment_context: str, pubmed_text: str, line_of_therapy: str) -> str:
        if treatment_context != "unspecified":
            return treatment_context
        if line_of_therapy == "consolidation" or any(
            phrase in pubmed_text
            for phrase in ("after chemoradiotherapy", "after chemoradiation", "post chemoradiation", "post-chemoradiation")
        ):
            return "post_chemoradiation"
        if line_of_therapy == "adjuvant" or any(
            phrase in pubmed_text for phrase in ("after surgery", "postoperative", "post surgery", "curative resection")
        ):
            return "post_surgery"
        return "unspecified"

    def _infer_pubmed_disease_setting(
        self,
        *,
        disease_setting: str,
        disease_stage: str,
        pubmed_text: str,
        line_of_therapy: str,
    ) -> str:
        if disease_setting != "unspecified":
            return disease_setting
        if "metastatic" in pubmed_text or disease_stage == "stage_iv":
            return "metastatic"
        if "locally advanced" in pubmed_text or disease_stage == "stage_iii" or line_of_therapy == "consolidation":
            return "locally_advanced"
        if line_of_therapy == "adjuvant" or disease_stage in {"stage_i", "stage_ii"}:
            return "early"
        return "unspecified"

    def _explicit_or_inferred_esmo_list(
        self,
        *,
        raw_value: object,
        allowed: set[str],
        inferred: list[str],
    ) -> list[str]:
        values: list[str] = []
        if isinstance(raw_value, list):
            values = [
                self._normalize_enum_value(str(value), allowed=allowed, fallback="__invalid__")
                for value in raw_value
                if str(value).strip()
            ]
        elif isinstance(raw_value, str) and raw_value.strip():
            values = [self._normalize_enum_value(raw_value, allowed=allowed, fallback="__invalid__")]
        values = [value for value in values if value in allowed]
        if values:
            return list(dict.fromkeys(values))
        return inferred

    def _infer_esmo_line_of_therapy(self, *, line_of_therapy: str, topic_text: str, intervention_tags: object) -> str:
        tag_text = " ".join(str(tag).strip().lower() for tag in intervention_tags if str(tag).strip()) if isinstance(intervention_tags, list) else ""
        searchable = f"{topic_text} {tag_text}"
        if "adjuvant" in searchable:
            return "adjuvant"
        if "consolidation" in searchable:
            return "consolidation"
        return line_of_therapy

    def _infer_esmo_disease_stages(self, *, topic_id: str, topic_title: str, topic_text: str) -> list[str]:
        primary_text = topic_title or topic_text
        stages: list[str] = []
        if topic_id.startswith("NSCLC_STAGE1_"):
            stages.append("stage_i")
        if re.search(r"\bstage\s+i(?:a|b|c)?\b", primary_text):
            stages.append("stage_i")
        if re.search(r"\bstage\s+ii(?!i)(?:a|b|c)?\b", primary_text):
            stages.append("stage_ii")
        if re.search(r"\bstage\s+iii(?:a|b|c)?\b", primary_text):
            stages.append("stage_iii")
        if "stage" in primary_text:
            if re.search(r"\bib\b", primary_text):
                stages.append("stage_i")
            if re.search(r"\bii(?!i)(?:a|b|c)?\b", primary_text):
                stages.append("stage_ii")
            if re.search(r"\biii(?:a|b|c)?\b", primary_text):
                stages.append("stage_iii")
        if stages:
            return list(dict.fromkeys(stages))
        if re.search(r"\bstage\s+i(?:a|b|c)?\b", topic_text):
            stages.append("stage_i")
        if re.search(r"\bstage\s+ii(?!i)(?:a|b|c)?\b", topic_text):
            stages.append("stage_ii")
        if re.search(r"\bstage\s+iii(?:a|b|c)?\b", topic_text):
            stages.append("stage_iii")
        return list(dict.fromkeys(stages)) or ["unspecified"]

    def _infer_esmo_resectability(self, *, topic_text: str, line_of_therapy: str) -> list[str]:
        if "unresectable" in topic_text:
            return ["unresectable"]
        if line_of_therapy == "adjuvant" or any(
            phrase in topic_text
            for phrase in (
                "completely resected",
                "resected",
                "after r0 resection",
                "after r1 resection",
                "postoperative",
                "post surgery",
                "after surgery",
            )
        ):
            return ["resected"]
        return ["unspecified"]

    def _infer_esmo_treatment_context(self, *, topic_text: str, line_of_therapy: str) -> list[str]:
        if line_of_therapy == "consolidation" or any(
            phrase in topic_text
            for phrase in (
                "after concurrent crt",
                "after sequential crt",
                "after crt",
                "after chemoradiotherapy",
                "after chemoradiation",
                "following crt",
                "end of crt",
            )
        ):
            return ["post_chemoradiation"]
        if line_of_therapy == "adjuvant" or any(
            phrase in topic_text
            for phrase in (
                "after surgery",
                "post surgery",
                "postoperative",
                "completely resected",
                "resected",
                "after r0 resection",
                "after r1 resection",
            )
        ):
            return ["post_surgery"]
        return ["unspecified"]

    def _infer_esmo_disease_settings(
        self,
        *,
        disease_setting: str,
        disease_stage: list[str],
        line_of_therapy: str,
        resectability_status: list[str],
        topic_text: str,
    ) -> list[str]:
        values = [disease_setting]
        if (
            disease_setting == "locally_advanced"
            and "stage_ii" in disease_stage
            and (line_of_therapy == "adjuvant" or "resected" in resectability_status or "resectable" in topic_text)
        ):
            values.insert(0, "early")
        return list(dict.fromkeys(value for value in values if value and value != "unspecified")) or ["unspecified"]

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
        return publication_mapped or "unspecified"

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
        if allowed is self.PUBMED_DISEASE_SETTING_ALLOWED:
            normalized = self.PUBMED_DISEASE_SETTING_ALIASES.get(normalized, normalized)
        return normalized if normalized in allowed else fallback

    def _resolve_source_path(self, *, dataset_kind: str, path: str | None) -> Path:
        if not path:
            return self._resolve_default_source_path(dataset_kind)

        raw_path = path.strip()
        if raw_path.startswith("/datasets/"):
            raw_path = raw_path.removeprefix("/")

        candidate = Path(raw_path).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()

        logical_root = self.LOGICAL_DATASET_ROOTS[dataset_kind]
        if candidate == logical_root or logical_root in candidate.parents:
            relative_path = candidate.relative_to(logical_root)
            for root in self._existing_dataset_roots(dataset_kind):
                resolved = (root / relative_path).resolve()
                if resolved.exists():
                    return resolved
            return (self._dataset_root_candidates(dataset_kind)[0] / relative_path).resolve()

        return (REPO_ROOT / candidate).resolve()

    def _resolve_default_source_path(self, dataset_kind: str) -> Path:
        filename = self.DEFAULT_DATASET_FILENAMES[dataset_kind]
        for root in self._existing_dataset_roots(dataset_kind):
            candidate = (root / filename).resolve()
            if candidate.exists():
                return candidate
        return (self._dataset_root_candidates(dataset_kind)[0] / filename).resolve()

    def _dataset_root_candidates(self, dataset_kind: str) -> list[Path]:
        candidates = self.DATASET_ROOT_CANDIDATES[dataset_kind]
        deduped: list[Path] = []
        seen: set[Path] = set()
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            deduped.append(resolved)
        return deduped

    def _existing_dataset_roots(self, dataset_kind: str) -> list[Path]:
        return [path for path in self._dataset_root_candidates(dataset_kind) if path.exists()]

    def _is_pubmed_append_only_source(self, source_path: Path) -> bool:
        if not source_path.exists():
            return False
        resolved = source_path.resolve()
        for root in self._existing_dataset_roots("pubmed"):
            demo_root = (root / "demo").resolve()
            try:
                resolved.relative_to(demo_root)
                return True
            except ValueError:
                continue
        return False

    def _count_records_from_packaged_dataset(self, dataset_kind: str) -> int:
        source_path = self._resolve_default_source_path(dataset_kind)
        if not source_path.exists():
            return 0
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return len(payload["records"])
        if isinstance(payload, list):
            return len(payload)
        return 0

    def _collect_source_files(self, *, dataset_kind: str, source_path: Path) -> list[Path]:
        suffixes = self.SUPPORTED_IMPORT_SUFFIXES[dataset_kind]
        if source_path.is_file():
            return [source_path]
        if not source_path.is_dir():
            raise ValueError(f"Import source does not exist: {source_path}")

        files = sorted(
            [
                path
                for path in source_path.rglob("*")
                if path.is_file()
                and path.suffix.lower() in suffixes
                and not any(part.startswith(".") for part in path.relative_to(source_path).parts)
            ]
        )
        if not files:
            raise ValueError(f"No supported {dataset_kind} files found in {source_path}")
        return files

    def _validate_dataset_file(self, source_path: Path, dataset_kind: str, *, strict_mvp_pubmed: bool = False) -> ValidationReport:
        try:
            from scripts.validate_data_drop import validate_dataset as external_validate_dataset
        except ModuleNotFoundError:
            external_validate_dataset = None

        if external_validate_dataset is not None:
            return external_validate_dataset(source_path, dataset_kind, strict_mvp_pubmed=strict_mvp_pubmed)

        suffix = source_path.suffix.lower()
        if suffix == ".json":
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            rows = payload["records"] if isinstance(payload, dict) and isinstance(payload.get("records"), list) else payload
        elif suffix in {".csv", ".txt"} and dataset_kind == "pubmed":
            with source_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        else:
            report = ValidationReport(dataset_kind=dataset_kind, dataset_shape="unsupported", path=str(source_path))
            report.add("error", "unsupported_runtime_format", f"This deployment cannot validate `{suffix}` for {dataset_kind}.")
            return report

        report = ValidationReport(dataset_kind=dataset_kind, dataset_shape=self._detect_dataset_shape(dataset_kind, rows), path=str(source_path))

        if not isinstance(rows, list) or not rows:
            report.add("error", "empty_payload", "Dataset must be a non-empty JSON array.")
            return report

        if dataset_kind == "esmo":
            if report.dataset_shape == "external_v2":
                self._validate_esmo_external_v2_rows(rows, report)
            else:
                self._validate_esmo_rows(rows, report)
        else:
            self._validate_pubmed_rows(rows, report, strict_mvp_pubmed=strict_mvp_pubmed)

        if report.error_count == 0:
            report.info.append("Serverless fallback validator completed.")
        return report

    def _detect_dataset_shape(self, dataset_kind: str, rows: object) -> str:
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            return "unknown"
        first_row = rows[0]
        if dataset_kind == "esmo":
            if self.ESMO_CANONICAL_REQUIRED_FIELDS.issubset(first_row.keys()):
                return "canonical"
            if {"topicId", "diseaseSetting", "histology", "lineOfTherapy"}.issubset(first_row.keys()):
                return "external_v2"
            return "raw"
        if self.PUBMED_CANONICAL_REQUIRED_FIELDS.issubset(first_row.keys()):
            return "canonical"
        if self.PUBMED_V2_REQUIRED_FIELDS.issubset(first_row.keys()):
            return "raw_v2"
        return "raw"

    def _validate_esmo_rows(self, rows: list[object], report: ValidationReport) -> None:
        seen_ids: set[str] = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                report.add("error", "non_object_row", f"Row {index} is not a JSON object.")
                continue
            record_id = str(row.get("topicId", f"row-{index}"))
            missing = self.ESMO_CANONICAL_REQUIRED_FIELDS - set(row.keys())
            if missing:
                report.add("error", "missing_required_fields", f"Missing ESMO fields: {sorted(missing)}", record_id)
                continue
            if record_id in seen_ids:
                report.add("error", "duplicate_topic_id", "Duplicate topicId.", record_id)
            seen_ids.add(record_id)
            if not isinstance(row.get("topicApplicability"), dict):
                report.add("error", "invalid_topic_applicability", "`topicApplicability` must be an object.", record_id)
            if not isinstance(row.get("topicInterventionTags"), list) or not row.get("topicInterventionTags"):
                report.add("error", "invalid_intervention_tags", "`topicInterventionTags` must be a non-empty list.", record_id)
            stance = str(row.get("guidelineStance", "")).strip()
            if stance not in {"recommend", "conditional", "do_not_recommend", "not_covered"}:
                report.add("error", "invalid_guideline_stance", f"Unknown guidelineStance `{stance}`.", record_id)

    def _validate_esmo_external_v2_rows(self, rows: list[object], report: ValidationReport) -> None:
        seen_ids: set[str] = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                report.add("error", "non_object_row", f"Row {index} is not a JSON object.")
                continue

            record_id = str(row.get("topicId", f"row-{index}"))
            missing = self.ESMO_EXTERNAL_V2_REQUIRED_FIELDS - set(row.keys())
            if missing:
                report.add("error", "missing_required_fields", f"Missing ESMO v2 fields: {sorted(missing)}", record_id)
                continue

            if record_id in seen_ids:
                report.add("error", "duplicate_topic_id", "Duplicate topicId.", record_id)
            seen_ids.add(record_id)

            for field in ("topicId", "topicTitle", "sourceExcerptShort", "applicabilityNotes"):
                if not isinstance(row.get(field), str) or not str(row.get(field)).strip():
                    report.add("error", "empty_required_value", f"Field `{field}` must be a non-empty string.", record_id)

            disease_setting = self._normalize_token(str(row.get("diseaseSetting", "")))
            histology = self._normalize_token(str(row.get("histology", "")))
            line_of_therapy_raw = self._normalize_token(str(row.get("lineOfTherapy", "")))
            line_of_therapy = self.ESMO_LINE_OF_THERAPY_ALIASES.get(line_of_therapy_raw, line_of_therapy_raw)
            stance = str(row.get("guidelineStance", "")).strip()

            if disease_setting not in self.PUBMED_DISEASE_SETTING_ALLOWED:
                report.add("error", "invalid_disease_setting", f"Unknown diseaseSetting `{row.get('diseaseSetting')}`.", record_id)
            if histology not in self.PUBMED_HISTOLOGY_ALLOWED:
                report.add("error", "invalid_histology", f"Unknown histology `{row.get('histology')}`.", record_id)
            if line_of_therapy not in self.PUBMED_LINE_ALLOWED:
                report.add("error", "invalid_line_of_therapy", f"Unknown lineOfTherapy `{row.get('lineOfTherapy')}`.", record_id)
            if stance not in {"recommend", "conditional", "do_not_recommend", "not_covered"}:
                report.add("error", "invalid_guideline_stance", f"Unknown guidelineStance `{stance}`.", record_id)

            tags = row.get("topicInterventionTags")
            if not isinstance(tags, list) or not tags:
                report.add("error", "invalid_intervention_tags", "`topicInterventionTags` must be a non-empty list.", record_id)

            biomarker_requirements = row.get("biomarkerRequirements")
            if not isinstance(biomarker_requirements, dict):
                report.add("error", "invalid_biomarker_requirements", "`biomarkerRequirements` must be an object.", record_id)
            else:
                pdl1_values = biomarker_requirements.get("PDL1Bucket", [])
                if not isinstance(pdl1_values, list):
                    report.add("error", "invalid_pdl1_bucket", "`biomarkerRequirements.PDL1Bucket` must be a list.", record_id)

            biomarker_logic = row.get("biomarkerLogic")
            if not isinstance(biomarker_logic, dict):
                report.add("error", "invalid_biomarker_logic", "`biomarkerLogic` must be an object.", record_id)
            else:
                for key in ("anyPositive", "allNegative"):
                    if not isinstance(biomarker_logic.get(key, []), list):
                        report.add("error", "invalid_biomarker_logic", f"`biomarkerLogic.{key}` must be a list.", record_id)
                if not isinstance(biomarker_logic.get("notes", ""), str):
                    report.add("error", "invalid_biomarker_logic", "`biomarkerLogic.notes` must be a string.", record_id)

            semantic_normalization = row.get("semanticNormalization")
            if not isinstance(semantic_normalization, dict):
                report.add("error", "invalid_semantic_normalization", "`semanticNormalization` must be an object.", record_id)
            else:
                ontology_tags = semantic_normalization.get("ontologyTags")
                if not isinstance(ontology_tags, dict):
                    report.add(
                        "error",
                        "invalid_semantic_normalization",
                        "`semanticNormalization.ontologyTags` must be an object.",
                        record_id,
                    )
                else:
                    for key in ("layer1", "layer2", "layer3"):
                        if not isinstance(ontology_tags.get(key, []), list):
                            report.add(
                                "error",
                                "invalid_semantic_normalization",
                                f"`ontologyTags.{key}` must be a list.",
                                record_id,
                            )

    def _validate_pubmed_rows(self, rows: list[object], report: ValidationReport, *, strict_mvp_pubmed: bool) -> None:
        seen_ids: set[str] = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                report.add("error", "non_object_row", f"Row {index} is not a JSON object.")
                continue
            record_id = str(row.get("evidenceId") or row.get("pmid") or f"row-{index}")
            required_fields = self.PUBMED_CANONICAL_REQUIRED_FIELDS
            if report.dataset_shape == "raw_v2":
                required_fields = self.PUBMED_V2_REQUIRED_FIELDS
            elif report.dataset_shape == "raw":
                required_fields = self.PUBMED_RAW_REQUIRED_FIELDS
            missing = required_fields - set(row.keys())
            if missing:
                report.add("error", "missing_required_fields", f"Missing PubMed fields: {sorted(missing)}", record_id)
                continue
            if record_id in seen_ids:
                report.add("error", "duplicate_evidence_id", "Duplicate evidence identifier.", record_id)
            seen_ids.add(record_id)

            if report.dataset_shape == "canonical":
                population_tags = row.get("populationTags")
                if not isinstance(population_tags, dict):
                    report.add("error", "invalid_population_tags", "`populationTags` must be an object.", record_id)
                evidence_type = str(row.get("evidenceType", "")).strip()
            else:
                evidence_type = self._normalize_evidence_type(
                    str(row.get("evidenceType", "")),
                    publication_type=str(row.get("publicationType", "")),
                )
            if evidence_type not in self.PUBMED_EVIDENCE_TYPES:
                report.add("error", "invalid_evidence_type", f"Unknown evidenceType `{evidence_type}`.", record_id)
            elif strict_mvp_pubmed and evidence_type not in {"phase3_rct", "systematic_review"}:
                report.add(
                    "error",
                    "evidence_type_outside_mvp_scope",
                    f"evidenceType `{evidence_type}` is outside MVP scope.",
                    record_id,
                )
            else:
                self._validate_pubmed_raw_row(row, report, record_id=record_id, strict_mvp_pubmed=strict_mvp_pubmed)

    def _validate_pubmed_raw_row(
        self,
        row: dict[str, object],
        report: ValidationReport,
        *,
        record_id: str,
        strict_mvp_pubmed: bool,
    ) -> None:
        if report.dataset_shape == "raw_v2":
            for field, allowed in (
                ("diseaseSetting", self.PUBMED_DISEASE_SETTING_ALLOWED),
                ("histology", self.PUBMED_HISTOLOGY_ALLOWED),
                ("lineOfTherapy", self.PUBMED_LINE_ALLOWED),
            ):
                raw_value = str(row.get(field, "")).strip()
                if not raw_value:
                    report.add("error", "empty_required_value", f"Field `{field}` must be a non-empty string.", record_id)
                    continue
                normalized = "mixed" if "," in raw_value else self._normalize_enum_value(raw_value, allowed=allowed, fallback="__invalid__")
                if normalized not in allowed:
                    report.add("error", f"invalid_{field}", f"Unknown {field} `{raw_value}`.", record_id)

            biomarkers = self._normalize_biomarkers(str(row.get("biomarkers", "")))
            if not biomarkers:
                report.add("error", "invalid_biomarkers_payload", "`biomarkers` cannot be parsed.", record_id)
            else:
                pdl1_flag_values: dict[str, str] = {}
                pdl1_bucket_seen = False
                for key, raw_value in biomarkers.items():
                    value = self._normalize_token(raw_value)
                    if key in self.PUBMED_RAW_PDL1_FLAG_KEYS:
                        pdl1_flag_values[key] = value
                        if value not in self.PUBMED_BIOMARKER_ALLOWED:
                            report.add("error", "invalid_biomarker_flag", f"Unknown value `{raw_value}` for `{key}`.", record_id)
                        continue
                    if key == "PDL1Bucket":
                        pdl1_bucket_seen = True
                        if value not in self.PUBMED_RAW_PDL1_BUCKETS:
                            report.add("error", "invalid_pdl1_bucket", f"Unknown PDL1Bucket `{raw_value}`.", record_id)
                        continue
                    if key not in self.PUBMED_BIOMARKER_KEYS:
                        report.add("warning", "unknown_biomarker_key", f"Unknown biomarker key `{key}`.", record_id)
                        continue
                    if value not in self.PUBMED_BIOMARKER_ALLOWED:
                        report.add("error", "invalid_biomarker_flag", f"Unknown biomarker value `{raw_value}` for `{key}`.", record_id)

                if pdl1_flag_values and pdl1_bucket_seen:
                    report.add(
                        "warning",
                        "mixed_pdl1_encodings",
                        "Found both `PDL1Bucket` and `PDL1_*` flags. Prefer only `PDL1Bucket`.",
                        record_id,
                    )
                if len([key for key, value in pdl1_flag_values.items() if value == "yes"]) > 1:
                    report.add("error", "ambiguous_pdl1_flags", "Multiple PD-L1 flags are marked `yes`.", record_id)

            for field, warning_code in (("interventionTags", "missing_intervention_tags"), ("outcomeTags", "missing_outcome_tags")):
                values = self._parse_list_cell(str(row.get(field, "")))
                if not values or values == ["unspecified"]:
                    report.add(
                        "error" if strict_mvp_pubmed and field == "interventionTags" else "warning",
                        warning_code,
                        f"{field} are missing or unspecified.",
                        record_id,
                    )
            return

        for field in ("title", "abstract", "pub_year", "publication_type", "journal_title"):
            if not str(row.get(field, "")).strip():
                report.add("error", "empty_required_value", f"Field `{field}` must be a non-empty string.", record_id)

        publication_year = str(row.get("pub_year", "")).strip()
        if not publication_year.isdigit():
            report.add("error", "invalid_publication_year", f"pub_year `{publication_year}` is not numeric.", record_id)

        for field in ("sample_size_total", "sample_size_arm_cemiplimab", "sample_size_arm_chemotherapy", "sample_size_arm_nivolumab"):
            raw_value = str(row.get(field, "")).strip()
            if raw_value not in {"", "unspecified"} and not raw_value.isdigit():
                report.add("error", "invalid_sample_size", f"Field `{field}` must be numeric or `unspecified`.", record_id)

        for field in ("EGFR_tag", "ALK_tag", "ROS1_tag"):
            raw_value = str(row.get(field, "")).strip().lower()
            if raw_value in self.PUBMED_RAW_BIOMARKER_RED_FLAGS:
                report.add(
                    "warning",
                    "ambiguous_biomarker_flag",
                    f"`{field}` uses `{row.get(field)}`. Use cohort meaning, not entity mention shortcuts.",
                    record_id,
                )

        pdl1_rule = str(row.get("PDL1_rule_tag", "")).strip()
        if len(pdl1_rule) > self.PUBMED_RAW_PDL1_FREE_TEXT_THRESHOLD:
            report.add(
                "warning",
                "free_text_pdl1_rule",
                "PDL1_rule_tag looks like long free text. Prefer a structured bucket such as lt1 / 1to49 / ge50.",
                record_id,
            )

        if str(row.get("intervention_tags", "")).strip() in {"", "unspecified"}:
            report.add("warning", "missing_intervention_tags", "Intervention tags are missing or unspecified.", record_id)
        if str(row.get("outcome_tags", "")).strip() in {"", "unspecified"}:
            report.add("warning", "missing_outcome_tags", "Outcome tags are missing or unspecified.", record_id)

    def _merge_validation_reports(self, *, dataset_kind: str, source_path: Path, reports: list[object]) -> dict:
        if len(reports) == 1:
            return reports[0].to_dict()

        info = [f"Folder batch with {len(reports)} files."]
        errors: list[dict] = []
        warnings: list[dict] = []

        for report in reports:
            report_dict = report.to_dict()
            report_name = Path(report_dict["path"]).name
            info.append(f"{report_name}: {report_dict['errorCount']} errors, {report_dict['warningCount']} warnings.")
            for issue in report_dict["errors"]:
                errors.append({**issue, "message": f"{report_name}: {issue['message']}"})
            for issue in report_dict["warnings"]:
                warnings.append({**issue, "message": f"{report_name}: {issue['message']}"})

        return {
            "datasetKind": dataset_kind,
            "datasetShape": "folder_batch",
            "path": str(source_path),
            "errorCount": len(errors),
            "warningCount": len(warnings),
            "info": info,
            "errors": errors,
            "warnings": warnings,
        }

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
