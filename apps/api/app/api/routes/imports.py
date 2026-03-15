from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.contracts import (
    DatasetBrowserResponseModel,
    EmbeddingManifestModel,
    EmbeddingNeighborModel,
    EmbeddingPointModel,
    ImportBatchModel,
    ImportDebugConfigModel,
    ImportDebugLogEntryModel,
    ImportRequestModel,
    ImportSummaryModel,
    SemanticImportStatusModel,
    ValidationReportModel,
)
from app.services.import_pipeline import import_pipeline_service
from app.services.runtime_prewarm_service import runtime_prewarm_service

try:
    from app.services.semantic_retrieval_service import semantic_retrieval_service
except Exception:
    semantic_retrieval_service = None

router = APIRouter(prefix="/api/v1", tags=["imports"])


def _require_semantic_retrieval_service():
    if semantic_retrieval_service is None:
        raise HTTPException(status_code=503, detail="Semantic Retrieval Lab is unavailable in this deployment.")
    return semantic_retrieval_service


@router.post("/import/esmo", response_model=ImportBatchModel)
def import_esmo(payload: ImportRequestModel | None = None):
    return import_pipeline_service.import_dataset(
        dataset_kind="esmo",
        path=payload.path if payload else None,
        mode=payload.mode if payload else "replace",
    )


@router.post("/import/pubmed", response_model=ImportBatchModel)
def import_pubmed(payload: ImportRequestModel | None = None):
    return import_pipeline_service.import_dataset(
        dataset_kind="pubmed",
        path=payload.path if payload else None,
        mode=payload.mode if payload else "replace",
    )


@router.post("/validate/esmo", response_model=ValidationReportModel)
def validate_esmo(payload: ImportRequestModel | None = None):
    return import_pipeline_service.validate_dataset(dataset_kind="esmo", path=payload.path if payload else None)


@router.post("/validate/pubmed", response_model=ValidationReportModel)
def validate_pubmed(payload: ImportRequestModel | None = None):
    return import_pipeline_service.validate_dataset(dataset_kind="pubmed", path=payload.path if payload else None)


@router.post("/sync/pubmed")
def sync_pubmed():
    return {
        "jobId": "job-sync-pubmed-sample",
        "status": "queued",
        "message": "Live PubMed sync is deferred until the curated import path is validated.",
    }


@router.get("/imports", response_model=list[ImportBatchModel])
def list_imports():
    return import_pipeline_service.list_import_batches()


@router.get("/imports/browse/{dataset_kind}", response_model=DatasetBrowserResponseModel)
def browse_import_sources(dataset_kind: str):
    if dataset_kind not in {"esmo", "pubmed"}:
        raise HTTPException(status_code=404, detail=f"Unknown dataset kind: {dataset_kind}")
    return import_pipeline_service.list_dataset_entries(dataset_kind=dataset_kind)


@router.get("/imports/summary", response_model=ImportSummaryModel)
def get_import_summary():
    return import_pipeline_service.get_import_summary()


@router.get("/imports/debug/config", response_model=ImportDebugConfigModel)
def get_import_debug_config():
    return import_pipeline_service.get_debug_config()


@router.put("/imports/debug/config", response_model=ImportDebugConfigModel)
def update_import_debug_config(payload: ImportDebugConfigModel):
    return import_pipeline_service.update_debug_config(
        strict_mvp_pubmed=payload.strictMvpPubmed,
        runtime_engine=payload.runtimeEngine,
        semantic_retrieval_enabled=payload.semanticRetrievalEnabled,
        retrieval_mode=payload.retrievalMode,
        llm_import_assist_enabled=payload.llmImportAssistEnabled,
        llm_explainability_enabled=payload.llmExplainabilityEnabled,
    )


@router.get("/imports/debug/logs", response_model=list[ImportDebugLogEntryModel])
def get_import_debug_logs(limit: int = Query(default=80, ge=1, le=300)):
    return import_pipeline_service.get_debug_logs(limit=limit)


@router.get("/jobs/{job_id}", response_model=ImportBatchModel)
def get_job(job_id: str):
    batch = import_pipeline_service.get_import_batch(job_id)
    if batch is None:
        raise HTTPException(status_code=404, detail=f"Import job {job_id} not found.")
    return batch


@router.post("/import/semantic/pubmed", response_model=SemanticImportStatusModel)
def import_semantic_pubmed(payload: ImportRequestModel | None = None):
    return import_pipeline_service.import_semantic_dataset(dataset_kind="pubmed", path=payload.path if payload else None)


@router.post("/import/semantic/esmo", response_model=SemanticImportStatusModel)
def import_semantic_esmo(payload: ImportRequestModel | None = None):
    return import_pipeline_service.import_semantic_dataset(dataset_kind="esmo", path=payload.path if payload else None)


@router.get("/imports/semantic/status/{dataset_kind}", response_model=SemanticImportStatusModel)
def get_semantic_status(dataset_kind: str):
    if dataset_kind not in {"esmo", "pubmed"}:
        raise HTTPException(status_code=404, detail=f"Unknown dataset kind: {dataset_kind}")
    return import_pipeline_service.get_semantic_status(dataset_kind=dataset_kind)


@router.post("/runtime/prewarm")
def prewarm_runtime(include_semantic: bool = Query(default=False), include_benchmark: bool = Query(default=False)):
    return runtime_prewarm_service.prewarm(include_semantic=include_semantic, include_benchmark=include_benchmark)


@router.get("/labs/embeddings/manifest", response_model=EmbeddingManifestModel)
def get_embeddings_manifest():
    return _require_semantic_retrieval_service().get_manifest()


@router.get("/labs/embeddings/points", response_model=list[EmbeddingPointModel])
def get_embeddings_points(source_type: str | None = Query(default=None)):
    return _require_semantic_retrieval_service().get_points(source_type=source_type)


@router.get("/labs/embeddings/neighbors/{point_id}", response_model=list[EmbeddingNeighborModel])
def get_embedding_neighbors(point_id: str, limit: int = Query(default=8, ge=1, le=24)):
    return _require_semantic_retrieval_service().get_neighbors(point_id=point_id, limit=limit)
