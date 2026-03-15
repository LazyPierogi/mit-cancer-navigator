import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SQLALCHEMY_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from app.api.routes.runs import create_run, get_evidence_explainability, get_uncertainty_flags_explainability
    from app.domain.contracts import (
        EvidenceExplainability,
        EvidenceExplainabilitySourceAnchor,
        EvidenceExplainabilityStudySummary,
        UncertaintyFlagsExplainability,
    )
    from app.repositories.corpus_store import corpus_store
    from app.repositories.bootstrap import bootstrap_database
    from app.repositories.run_store import run_store
    from app.services.import_pipeline import import_pipeline_service
    from app.services.llm_explainability_service import llm_explainability_service
    from app.services.sample_data import (
        _load_runtime_evidence_payload_cached,
        _load_runtime_topics_payload_cached,
        _load_sample_evidence_by_id_cached,
        _load_sample_evidence_cached,
        _load_sample_topics_cached,
    )
    from app.schemas.contracts import VignetteInputModel


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "SQLAlchemy is not installed in this environment.")
class RunsExplainabilityRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bootstrap_database()
        cls._restore_canonical_runtime_corpus()

    @classmethod
    def _restore_canonical_runtime_corpus(cls):
        esmo_batch_id = f"test-esmo-canonical-{uuid4()}"
        pubmed_batch_id = f"test-pubmed-canonical-{uuid4()}"
        topics_source = "datasets/esmo/v.5"
        evidence_source = "datasets/pubmed/v.5/pubmed-NSCLC-set_2090_results_10_years_extracted.csv"
        topics = import_pipeline_service.load_normalized_records_from_source(
            dataset_kind="esmo",
            source_path=topics_source,
        )
        evidence = import_pipeline_service.load_normalized_records_from_source(
            dataset_kind="pubmed",
            source_path=evidence_source,
        )

        corpus_store.replace_guideline_topics(batch_id=esmo_batch_id, topics=topics)
        corpus_store.replace_evidence_studies(batch_id=pubmed_batch_id, evidence_records=evidence)
        corpus_store.save_import_batch(
            batch_id=esmo_batch_id,
            dataset_kind="esmo",
            dataset_shape="canonical",
            source_path=topics_source,
            status="completed",
            record_count=len(topics),
            imported_count=len(topics),
            error_count=0,
            warning_count=0,
            validation_payload={},
            notes=["Test reset to canonical ESMO corpus."],
        )
        corpus_store.save_import_batch(
            batch_id=pubmed_batch_id,
            dataset_kind="pubmed",
            dataset_shape="canonical",
            source_path=evidence_source,
            status="completed",
            record_count=len(evidence),
            imported_count=len(evidence),
            error_count=0,
            warning_count=0,
            validation_payload={},
            notes=["Test reset to canonical PubMed corpus."],
        )

        _load_runtime_topics_payload_cached.cache_clear()
        _load_runtime_evidence_payload_cached.cache_clear()
        _load_sample_topics_cached.cache_clear()
        _load_sample_evidence_cached.cache_clear()
        _load_sample_evidence_by_id_cached.cache_clear()

    def _payload(self) -> VignetteInputModel:
        return VignetteInputModel(
            cancerType="NSCLC",
            diseaseSetting="metastatic",
            diseaseStage="stage_iv",
            histology="adenocarcinoma",
            lineOfTherapy="first_line",
            performanceStatus="1",
            resectabilityStatus="not_applicable",
            treatmentContext="treatment_naive",
            clinicalModifiers={"brainMetastases": "no"},
            biomarkers={
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
        )

    @staticmethod
    def _mock_explainability(evidence_id: str) -> EvidenceExplainability:
        return EvidenceExplainability(
            evidenceId=evidence_id,
            scoreRationale="ERS stayed high because the study is strong and recent.",
            studySummary=EvidenceExplainabilityStudySummary(
                objective="Test objective",
                signal="Test signal",
                takeaway="Test takeaway",
            ),
            sourceAnchors=[
                EvidenceExplainabilitySourceAnchor(
                    sourceId=evidence_id,
                    title="Test source",
                    snippet="Grounded snippet",
                    year=2024,
                )
            ],
            grounded=True,
            providerStatus="grounded_local",
            promptVersion="local-evidence-v1",
            validationStatus="not_attempted",
            sourceIds=[evidence_id],
        )

    @staticmethod
    def _mock_uncertainty_flags_explainability() -> UncertaintyFlagsExplainability:
        return UncertaintyFlagsExplainability(
            summary="Flags mark ambiguity in the run.",
            whyFlagsExist="They surface incomplete structured fit before operators overread the output.",
            whatItMeans="Treat the flagged evidence as usable but not frictionless.",
            flags=["unspecified_biomarker_applicability:PMID-10002"],
            grounded=True,
            providerStatus="grounded_local",
            promptVersion="local-uncertainty-flags-v1",
            validationStatus="not_attempted",
        )

    def test_top_five_evidence_returns_explainability_payload(self):
        run = create_run(self._payload())
        evidence_id = run["topEvidence"][0]["evidenceId"]

        with patch.object(
            llm_explainability_service,
            "summarize_evidence_item",
            return_value=self._mock_explainability(evidence_id),
        ):
            payload = get_evidence_explainability(run["run"]["id"], evidence_id)

        self.assertEqual(payload["evidenceId"], evidence_id)
        self.assertEqual(payload["studySummary"]["objective"], "Test objective")

    def test_non_top_five_evidence_returns_400(self):
        run = create_run(self._payload())
        sixth_item = run["topEvidence"][5]

        with self.assertRaises(HTTPException) as context:
            get_evidence_explainability(run["run"]["id"], sixth_item["evidenceId"])

        self.assertEqual(context.exception.status_code, 400)

    def test_manual_review_evidence_returns_400(self):
        run = create_run(self._payload())
        manual_item = run["manualReviewEvidence"][0]

        with self.assertRaises(HTTPException) as context:
            get_evidence_explainability(run["run"]["id"], manual_item["evidenceId"])

        self.assertEqual(context.exception.status_code, 400)

    def test_unknown_evidence_returns_404(self):
        run = create_run(self._payload())

        with self.assertRaises(HTTPException) as context:
            get_evidence_explainability(run["run"]["id"], "PMID-DOES-NOT-EXIST")

        self.assertEqual(context.exception.status_code, 404)

    def test_second_request_uses_cached_explainability(self):
        run = create_run(self._payload())
        evidence_id = run["topEvidence"][0]["evidenceId"]

        with patch.object(
            llm_explainability_service,
            "summarize_evidence_item",
            return_value=self._mock_explainability(evidence_id),
        ) as mocked:
            first = get_evidence_explainability(run["run"]["id"], evidence_id)
            second = get_evidence_explainability(run["run"]["id"], evidence_id)

        self.assertEqual(first["evidenceId"], evidence_id)
        self.assertEqual(second["evidenceId"], evidence_id)
        self.assertEqual(mocked.call_count, 1)

    def test_uncertainty_flags_route_returns_payload(self):
        run = create_run(self._payload())

        with patch.object(
            llm_explainability_service,
            "summarize_uncertainty_flags",
            return_value=self._mock_uncertainty_flags_explainability(),
        ):
            payload = get_uncertainty_flags_explainability(run["run"]["id"])

        self.assertEqual(payload["summary"], "Flags mark ambiguity in the run.")
        self.assertEqual(payload["flags"], ["unspecified_biomarker_applicability:PMID-10002"])

    def test_uncertainty_flags_route_uses_cached_payload(self):
        run = create_run(self._payload())

        with patch.object(
            llm_explainability_service,
            "summarize_uncertainty_flags",
            return_value=self._mock_uncertainty_flags_explainability(),
        ) as mocked:
            first = get_uncertainty_flags_explainability(run["run"]["id"])
            second = get_uncertainty_flags_explainability(run["run"]["id"])

        self.assertEqual(first["summary"], "Flags mark ambiguity in the run.")
        self.assertEqual(second["summary"], "Flags mark ambiguity in the run.")
        self.assertEqual(mocked.call_count, 1)

    def test_uncertainty_flags_route_limits_llm_payload_to_first_ten_flags(self):
        run = create_run(self._payload())
        record = run_store.get_analysis_run(run["run"]["id"])
        self.assertIsNotNone(record)
        assert record is not None

        mocked_record = dict(record)
        mocked_response = dict(mocked_record["response"])
        mocked_response["uncertaintyFlags"] = [f"flag_{index}:PMID-{index}" for index in range(12)]
        mocked_record["response"] = mocked_response
        mocked_record.pop("uncertaintyFlagsExplainability", None)

        with (
            patch.object(run_store, "get_analysis_run", return_value=mocked_record),
            patch.object(
                llm_explainability_service,
                "summarize_uncertainty_flags",
                return_value=self._mock_uncertainty_flags_explainability(),
            ) as mocked,
        ):
            get_uncertainty_flags_explainability(run["run"]["id"])

        forwarded_flags = mocked.call_args.kwargs["uncertainty_flags"]
        self.assertEqual(len(forwarded_flags), 10)
        self.assertEqual(forwarded_flags[0], "flag_0:PMID-0")
        self.assertEqual(forwarded_flags[-1], "flag_9:PMID-9")

    def test_create_run_returns_payload_even_when_persistence_fails(self):
        with patch.object(run_store, "save_analysis_run", side_effect=RuntimeError("db write failed")):
            run = create_run(self._payload())

        self.assertEqual(run["run"]["status"], "completed")
        self.assertGreater(len(run["topEvidence"]), 0)


if __name__ == "__main__":
    unittest.main()
