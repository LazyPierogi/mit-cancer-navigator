from __future__ import annotations

from fastapi import APIRouter

from app.schemas.contracts import EvalResultModel
from app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/api/v1/evals", tags=["evals"])
_LAST_EVAL: dict | None = None


@router.post("/run", response_model=EvalResultModel)
def run_eval():
    global _LAST_EVAL
    _LAST_EVAL = evaluation_service.run_sample_eval()
    return _LAST_EVAL


@router.get("/{eval_run_id}", response_model=EvalResultModel)
def get_eval(eval_run_id: str):
    if _LAST_EVAL is None:
        return evaluation_service.run_sample_eval()
    return _LAST_EVAL

