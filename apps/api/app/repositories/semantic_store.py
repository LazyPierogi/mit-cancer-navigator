from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select

from app.repositories.db import SessionLocal
from app.repositories.models import DocumentChunkRecord, EmbeddingJobRecord, ProjectionPointRecord, SourceDocumentRecord


class SemanticStore:
    @staticmethod
    def _latest_job_for_dataset(session, *, dataset_kind: str) -> EmbeddingJobRecord | None:
        return session.execute(
            select(EmbeddingJobRecord)
            .where(EmbeddingJobRecord.dataset_kind == dataset_kind)
            .order_by(EmbeddingJobRecord.created_at.desc(), EmbeddingJobRecord.job_id.desc())
        ).scalars().first()

    def replace_dataset(
        self,
        *,
        dataset_kind: str,
        import_batch_id: str,
        documents: Sequence[dict],
        chunks: Sequence[dict],
        projection_points: Sequence[dict],
        job: dict,
    ) -> dict:
        with SessionLocal() as session:
            existing_document_ids = session.execute(
                select(SourceDocumentRecord.document_id).where(SourceDocumentRecord.dataset_kind == dataset_kind)
            ).scalars().all()
            if existing_document_ids:
                session.query(DocumentChunkRecord).filter(DocumentChunkRecord.document_id.in_(existing_document_ids)).delete(
                    synchronize_session=False
                )
                session.query(ProjectionPointRecord).filter(
                    ProjectionPointRecord.document_id.in_(existing_document_ids)
                ).delete(synchronize_session=False)
                session.query(SourceDocumentRecord).filter(SourceDocumentRecord.dataset_kind == dataset_kind).delete(
                    synchronize_session=False
                )
                session.flush()

            session.query(EmbeddingJobRecord).filter(EmbeddingJobRecord.dataset_kind == dataset_kind).delete(
                synchronize_session=False
            )
            session.flush()

            for document in documents:
                session.add(
                    SourceDocumentRecord(
                        document_id=document["documentId"],
                        dataset_kind=dataset_kind,
                        source_id=document["sourceId"],
                        source_title=document["title"],
                        source_url=document.get("sourceUrl"),
                        import_batch_id=import_batch_id,
                        raw_text=document["rawText"],
                        histology_original=document.get("histologyOriginal"),
                        histology_normalized=document.get("histologyNormalized", "unspecified"),
                        histology_source=document.get("histologySource", "unknown"),
                        metadata_payload=document.get("metadata", {}),
                    )
                )

            for chunk in chunks:
                session.add(
                    DocumentChunkRecord(
                        chunk_id=chunk["chunkId"],
                        document_id=chunk["documentId"],
                        dataset_kind=dataset_kind,
                        source_type=chunk["sourceType"],
                        source_id=chunk["sourceId"],
                        topic_id=chunk.get("topicId"),
                        title=chunk["title"],
                        chunk_text=chunk["text"],
                        dense_vector=chunk["denseVector"],
                        sparse_vector=chunk["sparseVector"],
                        metadata_payload=chunk.get("metadata", {}),
                    )
                )

            for point in projection_points:
                session.add(
                    ProjectionPointRecord(
                        point_id=point["pointId"],
                        chunk_id=point["chunkId"],
                        document_id=point["documentId"],
                        dataset_kind=dataset_kind,
                        source_type=point["sourceType"],
                        source_id=point["sourceId"],
                        topic_id=point.get("topicId"),
                        title=point["title"],
                        histology=point.get("histology", "unspecified"),
                        x=point["x"],
                        y=point["y"],
                        label=point["label"],
                        metadata_payload=point.get("metadata", {}),
                    )
                )

            session.flush()
            current_document_count = session.execute(
                select(func.count()).select_from(SourceDocumentRecord).where(SourceDocumentRecord.dataset_kind == dataset_kind)
            ).scalar_one()
            current_chunk_count = session.execute(
                select(func.count()).select_from(DocumentChunkRecord).where(DocumentChunkRecord.dataset_kind == dataset_kind)
            ).scalar_one()

            session.add(
                EmbeddingJobRecord(
                    job_id=job["jobId"],
                    dataset_kind=dataset_kind,
                    import_batch_id=import_batch_id,
                    status=job["status"],
                    vector_store=job["vectorStore"],
                    retrieval_mode=job["retrievalMode"],
                    embedding_model=job["embeddingModel"],
                    chunking_strategy_version=job["chunkingStrategyVersion"],
                    document_count=current_document_count,
                    chunk_count=current_chunk_count,
                    notes=job.get("notes", []),
                )
            )
            session.commit()

        return self.get_dataset_status(dataset_kind=dataset_kind)

    def upsert_dataset(
        self,
        *,
        dataset_kind: str,
        import_batch_id: str,
        documents: Sequence[dict],
        chunks: Sequence[dict],
        projection_points: Sequence[dict],
        job: dict,
    ) -> dict:
        document_ids = [document["documentId"] for document in documents]
        with SessionLocal() as session:
            if document_ids:
                session.query(DocumentChunkRecord).filter(DocumentChunkRecord.document_id.in_(document_ids)).delete(
                    synchronize_session=False
                )
                session.query(ProjectionPointRecord).filter(
                    ProjectionPointRecord.document_id.in_(document_ids)
                ).delete(synchronize_session=False)
                session.query(SourceDocumentRecord).filter(SourceDocumentRecord.document_id.in_(document_ids)).delete(
                    synchronize_session=False
                )
                session.flush()

            for document in documents:
                session.add(
                    SourceDocumentRecord(
                        document_id=document["documentId"],
                        dataset_kind=dataset_kind,
                        source_id=document["sourceId"],
                        source_title=document["title"],
                        source_url=document.get("sourceUrl"),
                        import_batch_id=import_batch_id,
                        raw_text=document["rawText"],
                        histology_original=document.get("histologyOriginal"),
                        histology_normalized=document.get("histologyNormalized", "unspecified"),
                        histology_source=document.get("histologySource", "unknown"),
                        metadata_payload=document.get("metadata", {}),
                    )
                )

            for chunk in chunks:
                session.add(
                    DocumentChunkRecord(
                        chunk_id=chunk["chunkId"],
                        document_id=chunk["documentId"],
                        dataset_kind=dataset_kind,
                        source_type=chunk["sourceType"],
                        source_id=chunk["sourceId"],
                        topic_id=chunk.get("topicId"),
                        title=chunk["title"],
                        chunk_text=chunk["text"],
                        dense_vector=chunk["denseVector"],
                        sparse_vector=chunk["sparseVector"],
                        metadata_payload=chunk.get("metadata", {}),
                    )
                )

            for point in projection_points:
                session.add(
                    ProjectionPointRecord(
                        point_id=point["pointId"],
                        chunk_id=point["chunkId"],
                        document_id=point["documentId"],
                        dataset_kind=dataset_kind,
                        source_type=point["sourceType"],
                        source_id=point["sourceId"],
                        topic_id=point.get("topicId"),
                        title=point["title"],
                        histology=point.get("histology", "unspecified"),
                        x=point["x"],
                        y=point["y"],
                        label=point["label"],
                        metadata_payload=point.get("metadata", {}),
                    )
                )

            session.flush()
            current_document_count = session.execute(
                select(func.count()).select_from(SourceDocumentRecord).where(SourceDocumentRecord.dataset_kind == dataset_kind)
            ).scalar_one()
            current_chunk_count = session.execute(
                select(func.count()).select_from(DocumentChunkRecord).where(DocumentChunkRecord.dataset_kind == dataset_kind)
            ).scalar_one()

            session.add(
                EmbeddingJobRecord(
                    job_id=job["jobId"],
                    dataset_kind=dataset_kind,
                    import_batch_id=import_batch_id,
                    status=job["status"],
                    vector_store=job["vectorStore"],
                    retrieval_mode=job["retrievalMode"],
                    embedding_model=job["embeddingModel"],
                    chunking_strategy_version=job["chunkingStrategyVersion"],
                    document_count=current_document_count,
                    chunk_count=current_chunk_count,
                    notes=job.get("notes", []),
                )
            )
            session.commit()

        return self.get_dataset_status(dataset_kind=dataset_kind)

    def get_chunks(self, *, dataset_kind: str | None = None) -> list[dict]:
        with SessionLocal() as session:
            statement = select(DocumentChunkRecord)
            if dataset_kind:
                statement = statement.where(DocumentChunkRecord.dataset_kind == dataset_kind)
            records = session.execute(statement.order_by(DocumentChunkRecord.chunk_id)).scalars().all()
            return [
                {
                    "chunkId": record.chunk_id,
                    "documentId": record.document_id,
                    "datasetKind": record.dataset_kind,
                    "sourceType": record.source_type,
                    "sourceId": record.source_id,
                    "topicId": record.topic_id,
                    "title": record.title,
                    "text": record.chunk_text,
                    "denseVector": record.dense_vector,
                    "sparseVector": record.sparse_vector,
                    "metadata": record.metadata_payload,
                }
                for record in records
            ]

    def get_projection_points(self, *, dataset_kind: str | None = None) -> list[dict]:
        with SessionLocal() as session:
            statement = select(ProjectionPointRecord)
            if dataset_kind:
                statement = statement.where(ProjectionPointRecord.dataset_kind == dataset_kind)
            records = session.execute(statement.order_by(ProjectionPointRecord.point_id)).scalars().all()
            return [
                {
                    "pointId": record.point_id,
                    "chunkId": record.chunk_id,
                    "documentId": record.document_id,
                    "datasetKind": record.dataset_kind,
                    "sourceType": record.source_type,
                    "sourceId": record.source_id,
                    "topicId": record.topic_id,
                    "title": record.title,
                    "histology": record.histology,
                    "x": record.x,
                    "y": record.y,
                    "label": record.label,
                    "metadata": record.metadata_payload,
                }
                for record in records
            ]

    def get_projection_summary(self) -> dict:
        with SessionLocal() as session:
            total_points = session.execute(select(func.count()).select_from(ProjectionPointRecord)).scalar_one()
            source_counts = session.execute(
                select(ProjectionPointRecord.source_type, func.count())
                .group_by(ProjectionPointRecord.source_type)
                .order_by(ProjectionPointRecord.source_type.asc())
            ).all()
            histology_counts = session.execute(
                select(ProjectionPointRecord.histology, func.count())
                .group_by(ProjectionPointRecord.histology)
                .order_by(ProjectionPointRecord.histology.asc())
            ).all()
            return {
                "pointCount": total_points,
                "sourceCounts": {source_type: count for source_type, count in source_counts},
                "histologyCounts": {histology: count for histology, count in histology_counts},
            }

    def get_dataset_status(self, *, dataset_kind: str) -> dict:
        with SessionLocal() as session:
            latest_job = self._latest_job_for_dataset(session, dataset_kind=dataset_kind)
            if latest_job is not None:
                document_count = latest_job.document_count
                chunk_count = latest_job.chunk_count
            else:
                document_count = session.execute(
                    select(func.count()).select_from(SourceDocumentRecord).where(SourceDocumentRecord.dataset_kind == dataset_kind)
                ).scalar_one()
                chunk_count = session.execute(
                    select(func.count()).select_from(DocumentChunkRecord).where(DocumentChunkRecord.dataset_kind == dataset_kind)
                ).scalar_one()

            return {
                "datasetKind": dataset_kind,
                "latestBatchId": latest_job.import_batch_id if latest_job else None,
                "latestStatus": latest_job.status if latest_job else None,
                "documentCount": document_count,
                "chunkCount": chunk_count,
                "latestJob": None
                if latest_job is None
                else {
                    "jobId": latest_job.job_id,
                    "status": latest_job.status,
                    "vectorStore": latest_job.vector_store,
                    "retrievalMode": latest_job.retrieval_mode,
                    "embeddingModel": latest_job.embedding_model,
                    "chunkingStrategyVersion": latest_job.chunking_strategy_version,
                    "documentCount": latest_job.document_count,
                    "chunkCount": latest_job.chunk_count,
                    "notes": latest_job.notes,
                    "createdAt": latest_job.created_at,
                },
            }

    def get_summary(self) -> dict:
        with SessionLocal() as session:
            latest_jobs = {
                dataset_kind: job
                for dataset_kind in ("esmo", "pubmed")
                if (job := self._latest_job_for_dataset(session, dataset_kind=dataset_kind)) is not None
            }
            if latest_jobs:
                documents = sum(job.document_count for job in latest_jobs.values())
                chunks = sum(job.chunk_count for job in latest_jobs.values())
                source_counts = {
                    dataset_kind: job.chunk_count
                    for dataset_kind, job in latest_jobs.items()
                    if job.chunk_count > 0
                }
                return {
                    "semanticDocuments": documents,
                    "semanticChunks": chunks,
                    "semanticCollections": source_counts,
                }

            documents = session.execute(select(func.count()).select_from(SourceDocumentRecord)).scalar_one()
            chunks = session.execute(select(func.count()).select_from(DocumentChunkRecord)).scalar_one()
            return {
                "semanticDocuments": documents,
                "semanticChunks": chunks,
                "semanticCollections": {},
            }


semantic_store = SemanticStore()
