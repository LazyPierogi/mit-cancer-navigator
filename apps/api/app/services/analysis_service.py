from __future__ import annotations

from app.config.settings import settings
from app.domain.contracts import Biomarkers, VignetteInput
from app.domain.rules import analyze_records
from app.services.sample_data import load_sample_evidence, load_sample_topics


class AnalysisService:
    def analyze(self, payload: dict):
        vignette = VignetteInput(
            cancerType=payload["cancerType"],
            diseaseSetting=payload["diseaseSetting"],
            histology=payload["histology"],
            performanceStatus=payload["performanceStatus"],
            biomarkers=Biomarkers(**payload["biomarkers"]),
            lineOfTherapy=payload.get("lineOfTherapy", "unspecified"),
        )
        response, trace = analyze_records(
            vignette,
            load_sample_evidence(),
            load_sample_topics(),
            current_year=2026,
            input_schema_version=settings.input_schema_version,
            ruleset_version=settings.ruleset_version,
            corpus_version=settings.corpus_version,
            safety_footer_key=settings.safety_template_version,
        )
        return response, trace


analysis_service = AnalysisService()
