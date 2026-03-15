from __future__ import annotations

from app.config.settings import settings
from app.domain.contracts import Biomarkers, ClinicalModifiers, VignetteInput
from app.domain.rules import analyze_records
from app.services.sample_data import load_sample_evidence, load_sample_topics

try:
    from app.services.semantic_retrieval_service import semantic_retrieval_service
except Exception:
    semantic_retrieval_service = None


class AnalysisService:
    def _build_vignette(self, payload: dict) -> VignetteInput:
        return VignetteInput(
            cancerType=payload["cancerType"],
            diseaseSetting=payload["diseaseSetting"],
            histology=payload["histology"],
            performanceStatus=payload["performanceStatus"],
            biomarkers=Biomarkers(**payload["biomarkers"]),
            lineOfTherapy=payload.get("lineOfTherapy", "unspecified"),
            diseaseStage=payload.get("diseaseStage", "unspecified"),
            resectabilityStatus=payload.get("resectabilityStatus", "not_applicable"),
            treatmentContext=payload.get("treatmentContext", "unspecified"),
            clinicalModifiers=ClinicalModifiers(**payload.get("clinicalModifiers", {})),
        )

    def analyze(self, payload: dict):
        return self.analyze_with_runtime(payload, runtime_engine="deterministic")

    def analyze_with_runtime(
        self,
        payload: dict,
        *,
        runtime_engine: str,
        retrieval_mode: str = "hybrid",
        llm_explainability_enabled: bool = False,
    ):
        vignette = self._build_vignette(payload)
        evidence_records = load_sample_evidence()
        topics = load_sample_topics()
        semantic_augmentation = None
        if runtime_engine == "semantic_retrieval_lab":
            if semantic_retrieval_service is None:
                raise RuntimeError("Semantic Retrieval Lab is unavailable in this deployment.")
            semantic_augmentation = semantic_retrieval_service.build_runtime_augmentation(
                vignette=vignette,
                retrieval_mode=retrieval_mode,
                topics=topics,
            )
        response, trace = analyze_records(
            vignette,
            evidence_records,
            topics,
            current_year=2026,
            input_schema_version=settings.input_schema_version,
            ruleset_version=settings.ruleset_version,
            corpus_version=settings.corpus_version,
            safety_footer_key=settings.safety_template_version,
            semantic_evidence_scores=(semantic_augmentation or {}).get("semanticEvidenceScores"),
            semantic_topic_hints=(semantic_augmentation or {}).get("semanticTopicHintsByEvidenceId"),
            semantic_rescue_ids=(semantic_augmentation or {}).get("semanticRescueEvidenceIds"),
        )
        if runtime_engine == "semantic_retrieval_lab":
            response, trace = semantic_retrieval_service.decorate_response(
                vignette=vignette,
                response=response,
                trace=trace,
                retrieval_mode=retrieval_mode,
                llm_explainability_enabled=llm_explainability_enabled,
                augmentation=semantic_augmentation,
            )
        return response, trace


analysis_service = AnalysisService()
