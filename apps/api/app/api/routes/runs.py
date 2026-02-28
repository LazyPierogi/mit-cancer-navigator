from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from app.config.settings import settings
from app.repositories.run_store import run_store
from app.schemas.contracts import AnalyzeRunResponseModel, TracePayloadModel, VignetteInputModel
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])
_TRACE_CACHE: dict[str, dict] = {}


@router.post("", response_model=AnalyzeRunResponseModel)
def create_run(payload: VignetteInputModel):
    response, trace = analysis_service.analyze(payload.model_dump())
    encoded_response = jsonable_encoder(asdict(response))
    _TRACE_CACHE[response.run.id] = trace
    run_store.save_analysis_run(
        run_id=response.run.id,
        trace_id=response.traceId,
        ruleset_version=response.run.rulesetVersion,
        corpus_version=response.run.corpusVersion,
        input_schema_version=settings.input_schema_version,
        payload={"response": encoded_response, "trace": trace, "input": payload.model_dump()},
    )
    return encoded_response


@router.get("/{run_id}", response_model=AnalyzeRunResponseModel)
def get_run(run_id: str):
    record = run_store.get_analysis_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found.")
    return record["response"]


@router.get("/{run_id}/trace", response_model=TracePayloadModel)
def get_run_trace(run_id: str):
    if run_id in _TRACE_CACHE:
        return _TRACE_CACHE[run_id]
    record = run_store.get_analysis_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} trace not found.")
    return record["trace"]


@router.get("/{run_id}/review-sheet")
def get_review_sheet(run_id: str):
    record = run_store.get_analysis_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} review sheet not found.")
    response = record["response"]
    trace = record["trace"]
    return {
        "runId": run_id,
        "response": response,
        "trace": trace,
        "instructions": [
            "Check relevance of top evidence against the vignette.",
            "Verify mapping label against the guideline topic.",
            "Verify the citation supports the claim and population context.",
        ],
    }
