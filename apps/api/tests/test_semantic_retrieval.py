import unittest
import sys
from pathlib import Path
import importlib.util
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[3]
SQLALCHEMY_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from app.repositories.bootstrap import bootstrap_database
    from app.repositories.corpus_store import corpus_store
    from app.repositories.db import SessionLocal
    from app.repositories.models import (
        DocumentChunkRecord,
        EmbeddingJobRecord,
        EvidenceStudyRecord,
        ProjectionPointRecord,
        SourceDocumentRecord,
    )
    from app.repositories.semantic_store import semantic_store
    from app.services.import_pipeline import import_pipeline_service
    from app.services.semantic_retrieval_service import (
        _dense_vector,
        _projection_label,
        _qdrant_point_id,
        _qdrant_sparse_vector,
        _stable_token_index,
        semantic_retrieval_service,
    )
    from app.services.evaluation_service import evaluation_service
    from app.domain.contracts import EvidenceRecord, PopulationTags


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "SQLAlchemy is not installed in this environment.")
class SemanticRetrievalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bootstrap_database()

    def test_translation_sheet_normalizes_histology_from_text(self):
        normalized, source = semantic_retrieval_service._normalize_histology(
            None,
            "Improved survival outcomes were observed in squamous histology.",
        )
        self.assertEqual(normalized, "squamous")
        self.assertEqual(source, "translation_sheet")

    def test_semantic_import_builds_pubmed_status(self):
        status = semantic_retrieval_service.import_dataset(
            dataset_kind="pubmed",
            source_path=str(ROOT / "datasets" / "pubmed" / "v.4" / "pubmed-NSCLCANDlo-set_100entries_extracted_v4.csv"),
            retrieval_mode="hybrid",
        )
        self.assertEqual(status["datasetKind"], "pubmed")
        self.assertGreater(status["documentCount"], 0)
        self.assertGreater(status["chunkCount"], 0)

    def test_manifest_returns_projection_counts(self):
        manifest = semantic_retrieval_service.get_manifest()
        self.assertIn("pointCount", manifest)
        self.assertIn("vectorStore", manifest)

    def test_projection_label_is_trimmed_for_visualization(self):
        label = _projection_label("Very long title " * 20)
        self.assertLessEqual(len(label), 160)
        self.assertTrue(label.endswith("..."))

    def test_stable_token_index_is_deterministic(self):
        self.assertEqual(_stable_token_index("egfr"), _stable_token_index("egfr"))
        self.assertNotEqual(_stable_token_index("egfr"), _stable_token_index("alk"))

    def test_dense_vector_is_deterministic(self):
        self.assertEqual(_dense_vector("EGFR TKI improves PFS"), _dense_vector("EGFR TKI improves PFS"))

    def test_qdrant_sparse_vector_is_stable(self):
        first = _qdrant_sparse_vector("EGFR TKI improves PFS")
        second = _qdrant_sparse_vector("EGFR TKI improves PFS")
        self.assertEqual(first, second)
        self.assertEqual(len(first["indices"]), len(first["values"]))

    def test_qdrant_point_id_is_uuid_and_stable(self):
        self.assertEqual(_qdrant_point_id("chunk-1"), _qdrant_point_id("chunk-1"))
        self.assertNotEqual(_qdrant_point_id("chunk-1"), _qdrant_point_id("chunk-2"))

    def test_prewarm_query_embeddings_batches_unique_queries_once(self):
        vignette = SimpleNamespace(
            cancerType="NSCLC",
            diseaseSetting="metastatic",
            diseaseStage="stage_iv",
            histology="non_squamous",
            lineOfTherapy="first_line",
            resectabilityStatus="unresectable",
            treatmentContext="advanced",
            performanceStatus="0_1",
            biomarkers=SimpleNamespace(EGFR="unspecified"),
            clinicalModifiers=SimpleNamespace(brainMetastases="unspecified"),
        )

        with (
            patch.object(semantic_retrieval_service, "_configured_vector_store", return_value="qdrant_hybrid"),
            patch.object(semantic_retrieval_service, "_embedding_model_name", return_value="text-embedding-3-small"),
            patch.object(semantic_retrieval_service, "_embed_texts", return_value=[[0.1, 0.2, 0.3]]) as embed_mock,
        ):
            semantic_retrieval_service._runtime_cache.clear()
            warmed = semantic_retrieval_service.prewarm_query_embeddings_for_vignettes([vignette, vignette])

        self.assertEqual(warmed, 1)
        embed_mock.assert_called_once()

    def test_build_runtime_augmentation_falls_back_to_local_when_qdrant_runtime_fails(self):
        vignette = SimpleNamespace()
        local_payload = {"semanticEvidence": [], "semanticGuidelineCandidates": []}

        with (
            patch.object(semantic_retrieval_service, "_ensure_seeded"),
            patch.object(semantic_retrieval_service, "_configured_vector_store", return_value="qdrant_hybrid"),
            patch.object(semantic_retrieval_service, "_build_runtime_augmentation_qdrant", side_effect=RuntimeError("embedding timeout")),
            patch.object(semantic_retrieval_service, "_build_runtime_augmentation_local", return_value=local_payload) as local_mock,
        ):
            payload = semantic_retrieval_service.build_runtime_augmentation(
                vignette=vignette,
                retrieval_mode="hybrid",
                topics=[],
            )

        local_mock.assert_called_once()
        self.assertEqual(payload, local_payload)

    def test_rescue_selection_prioritizes_sparse_records(self):
        def record(evidence_id: str, *, facets: int) -> EvidenceRecord:
            disease_setting = "metastatic" if facets >= 1 else "unspecified"
            histology = "adenocarcinoma" if facets >= 2 else "unspecified"
            line_of_therapy = "first_line" if facets >= 3 else "unspecified"
            biomarkers = {
                "EGFR": "yes" if facets >= 4 else "unspecified",
                "ALK": "unspecified",
                "ROS1": "unspecified",
                "PDL1Bucket": "unspecified",
                "BRAF": "unspecified",
                "RET": "unspecified",
                "MET": "unspecified",
                "KRAS": "unspecified",
                "NTRK": "unspecified",
                "HER2": "unspecified",
                "EGFRExon20ins": "unspecified",
            }
            return EvidenceRecord(
                evidenceId=evidence_id,
                title=evidence_id,
                abstract=None,
                journalTitle=None,
                publicationYear=2025,
                evidenceType="systematic_review",
                sourceCategory="high_impact_journal",
                relevantN=200,
                populationTags=PopulationTags(
                    disease="NSCLC",
                    diseaseSetting=disease_setting,
                    histology=histology,
                    lineOfTherapy=line_of_therapy,
                    biomarkers=biomarkers,
                ),
                interventionTags=["egfr-tki"],
                outcomeTags=[],
            )

        evidence_by_id = {
            "A": record("A", facets=2),
            "B": record("B", facets=1),
            "C": record("C", facets=1),
            "D": record("D", facets=3),
        }
        selected = semantic_retrieval_service._select_semantic_rescue_ids(
            ranked_evidence_ids=["A", "B", "C", "D"],
            evidence_by_id=evidence_by_id,
            rescue_limit=2,
        )
        self.assertEqual(selected, {"B", "C"})

    def test_semantic_candidate_window_expands_beyond_top_k(self):
        self.assertEqual(semantic_retrieval_service._semantic_candidate_window(25), 60)
        self.assertEqual(semantic_retrieval_service._semantic_candidate_window(10), 30)
        self.assertEqual(semantic_retrieval_service._semantic_candidate_window(80), 80)

    def test_limit_chunk_results_caps_pubmed_and_esmo_separately(self):
        chunk_results = [
            {
                "score": float(300 - index),
                "denseScore": float(300 - index),
                "chunkId": f"pubmed-{index}",
                "sourceType": "pubmed",
            }
            for index in range(250)
        ] + [
            {
                "score": float(120 - index),
                "denseScore": float(120 - index),
                "chunkId": f"esmo-{index}",
                "sourceType": "esmo",
            }
            for index in range(100)
        ]
        limited = semantic_retrieval_service._limit_chunk_results(chunk_results)
        pubmed_hits = [chunk for chunk in limited if chunk["sourceType"] == "pubmed"]
        esmo_hits = [chunk for chunk in limited if chunk["sourceType"] == "esmo"]
        self.assertEqual(len(pubmed_hits), 150)
        self.assertEqual(len(esmo_hits), 40)
        self.assertEqual(pubmed_hits[0]["chunkId"], "pubmed-0")
        self.assertEqual(esmo_hits[0]["chunkId"], "esmo-0")

    def test_query_text_includes_stage_context_and_brain_mets(self):
        from app.domain.contracts import Biomarkers, ClinicalModifiers, VignetteInput

        vignette = VignetteInput(
            cancerType="NSCLC",
            diseaseSetting="locally_advanced",
            diseaseStage="stage_iii",
            histology="non_squamous",
            performanceStatus="1",
            biomarkers=Biomarkers(EGFR="no", ALK="no", ROS1="no", PDL1Bucket="1to49"),
            lineOfTherapy="consolidation",
            resectabilityStatus="unresectable",
            treatmentContext="post_chemoradiation",
            clinicalModifiers=ClinicalModifiers(brainMetastases="yes"),
        )

        query_text = semantic_retrieval_service._build_query_text(vignette)
        self.assertIn("stage_iii", query_text)
        self.assertIn("unresectable", query_text)
        self.assertIn("post_chemoradiation", query_text)
        self.assertIn("brain_metastases:yes", query_text)

    def test_runtime_payload_reports_bounded_raw_retrieval_pool(self):
        payload = semantic_retrieval_service._build_runtime_payload(
            vignette=None,  # not used by the current payload assembly path
            retrieval_mode="hybrid",
            topics=[],
            chunk_results=[
                {
                    "score": 0.9,
                    "denseScore": 0.9,
                    "sparseScore": 0.0,
                    "chunkId": "chunk-a1",
                    "sourceType": "pubmed",
                    "sourceId": "A",
                    "topicId": None,
                    "title": "A",
                    "text": "A",
                    "metadata": {},
                },
                {
                    "score": 0.8,
                    "denseScore": 0.8,
                    "sparseScore": 0.0,
                    "chunkId": "chunk-a2",
                    "sourceType": "pubmed",
                    "sourceId": "A",
                    "topicId": None,
                    "title": "A",
                    "text": "A 2",
                    "metadata": {},
                },
                {
                    "score": 0.7,
                    "denseScore": 0.7,
                    "sparseScore": 0.0,
                    "chunkId": "chunk-b1",
                    "sourceType": "pubmed",
                    "sourceId": "B",
                    "topicId": None,
                    "title": "B",
                    "text": "B",
                    "metadata": {},
                },
            ],
            vector_store="local_hybrid_fallback",
            embedding_model="hash-embedding-v1",
            evidence_by_id={},
        )
        self.assertEqual(payload["retrievalCandidateCount"], 2)
        self.assertEqual(payload["semanticCandidateOnlyCount"], 2)

    def test_append_evidence_studies_updates_without_duplication(self):
        unique_id = f"PMID-TEST-APPEND-{uuid4()}"
        baseline = corpus_store.get_import_summary()["activeEvidenceStudies"]
        payload = {
            "evidenceId": unique_id,
            "title": "Append test study",
            "abstract": "Append test abstract",
            "journalTitle": "Test Journal",
            "publicationYear": 2026,
            "evidenceType": "phase3_rct",
            "relevantN": 42,
            "sourceCategory": "specialty_journal",
            "populationTags": {
                "disease": "NSCLC",
                "diseaseSetting": "metastatic",
                "histology": "adenocarcinoma",
                "lineOfTherapy": "first_line",
                "biomarkers": {
                    "EGFR": "no",
                    "ALK": "no",
                    "ROS1": "no",
                    "PDL1Bucket": "ge50",
                    "BRAF": "no",
                    "RET": "no",
                    "MET": "no",
                    "KRAS": "no",
                    "NTRK": "no",
                    "HER2": "no",
                    "EGFRExon20ins": "no",
                },
            },
            "interventionTags": ["pembrolizumab", "ici"],
            "outcomeTags": ["os", "pfs"],
        }
        first = corpus_store.append_evidence_studies(batch_id=f"test-batch-{uuid4()}", evidence_records=[payload])
        after_first = corpus_store.get_import_summary()["activeEvidenceStudies"]
        self.assertEqual(first["addedCount"], 1)
        self.assertEqual(first["updatedCount"], 0)
        self.assertEqual(after_first, baseline + 1)

        updated_payload = {**payload, "title": "Append test study updated"}
        second = corpus_store.append_evidence_studies(batch_id=f"test-batch-{uuid4()}", evidence_records=[updated_payload])
        after_second = corpus_store.get_import_summary()["activeEvidenceStudies"]
        self.assertEqual(second["addedCount"], 0)
        self.assertEqual(second["updatedCount"], 1)
        self.assertEqual(after_second, after_first)

        stored = next(item for item in corpus_store.get_evidence_studies() if item["evidenceId"] == unique_id)
        self.assertEqual(stored["title"], "Append test study updated")
        with SessionLocal() as session:
            session.query(EvidenceStudyRecord).where(EvidenceStudyRecord.evidence_id == unique_id).delete()
            session.commit()

    def test_demo_pubmed_delta_path_is_blocked_for_replace_mode(self):
        baseline = corpus_store.get_import_summary()["activeEvidenceStudies"]
        result = import_pipeline_service.import_dataset(
            dataset_kind="pubmed",
            path="datasets/pubmed/demo/pubmed-live-delta-10.csv",
            mode="replace",
        )
        after = corpus_store.get_import_summary()["activeEvidenceStudies"]
        self.assertEqual(result["status"], "unsafe_mode_blocked")
        self.assertEqual(after, baseline)
        self.assertIn("append-only", " ".join(result["notes"]).lower())

    def test_semantic_upsert_dataset_replaces_only_target_documents(self):
        unique_id = str(uuid4())
        document_id = f"semantic-test-doc-{unique_id}"
        chunk_id = f"semantic-test-chunk-{unique_id}"
        point_id = f"semantic-test-point-{unique_id}"
        first_job_id = f"semantic-job-{uuid4()}"
        second_job_id = f"semantic-job-{uuid4()}"
        baseline = semantic_store.get_dataset_status(dataset_kind="pubmed")

        first = semantic_store.upsert_dataset(
            dataset_kind="pubmed",
            import_batch_id=f"semantic-batch-{uuid4()}",
            documents=[
                {
                    "documentId": document_id,
                    "sourceId": f"PMID-SEMANTIC-{unique_id}",
                    "title": "Semantic append title",
                    "sourceUrl": None,
                    "rawText": "Semantic append raw text",
                    "histologyOriginal": "adenocarcinoma",
                    "histologyNormalized": "adenocarcinoma",
                    "histologySource": "test",
                    "metadata": {"datasetKind": "pubmed", "sourceType": "pubmed"},
                }
            ],
            chunks=[
                {
                    "chunkId": chunk_id,
                    "documentId": document_id,
                    "sourceType": "pubmed",
                    "sourceId": f"PMID-SEMANTIC-{unique_id}",
                    "topicId": None,
                    "title": "Semantic append title",
                    "text": "Semantic append raw text",
                    "denseVector": [0.1, 0.2],
                    "sparseVector": {"semantic": 1.0},
                    "metadata": {"datasetKind": "pubmed", "sourceType": "pubmed"},
                }
            ],
            projection_points=[
                {
                    "pointId": point_id,
                    "chunkId": chunk_id,
                    "documentId": document_id,
                    "sourceType": "pubmed",
                    "sourceId": f"PMID-SEMANTIC-{unique_id}",
                    "topicId": None,
                    "title": "Semantic append title",
                    "histology": "adenocarcinoma",
                    "x": 0.1,
                    "y": 0.2,
                    "label": "Semantic append title",
                    "metadata": {"datasetKind": "pubmed", "sourceType": "pubmed"},
                }
            ],
            job={
                "jobId": first_job_id,
                "status": "completed",
                "vectorStore": "local_hybrid_fallback",
                "retrievalMode": "hybrid",
                "embeddingModel": "hash-embedding-v1",
                "chunkingStrategyVersion": "semantic-chunking-v1",
                "documentCount": 1,
                "chunkCount": 1,
                "notes": ["test insert"],
            },
        )
        self.assertEqual(first["documentCount"], baseline["documentCount"] + 1)
        self.assertEqual(first["chunkCount"], baseline["chunkCount"] + 1)

        second = semantic_store.upsert_dataset(
            dataset_kind="pubmed",
            import_batch_id=f"semantic-batch-{uuid4()}",
            documents=[
                {
                    "documentId": document_id,
                    "sourceId": f"PMID-SEMANTIC-{unique_id}",
                    "title": "Semantic append title updated",
                    "sourceUrl": None,
                    "rawText": "Semantic append raw text updated",
                    "histologyOriginal": "adenocarcinoma",
                    "histologyNormalized": "adenocarcinoma",
                    "histologySource": "test",
                    "metadata": {"datasetKind": "pubmed", "sourceType": "pubmed"},
                }
            ],
            chunks=[
                {
                    "chunkId": chunk_id,
                    "documentId": document_id,
                    "sourceType": "pubmed",
                    "sourceId": f"PMID-SEMANTIC-{unique_id}",
                    "topicId": None,
                    "title": "Semantic append title updated",
                    "text": "Semantic append raw text updated",
                    "denseVector": [0.3, 0.4],
                    "sparseVector": {"semantic": 0.5},
                    "metadata": {"datasetKind": "pubmed", "sourceType": "pubmed"},
                }
            ],
            projection_points=[
                {
                    "pointId": point_id,
                    "chunkId": chunk_id,
                    "documentId": document_id,
                    "sourceType": "pubmed",
                    "sourceId": f"PMID-SEMANTIC-{unique_id}",
                    "topicId": None,
                    "title": "Semantic append title updated",
                    "histology": "adenocarcinoma",
                    "x": 0.3,
                    "y": 0.4,
                    "label": "Semantic append title updated",
                    "metadata": {"datasetKind": "pubmed", "sourceType": "pubmed"},
                }
            ],
            job={
                "jobId": second_job_id,
                "status": "completed",
                "vectorStore": "local_hybrid_fallback",
                "retrievalMode": "hybrid",
                "embeddingModel": "hash-embedding-v1",
                "chunkingStrategyVersion": "semantic-chunking-v1",
                "documentCount": 1,
                "chunkCount": 1,
                "notes": ["test update"],
            },
        )
        self.assertEqual(second["documentCount"], first["documentCount"])
        self.assertEqual(second["chunkCount"], first["chunkCount"])
        with SessionLocal() as session:
            session.query(ProjectionPointRecord).where(ProjectionPointRecord.point_id == point_id).delete()
            session.query(DocumentChunkRecord).where(DocumentChunkRecord.chunk_id == chunk_id).delete()
            session.query(SourceDocumentRecord).where(SourceDocumentRecord.document_id == document_id).delete()
            session.query(EmbeddingJobRecord).where(EmbeddingJobRecord.job_id.in_([first_job_id, second_job_id])).delete()
            session.commit()

    def test_engine_benchmark_breakdown_reports_unique_union_and_overlap(self):
        def make_response(*, engine: str, aligned_ids: list[str], guideline_silent_ids: list[str], manual_ids: list[str]):
            top_evidence = [
                SimpleNamespace(evidenceId=evidence_id, mappingLabel="aligned", mappedTopicTitle="topic")
                for evidence_id in aligned_ids
            ] + [
                SimpleNamespace(evidenceId=evidence_id, mappingLabel="guideline_silent", mappedTopicTitle="topic")
                for evidence_id in guideline_silent_ids
            ]
            manual_review = [
                SimpleNamespace(evidenceId=evidence_id, mappingLabel="guideline_silent", mappedTopicTitle="topic")
                for evidence_id in manual_ids
            ]
            return SimpleNamespace(
                engine=engine,
                retrievalMode="hybrid",
                topEvidence=top_evidence,
                manualReviewEvidence=manual_review,
                secondaryReferences=[],
                uncertaintyFlags=[],
            )

        pack = {
            "packId": "demo-pack",
            "packLabel": "Demo pack",
            "cases": [
                {"caseId": "case-1", "caseLabel": "Case 1", "detail": "alpha", "vignette": {}},
                {"caseId": "case-2", "caseLabel": "Case 2", "detail": "beta", "vignette": {}},
            ],
        }
        runs = iter(
            [
                (
                    make_response(engine="deterministic", aligned_ids=["A"], guideline_silent_ids=[], manual_ids=[]),
                    {
                        "retrievalCandidateCount": 0,
                        "semanticCandidateOnlyCount": 0,
                        "retrievalCandidateEvidenceIds": [],
                        "semanticCandidateOnlyEvidenceIds": [],
                    },
                    None,
                ),
                (
                    make_response(engine="deterministic", aligned_ids=["B"], guideline_silent_ids=["GS-1"], manual_ids=[]),
                    {
                        "retrievalCandidateCount": 0,
                        "semanticCandidateOnlyCount": 0,
                        "retrievalCandidateEvidenceIds": [],
                        "semanticCandidateOnlyEvidenceIds": [],
                    },
                    None,
                ),
                (
                    make_response(
                        engine="semantic_retrieval_lab",
                        aligned_ids=["A", "C"],
                        guideline_silent_ids=[],
                        manual_ids=["MR-1"],
                    ),
                    {
                        "retrievalCandidateCount": 3,
                        "semanticCandidateOnlyCount": 2,
                        "retrievalCandidateEvidenceIds": ["R1", "R2", "R3"],
                        "semanticCandidateOnlyEvidenceIds": ["R2", "R3"],
                    },
                    None,
                ),
                (
                    make_response(
                        engine="semantic_retrieval_lab",
                        aligned_ids=["B", "D"],
                        guideline_silent_ids=["GS-1", "GS-2"],
                        manual_ids=["MR-2"],
                    ),
                    {
                        "retrievalCandidateCount": 2,
                        "semanticCandidateOnlyCount": 1,
                        "retrievalCandidateEvidenceIds": ["R3", "R4"],
                        "semanticCandidateOnlyEvidenceIds": ["R4"],
                    },
                    None,
                ),
            ]
        )

        with (
            patch.object(evaluation_service, "_benchmark_cache_context", return_value={
                "cacheId": "benchmark-cache-test",
                "pubmedBatchId": "pubmed-batch",
                "esmoBatchId": "esmo-batch",
                "pubmedSemanticJobId": "pubmed-semantic-job",
                "esmoSemanticJobId": "esmo-semantic-job",
            }),
            patch.object(evaluation_service, "_load_pack", return_value=pack),
            patch.object(evaluation_service, "_run_engine", side_effect=lambda **_kwargs: next(runs)),
            patch("app.services.evaluation_service.run_store.get_benchmark_cache", return_value=None),
            patch("app.services.evaluation_service.run_store.save_benchmark_cache"),
        ):
            result = evaluation_service.run_engine_comparison(
                pack_id="demo_presets",
                retrieval_mode="hybrid",
                force_refresh=True,
            )

        hybrid = next(engine for engine in result["engines"] if engine["engineKey"] == "hybrid_semantic")
        self.assertEqual(hybrid["aggregate"]["totalRetrievalCandidates"], 4)
        self.assertEqual(hybrid["aggregate"]["totalRetrievalCaseHits"], 5)
        self.assertEqual(hybrid["aggregate"]["retrievalOverlapCount"], 1)
        self.assertEqual(hybrid["aggregate"]["retrievalMultiCaseEvidenceCount"], 1)
        self.assertEqual(result["breakdown"]["retrieval"]["hybridUniqueEvidenceCount"], 4)
        self.assertEqual(result["breakdown"]["retrieval"]["hybridOverlapCount"], 1)
        self.assertEqual(result["breakdown"]["decisionLayer"]["promotedAlignedUniqueCount"], 2)
        self.assertEqual(result["breakdown"]["decisionLayer"]["promotedManualReviewUniqueCount"], 2)
        case_two = next(item for item in result["breakdown"]["caseDeltas"] if item["caseId"] == "case-2")
        self.assertEqual(case_two["retrievalDelta"], 2)
        self.assertEqual(case_two["promotedAlignedCount"], 1)
        self.assertEqual(case_two["promotedGuidelineSilentCount"], 1)
        self.assertEqual(case_two["promotedManualReviewCount"], 1)


if __name__ == "__main__":
    unittest.main()
