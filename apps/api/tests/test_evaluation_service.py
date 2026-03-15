import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.evaluation_service import evaluation_service


class EvaluationServiceTest(unittest.TestCase):
    def test_comparison_payload_reports_matches_misses_and_unexpected(self):
        response = SimpleNamespace(
            topEvidence=[
                SimpleNamespace(
                    evidenceId="PMID-36470213",
                    mappingLabel="aligned",
                    mappedTopicId="EGFR_IV_01",
                    mappedTopicTitle="Osimertinib first-line for classical activating EGFR mutation",
                ),
                SimpleNamespace(
                    evidenceId="PMID-EXTRA-1",
                    mappingLabel="guideline_silent",
                    mappedTopicId=None,
                    mappedTopicTitle=None,
                ),
            ]
        )
        comparison = evaluation_service._comparison_payload(
            response=response,
            reference={
                "expectedPrimaryLabel": "aligned",
                "expectedGuidelineTopic": {
                    "topicId": "EGFR_IV_01",
                    "topicTitle": "Osimertinib first-line for classical activating EGFR mutation",
                },
                "expectedTopEvidence": ["PMID-36470213", "PMID-MISSED-1"],
            },
            source_fingerprint="source-hash",
            runtime_config_fingerprint="runtime-hash",
        )

        self.assertEqual(comparison["matchedExpectedEvidenceIds"], ["PMID-36470213"])
        self.assertEqual(comparison["missedExpectedEvidenceIds"], ["PMID-MISSED-1"])
        self.assertEqual(comparison["unexpectedPromotedEvidenceIds"], ["PMID-EXTRA-1"])
        self.assertTrue(comparison["topicMatch"])
        self.assertTrue(comparison["primaryLabelHit"])

    def test_pack_completeness_requires_reference_label_and_pmids(self):
        pack = {
            "cases": [
                {"reference": {"expectedPrimaryLabel": "aligned", "expectedTopEvidence": ["PMID-1"]}},
                {"reference": {"expectedPrimaryLabel": "conflict", "expectedTopEvidence": ["PMID-2"]}},
                {"reference": {"expectedPrimaryLabel": "guideline_silent", "expectedTopEvidence": []}},
            ]
        }
        completeness, is_complete = evaluation_service._pack_completeness(pack)
        self.assertEqual(completeness, "2/3 quantitative goldens present")
        self.assertFalse(is_complete)

    def test_benchmark_narrative_skips_llm_when_explainability_disabled(self):
        pack = {
            "packId": "frozen-pack-canonical-v2",
            "packLabel": "Frozen Benchmark Pack",
            "cases": [
                {
                    "caseId": "case-1",
                    "caseLabel": "Case 1",
                    "detail": "detail",
                    "category": "demo",
                    "clinicalQuestion": "question",
                    "vignette": {"patientId": "case-1"},
                    "reference": {
                        "expectedPrimaryLabel": "aligned",
                        "expectedTopEvidence": ["PMID-1"],
                        "expectedLabelByEvidenceId": {"PMID-1": "aligned"},
                    },
                }
            ],
        }
        response = SimpleNamespace(
            engine="deterministic",
            retrievalMode="hybrid",
            topEvidence=[SimpleNamespace(evidenceId="PMID-1", mappingLabel="aligned", mappedTopicId="TOPIC-1", mappedTopicTitle="Topic 1")],
            manualReviewEvidence=[],
            secondaryReferences=[],
            uncertaintyFlags=[],
        )
        trace = {
            "retrievalCandidateEvidenceIds": ["PMID-1"],
            "semanticCandidateOnlyEvidenceIds": [],
        }

        with (
            patch("app.services.evaluation_service.import_pipeline_service.get_debug_config", return_value={"llmExplainabilityEnabled": False}),
            patch.object(evaluation_service, "_benchmark_cache_context", return_value={
                "cacheId": "benchmark-cache-test",
                "pubmedBatchId": "pubmed-batch",
                "esmoBatchId": "esmo-batch",
                "pubmedSemanticJobId": "pubmed-job",
                "esmoSemanticJobId": "esmo-job",
                "sourceFingerprint": "source-fingerprint",
                "runtimeConfigFingerprint": "runtime-fingerprint",
                "vectorStore": "qdrant_hybrid",
                "embeddingModel": "text-embedding-004",
            }),
            patch.object(evaluation_service, "_load_pack", return_value=pack),
            patch.object(evaluation_service, "_run_engine", return_value=(response, trace, None)),
            patch("app.services.evaluation_service.semantic_retrieval_service.prewarm_query_embeddings_for_vignettes", return_value=1) as prewarm_mock,
            patch("app.services.evaluation_service.run_store.get_benchmark_cache", return_value=None),
            patch("app.services.evaluation_service.run_store.save_benchmark_cache"),
            patch("app.services.llm_explainability_service.llm_explainability_service._gemini_json") as gemini_mock,
        ):
            result = evaluation_service.run_engine_comparison(pack_id="frozen_pack", retrieval_mode="hybrid", force_refresh=True)

        prewarm_mock.assert_called_once()
        gemini_mock.assert_not_called()
        self.assertEqual(result["summary"]["benchmarkNarrative"]["providerStatus"], "llm_disabled")


if __name__ == "__main__":
    unittest.main()
