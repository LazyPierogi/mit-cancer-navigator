from __future__ import annotations

from threading import Lock, Thread

from app.services.evaluation_service import evaluation_service
from app.services.import_pipeline import import_pipeline_service
from app.services.sample_data import load_sample_evidence, load_sample_topics

try:
    from app.services.semantic_retrieval_service import semantic_retrieval_service
except Exception:
    semantic_retrieval_service = None


_SCHEDULE_LOCK = Lock()
_SCHEDULED_BUILD_KEYS: set[str] = set()
BENCHMARK_PRIMER_PACK_ID = "demo_presets"
BENCHMARK_PRIMER_RETRIEVAL_MODE = "hybrid"
BENCHMARK_CACHE_PACK_ID = "frozen_pack"
BENCHMARK_CACHE_RETRIEVAL_MODE = "hybrid"


class RuntimePrewarmService:
    def prewarm(self, *, include_semantic: bool = False, include_benchmark: bool = False) -> dict:
        summary = import_pipeline_service.get_import_summary()
        topics = load_sample_topics()
        evidence = load_sample_evidence()
        semantic = None
        if include_semantic and semantic_retrieval_service is not None:
            semantic = semantic_retrieval_service.prewarm_runtime()
        benchmark = None
        if include_benchmark:
            try:
                frozen_cached_payload = evaluation_service.get_cached_engine_comparison(
                    pack_id=BENCHMARK_CACHE_PACK_ID,
                    retrieval_mode=BENCHMARK_CACHE_RETRIEVAL_MODE,
                )
                strategy = "cache_hit"
                benchmark_pack_id = BENCHMARK_CACHE_PACK_ID
                benchmark_retrieval_mode = BENCHMARK_CACHE_RETRIEVAL_MODE
                benchmark_payload = frozen_cached_payload
                if benchmark_payload is None:
                    strategy = "primer"
                    benchmark_pack_id = BENCHMARK_PRIMER_PACK_ID
                    benchmark_retrieval_mode = BENCHMARK_PRIMER_RETRIEVAL_MODE
                    benchmark_payload = evaluation_service.run_engine_comparison(
                        pack_id=BENCHMARK_PRIMER_PACK_ID,
                        retrieval_mode=BENCHMARK_PRIMER_RETRIEVAL_MODE,
                        force_refresh=False,
                    )
                benchmark = {
                    "packId": benchmark_pack_id,
                    "retrievalMode": benchmark_retrieval_mode,
                    "cacheReady": True,
                    "cached": bool((benchmark_payload.get("meta") or {}).get("cached", False)),
                    "cacheKey": (benchmark_payload.get("meta") or {}).get("cacheKey"),
                    "strategy": strategy,
                }
            except Exception as exc:
                benchmark = {
                    "packId": BENCHMARK_PRIMER_PACK_ID,
                    "retrievalMode": BENCHMARK_PRIMER_RETRIEVAL_MODE,
                    "cacheReady": False,
                    "strategy": "primer",
                    "error": str(exc),
                }

        return {
            "status": "ready",
            "deterministic": {
                "topicCount": len(topics),
                "evidenceCount": len(evidence),
            },
            "summary": {
                "activeTopics": summary.get("activeTopics", 0),
                "activeEvidenceStudies": summary.get("activeEvidenceStudies", 0),
            },
            "semantic": semantic,
            "benchmark": benchmark,
        }

    def schedule_post_deploy_prewarm(self, *, build_key: str, include_semantic: bool = True, include_benchmark: bool = True) -> bool:
        with _SCHEDULE_LOCK:
            if build_key in _SCHEDULED_BUILD_KEYS:
                return False
            _SCHEDULED_BUILD_KEYS.add(build_key)

        Thread(
            target=self._run_scheduled_prewarm,
            kwargs={
                "build_key": build_key,
                "include_semantic": include_semantic,
                "include_benchmark": include_benchmark,
            },
            daemon=True,
            name=f"runtime-prewarm-{build_key}",
        ).start()
        return True

    def _run_scheduled_prewarm(self, *, build_key: str, include_semantic: bool, include_benchmark: bool) -> None:
        try:
            print(
                "[runtime_prewarm] scheduled_start "
                f"build={build_key} include_semantic={include_semantic} include_benchmark={include_benchmark}"
            )
            payload = self.prewarm(include_semantic=include_semantic, include_benchmark=include_benchmark)
            benchmark = payload.get("benchmark") or {}
            print(
                "[runtime_prewarm] scheduled_complete "
                f"build={build_key} benchmark_cache_ready={benchmark.get('cacheReady')} "
                f"benchmark_cached={benchmark.get('cached')}"
            )
        except Exception as exc:
            print(f"[runtime_prewarm] scheduled_failed build={build_key} reason={type(exc).__name__}: {exc}")


runtime_prewarm_service = RuntimePrewarmService()
