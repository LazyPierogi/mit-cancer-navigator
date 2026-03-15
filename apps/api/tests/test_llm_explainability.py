import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import settings
from app.domain.contracts import Biomarkers, SemanticEvidenceItem, SemanticGuidelineCandidate, UncertaintyFlagsExplainability, VignetteInput
from app.services.llm_explainability_service import llm_explainability_service


class LlmExplainabilityTest(unittest.TestCase):
    def setUp(self):
        self.vignette = VignetteInput(
            cancerType="NSCLC",
            diseaseSetting="metastatic",
            diseaseStage="stage_iv",
            histology="adenocarcinoma",
            performanceStatus="1",
            biomarkers=Biomarkers(EGFR="yes", ALK="no", ROS1="no", PDL1Bucket="unspecified"),
            lineOfTherapy="first_line",
        )
        self.semantic_evidence = [
            SemanticEvidenceItem(
                chunkId="chunk-1",
                sourceType="pubmed",
                sourceId="PMID-36470213",
                title="Osimertinib meta-analysis",
                snippet="Osimertinib improved outcomes in EGFR-mutant NSCLC.",
                score=0.92,
                denseScore=0.81,
                sparseScore=0.11,
                mappedTopicId="EGFR_IV_01",
                mappedTopicTitle="Osimertinib first-line for classical activating EGFR mutation",
            )
        ]
        self.semantic_candidates = [
            SemanticGuidelineCandidate(
                topicId="EGFR_IV_01",
                topicTitle="Osimertinib first-line for classical activating EGFR mutation",
                score=0.91,
                supportingChunkIds=["chunk-1"],
            )
        ]

    def test_semantic_summary_falls_back_when_provider_unconfigured(self):
        with patch.object(settings, "llm_provider", "disabled"), patch.object(settings, "llm_api_key", None), patch.object(
            settings, "llm_model", ""
        ):
            result = llm_explainability_service.summarize_semantic_case(
                vignette=self.vignette,
                semantic_evidence=self.semantic_evidence,
                semantic_candidates=self.semantic_candidates,
                fallback_summary="Fallback summary.",
            )

        self.assertEqual(result.summary, "Fallback summary.")
        self.assertEqual(result.providerStatus, "provider_unconfigured")
        self.assertEqual(result.validationStatus, "not_attempted")

    def test_semantic_summary_rejects_ungrounded_llm_output(self):
        with (
            patch.object(settings, "llm_provider", "gemini"),
            patch.object(settings, "llm_api_key", "test-key"),
            patch.object(settings, "llm_model", "gemini-2.5-flash"),
            patch.object(
                llm_explainability_service,
                "_gemini_json",
                return_value=(
                    {
                        "candidates": [
                            {
                                "content": {
                                    "parts": [
                                        {
                                            "text": '{"summary":"Bad citation","sourceChunkIds":["chunk-does-not-exist"],"sourceIds":["PMID-999"]}'
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                    12,
                ),
            ),
        ):
            result = llm_explainability_service.summarize_semantic_case(
                vignette=self.vignette,
                semantic_evidence=self.semantic_evidence,
                semantic_candidates=self.semantic_candidates,
                fallback_summary="Fallback summary.",
            )

        self.assertEqual(result.summary, "Fallback summary.")
        self.assertEqual(result.providerStatus, "provider_error")
        self.assertEqual(result.validationStatus, "failed")

    def test_evidence_explainability_falls_back_when_provider_unconfigured(self):
        with patch.object(settings, "llm_provider", "disabled"), patch.object(settings, "llm_api_key", None), patch.object(
            settings, "llm_model", ""
        ):
            result = llm_explainability_service.summarize_evidence_item(
                evidence_id="PMID-1",
                title="Example title",
                abstract="Objective: test fallback. Results: signal present. Conclusion: still grounded.",
                journal_title="Example journal",
                publication_year=2024,
                ers_total=55,
                ers_breakdown={
                    "evidenceStrength": 20,
                    "datasetRobustness": 15,
                    "sourceCredibility": 10,
                    "recency": 10,
                },
                mapping_label="aligned",
                mapped_topic_title="Example topic",
                applicability_note="Matches the vignette.",
                citations=[{"sourceId": "PMID-1", "title": "Example title", "year": 2024, "summary": "Preview"}],
                llm_enabled=True,
            )

        self.assertEqual(result.evidenceId, "PMID-1")
        self.assertEqual(result.providerStatus, "provider_unconfigured")
        self.assertEqual(result.validationStatus, "not_attempted")
        self.assertTrue(result.studySummary.objective)

    def test_evidence_explainability_rejects_ungrounded_llm_output(self):
        with (
            patch.object(settings, "llm_provider", "gemini"),
            patch.object(settings, "llm_api_key", "test-key"),
            patch.object(settings, "llm_model", "gemini-2.5-flash"),
            patch.object(
                llm_explainability_service,
                "_gemini_json",
                return_value=(
                    {
                        "candidates": [
                            {
                                "content": {
                                    "parts": [
                                        {
                                            "text": (
                                                '{"evidenceId":"PMID-1","scoreRationale":"Bad","studySummary":{"objective":"a","signal":"b","takeaway":"c"},'
                                                '"sourceAnchors":[{"sourceId":"PMID-999","title":"Nope","snippet":"bad","year":2024}]}'
                                            )
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                    12,
                ),
            ),
        ):
            result = llm_explainability_service.summarize_evidence_item(
                evidence_id="PMID-1",
                title="Example title",
                abstract="Objective sentence. Results sentence. Conclusion sentence.",
                journal_title="Example journal",
                publication_year=2024,
                ers_total=55,
                ers_breakdown={
                    "evidenceStrength": 20,
                    "datasetRobustness": 15,
                    "sourceCredibility": 10,
                    "recency": 10,
                },
                mapping_label="aligned",
                mapped_topic_title="Example topic",
                applicability_note="Matches the vignette.",
                citations=[{"sourceId": "PMID-1", "title": "Example title", "year": 2024, "summary": "Preview"}],
                llm_enabled=True,
            )

        self.assertEqual(result.providerStatus, "provider_error")
        self.assertEqual(result.validationStatus, "failed")
        self.assertNotEqual(result.sourceAnchors[0].sourceId, "PMID-999")

    def test_evidence_explainability_accepts_grounded_llm_output(self):
        with (
            patch.object(settings, "llm_provider", "gemini"),
            patch.object(settings, "llm_api_key", "test-key"),
            patch.object(settings, "llm_model", "gemini-2.5-flash"),
            patch.object(
                llm_explainability_service,
                "_gemini_json",
                return_value=(
                    {
                        "candidates": [
                            {
                                "content": {
                                    "parts": [
                                        {
                                            "text": (
                                                '{"evidenceId":"PMID-1","scoreRationale":"ERS stayed high because the evidence is recent and well-typed.",'
                                                '"studySummary":{"objective":"Test objective","signal":"Test signal","takeaway":"Test takeaway"},'
                                                '"sourceAnchors":[{"sourceId":"PMID-1","title":"Example title","snippet":"Grounded snippet","year":2024}]}'
                                            )
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                    18,
                ),
            ),
        ):
            result = llm_explainability_service.summarize_evidence_item(
                evidence_id="PMID-1",
                title="Example title",
                abstract="Objective sentence. Results sentence. Conclusion sentence.",
                journal_title="Example journal",
                publication_year=2024,
                ers_total=55,
                ers_breakdown={
                    "evidenceStrength": 20,
                    "datasetRobustness": 15,
                    "sourceCredibility": 10,
                    "recency": 10,
                },
                mapping_label="aligned",
                mapped_topic_title="Example topic",
                applicability_note="Matches the vignette.",
                citations=[{"sourceId": "PMID-1", "title": "Example title", "year": 2024, "summary": "Preview"}],
                llm_enabled=True,
            )

        self.assertEqual(result.providerStatus, "llm_grounded")
        self.assertEqual(result.validationStatus, "passed")
        self.assertEqual(result.studySummary.objective, "Test objective")
        self.assertEqual(result.sourceAnchors[0].sourceId, "PMID-1")

    def test_uncertainty_flags_explainability_falls_back_when_provider_unconfigured(self):
        with patch.object(settings, "llm_provider", "disabled"), patch.object(settings, "llm_api_key", None), patch.object(
            settings, "llm_model", ""
        ):
            result = llm_explainability_service.summarize_uncertainty_flags(
                uncertainty_flags=["unspecified_biomarker_applicability:PMID-1"],
                engine="deterministic",
                top_evidence_count=4,
                manual_review_count=2,
                llm_enabled=True,
            )

        self.assertIsInstance(result, UncertaintyFlagsExplainability)
        self.assertEqual(result.providerStatus, "provider_unconfigured")
        self.assertEqual(result.validationStatus, "not_attempted")
        self.assertTrue(result.summary)

    def test_uncertainty_flags_explainability_accepts_grounded_llm_output(self):
        with (
            patch.object(settings, "llm_provider", "gemini"),
            patch.object(settings, "llm_api_key", "test-key"),
            patch.object(settings, "llm_model", "gemini-2.5-flash"),
            patch.object(
                llm_explainability_service,
                "_gemini_json",
                return_value=(
                    {
                        "candidates": [
                            {
                                "content": {
                                    "parts": [
                                        {
                                            "text": (
                                                '{"summary":"Flags mark ambiguity in the run.",'
                                                '"whyFlagsExist":"They surface incomplete structured fit before operators overread the output.",'
                                                '"whatItMeans":"Treat the flagged evidence as usable but not frictionless.",'
                                                '"flags":["unspecified_biomarker_applicability:PMID-1"]}'
                                            )
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                    21,
                ),
            ),
        ):
            result = llm_explainability_service.summarize_uncertainty_flags(
                uncertainty_flags=["unspecified_biomarker_applicability:PMID-1"],
                engine="deterministic",
                top_evidence_count=4,
                manual_review_count=2,
                llm_enabled=True,
            )

        self.assertEqual(result.providerStatus, "llm_grounded")
        self.assertEqual(result.validationStatus, "passed")
        self.assertEqual(result.flags, ["unspecified_biomarker_applicability:PMID-1"])

    def test_uncertainty_flags_explainability_accepts_grounded_openrouter_output(self):
        with (
            patch.object(settings, "llm_provider", "openrouter"),
            patch.object(settings, "llm_api_key", "test-key"),
            patch.object(settings, "llm_model", "google/gemini-2.5-flash-lite-preview-09-2025:nitro"),
            patch.object(
                llm_explainability_service,
                "_openrouter_json",
                return_value=(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": (
                                        '{"summary":"Flags mark ambiguity in the run.",'
                                        '"whyFlagsExist":"They surface incomplete structured fit before operators overread the output.",'
                                        '"whatItMeans":"Treat the flagged evidence as usable but not frictionless.",'
                                        '"flags":["unspecified_biomarker_applicability:PMID-1"]}'
                                    )
                                }
                            }
                        ]
                    },
                    32,
                ),
            ),
        ):
            result = llm_explainability_service.summarize_uncertainty_flags(
                uncertainty_flags=["unspecified_biomarker_applicability:PMID-1"],
                engine="deterministic",
                top_evidence_count=4,
                manual_review_count=2,
                llm_enabled=True,
            )

        self.assertEqual(result.providerStatus, "llm_grounded")
        self.assertEqual(result.validationStatus, "passed")
        self.assertEqual(result.flags, ["unspecified_biomarker_applicability:PMID-1"])
        self.assertEqual(result.provider, "openrouter")


if __name__ == "__main__":
    unittest.main()
