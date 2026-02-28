from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from app.schemas.contracts import AnalyzeRunResponseModel, TracePayloadModel, VignetteInputModel
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])
_TRACE_CACHE: dict[str, dict] = {}
_RESPONSE_CACHE: dict[str, dict] = {}


@router.post("", response_model=AnalyzeRunResponseModel)
def create_run(payload: VignetteInputModel):
    response, trace = analysis_service.analyze(payload.model_dump())
    _TRACE_CACHE[response.run.id] = trace
    _RESPONSE_CACHE[response.run.id] = asdict(response)
    return asdict(response)


@router.get("/{run_id}", response_model=AnalyzeRunResponseModel)
def get_run(run_id: str):
    return _RESPONSE_CACHE.get(run_id, next(iter(_RESPONSE_CACHE.values()), {}))


@router.get("/{run_id}/trace", response_model=TracePayloadModel)
def get_run_trace(run_id: str):
    return _TRACE_CACHE.get(run_id, next(iter(_TRACE_CACHE.values()), {}))


@router.get("/{run_id}/review-sheet")
def get_review_sheet(run_id: str):
    response = _RESPONSE_CACHE.get(run_id, next(iter(_RESPONSE_CACHE.values()), None))
    trace = _TRACE_CACHE.get(run_id, next(iter(_TRACE_CACHE.values()), None))
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

