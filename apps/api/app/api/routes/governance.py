from __future__ import annotations

from fastapi import APIRouter

from app.schemas.contracts import GovernancePolicyModel
from app.services.governance_service import governance_service

router = APIRouter(prefix="/api/v1/governance", tags=["governance"])


@router.get("/policy", response_model=GovernancePolicyModel)
def get_policy():
    return governance_service.policy()

