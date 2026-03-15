from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.domain.contracts import ExplainabilitySummary, SemanticEvidenceItem, SemanticGuidelineCandidate, VignetteInput
from app.domain.rules import MIN_STRUCTURED_FACETS_FOR_PRIMARY, relevance_gate, structured_facets_count, topic_applies
from app.config.settings import settings
from app.repositories.bootstrap import bootstrap_database
from app.repositories.corpus_store import corpus_store
from app.repositories.semantic_store import semantic_store
from app.services.llm_explainability_service import llm_explainability_service


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
HISTOLOGY_TRANSLATION_PATH_CANDIDATES = (
    PACKAGE_ROOT / "datasets" / "histology_translation_compact.json",
    REPO_ROOT / "datasets" / "histology_translation_compact.json",
)
EMBEDDING_MODEL = "hash-embedding-v1"
CHUNKING_STRATEGY_VERSION = "semantic-chunking-v1"
PROJECTION_METHOD = "hash-projection-v1"
PROJECTION_LABEL_MAX_LENGTH = 160
LOCAL_VECTOR_STORE = "local_hybrid_fallback"
QDRANT_VECTOR_STORE = "qdrant_hybrid"
QDRANT_DENSE_VECTOR_NAME = "dense"
QDRANT_SPARSE_VECTOR_NAME = "sparse"
EMBEDDING_BATCH_SIZE = 64
QDRANT_UPSERT_BATCH_SIZE = 64
QUERY_EMBEDDING_TIMEOUT_SECONDS = 5
QDRANT_QUERY_TIMEOUT_SECONDS = 5
QDRANT_FAILURE_COOLDOWN_SECONDS = 60
DEFAULT_SEMANTIC_DATASET_FILENAMES = {
    "esmo": "topics.curated.json",
    "pubmed": "evidence.curated.json",
}
DEFAULT_SEMANTIC_DATASET_ROOTS = {
    "esmo": (
        PACKAGE_ROOT / "datasets" / "esmo",
        REPO_ROOT / "datasets" / "esmo",
    ),
    "pubmed": (
        PACKAGE_ROOT / "datasets" / "pubmed",
        REPO_ROOT / "datasets" / "pubmed",
    ),
}


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9\+\-]+", text.lower()) if token]


def _dense_vector(text: str, dims: int = 48) -> list[float]:
    vector = [0.0] * dims
    for token in _tokenize(text):
        vector[_stable_token_index(token) % dims] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


def _sparse_vector(text: str) -> dict[str, float]:
    counts = Counter(_tokenize(text))
    total = sum(counts.values()) or 1
    return {token: round(count / total, 6) for token, count in counts.items()}


def _stable_token_index(token: str) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % 2_147_483_647


def _qdrant_sparse_vector(text: str) -> dict[str, list[float] | list[int]]:
    merged: dict[int, float] = {}
    for token, weight in _sparse_vector(text).items():
        index = _stable_token_index(token)
        merged[index] = round(merged.get(index, 0.0) + weight, 6)
    indices = sorted(merged)
    return {
        "indices": indices,
        "values": [merged[index] for index in indices],
    }


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return round(sum(l * r for l, r in zip(left, right, strict=False)), 6)


def _sparse_overlap(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    overlap = set(left) & set(right)
    if not overlap:
        return 0.0
    score = sum(min(left[token], right[token]) for token in overlap)
    return round(score, 6)


def _project(vector: list[float]) -> tuple[float, float]:
    if len(vector) < 4:
        return (0.0, 0.0)
    return (round(vector[0] - vector[1], 6), round(vector[2] - vector[3], 6))


def _projection_label(title: str) -> str:
    normalized = " ".join(title.split())
    if len(normalized) <= PROJECTION_LABEL_MAX_LENGTH:
        return normalized
    return f"{normalized[: PROJECTION_LABEL_MAX_LENGTH - 3].rstrip()}..."


def _qdrant_point_id(chunk_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, chunk_id))


