from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from app.config.settings import settings
from app.repositories.run_store import run_store
from app.schemas.contracts import (
    AnalyzeRunResponseModel,
    EvidenceExplainabilityModel,
    TracePayloadModel,
    UncertaintyFlagsExplainabilityModel,
    VignetteInputModel,
)
from app.services.import_pipeline import import_pipeline_service
from app.services.analysis_service import analysis_service
from app.services.llm_explainability_service import llm_explainability_service

try:
    from app.services.semantic_retrieval_service import semantic_retrieval_service
except Exception:
    semantic_retrieval_service = None

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])
_TRACE_CACHE: dict[str, dict] = {}
_MAX_UNCERTAINTY_FLAGS_FOR_EXPLAINABILITY = 10


def _persist_run_best_effort(
    *,
    run_id: str,
    trace_id: str,
    ruleset_version: str,
    corpus_version: str,
    input_schema_version: str,
    payload: dict,
) -> None:
    try:
        run_store.save_analysis_run(
            run_id=run_id,
            trace_id=trace_id,
            ruleset_version=ruleset_version,
            corpus_version=corpus_version,
            input_schema_version=input_schema_version,
            payload=payload,
        )
    except Exception as exc:
        print(f"[runs] save_analysis_run_failed run_id={run_id} error={exc!r}")


def _require_semantic_retrieval_service():
    if semantic_retrieval_service is None:
        raise HTTPException(status_code=503, detail="Semantic Retrieval Lab is unavailable in this deployment.")
    return semantic_retrieval_service


@router.post("", response_model=AnalyzeRunResponseModel)
def create_run(payload: VignetteInputModel):
    try:
        debug_config = import_pipeline_service.get_debug_config()
        runtime_engine = "deterministic"
        if debug_config.get("runtimeEngine") == "semantic_retrieval_lab" and debug_config.get("semanticRetrievalEnabled", False):
            _require_semantic_retrieval_service()
            runtime_engine = "semantic_retrieval_lab"
        response, trace = analysis_service.analyze_with_runtime(
            payload.model_dump(),
            runtime_engine=runtime_engine,
            retrieval_mode=str(debug_config.get("retrievalMode", "hybrid")),
            llm_explainability_enabled=bool(debug_config.get("llmExplainabilityEnabled", False)),
        )
        encoded_response = jsonable_encoder(asdict(response))
        _TRACE_CACHE[response.run.id] = trace
        _persist_run_best_effort(
            run_id=response.run.id,
            trace_id=response.traceId,
            ruleset_version=response.run.rulesetVersion,
            corpus_version=response.run.corpusVersion,
            input_schema_version=settings.input_schema_version,
            payload={"response": encoded_response, "trace": trace, "input": payload.model_dump()},
        )
        return encoded_response
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[runs] create_run_failed error={exc!r}", flush=True)
        raise HTTPException(status_code=500, detail="Run analysis failed.")


@router.post("/semantic", response_model=AnalyzeRunResponseModel)
def create_semantic_run(payload: VignetteInputModel):
    _require_semantic_retrieval_service()
    import_pipeline_service.update_debug_config(
        strict_mvp_pubmed=bool(import_pipeline_service.get_debug_config().get("strictMvpPubmed", False)),
        runtime_engine="semantic_retrieval_lab",
        semantic_retrieval_enabled=True,
        retrieval_mode=str(import_pipeline_service.get_debug_config().get("retrievalMode", "hybrid")),
        llm_import_assist_enabled=bool(import_pipeline_service.get_debug_config().get("llmImportAssistEnabled", False)),
        llm_explainability_enabled=bool(import_pipeline_service.get_debug_config().get("llmExplainabilityEnabled", False)),
    )
    return create_run(payload)


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


@router.get("/{run_id}/evidence/{evidence_id}/explainability", response_model=EvidenceExplainabilityModel)
def get_evidence_explainability(run_id: str, evidence_id: str):
    record = run_store.get_analysis_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found.")

    cached = record.get("evidenceExplainabilityById", {}).get(evidence_id)
    if cached is not None:
        return cached

    response = record.get("response", {})
    top_evidence = response.get("topEvidence", [])
    manual_review_evidence = response.get("manualReviewEvidence", [])

    top_item = next((item for item in top_evidence if item.get("evidenceId") == evidence_id), None)
    if top_item is None:
        if any(item.get("evidenceId") == evidence_id for item in manual_review_evidence):
            raise HTTPException(status_code=400, detail=f"Evidence {evidence_id} is manual-review only and is not eligible for LLM explainability.")
        raise HTTPException(status_code=404, detail=f"Evidence {evidence_id} not found in run {run_id}.")

    if int(top_item.get("rank", 999)) > 5:
        raise HTTPException(status_code=400, detail=f"Evidence {evidence_id} is outside the top-5 explainability window.")

    debug_config = import_pipeline_service.get_debug_config()
    explainability = llm_explainability_service.summarize_evidence_item(
        evidence_id=evidence_id,
        title=str(top_item.get("title", "")),
        abstract=top_item.get("abstract"),
        journal_title=top_item.get("journalTitle"),
        publication_year=top_item.get("publicationYear"),
        ers_total=int(top_item.get("ersTotal", 0)),
        ers_breakdown=dict(top_item.get("ersBreakdown", {})),
        mapping_label=str(top_item.get("mappingLabel", "guideline_silent")),
        mapped_topic_title=top_item.get("mappedTopicTitle"),
        applicability_note=str(top_item.get("applicabilityNote", "")),
        citations=list(top_item.get("citations", [])),
        llm_enabled=bool(debug_config.get("llmExplainabilityEnabled", False)),
    )
    payload = jsonable_encoder(asdict(explainability))
    run_store.save_analysis_run_evidence_explainability(run_id=run_id, evidence_id=evidence_id, payload=payload)
    return payload


@router.get("/{run_id}/uncertainty-flags/explainability", response_model=UncertaintyFlagsExplainabilityModel)
def get_uncertainty_flags_explainability(run_id: str):
    record = run_store.get_analysis_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found.")

    cached = record.get("uncertaintyFlagsExplainability")
    if cached is not None:
        return cached

    response = record.get("response", {})
    uncertainty_flags = list(response.get("uncertaintyFlags", []))
    uncertainty_flags_for_explainability = uncertainty_flags[:_MAX_UNCERTAINTY_FLAGS_FOR_EXPLAINABILITY]
    debug_config = import_pipeline_service.get_debug_config()

    explainability = llm_explainability_service.summarize_uncertainty_flags(
        uncertainty_flags=uncertainty_flags_for_explainability,
        engine=str(response.get("engine", "deterministic")),
        top_evidence_count=len(response.get("topEvidence", [])),
        manual_review_count=len(response.get("manualReviewEvidence", [])),
        llm_enabled=bool(debug_config.get("llmExplainabilityEnabled", False)),
    )
    payload = jsonable_encoder(asdict(explainability))
    run_store.save_analysis_run_uncertainty_flags_explainability(run_id=run_id, payload=payload)
    return payload
