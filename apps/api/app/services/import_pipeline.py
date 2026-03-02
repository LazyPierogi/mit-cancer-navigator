from __future__ import annotations

import json
import sys
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

    def import_dataset(self, *, dataset_kind: str, path: str | None = None) -> dict:
        from scripts.validate_data_drop import validate_dataset

        bootstrap_database()
        source_path = Path(path).expanduser().resolve() if path else self.DEFAULT_PATHS[dataset_kind].resolve()
        report = validate_dataset(source_path, dataset_kind)
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
            return corpus_store.get_import_batch(batch_id) or {}

        imported_count = self._ingest(dataset_kind=dataset_kind, batch_id=batch_id, records=normalized_records)
        notes = ["Imported successfully."] if not report.warning_count else ["Imported with validation warnings."]
        corpus_store.save_import_batch(
            batch_id=batch_id,
            dataset_kind=dataset_kind,
            dataset_shape=report.dataset_shape,
            source_path=str(source_path),
            status="completed" if not report.warning_count else "completed_with_warnings",
            record_count=len(normalized_records),
            imported_count=imported_count,
            error_count=report.error_count,
            warning_count=report.warning_count,
            validation_payload=report_dict,
            notes=notes,
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

    def _normalize(self, *, dataset_kind: str, source_path: Path, dataset_shape: str) -> list[dict]:
        from scripts.build_curated_preview import build_evidence, build_topics

        if dataset_shape == "canonical":
            return json.loads(source_path.read_text(encoding="utf-8"))

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

    @staticmethod
    def _record_count(report_dict: dict) -> int:
        info_lines = report_dict.get("info", [])
        for line in info_lines:
            if line.startswith("Validated ") and line.endswith(" records."):
                raw_number = line.removeprefix("Validated ").removesuffix(" records.")
                if raw_number.isdigit():
                    return int(raw_number)
        return 0


import_pipeline_service = ImportPipelineService()