class SemanticRetrievalService:
    def __init__(self) -> None:
        translation_path = next((path for path in HISTOLOGY_TRANSLATION_PATH_CANDIDATES if path.exists()), None)
        translation_payload = (
            json.loads(translation_path.read_text(encoding="utf-8"))
            if translation_path is not None
            else {"mapping": {}}
        )
        self._histology_mapping = {
            key.strip().lower(): value for key, value in translation_payload.get("mapping", {}).items() if key.strip()
        }
        self._runtime_cache: dict[tuple, object] = {}
        self._seed_lock = Lock()
        self._qdrant_circuit_open_until = 0.0

    def _semantic_runtime_revision(self) -> tuple[str, str, str, str]:
        pubmed_status = semantic_store.get_dataset_status(dataset_kind="pubmed")
        esmo_status = semantic_store.get_dataset_status(dataset_kind="esmo")
        return (
            pubmed_status.get("latestBatchId") or "no-pubmed-batch",
            esmo_status.get("latestBatchId") or "no-esmo-batch",
            pubmed_status.get("latestJob", {}).get("jobId") or "no-pubmed-job",
            esmo_status.get("latestJob", {}).get("jobId") or "no-esmo-job",
        )

    def _get_chunks_cached(self, *, dataset_kind: str | None = None) -> list[dict]:
        cache_key = ("chunks", dataset_kind, *self._semantic_runtime_revision())
        cached = self._runtime_cache.get(cache_key)
        if cached is not None:
            return list(cached)

        chunks = tuple(semantic_store.get_chunks(dataset_kind=dataset_kind))
        self._runtime_cache[cache_key] = chunks
        return list(chunks)

    def _get_points_cached(self, *, dataset_kind: str | None = None) -> list[dict]:
        cache_key = ("points", dataset_kind, *self._semantic_runtime_revision())
        cached = self._runtime_cache.get(cache_key)
        if cached is not None:
            return list(cached)

        points = tuple(semantic_store.get_projection_points(dataset_kind=dataset_kind))
        self._runtime_cache[cache_key] = points
        return list(points)

    def _build_semantic_artifacts(self, *, dataset_kind: str, documents: list[dict]) -> tuple[list[dict], list[dict]]:
        chunks: list[dict] = []
        points: list[dict] = []
        for document in documents:
            document_chunks = self._build_chunks(document)
            chunks.extend(document_chunks)
            for chunk in document_chunks:
                x, y = _project(chunk["denseVector"])
                points.append(
                    {
                        "pointId": f"point-{chunk['chunkId']}",
                        "chunkId": chunk["chunkId"],
                        "documentId": chunk["documentId"],
                        "sourceType": chunk["sourceType"],
                        "sourceId": chunk["sourceId"],
                        "topicId": chunk.get("topicId"),
                        "title": chunk["title"],
                        "histology": chunk["metadata"].get("histology", "unspecified"),
                        "x": x,
                        "y": y,
                        "label": _projection_label(chunk["title"]),
                        "metadata": {
                            "datasetKind": dataset_kind,
                            "projectionMethod": PROJECTION_METHOD,
                            "sourceType": chunk["sourceType"],
                            "runtimeBacked": True,
                        },
                    }
                )
        return chunks, points

    @staticmethod
    def _batched(items: list, size: int) -> list[list]:
        return [items[index : index + size] for index in range(0, len(items), size)]

    def _embedding_model_name(self) -> str:
        provider = settings.embedding_provider.strip().lower()
        if provider in {"openrouter", "openai"} and settings.embedding_model.strip():
            return settings.embedding_model.strip()
        return EMBEDDING_MODEL

    def _configured_vector_store(self) -> str:
        if (
            settings.semantic_vector_backend.strip().lower() == "qdrant"
            and settings.qdrant_url
            and settings.qdrant_api_key
            and settings.embedding_api_key
            and settings.embedding_provider.strip().lower() in {"openrouter", "openai"}
        ):
            return QDRANT_VECTOR_STORE
        return LOCAL_VECTOR_STORE

    def _http_json(self, *, method: str, url: str, payload: dict | None, headers: dict[str, str], timeout: int = 60) -> dict:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib_request.Request(url=url, data=body, method=method.upper())
        for key, value in headers.items():
            request.add_header(key, value)
        try:
            with urllib_request.urlopen(request, timeout=timeout) as response:
                content = response.read().decode("utf-8")
        except urllib_error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method.upper()} {url} failed with {exc.code}: {details}") from exc
        if not content:
            return {}
        return json.loads(content)

    def _embed_texts(self, texts: list[str], *, input_type: str, timeout: int | None = None) -> list[list[float]]:
        if not texts:
            return []

        provider = settings.embedding_provider.strip().lower()
        if provider not in {"openrouter", "openai"} or not settings.embedding_api_key:
            return [_dense_vector(text) for text in texts]

        endpoint = (
            "https://openrouter.ai/api/v1/embeddings"
            if provider == "openrouter"
            else "https://api.openai.com/v1/embeddings"
        )
        headers = {
            "Authorization": f"Bearer {settings.embedding_api_key}",
            "Content-Type": "application/json",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://mit-cancer-navigator-api.vercel.app"
            headers["X-Title"] = "MIT Cancer Navigator"

        embeddings: list[list[float]] = []
        for batch in self._batched(texts, EMBEDDING_BATCH_SIZE):
            payload: dict[str, object] = {
                "model": self._embedding_model_name(),
                "input": batch,
                "encoding_format": "float",
            }
            if provider == "openrouter":
                payload["input_type"] = input_type
            response = self._http_json(
                method="POST",
                url=endpoint,
                payload=payload,
                headers=headers,
                timeout=timeout or 90,
            )
            data = response.get("data", [])
            ordered = sorted(data, key=lambda item: item.get("index", 0))
            embeddings.extend([list(item.get("embedding", [])) for item in ordered])
        return embeddings

    def _qdrant_collection_name(self, dataset_kind: str) -> str:
        return settings.qdrant_collection_pubmed if dataset_kind == "pubmed" else settings.qdrant_collection_esmo

    def _qdrant_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "api-key": settings.qdrant_api_key or "",
        }

    def _qdrant_request(
        self,
        *,
        method: str,
        path: str,
        payload: dict | None = None,
        timeout: int = 60,
        allow_statuses: set[int] | None = None,
    ) -> tuple[int, dict]:
        url = f"{(settings.qdrant_url or '').rstrip('/')}{path}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib_request.Request(url=url, data=body, method=method.upper())
        for key, value in self._qdrant_headers().items():
            request.add_header(key, value)
        try:
            with urllib_request.urlopen(request, timeout=timeout) as response:
                content = response.read().decode("utf-8")
                return response.status, json.loads(content) if content else {}
        except urllib_error.HTTPError as exc:
            if allow_statuses and exc.code in allow_statuses:
                content = exc.read().decode("utf-8", errors="replace")
                return exc.code, json.loads(content) if content else {}
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method.upper()} {url} failed with {exc.code}: {details}") from exc

    def _ensure_qdrant_collection(self, *, dataset_kind: str, vector_size: int) -> None:
        collection_name = self._qdrant_collection_name(dataset_kind)
        path = f"/collections/{urllib_parse.quote(collection_name, safe='')}"
        status, _payload = self._qdrant_request(method="GET", path=path, allow_statuses={404})
        if status == 200:
            return

        self._qdrant_request(
            method="PUT",
            path=path,
            payload={
                "vectors": {
                    QDRANT_DENSE_VECTOR_NAME: {
                        "size": vector_size,
                        "distance": "Cosine",
                    }
                },
                "sparse_vectors": {
                    QDRANT_SPARSE_VECTOR_NAME: {},
                },
            },
        )

        for field_name in ("sourceId", "topicId", "histology", "diseaseSetting", "lineOfTherapy"):
            self._qdrant_request(
                method="PUT",
                path=f"{path}/index",
                payload={
                    "field_name": field_name,
                    "field_schema": "keyword",
                },
            )

    def _qdrant_upsert_points(self, *, dataset_kind: str, points: list[dict]) -> None:
        if not points:
            return
        path = f"/collections/{urllib_parse.quote(self._qdrant_collection_name(dataset_kind), safe='')}/points?wait=true"
        for batch in self._batched(points, QDRANT_UPSERT_BATCH_SIZE):
            self._qdrant_request(method="PUT", path=path, payload={"points": batch}, timeout=120)

    def _sync_qdrant_dataset(self, *, dataset_kind: str, chunks: list[dict]) -> str:
        if not chunks:
            return QDRANT_VECTOR_STORE

        chunk_batches = self._batched(chunks, EMBEDDING_BATCH_SIZE)
        first_batch = chunk_batches[0]
        first_vectors = self._embed_texts([chunk["text"] for chunk in first_batch], input_type="document")
        if not first_vectors or not first_vectors[0]:
            raise RuntimeError("Embedding provider returned no vectors for Qdrant sync.")

        self._ensure_qdrant_collection(dataset_kind=dataset_kind, vector_size=len(first_vectors[0]))

        def build_points(batch_chunks: list[dict], dense_vectors: list[list[float]]) -> list[dict]:
            batch_points: list[dict] = []
            for chunk, dense_vector in zip(batch_chunks, dense_vectors, strict=False):
                metadata = chunk["metadata"]
                batch_points.append(
                    {
                        "id": _qdrant_point_id(chunk["chunkId"]),
                        "vector": {
                            QDRANT_DENSE_VECTOR_NAME: dense_vector,
                            QDRANT_SPARSE_VECTOR_NAME: _qdrant_sparse_vector(chunk["text"]),
                        },
                        "payload": {
                            "chunkId": chunk["chunkId"],
                            "documentId": chunk["documentId"],
                            "datasetKind": metadata.get("datasetKind"),
                            "sourceType": chunk["sourceType"],
                            "sourceId": chunk["sourceId"],
                            "topicId": chunk.get("topicId"),
                            "title": chunk["title"],
                            "text": chunk["text"],
                            "topicTitle": metadata.get("topicTitle"),
                            "histology": metadata.get("histology", "unspecified"),
                            "diseaseSetting": metadata.get("diseaseSetting", "unspecified"),
                            "lineOfTherapy": metadata.get("lineOfTherapy", "unspecified"),
                            "guidelineStance": metadata.get("guidelineStance"),
                        },
                    }
                )
            return batch_points

        self._qdrant_upsert_points(dataset_kind=dataset_kind, points=build_points(first_batch, first_vectors))
        for batch_chunks in chunk_batches[1:]:
            dense_vectors = self._embed_texts([chunk["text"] for chunk in batch_chunks], input_type="document")
            self._qdrant_upsert_points(dataset_kind=dataset_kind, points=build_points(batch_chunks, dense_vectors))
        return QDRANT_VECTOR_STORE

    def _qdrant_search(self, *, dataset_kind: str, query_text: str, limit: int, retrieval_mode: str) -> list[dict]:
        collection_name = self._qdrant_collection_name(dataset_kind)
        path = f"/collections/{urllib_parse.quote(collection_name, safe='')}/points/query"
        dense_query = self._get_query_embedding_cached(query_text)
        dense_response = self._qdrant_request(
            method="POST",
            path=path,
            payload={
                "query": dense_query,
                "using": QDRANT_DENSE_VECTOR_NAME,
                "limit": limit,
                "with_payload": True,
            },
            timeout=QDRANT_QUERY_TIMEOUT_SECONDS,
        )[1]
        dense_hits = dense_response.get("result", {}).get("points", [])

        sparse_hits: list[dict] = []
        if retrieval_mode != "dense_only":
            sparse_response = self._qdrant_request(
                method="POST",
                path=path,
                payload={
                    "query": _qdrant_sparse_vector(query_text),
                    "using": QDRANT_SPARSE_VECTOR_NAME,
                    "limit": limit,
                    "with_payload": True,
                },
                timeout=QDRANT_QUERY_TIMEOUT_SECONDS,
            )[1]
            sparse_hits = sparse_response.get("result", {}).get("points", [])

        merged: dict[str, dict] = {}
        for rank, hit in enumerate(dense_hits, start=1):
            payload = hit.get("payload", {})
            merged[str(hit.get("id"))] = {
                "chunkId": payload.get("chunkId", hit.get("id")),
                "sourceType": payload.get("sourceType"),
                "sourceId": payload.get("sourceId"),
                "topicId": payload.get("topicId"),
                "title": payload.get("title", ""),
                "text": payload.get("text", ""),
                "metadata": payload,
                "denseScore": round(float(hit.get("score", 0.0)), 6),
                "sparseScore": 0.0,
                "denseRank": rank,
                "sparseRank": None,
            }
        for rank, hit in enumerate(sparse_hits, start=1):
            payload = hit.get("payload", {})
            key = str(hit.get("id"))
            existing = merged.setdefault(
                key,
                {
                    "chunkId": payload.get("chunkId", hit.get("id")),
                    "sourceType": payload.get("sourceType"),
                    "sourceId": payload.get("sourceId"),
                    "topicId": payload.get("topicId"),
                    "title": payload.get("title", ""),
                    "text": payload.get("text", ""),
                    "metadata": payload,
                    "denseScore": 0.0,
                    "sparseScore": 0.0,
                    "denseRank": None,
                    "sparseRank": rank,
                },
            )
            existing["sparseScore"] = round(float(hit.get("score", 0.0)), 6)
            existing["sparseRank"] = rank

        results = []
        for payload in merged.values():
            payload["score"] = (
                payload["denseScore"]
                if retrieval_mode == "dense_only"
                else round(
                    (
                        (1 / (settings.semantic_rrf_k + payload["denseRank"]))
                        if payload.get("denseRank") is not None
                        else 0.0
                    )
                    + (
                        (1 / (settings.semantic_rrf_k + payload["sparseRank"]))
                        if payload.get("sparseRank") is not None
                        else 0.0
                    ),
                    6,
                )
            )
            results.append(payload)
        results.sort(key=lambda item: (-item["score"], -item["denseScore"], item["chunkId"]))
        return results

    def import_dataset(self, *, dataset_kind: str, source_path: str, retrieval_mode: str) -> dict:
        bootstrap_database()
        path = Path(source_path).expanduser()
        if not path.is_absolute():
            path = PACKAGE_ROOT / path
        path = path.resolve()

        source_files = self._collect_source_files(dataset_kind=dataset_kind, source_path=path)
        documents: list[dict] = []
        for file_path in source_files:
            loaded = self._load_pubmed_documents(file_path) if dataset_kind == "pubmed" else self._load_esmo_documents(file_path)
            documents.extend(loaded)
        chunks, points = self._build_semantic_artifacts(dataset_kind=dataset_kind, documents=documents)

        batch_id = f"semantic-{dataset_kind}-{uuid4()}"
        vector_store = LOCAL_VECTOR_STORE
        notes = [
            "Qdrant-compatible semantic artifacts generated.",
            "Local hybrid fallback is active until an external vector backend is configured.",
        ]
        if self._configured_vector_store() == QDRANT_VECTOR_STORE:
            try:
                vector_store = self._sync_qdrant_dataset(dataset_kind=dataset_kind, chunks=chunks)
                notes = [
                    "Semantic artifacts synced to Qdrant with external embeddings.",
                    "Local semantic tables remain available for atlas/debug surfaces.",
                ]
            except Exception as exc:
                notes.append(f"External vector sync failed; fallback stayed local. Reason: {exc}")
        job = {
            "jobId": f"job-semantic-{dataset_kind}-{uuid4()}",
            "status": "completed",
            "vectorStore": vector_store,
            "retrievalMode": retrieval_mode,
            "embeddingModel": self._embedding_model_name() if vector_store == QDRANT_VECTOR_STORE else EMBEDDING_MODEL,
            "chunkingStrategyVersion": CHUNKING_STRATEGY_VERSION,
            "documentCount": len(documents),
            "chunkCount": len(chunks),
            "notes": notes,
        }
        self._runtime_cache.clear()
        return semantic_store.replace_dataset(
            dataset_kind=dataset_kind,
            import_batch_id=batch_id,
            documents=documents,
            chunks=chunks,
            projection_points=points,
            job=job,
        )

    def _load_runtime_records(self, dataset_kind: str) -> list[dict]:
        if dataset_kind == "esmo":
            payload = corpus_store.get_guideline_topics()
            if payload:
                return payload
            source_path = self._default_source_path(dataset_kind)
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            return payload.get("records", payload) if isinstance(payload, dict) else payload

        payload = corpus_store.get_evidence_studies()
        if payload:
            return payload
        source_path = self._default_source_path(dataset_kind)
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        return payload.get("records", payload) if isinstance(payload, dict) else payload

    def import_runtime_dataset(self, *, dataset_kind: str, retrieval_mode: str) -> dict:
        bootstrap_database()
        records = self._load_runtime_records(dataset_kind)
        documents = self._documents_from_runtime_records(dataset_kind=dataset_kind, records=records)
        chunks, points = self._build_semantic_artifacts(dataset_kind=dataset_kind, documents=documents)

        summary = corpus_store.get_import_summary()
        upstream_batch = summary.get("latestByKind", {}).get(dataset_kind, {}).get("batchId")
        batch_id = upstream_batch or f"semantic-runtime-{dataset_kind}-{uuid4()}"
        vector_store = LOCAL_VECTOR_STORE
        notes = [
            "Runtime semantic corpus generated from the currently imported deterministic dataset.",
            "Local hybrid fallback is active until an external vector backend is configured.",
        ]
        if self._configured_vector_store() == QDRANT_VECTOR_STORE:
            try:
                vector_store = self._sync_qdrant_dataset(dataset_kind=dataset_kind, chunks=chunks)
                notes = [
                    "Runtime semantic corpus synced to Qdrant from the imported deterministic dataset.",
                    "Local semantic tables remain available for atlas/debug surfaces.",
                ]
            except Exception as exc:
                notes.append(f"External vector sync failed; fallback stayed local. Reason: {exc}")
        job = {
            "jobId": f"job-semantic-runtime-{dataset_kind}-{uuid4()}",
            "status": "completed",
            "vectorStore": vector_store,
            "retrievalMode": retrieval_mode,
            "embeddingModel": self._embedding_model_name() if vector_store == QDRANT_VECTOR_STORE else EMBEDDING_MODEL,
            "chunkingStrategyVersion": CHUNKING_STRATEGY_VERSION,
            "documentCount": len(documents),
            "chunkCount": len(chunks),
            "notes": notes,
        }
        self._runtime_cache.clear()
        return semantic_store.replace_dataset(
            dataset_kind=dataset_kind,
            import_batch_id=batch_id,
            documents=documents,
            chunks=chunks,
            projection_points=points,
            job=job,
        )

    def import_runtime_records_delta(
        self,
        *,
        dataset_kind: str,
        records: list[dict],
        retrieval_mode: str,
        import_batch_id: str,
    ) -> dict:
        bootstrap_database()
        existing_status = semantic_store.get_dataset_status(dataset_kind=dataset_kind)
        if existing_status.get("documentCount", 0) == 0:
            return self.import_runtime_dataset(dataset_kind=dataset_kind, retrieval_mode=retrieval_mode)

        documents = self._documents_from_runtime_records(dataset_kind=dataset_kind, records=records)
        chunks, points = self._build_semantic_artifacts(dataset_kind=dataset_kind, documents=documents)
        vector_store = LOCAL_VECTOR_STORE
        notes = [
            "Incremental semantic refresh for newly appended runtime records.",
            "Only the appended records were chunked, embedded, and upserted.",
        ]
        if self._configured_vector_store() == QDRANT_VECTOR_STORE:
            try:
                vector_store = self._sync_qdrant_dataset(dataset_kind=dataset_kind, chunks=chunks)
                notes = [
                    "Incremental semantic runtime delta synced to Qdrant.",
                    "Only the appended records were reindexed; the existing corpus stayed intact.",
                ]
            except Exception as exc:
                notes.append(f"External vector sync failed; local semantic tables were still updated. Reason: {exc}")
        job = {
            "jobId": f"job-semantic-runtime-delta-{dataset_kind}-{uuid4()}",
            "status": "completed",
            "vectorStore": vector_store,
            "retrievalMode": retrieval_mode,
            "embeddingModel": self._embedding_model_name() if vector_store == QDRANT_VECTOR_STORE else EMBEDDING_MODEL,
            "chunkingStrategyVersion": CHUNKING_STRATEGY_VERSION,
            "documentCount": len(documents),
            "chunkCount": len(chunks),
            "notes": notes,
        }
        self._runtime_cache.clear()
        return semantic_store.upsert_dataset(
            dataset_kind=dataset_kind,
            import_batch_id=import_batch_id,
            documents=documents,
            chunks=chunks,
            projection_points=points,
            job=job,
        )

    def _default_source_path(self, dataset_kind: str) -> Path:
        filename = DEFAULT_SEMANTIC_DATASET_FILENAMES[dataset_kind]
        for root in DEFAULT_SEMANTIC_DATASET_ROOTS[dataset_kind]:
            candidate = (root / filename).resolve()
            if candidate.exists():
                return candidate
        return (DEFAULT_SEMANTIC_DATASET_ROOTS[dataset_kind][0] / filename).resolve()

    def _ensure_seeded(self) -> None:
        with self._seed_lock:
            bootstrap_database()
            import_summary = corpus_store.get_import_summary()
            if semantic_store.get_summary().get("semanticChunks", 0) > 0:
                semantic_pubmed = semantic_store.get_dataset_status(dataset_kind="pubmed")
                semantic_esmo = semantic_store.get_dataset_status(dataset_kind="esmo")
                latest_pubmed_batch = import_summary.get("latestByKind", {}).get("pubmed", {}).get("batchId")
                latest_esmo_batch = import_summary.get("latestByKind", {}).get("esmo", {}).get("batchId")
                desired_vector_store = self._configured_vector_store()
                if (
                    semantic_pubmed.get("latestBatchId") == latest_pubmed_batch
                    and semantic_esmo.get("latestBatchId") == latest_esmo_batch
                    and semantic_pubmed.get("documentCount", 0) > 0
                    and semantic_esmo.get("documentCount", 0) > 0
                    and semantic_pubmed.get("latestJob", {}).get("vectorStore") == desired_vector_store
                    and semantic_esmo.get("latestJob", {}).get("vectorStore") == desired_vector_store
                ):
                    return

            for dataset_kind in ("esmo", "pubmed"):
                self.import_runtime_dataset(dataset_kind=dataset_kind, retrieval_mode="hybrid")

    def get_status(self, *, dataset_kind: str) -> dict:
        bootstrap_database()
        return semantic_store.get_dataset_status(dataset_kind=dataset_kind)

    def get_manifest(self) -> dict:
        self._ensure_seeded()
        bootstrap_database()
        pubmed_status = semantic_store.get_dataset_status(dataset_kind="pubmed")
        esmo_status = semantic_store.get_dataset_status(dataset_kind="esmo")
        cache_key = (
            "manifest",
            pubmed_status.get("latestBatchId"),
            esmo_status.get("latestBatchId"),
            pubmed_status.get("latestJob", {}).get("jobId"),
            esmo_status.get("latestJob", {}).get("jobId"),
        )
        cached = self._runtime_cache.get(cache_key)
        if cached is not None:
            return cached

        summary = semantic_store.get_projection_summary()
        vector_store = pubmed_status.get("latestJob", {}).get("vectorStore") or esmo_status.get("latestJob", {}).get("vectorStore") or LOCAL_VECTOR_STORE
        embedding_model = pubmed_status.get("latestJob", {}).get("embeddingModel") or esmo_status.get("latestJob", {}).get("embeddingModel") or self._embedding_model_name()
        manifest = {
            "pointCount": summary["pointCount"],
            "sourceCounts": summary["sourceCounts"],
            "histologyCounts": summary["histologyCounts"],
            "embeddingModel": embedding_model,
            "projectionMethod": PROJECTION_METHOD,
            "vectorStore": vector_store,
        }
        self._runtime_cache = {key: value for key, value in self._runtime_cache.items() if key[0] != "manifest"}
        self._runtime_cache[cache_key] = manifest
        return manifest

    def _get_query_embedding_cached(self, query_text: str) -> list[float]:
        cache_key = ("query-embedding", self._embedding_model_name(), query_text)
        cached = self._runtime_cache.get(cache_key)
        if cached is not None:
            return list(cached)

        embedding = self._embed_texts([query_text], input_type="query", timeout=QUERY_EMBEDDING_TIMEOUT_SECONDS)[0]
        self._runtime_cache[cache_key] = tuple(embedding)
        return list(embedding)

    def prewarm_query_embeddings_for_vignettes(self, vignettes: list[VignetteInput]) -> int:
        if self._configured_vector_store() != QDRANT_VECTOR_STORE:
            return 0

        missing_queries: list[str] = []
        seen_queries: set[str] = set()
        model_name = self._embedding_model_name()
        for vignette in vignettes:
            query_text = self._build_query_text(vignette)
            if not query_text or query_text in seen_queries:
                continue
            seen_queries.add(query_text)
            cache_key = ("query-embedding", model_name, query_text)
            if cache_key not in self._runtime_cache:
                missing_queries.append(query_text)

        if not missing_queries:
            return 0

        embeddings = self._embed_texts(
            missing_queries,
            input_type="query",
            timeout=QUERY_EMBEDDING_TIMEOUT_SECONDS,
        )
        for query_text, embedding in zip(missing_queries, embeddings, strict=False):
            self._runtime_cache[("query-embedding", model_name, query_text)] = tuple(embedding)
        return len(missing_queries)

    def get_points(self, *, source_type: str | None = None) -> list[dict]:
        self._ensure_seeded()
        bootstrap_database()
        points = self._get_points_cached()
        if source_type:
            return [point for point in points if point["sourceType"] == source_type]
        return points

    def get_neighbors(self, *, point_id: str, limit: int = 8) -> list[dict]:
        self._ensure_seeded()
        bootstrap_database()
        points = self._get_points_cached()
        target = next((point for point in points if point["pointId"] == point_id), None)
        if target is None:
            return []
        chunks = {chunk["chunkId"]: chunk for chunk in self._get_chunks_cached()}
        target_chunk = chunks.get(target["chunkId"])
        if target_chunk is None:
            return []
        neighbors: list[dict] = []
        for point in points:
            if point["pointId"] == point_id:
                continue
            chunk = chunks.get(point["chunkId"])
            if chunk is None:
                continue
            similarity = _cosine_similarity(target_chunk["denseVector"], chunk["denseVector"])
            neighbors.append(
                {
                    "pointId": point["pointId"],
                    "title": point["title"],
                    "sourceType": point["sourceType"],
                    "sourceId": point["sourceId"],
                    "similarity": similarity,
                }
            )
        neighbors.sort(key=lambda item: (-item["similarity"], item["title"]))
        return neighbors[:limit]

    def decorate_response(
        self,
        *,
        vignette: VignetteInput,
        response,
        trace: dict,
        retrieval_mode: str,
        llm_explainability_enabled: bool,
        augmentation: dict | None = None,
    ):
        payload = augmentation or self.build_runtime_augmentation(vignette=vignette, retrieval_mode=retrieval_mode)
        semantic_evidence = payload["semanticEvidence"]
        semantic_candidates = payload["semanticGuidelineCandidates"]
        summary = self._build_summary(vignette, semantic_evidence, semantic_candidates, llm_explainability_enabled)

        response.engine = "semantic_retrieval_lab"
        response.retrievalMode = retrieval_mode
        response.vectorStore = payload["vectorStore"]
        response.embeddingModel = payload["embeddingModel"]
        response.chunkingStrategyVersion = CHUNKING_STRATEGY_VERSION
        response.retrievalCandidateCount = payload["retrievalCandidateCount"]
        response.semanticEvidence = semantic_evidence
        response.semanticGuidelineCandidates = semantic_candidates
        response.explainabilitySummary = summary
        response.semanticCandidateOnlyCount = payload["semanticCandidateOnlyCount"]

        trace["engine"] = response.engine
        trace["retrievalMode"] = response.retrievalMode
        trace["vectorStore"] = response.vectorStore
        trace["embeddingModel"] = response.embeddingModel
        trace["chunkingStrategyVersion"] = response.chunkingStrategyVersion
        trace["retrievalCandidateCount"] = response.retrievalCandidateCount
        trace["semanticCandidateOnlyCount"] = response.semanticCandidateOnlyCount
        trace["retrievalCandidateEvidenceIds"] = payload.get("retrievalCandidateEvidenceIds", [])
        trace["semanticCandidateOnlyEvidenceIds"] = payload.get("semanticCandidateOnlyEvidenceIds", [])
        trace["semanticRescueEvidenceCount"] = len(payload["semanticRescueEvidenceIds"])
        trace["semanticTopicHintCount"] = len(payload["semanticTopicHintsByEvidenceId"])
        return response, trace

    def build_runtime_augmentation(self, *, vignette: VignetteInput, retrieval_mode: str, topics: list | None = None) -> dict:
        self._ensure_seeded()
        if self._configured_vector_store() == QDRANT_VECTOR_STORE:
            if self._qdrant_circuit_is_open():
                return self._build_runtime_augmentation_local(vignette=vignette, retrieval_mode=retrieval_mode, topics=topics)
            try:
                return self._build_runtime_augmentation_qdrant(vignette=vignette, retrieval_mode=retrieval_mode, topics=topics)
            except Exception as exc:
                self._trip_qdrant_circuit()
                print(
                    "[semantic] qdrant_runtime_failed "
                    f"retrieval={retrieval_mode} reason={type(exc).__name__}: {exc}"
                )

        return self._build_runtime_augmentation_local(vignette=vignette, retrieval_mode=retrieval_mode, topics=topics)

    def _qdrant_circuit_is_open(self) -> bool:
        return time.monotonic() < self._qdrant_circuit_open_until

    def _trip_qdrant_circuit(self) -> None:
        self._qdrant_circuit_open_until = time.monotonic() + QDRANT_FAILURE_COOLDOWN_SECONDS

    def _build_runtime_augmentation_local(self, *, vignette: VignetteInput, retrieval_mode: str, topics: list | None = None) -> dict:
        query_text = self._build_query_text(vignette)
        query_dense = _dense_vector(query_text)
        query_sparse = _sparse_vector(query_text)
        evidence_by_id = self._load_evidence_by_id()
        applicable_topic_ids = self._applicable_topic_ids(vignette=vignette, topics=topics or [])
        chunks = self._get_chunks_cached()
        chunk_results: list[dict] = []
        for chunk in chunks:
            metadata = chunk["metadata"]
            if not self._semantic_hit_is_patient_fit(
                vignette=vignette,
                chunk=chunk,
                evidence_by_id=evidence_by_id,
                applicable_topic_ids=applicable_topic_ids,
            ):
                continue

            dense_score = _cosine_similarity(query_dense, chunk["denseVector"])
            sparse_score = _sparse_overlap(query_sparse, chunk["sparseVector"])
            score = self._hybrid_score(dense_score=dense_score, sparse_score=sparse_score, retrieval_mode=retrieval_mode)
            if score <= 0:
                continue
            chunk_results.append(
                {
                    "score": score,
                    "denseScore": dense_score,
                    "sparseScore": sparse_score,
                    "chunkId": chunk["chunkId"],
                    "sourceType": chunk["sourceType"],
                    "sourceId": chunk["sourceId"],
                    "topicId": chunk.get("topicId"),
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "metadata": chunk["metadata"],
                }
            )

        chunk_results = self._limit_chunk_results(chunk_results)

        return self._build_runtime_payload(
            vignette=vignette,
            retrieval_mode=retrieval_mode,
            topics=topics,
            chunk_results=chunk_results,
            vector_store=LOCAL_VECTOR_STORE,
            embedding_model=EMBEDDING_MODEL,
            evidence_by_id=evidence_by_id,
        )

    def _build_runtime_augmentation_qdrant(self, *, vignette: VignetteInput, retrieval_mode: str, topics: list | None = None) -> dict:
        query_text = self._build_query_text(vignette)
        pubmed_limit = max(40, settings.semantic_top_k * 6)
        esmo_limit = 40
        evidence_by_id = self._load_evidence_by_id()
        applicable_topic_ids = self._applicable_topic_ids(vignette=vignette, topics=topics or [])
        # Run pubmed + esmo Qdrant searches concurrently (independent I/O)
        with ThreadPoolExecutor(max_workers=2) as _pool:
            _pubmed_future = _pool.submit(
                self._qdrant_search,
                dataset_kind="pubmed",
                query_text=query_text,
                limit=pubmed_limit,
                retrieval_mode=retrieval_mode,
            )
            _esmo_future = _pool.submit(
                self._qdrant_search,
                dataset_kind="esmo",
                query_text=query_text,
                limit=esmo_limit,
                retrieval_mode=retrieval_mode,
            )
            _raw_pubmed = _pubmed_future.result()
            _raw_esmo = _esmo_future.result()
        pubmed_hits = [
            hit for hit in _raw_pubmed
            if self._semantic_hit_is_patient_fit(
                vignette=vignette, chunk=hit, evidence_by_id=evidence_by_id, applicable_topic_ids=applicable_topic_ids,
            )
        ]
        esmo_hits = [
            hit for hit in _raw_esmo
            if self._semantic_hit_is_patient_fit(
                vignette=vignette, chunk=hit, evidence_by_id=evidence_by_id, applicable_topic_ids=applicable_topic_ids,
            )
        ]
        return self._build_runtime_payload(
            vignette=vignette,
            retrieval_mode=retrieval_mode,
            topics=topics,
            chunk_results=pubmed_hits + esmo_hits,
            vector_store=QDRANT_VECTOR_STORE,
            embedding_model=self._embedding_model_name(),
            evidence_by_id=evidence_by_id,
        )

    def _build_runtime_payload(
        self,
        *,
        vignette: VignetteInput,
        retrieval_mode: str,
        topics: list | None,
        chunk_results: list[dict],
        vector_store: str,
        embedding_model: str,
        evidence_by_id: dict,
    ) -> dict:
        chunk_results.sort(key=lambda item: (-item["score"], -item["denseScore"], item["chunkId"]))
        top_chunks = chunk_results[:10]

        semantic_evidence = [
            SemanticEvidenceItem(
                chunkId=chunk["chunkId"],
                sourceType=chunk["sourceType"],
                sourceId=chunk["sourceId"],
                title=chunk["title"],
                snippet=chunk["text"][:280],
                score=chunk["score"],
                denseScore=chunk["denseScore"],
                sparseScore=chunk["sparseScore"],
                mappedTopicId=chunk.get("topicId"),
                mappedTopicTitle=chunk["metadata"].get("topicTitle"),
            )
            for chunk in top_chunks
        ]

        topic_scores: dict[str, dict] = {}
        evidence_scores: dict[str, float] = {}
        for chunk in chunk_results:
            if chunk["sourceType"] == "esmo":
                topic_id = chunk.get("topicId")
                topic_title = chunk["metadata"].get("topicTitle")
                if topic_id and topic_title:
                    existing = topic_scores.setdefault(topic_id, {"title": topic_title, "score": 0.0, "chunkIds": []})
                    existing["score"] = max(existing["score"], chunk["score"])
                    existing["chunkIds"].append(chunk["chunkId"])
            if chunk["sourceType"] == "pubmed":
                evidence_scores[chunk["sourceId"]] = max(evidence_scores.get(chunk["sourceId"], 0.0), chunk["score"])

        semantic_candidates = [
            SemanticGuidelineCandidate(
                topicId=topic_id,
                topicTitle=payload["title"],
                score=round(payload["score"], 6),
                supportingChunkIds=payload["chunkIds"][:3],
            )
            for topic_id, payload in topic_scores.items()
        ]
        semantic_candidates.sort(key=lambda item: (-item.score, item.topicId))
        semantic_candidates = semantic_candidates[:5]

        ranked_evidence_ids = [source_id for source_id, _score in sorted(evidence_scores.items(), key=lambda item: (-item[1], item[0]))]
        candidate_evidence_ids = ranked_evidence_ids[: self._semantic_candidate_window(settings.semantic_top_k)]
        rescue_limit = min(len(candidate_evidence_ids), max(12, min(24, len(candidate_evidence_ids) // 2)))
        rescue_evidence_ids = self._select_semantic_rescue_ids(
            ranked_evidence_ids=candidate_evidence_ids,
            evidence_by_id=evidence_by_id,
            rescue_limit=rescue_limit,
        )
        chunks = self._get_chunks_cached()
        semantic_topic_hints = self._build_evidence_topic_hints(
            vignette=vignette,
            topics=topics or [],
            chunks=chunks,
            candidate_evidence_ids=list(rescue_evidence_ids),
            retrieval_mode=retrieval_mode,
        )
        semantic_candidate_only_count = len(
            [evidence_id for evidence_id in ranked_evidence_ids if evidence_id not in semantic_topic_hints]
        )

        return {
            "chunkResults": chunk_results,
            "semanticEvidence": semantic_evidence,
            "semanticGuidelineCandidates": semantic_candidates,
            "retrievalCandidateCount": len(ranked_evidence_ids),
            "semanticCandidateOnlyCount": semantic_candidate_only_count,
            "retrievalCandidateEvidenceIds": ranked_evidence_ids,
            "semanticCandidateOnlyEvidenceIds": [
                evidence_id for evidence_id in ranked_evidence_ids if evidence_id not in semantic_topic_hints
            ],
            "semanticEvidenceScores": evidence_scores,
            "semanticRescueEvidenceIds": rescue_evidence_ids,
            "semanticTopicHintsByEvidenceId": semantic_topic_hints,
            "vectorStore": vector_store,
            "embeddingModel": embedding_model,
        }

    @staticmethod
    def _applicable_topic_ids(*, vignette: VignetteInput, topics: list) -> set[str]:
        return {topic.topicId for topic in topics if topic_applies(vignette, topic)}

    @staticmethod
    def _semantic_hit_is_patient_fit(
        *,
        vignette: VignetteInput,
        chunk: dict,
        evidence_by_id: dict,
        applicable_topic_ids: set[str],
    ) -> bool:
        if chunk["sourceType"] == "esmo":
            topic_id = chunk.get("topicId") or chunk["metadata"].get("topicId")
            return topic_id in applicable_topic_ids

        evidence = evidence_by_id.get(chunk["sourceId"])
        if evidence is not None:
            passed, _reasons = relevance_gate(vignette, evidence)
            return passed

        metadata = chunk["metadata"]
        return (
            metadata.get("diseaseSetting") in {None, "unspecified", vignette.diseaseSetting, "mixed"}
            and metadata.get("lineOfTherapy") in {None, "unspecified", vignette.lineOfTherapy, "mixed"}
            and metadata.get("diseaseStage") in {None, "unspecified", vignette.diseaseStage, "mixed"}
            and metadata.get("resectabilityStatus") in {None, "unspecified", vignette.resectabilityStatus}
            and metadata.get("treatmentContext") in {None, "unspecified", vignette.treatmentContext}
            and metadata.get("brainMetastases")
            in {None, "unspecified", vignette.clinicalModifiers.brainMetastases}
        )

    @staticmethod
    def _load_evidence_by_id() -> dict:
        from app.services.sample_data import load_sample_evidence_by_id

        return load_sample_evidence_by_id()

    def prewarm_runtime(self) -> dict:
        self._ensure_seeded()
        bootstrap_database()
        points = self._get_points_cached()
        chunks = self._get_chunks_cached()
        return {
            "semanticReady": True,
            "chunkCount": len(chunks),
            "pointCount": len(points),
            "vectorStore": self.get_manifest().get("vectorStore"),
        }

    def _documents_from_runtime_records(self, *, dataset_kind: str, records: list[dict]) -> list[dict]:
        if dataset_kind == "pubmed":
            return [self._load_pubmed_document_from_runtime_record(row) for row in records]
        return [self._esmo_row_to_document(row) for row in records]

    @staticmethod
    def _semantic_candidate_window(top_k: int) -> int:
        return max(top_k, min(60, top_k * 3))

    @staticmethod
    def _limit_chunk_results(chunk_results: list[dict]) -> list[dict]:
        if not chunk_results:
            return []
        pubmed_limit = max(40, settings.semantic_top_k * 6)
        esmo_limit = 40
        pubmed_hits = sorted(
            [chunk for chunk in chunk_results if chunk["sourceType"] == "pubmed"],
            key=lambda item: (-item["score"], -item["denseScore"], item["chunkId"]),
        )[:pubmed_limit]
        esmo_hits = sorted(
            [chunk for chunk in chunk_results if chunk["sourceType"] == "esmo"],
            key=lambda item: (-item["score"], -item["denseScore"], item["chunkId"]),
        )[:esmo_limit]
        return pubmed_hits + esmo_hits

    @staticmethod
    def _select_semantic_rescue_ids(*, ranked_evidence_ids: list[str], evidence_by_id: dict, rescue_limit: int) -> set[str]:
        sparse_ranked_ids = [
            evidence_id
            for evidence_id in ranked_evidence_ids
            if (record := evidence_by_id.get(evidence_id)) is not None
            and structured_facets_count(record) < MIN_STRUCTURED_FACETS_FOR_PRIMARY
        ]
        selected = sparse_ranked_ids[:rescue_limit]
        if len(selected) < rescue_limit:
            for evidence_id in ranked_evidence_ids:
                if evidence_id in selected:
                    continue
                selected.append(evidence_id)
                if len(selected) >= rescue_limit:
                    break
        return set(selected)

    def _build_query_text(self, vignette: VignetteInput) -> str:
        biomarker_tokens = [
            f"{field_name}:{value}"
            for field_name in getattr(type(vignette.biomarkers), "__dataclass_fields__", {})
            if (value := getattr(vignette.biomarkers, field_name)) != "unspecified"
        ]
        modifier_tokens = [
            f"brain_metastases:{vignette.clinicalModifiers.brainMetastases}"
            if vignette.clinicalModifiers.brainMetastases != "unspecified"
            else ""
        ]
        return " ".join(
            item
            for item in [
                vignette.cancerType,
                vignette.diseaseSetting,
                vignette.diseaseStage,
                vignette.histology,
                vignette.lineOfTherapy,
                vignette.resectabilityStatus,
                vignette.treatmentContext,
                f"ps:{vignette.performanceStatus}",
                *biomarker_tokens,
                *modifier_tokens,
            ]
            if item
        )

    def _build_evidence_topic_hints(
        self,
        *,
        vignette: VignetteInput,
        topics: list,
        chunks: list[dict],
        candidate_evidence_ids: list[str],
        retrieval_mode: str,
    ) -> dict[str, str]:
        if not topics or not candidate_evidence_ids:
            return {}

        applicable_topics = [topic for topic in topics if topic_applies(vignette, topic)]
        if not applicable_topics:
            return {}

        topic_ids = {topic.topicId for topic in applicable_topics}
        topic_chunks_by_id: dict[str, list[dict]] = {}
        evidence_chunks_by_id: dict[str, list[dict]] = {}
        for chunk in chunks:
            if chunk["sourceType"] == "esmo" and chunk.get("topicId") in topic_ids:
                topic_chunks_by_id.setdefault(chunk["topicId"], []).append(chunk)
            if chunk["sourceType"] == "pubmed" and chunk["sourceId"] in candidate_evidence_ids:
                evidence_chunks_by_id.setdefault(chunk["sourceId"], []).append(chunk)

        use_external_vectors = self._configured_vector_store() == QDRANT_VECTOR_STORE
        chunk_texts: dict[str, str] = {}
        dense_by_chunk_id: dict[str, list[float]] = {}
        sparse_by_chunk_id: dict[str, dict[str, float]] = {}
        if use_external_vectors:
            texts_to_embed: list[str] = []
            chunk_ids_in_order: list[str] = []
            for evidence_chunks in evidence_chunks_by_id.values():
                for chunk in evidence_chunks:
                    chunk_id = chunk["chunkId"]
                    chunk_texts[chunk_id] = chunk["text"]
                    texts_to_embed.append(chunk["text"])
                    chunk_ids_in_order.append(chunk_id)
            for topic_chunk_group in topic_chunks_by_id.values():
                for chunk in topic_chunk_group:
                    chunk_id = chunk["chunkId"]
                    if chunk_id in chunk_texts:
                        continue
                    chunk_texts[chunk_id] = chunk["text"]
                    texts_to_embed.append(chunk["text"])
                    chunk_ids_in_order.append(chunk_id)
            embedded_vectors = self._embed_texts(texts_to_embed, input_type="document")
            for chunk_id, dense_vector in zip(chunk_ids_in_order, embedded_vectors, strict=False):
                dense_by_chunk_id[chunk_id] = dense_vector
                sparse_by_chunk_id[chunk_id] = _sparse_vector(chunk_texts[chunk_id])

        hints: dict[str, str] = {}
        for evidence_id in candidate_evidence_ids:
            evidence_chunks = evidence_chunks_by_id.get(evidence_id, [])
            if not evidence_chunks:
                continue

            best_topic_id = None
            best_score = 0.0
            for topic in applicable_topics:
                for evidence_chunk in evidence_chunks:
                    for topic_chunk in topic_chunks_by_id.get(topic.topicId, []):
                        if use_external_vectors:
                            dense_score = _cosine_similarity(
                                dense_by_chunk_id.get(evidence_chunk["chunkId"], []),
                                dense_by_chunk_id.get(topic_chunk["chunkId"], []),
                            )
                            sparse_score = _sparse_overlap(
                                sparse_by_chunk_id.get(evidence_chunk["chunkId"], {}),
                                sparse_by_chunk_id.get(topic_chunk["chunkId"], {}),
                            )
                        else:
                            dense_score = _cosine_similarity(evidence_chunk["denseVector"], topic_chunk["denseVector"])
                            sparse_score = _sparse_overlap(evidence_chunk["sparseVector"], topic_chunk["sparseVector"])
                        score = self._hybrid_score(
                            dense_score=dense_score,
                            sparse_score=sparse_score,
                            retrieval_mode=retrieval_mode,
                        )
                        if score > best_score:
                            best_score = score
                            best_topic_id = topic.topicId
            if best_topic_id is not None and best_score >= 0.2:
                hints[evidence_id] = best_topic_id

        return hints

    def _build_summary(
        self,
        vignette: VignetteInput,
        semantic_evidence: list[SemanticEvidenceItem],
        semantic_candidates: list[SemanticGuidelineCandidate],
        llm_explainability_enabled: bool,
    ) -> ExplainabilitySummary:
        if not semantic_evidence:
            return ExplainabilitySummary(
                summary=(
                    "Semantic Retrieval Lab did not find grounded chunk matches for this vignette. "
                    "The deterministic engine remains the source of truth for the current result."
                ),
                grounded=False,
                sourceChunkIds=[],
                providerStatus="grounded_local",
                promptVersion="local-summary-v1",
                validationStatus="not_applicable",
            )

        lead_evidence = semantic_evidence[0]
        lead_topic = semantic_candidates[0].topicTitle if semantic_candidates else "no clear guideline topic"
        fallback_summary = (
            f"Grounded semantic summary: retrieved evidence centers on {lead_evidence.title}. "
            f"The top semantic topic candidate is {lead_topic}. "
            f"All semantic claims are grounded in retrieved chunks and do not replace the deterministic label."
        )
        if llm_explainability_enabled:
            return llm_explainability_service.summarize_semantic_case(
                vignette=vignette,
                semantic_evidence=semantic_evidence,
                semantic_candidates=semantic_candidates,
                fallback_summary=fallback_summary,
            )
        return ExplainabilitySummary(
            summary=fallback_summary,
            grounded=True,
            sourceChunkIds=[item.chunkId for item in semantic_evidence[:3]],
            providerStatus="grounded_local",
            promptVersion="local-summary-v1",
            validationStatus="not_attempted",
            sourceIds=list(dict.fromkeys(item.sourceId for item in semantic_evidence[:5])),
        )

    @staticmethod
    def _hybrid_score(*, dense_score: float, sparse_score: float, retrieval_mode: str) -> float:
        return dense_score if retrieval_mode == "dense_only" else round((dense_score * 0.65) + (sparse_score * 0.35), 6)

    def _load_pubmed_documents(self, source_path: Path) -> list[dict]:
        if source_path.suffix.lower() in {".csv", ".txt"}:
            with source_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            return [self._pubmed_row_to_document(row) for row in rows]

        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [self._pubmed_canonical_to_document(row) for row in payload]
        rows = payload.get("records", payload)
        return [self._pubmed_canonical_to_document(row) for row in rows]

    def _load_esmo_documents(self, source_path: Path) -> list[dict]:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        rows = payload.get("records", payload) if isinstance(payload, dict) else payload
        return [self._esmo_row_to_document(row) for row in rows]

    def _collect_source_files(self, *, dataset_kind: str, source_path: Path) -> list[Path]:
        suffixes = {".json"} if dataset_kind == "esmo" else {".csv", ".txt", ".json"}
        if source_path.is_file():
            return [source_path]
        if not source_path.is_dir():
            raise FileNotFoundError(f"Semantic import source does not exist: {source_path}")
        return sorted([path for path in source_path.rglob("*") if path.is_file() and path.suffix.lower() in suffixes])

    def _pubmed_row_to_document(self, row: dict[str, str]) -> dict:
        pmid = row.get("pmid", "").strip()
        title = row.get("title", "").strip()
        abstract = row.get("abstract", "").strip()
        histology_original = row.get("histology", "").strip() or None
        histology_normalized, histology_source = self._normalize_histology(histology_original, f"{title} {abstract}")
        line_of_therapy = self._normalize_token(row.get("lineOfTherapy", "")) or "unspecified"
        disease_setting = self._normalize_token(row.get("diseaseSetting", "")) or "unspecified"
        raw_text = "\n\n".join(part for part in [title, abstract] if part)
        return {
            "documentId": f"semantic-pubmed-{pmid}",
            "sourceId": f"PMID-{pmid}",
            "title": title,
            "sourceUrl": row.get("url"),
            "rawText": raw_text,
            "histologyOriginal": histology_original,
            "histologyNormalized": histology_normalized,
            "histologySource": histology_source,
            "metadata": {
                "datasetKind": "pubmed",
                "sourceType": "pubmed",
                "publicationYear": self._parse_int(row.get("publicationYear", "")),
                "publicationType": row.get("publicationType", "").strip(),
                "evidenceType": row.get("evidenceType", "").strip() or "unspecified",
                "diseaseSetting": disease_setting,
                "histology": histology_normalized,
                "lineOfTherapy": line_of_therapy,
                "topicTitle": None,
            },
        }

    def _pubmed_canonical_to_document(self, row: dict[str, object]) -> dict:
        population = row.get("populationTags", {}) if isinstance(row.get("populationTags"), dict) else {}
        title = str(row.get("title", "")).strip()
        abstract = str(row.get("abstract", "") or "").strip()
        histology_original = str(population.get("histology", "")).strip() or None
        intervention_tags = ", ".join(str(item) for item in row.get("interventionTags", []) if str(item).strip())
        biomarker_summary = ", ".join(
            f"{key}:{value}" for key, value in population.get("biomarkers", {}).items() if str(value).strip() and str(value) != "unspecified"
        )
        context_summary = ", ".join(
            part
            for part in [
                f"diseaseStage:{population.get('diseaseStage')}" if population.get("diseaseStage", "unspecified") != "unspecified" else "",
                (
                    f"resectability:{population.get('resectabilityStatus')}"
                    if population.get("resectabilityStatus", "unspecified") not in {"unspecified", "not_applicable"}
                    else ""
                ),
                (
                    f"treatmentContext:{population.get('treatmentContext')}"
                    if population.get("treatmentContext", "unspecified") != "unspecified"
                    else ""
                ),
                (
                    f"brainMetastases:{population.get('brainMetastases')}"
                    if population.get("brainMetastases", "unspecified") != "unspecified"
                    else ""
                ),
            ]
            if part
        )
        outcome_tags = ", ".join(str(item) for item in row.get("outcomeTags", []) if str(item).strip())
        raw_text = "\n\n".join(
            part for part in [title, abstract, intervention_tags, outcome_tags, biomarker_summary, context_summary] if part
        )
        histology_normalized, histology_source = self._normalize_histology(histology_original, raw_text)
        return {
            "documentId": f"semantic-{row.get('evidenceId', '')}",
            "sourceId": str(row.get("evidenceId", "")).strip(),
            "title": title,
            "sourceUrl": None,
            "rawText": raw_text,
            "histologyOriginal": histology_original,
            "histologyNormalized": histology_normalized,
            "histologySource": histology_source,
            "metadata": {
                "datasetKind": "pubmed",
                "sourceType": "pubmed",
                "publicationYear": row.get("publicationYear"),
                "publicationType": None,
                "evidenceType": row.get("evidenceType", "unspecified"),
                "diseaseSetting": population.get("diseaseSetting", "unspecified"),
                "histology": histology_normalized,
                "lineOfTherapy": population.get("lineOfTherapy", "unspecified"),
                "diseaseStage": population.get("diseaseStage", "unspecified"),
                "resectabilityStatus": population.get("resectabilityStatus", "unspecified"),
                "treatmentContext": population.get("treatmentContext", "unspecified"),
                "brainMetastases": population.get("brainMetastases", "unspecified"),
                "topicTitle": None,
            },
        }

    def _load_pubmed_document_from_runtime_record(self, row: dict[str, object]) -> dict:
        return self._pubmed_canonical_to_document(row)

    def _esmo_row_to_document(self, row: dict[str, object]) -> dict:
        topic_id = str(row.get("topicId", "")).strip()
        title = str(row.get("topicTitle", "")).strip()
        applicability = row.get("topicApplicability", {}) if isinstance(row.get("topicApplicability"), dict) else {}
        histology_candidates = applicability.get("histology", []) if isinstance(applicability.get("histology"), list) else []
        histology_original = str(histology_candidates[0]).strip() if histology_candidates else None
        prerequisites = row.get("prerequisites", []) if isinstance(row.get("prerequisites"), list) else []
        stance_notes = str(row.get("stanceNotes", "")).strip()
        intervention_tags = ", ".join(str(item) for item in row.get("topicInterventionTags", []) if str(item).strip())
        applicability_blob = json.dumps(applicability, ensure_ascii=True, sort_keys=True)
        raw_text = "\n\n".join(
            part
            for part in [title, stance_notes, intervention_tags, applicability_blob, " | ".join(str(item) for item in prerequisites if str(item).strip())]
            if part
        )
        histology_normalized, histology_source = self._normalize_histology(histology_original, raw_text)
        disease_values = applicability.get("diseaseSetting", []) if isinstance(applicability.get("diseaseSetting"), list) else []
        line_values = applicability.get("lineOfTherapy", []) if isinstance(applicability.get("lineOfTherapy"), list) else []
        disease_stage_values = applicability.get("diseaseStage", []) if isinstance(applicability.get("diseaseStage"), list) else []
        resectability_values = (
            applicability.get("resectabilityStatus", [])
            if isinstance(applicability.get("resectabilityStatus"), list)
            else []
        )
        treatment_context_values = (
            applicability.get("treatmentContext", [])
            if isinstance(applicability.get("treatmentContext"), list)
            else []
        )
        return {
            "documentId": f"semantic-esmo-{topic_id}",
            "sourceId": topic_id,
            "title": title,
            "sourceUrl": None,
            "rawText": raw_text,
            "histologyOriginal": histology_original,
            "histologyNormalized": histology_normalized,
            "histologySource": histology_source,
            "metadata": {
                "datasetKind": "esmo",
                "sourceType": "esmo",
                "publicationYear": None,
                "publicationType": None,
                "evidenceType": row.get("guidelineStance", "unspecified"),
                "diseaseSetting": disease_values[0] if disease_values else "unspecified",
                "histology": histology_normalized,
                "lineOfTherapy": line_values[0] if line_values else "unspecified",
                "diseaseStage": disease_stage_values[0] if disease_stage_values else "unspecified",
                "resectabilityStatus": resectability_values[0] if resectability_values else "unspecified",
                "treatmentContext": treatment_context_values[0] if treatment_context_values else "unspecified",
                "topicTitle": title,
                "topicId": topic_id,
                "guidelineStance": row.get("guidelineStance", "not_covered"),
            },
        }

    def _build_chunks(self, document: dict) -> list[dict]:
        paragraphs = [segment.strip() for segment in re.split(r"\n{2,}", document["rawText"]) if segment.strip()]
        segments = paragraphs or [document["rawText"]]
        chunks: list[dict] = []
        for index, segment in enumerate(segments):
            dense = _dense_vector(segment)
            sparse = _sparse_vector(segment)
            chunks.append(
                {
                    "chunkId": f"{document['documentId']}-chunk-{index + 1}",
                    "documentId": document["documentId"],
                    "sourceType": document["metadata"]["sourceType"],
                    "sourceId": document["sourceId"],
                    "topicId": document["metadata"].get("topicId"),
                    "title": document["title"],
                    "text": segment,
                    "denseVector": dense,
                    "sparseVector": sparse,
                    "metadata": document["metadata"],
                }
            )
        return chunks

    def _normalize_histology(self, original: str | None, context: str) -> tuple[str, str]:
        if original:
            normalized_original = self._normalize_token(original)
            if normalized_original in {"squamous", "non_squamous", "all_nsclc"}:
                return normalized_original, "existing_metadata"

        haystack = f"{original or ''} {context}".lower()
        if "nonsquamous" in haystack or "non-squamous" in haystack or "non squamous" in haystack:
            return "non_squamous", "translation_sheet"
        if "squamous" in haystack:
            return "squamous", "translation_sheet"
        for label, bucket in self._histology_mapping.items():
            if label in haystack:
                return bucket, "translation_sheet"
        return "unspecified", "unknown"

    @staticmethod
    def _normalize_token(value: str) -> str:
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        while "__" in normalized:
            normalized = normalized.replace("__", "_")
        return normalized

    @staticmethod
    def _parse_int(value: str) -> int | None:
        cleaned = value.strip()
        if cleaned.isdigit():
            return int(cleaned)
        return None


semantic_retrieval_service = SemanticRetrievalService()
