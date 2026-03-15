import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SQLALCHEMY_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from app.api.routes.evals import get_cached_engine_comparison
    from app.schemas.contracts import EngineBenchmarkRequestModel


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "SQLAlchemy is not installed in this environment.")
class EvalsCachedRouteTest(unittest.TestCase):
    def _payload(self) -> EngineBenchmarkRequestModel:
        return EngineBenchmarkRequestModel(
            packId="frozen_pack",
            retrievalMode="hybrid",
            forceRefresh=False,
        )

    def test_cached_compare_returns_cached_payload(self):
        with patch("app.api.routes.evals.evaluation_service.get_cached_engine_comparison", return_value={
            "evalRunId": "benchmark-cache-hit",
            "packId": "frozen_pack",
            "summary": {
                "packLabel": "Frozen Benchmark Pack",
                "semanticChangesDecisionLayer": False,
                "headline": "Cached benchmark",
                "recommendedTakeaway": "Use cached benchmark.",
                "benchmarkNarrative": None,
            },
            "engines": [],
            "breakdown": {
                "retrieval": {},
                "decisionLayer": {},
                "caseDeltas": [],
            },
            "meta": {
                "cached": True,
                "cacheKey": "benchmark-cache-hit",
                "benchmarkVersion": "benchmark-v4",
                "pubmedBatchId": "pubmed-batch",
                "esmoBatchId": "esmo-batch",
                "pubmedSemanticJobId": "pubmed-semantic-job",
                "esmoSemanticJobId": "esmo-semantic-job",
                "sourceFingerprint": "source-fingerprint",
                "runtimeConfigFingerprint": "runtime-fingerprint",
                "vectorStore": "local_hybrid_fallback",
                "embeddingModel": "hash-embedding-v1",
            },
            "notes": [],
        }):
            payload = get_cached_engine_comparison(self._payload())

        self.assertEqual(payload["meta"]["cached"], True)
        self.assertEqual(payload["meta"]["cacheKey"], "benchmark-cache-hit")

    def test_cached_compare_returns_404_on_cache_miss(self):
        with patch("app.api.routes.evals.evaluation_service.get_cached_engine_comparison", return_value=None):
            with self.assertRaises(HTTPException) as context:
                get_cached_engine_comparison(self._payload())

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
