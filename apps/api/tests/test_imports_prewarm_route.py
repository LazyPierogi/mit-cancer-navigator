import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SQLALCHEMY_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from app.api.routes.imports import prewarm_runtime


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "SQLAlchemy is not installed in this environment.")
class ImportsPrewarmRouteTest(unittest.TestCase):
    def test_prewarm_returns_deterministic_counts_without_semantic(self):
        with (
            patch("app.services.runtime_prewarm_service.import_pipeline_service.get_import_summary", return_value={
                "activeTopics": 71,
                "activeEvidenceStudies": 2090,
            }),
            patch("app.services.runtime_prewarm_service.load_sample_topics", return_value=[object()] * 71),
            patch("app.services.runtime_prewarm_service.load_sample_evidence", return_value=[object()] * 2090),
        ):
            payload = prewarm_runtime(include_semantic=False)

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["deterministic"]["topicCount"], 71)
        self.assertEqual(payload["deterministic"]["evidenceCount"], 2090)
        self.assertIsNone(payload["semantic"])

    def test_prewarm_can_prime_semantic_runtime(self):
        semantic_mock = Mock()
        semantic_mock.prewarm_runtime.return_value = {
            "semanticReady": True,
            "chunkCount": 5705,
            "pointCount": 5705,
            "vectorStore": "qdrant_hybrid",
        }

        with (
            patch("app.services.runtime_prewarm_service.import_pipeline_service.get_import_summary", return_value={
                "activeTopics": 71,
                "activeEvidenceStudies": 2090,
            }),
            patch("app.services.runtime_prewarm_service.load_sample_topics", return_value=[object()] * 71),
            patch("app.services.runtime_prewarm_service.load_sample_evidence", return_value=[object()] * 2090),
            patch("app.services.runtime_prewarm_service.semantic_retrieval_service", semantic_mock),
        ):
            payload = prewarm_runtime(include_semantic=True)

        semantic_mock.prewarm_runtime.assert_called_once_with()
        self.assertEqual(payload["semantic"]["chunkCount"], 5705)
        self.assertEqual(payload["semantic"]["vectorStore"], "qdrant_hybrid")

    def test_prewarm_uses_lightweight_benchmark_primer_when_frozen_cache_is_missing(self):
        benchmark_payload = {
            "meta": {
                "cached": False,
                "cacheKey": "benchmark-cache-key",
            }
        }

        with (
            patch("app.services.runtime_prewarm_service.import_pipeline_service.get_import_summary", return_value={
                "activeTopics": 71,
                "activeEvidenceStudies": 2090,
            }),
            patch("app.services.runtime_prewarm_service.load_sample_topics", return_value=[object()] * 71),
            patch("app.services.runtime_prewarm_service.load_sample_evidence", return_value=[object()] * 2090),
            patch("app.services.runtime_prewarm_service.evaluation_service.get_cached_engine_comparison", return_value=None),
            patch("app.services.runtime_prewarm_service.evaluation_service.run_engine_comparison", return_value=benchmark_payload) as benchmark_mock,
        ):
            payload = prewarm_runtime(include_semantic=False, include_benchmark=True)

        benchmark_mock.assert_called_once_with(pack_id="demo_presets", retrieval_mode="hybrid", force_refresh=False)
        self.assertEqual(payload["benchmark"]["packId"], "demo_presets")
        self.assertEqual(payload["benchmark"]["cacheKey"], "benchmark-cache-key")
        self.assertTrue(payload["benchmark"]["cacheReady"])
        self.assertEqual(payload["benchmark"]["strategy"], "primer")

    def test_prewarm_keeps_frozen_cache_when_already_available(self):
        benchmark_payload = {
            "meta": {
                "cached": True,
                "cacheKey": "benchmark-cache-frozen_pack-hybrid-hit",
            }
        }

        with (
            patch("app.services.runtime_prewarm_service.import_pipeline_service.get_import_summary", return_value={
                "activeTopics": 71,
                "activeEvidenceStudies": 2090,
            }),
            patch("app.services.runtime_prewarm_service.load_sample_topics", return_value=[object()] * 71),
            patch("app.services.runtime_prewarm_service.load_sample_evidence", return_value=[object()] * 2090),
            patch("app.services.runtime_prewarm_service.evaluation_service.get_cached_engine_comparison", return_value=benchmark_payload),
            patch("app.services.runtime_prewarm_service.evaluation_service.run_engine_comparison") as benchmark_mock,
        ):
            payload = prewarm_runtime(include_semantic=False, include_benchmark=True)

        benchmark_mock.assert_not_called()
        self.assertEqual(payload["benchmark"]["packId"], "frozen_pack")
        self.assertEqual(payload["benchmark"]["strategy"], "cache_hit")


if __name__ == "__main__":
    unittest.main()
