from __future__ import annotations

from fastapi import APIRouter

from app.services.sample_data import load_sample_topics

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


@router.get("/topics")
def list_topics():
    return {"topics": [topic.__dict__ | {"topicApplicability": topic.topicApplicability.__dict__} for topic in load_sample_topics()]}

