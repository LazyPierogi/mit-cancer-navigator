from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["imports"])


@router.post("/import/esmo")
def import_esmo():
    return {
        "jobId": "job-import-esmo-sample",
        "status": "queued",
        "message": "Scaffold endpoint ready for canonical ESMO topic/snippet import.",
    }


@router.post("/import/pubmed")
def import_pubmed():
    return {
        "jobId": "job-import-pubmed-sample",
        "status": "queued",
        "message": "Scaffold endpoint ready for curated PubMed evidence import.",
    }


@router.post("/sync/pubmed")
def sync_pubmed():
    return {
        "jobId": "job-sync-pubmed-sample",
        "status": "queued",
        "message": "Live PubMed sync is deferred until the curated import path is validated.",
    }


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    return {"jobId": job_id, "status": "queued"}

