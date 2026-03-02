from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select

from app.repositories.db import SessionLocal
from app.repositories.models import EvidenceStudyRecord, GuidelineTopicRecord, ImportBatchRecord


class CorpusStore:
    def replace_guideline_topics(self, *, batch_id: str, topics: Sequence[dict]) -> int:
        with SessionLocal() as session:
            session.query(GuidelineTopicRecord).delete()
            for topic in topics:
                session.add(
                    GuidelineTopicRecord(
                        topic_id=topic["topicId"],
                        import_batch_id=batch_id,
                        topic_title=topic["topicTitle"],
                        topic_applicability=topic["topicApplicability"],
                        topic_intervention_tags=topic["topicInterventionTags"],
                        guideline_stance=topic["guidelineStance"],
                        stance_notes=topic.get("stanceNotes"),
                        prerequisites=topic.get("prerequisites", []),
                    )
                )
            session.commit()
        return len(topics)

    def replace_evidence_studies(self, *, batch_id: str, evidence_records: Sequence[dict]) -> int:
        with SessionLocal() as session:
            session.query(EvidenceStudyRecord).delete()
            for record in evidence_records:
                session.add(
                    EvidenceStudyRecord(
                        evidence_id=record["evidenceId"],
                        import_batch_id=batch_id,
                        title=record["title"],
                        publication_year=record.get("publicationYear"),
                        evidence_type=record["evidenceType"],
                        source_category=record.get("sourceCategory"),
                        normalized_payload=record,
                    )
                )
            session.commit()
        return len(evidence_records)

    def get_guideline_topics(self) -> list[dict]:
        with SessionLocal() as session:
            records = session.execute(select(GuidelineTopicRecord).order_by(GuidelineTopicRecord.topic_id)).scalars().all()
            return [
                {
                    "topicId": record.topic_id,
                    "topicTitle": record.topic_title,
                    "topicApplicability": record.topic_applicability,
                    "topicInterventionTags": record.topic_intervention_tags,
                    "guidelineStance": record.guideline_stance,
                    "stanceNotes": record.stance_notes,
                    "prerequisites": record.prerequisites,
                }
                for record in records
            ]

    def get_evidence_studies(self) -> list[dict]:
        with SessionLocal() as session:
            records = session.execute(select(EvidenceStudyRecord).order_by(EvidenceStudyRecord.evidence_id)).scalars().all()
            return [record.normalized_payload for record in records]

    def save_import_batch(
        self,
        *,
        batch_id: str,
        dataset_kind: str,
        dataset_shape: str,
        source_path: str,
        status: str,
        record_count: int,
        imported_count: int,
        error_count: int,
        warning_count: int,
        validation_payload: dict,
        notes: Sequence[str],
    ) -> None:
        with SessionLocal() as session:
            session.add(
                ImportBatchRecord(
                    batch_id=batch_id,
                    dataset_kind=dataset_kind,
                    dataset_shape=dataset_shape,
                    source_path=source_path,
                    status=status,
                    record_count=record_count,
                    imported_count=imported_count,
                    error_count=error_count,
                    warning_count=warning_count,
                    validation_payload=validation_payload,
                    notes=list(notes),
                )
            )
            session.commit()

    def get_import_batch(self, batch_id: str) -> dict | None:
        with SessionLocal() as session:
            record = session.execute(select(ImportBatchRecord).where(ImportBatchRecord.batch_id == batch_id)).scalar_one_or_none()
            if record is None:
                return None
            return {
                "batchId": record.batch_id,
                "datasetKind": record.dataset_kind,
                "datasetShape": record.dataset_shape,
                "sourcePath": record.source_path,
                "status": record.status,
                "recordCount": record.record_count,
                "importedCount": record.imported_count,
                "errorCount": record.error_count,
                "warningCount": record.warning_count,
                "validation": record.validation_payload,
                "notes": record.notes,
                "createdAt": record.created_at,
            }

    def list_import_batches(self) -> list[dict]:
        with SessionLocal() as session:
            records = session.execute(
                select(ImportBatchRecord).order_by(ImportBatchRecord.created_at.desc(), ImportBatchRecord.batch_id.desc())
            ).scalars().all()
            return [
                {
                    "batchId": record.batch_id,
                    "datasetKind": record.dataset_kind,
                    "datasetShape": record.dataset_shape,
                    "sourcePath": record.source_path,
                    "status": record.status,
                    "recordCount": record.record_count,
                    "importedCount": record.imported_count,
                    "errorCount": record.error_count,
                    "warningCount": record.warning_count,
                    "validation": record.validation_payload,
                    "notes": record.notes,
                    "createdAt": record.created_at,
                }
                for record in records
            ]

    def get_import_summary(self) -> dict:
        with SessionLocal() as session:
            topic_count = session.execute(select(func.count()).select_from(GuidelineTopicRecord)).scalar_one()
            evidence_count = session.execute(select(func.count()).select_from(EvidenceStudyRecord)).scalar_one()
            batch_count = session.execute(select(func.count()).select_from(ImportBatchRecord)).scalar_one()
            runtime_sources = {
                "topics": "db_imported" if topic_count > 0 else "file_fallback",
                "evidence": "db_imported" if evidence_count > 0 else "file_fallback",
            }

            latest_batch = session.execute(
                select(ImportBatchRecord).order_by(ImportBatchRecord.created_at.desc(), ImportBatchRecord.batch_id.desc())
            ).scalars().first()

            latest_by_kind: dict[str, dict] = {}
            for kind in ("esmo", "pubmed"):
                record = session.execute(
                    select(ImportBatchRecord)
                    .where(ImportBatchRecord.dataset_kind == kind)
                    .order_by(ImportBatchRecord.created_at.desc(), ImportBatchRecord.batch_id.desc())
                ).scalars().first()
                if record is not None:
                    latest_by_kind[kind] = {
                        "batchId": record.batch_id,
                        "status": record.status,
                        "recordCount": record.record_count,
                        "importedCount": record.imported_count,
                        "warningCount": record.warning_count,
                        "errorCount": record.error_count,
                        "createdAt": record.created_at,
                    }

            return {
                "activeTopics": topic_count,
                "activeEvidenceStudies": evidence_count,
                "importBatchCount": batch_count,
                "latestBatchId": latest_batch.batch_id if latest_batch else None,
                "latestBatchStatus": latest_batch.status if latest_batch else None,
                "latestByKind": latest_by_kind,
                "runtimeSources": runtime_sources,
            }


corpus_store = CorpusStore()
