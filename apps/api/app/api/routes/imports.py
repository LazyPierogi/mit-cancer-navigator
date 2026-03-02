from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.contracts import ImportBatchModel, ImportRequestModel, ImportSummaryModel
from app.services.import_pipeline import import_pipeline_service

router = APIRouter(prefix="/api/v1", tags=["imports"])


@router.post("/import/esmo", response_model=ImportBatchModel)
def import_esmo(payload: ImportRequestModel | None = None):
    return import_pipeline_service.import_dataset(dataset_kind="esmo", path=payload.path if payload else None)


@router.post("/import/pubmed", response_model=ImportBatchModel)
def import_pubmed(payload: ImportRequestModel | None = None):
    return import_pipeline_service.import_dataset(dataset_kind="pubmed", path=payload.path if payload else None)


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


@router.get("/imports/summary", response_model=ImportSummaryModel)
def get_import_summary():
    return import_pipeline_service.get_import_summary()


@router.get("/jobs/{job_id}", response_model=ImportBatchModel)
def get_job(job_id: str):
    batch = import_pipeline_service.get_import_batch(job_id)
    if batch is None:
        raise HTTPException(status_code=404, detail=f"Import job {job_id} not found.")
    return batch
