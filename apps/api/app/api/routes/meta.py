from __future__ import annotations

from fastapi import APIRouter

from app.config.versioning import load_version_manifest
from app.schemas.contracts import AppVersionModel


router = APIRouter(prefix="/api/v1/meta", tags=["meta"])


@router.get("/version", response_model=AppVersionModel)
def get_version():
    return load_version_manifest()
