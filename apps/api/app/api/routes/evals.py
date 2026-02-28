from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.repositories.run_store import run_store
from app.schemas.contracts import EvalResultModel
from app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/api/v1/evals", tags=["evals"])


@router.post("/run", response_model=EvalResultModel)
def run_eval():
    payload = evaluation_service.run_sample_eval()
    run_store.save_eval_run(
        eval_run_id=payload["evalRunId"],
        pack_id=payload["packId"],
        layer1_payload=payload["layer1"],
        layer2_metrics=payload["layer2Metrics"],
        notes=payload["notes"],
    )
    return payload


@router.get("/{eval_run_id}", response_model=EvalResultModel)
def get_eval(eval_run_id: str):
    record = run_store.get_eval_run(eval_run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Eval run {eval_run_id} not found.")
    return record

