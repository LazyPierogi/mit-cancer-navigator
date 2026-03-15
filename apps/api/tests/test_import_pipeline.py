import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.import_pipeline import ImportPipelineService


class ImportPipelineServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ImportPipelineService()

    def test_normalize_esmo_v2_record_infers_consolidation_context(self):
        record = self.service._normalize_esmo_v2_record(
            {
                "topicId": "NSCLC_UNRESECTABLE_05",
                "topicTitle": "Consolidation durvalumab after concurrent CRT for EGFR wild-type and PD-L1 >=1% unresectable stage III NSCLC",
                "diseaseSetting": "locally_advanced",
                "histology": "all_nsclc",
                "lineOfTherapy": "first_line",
                "guidelineStance": "recommend",
                "topicInterventionTags": ["durvalumab", "consolidation"],
                "biomarkerRequirements": {"PDL1Bucket": ["1to49", "ge50"]},
                "biomarkerLogic": {"anyPositive": [], "allNegative": ["EGFR"], "notes": ""},
                "semanticNormalization": {"ontologyTags": {"layer1": [], "layer2": [], "layer3": []}},
                "sourceExcerptShort": "Durvalumab consolidation is recommended after concurrent CRT in EGFR wild-type stage III NSCLC without progression.",
                "applicabilityNotes": "Use after chemoradiation in unresectable stage III disease.",
            }
        )

        applicability = record["topicApplicability"]
        self.assertEqual(applicability["lineOfTherapy"], ["consolidation"])
        self.assertEqual(applicability["diseaseStage"], ["stage_iii"])
        self.assertEqual(applicability["resectabilityStatus"], ["unresectable"])
        self.assertEqual(applicability["treatmentContext"], ["post_chemoradiation"])

    def test_normalize_esmo_v2_record_infers_adjuvant_context_and_early_alias(self):
        record = self.service._normalize_esmo_v2_record(
            {
                "topicId": "NSCLC_RESECTABLE_10",
                "topicTitle": "Adjuvant osimertinib for completely resected EGFR-mutated stage II-IIIA NSCLC",
                "diseaseSetting": "locally_advanced",
                "histology": "all_nsclc",
                "lineOfTherapy": "first_line",
                "guidelineStance": "recommend",
                "topicInterventionTags": ["targeted", "egfr-tki", "osimertinib", "adjuvant"],
                "biomarkerRequirements": {"PDL1Bucket": ["unspecified"]},
                "biomarkerLogic": {"anyPositive": ["EGFR"], "allNegative": [], "notes": ""},
                "semanticNormalization": {"ontologyTags": {"layer1": [], "layer2": [], "layer3": []}},
                "sourceExcerptShort": "Adjuvant osimertinib for 3 years is recommended for completely resected EGFR-mutated stage IB-IIIA NSCLC.",
                "applicabilityNotes": "For stage II-III disease, use after surgery and chemotherapy as appropriate.",
            }
        )

        applicability = record["topicApplicability"]
        self.assertEqual(applicability["diseaseSetting"], ["early", "locally_advanced"])
        self.assertEqual(applicability["lineOfTherapy"], ["adjuvant"])
        self.assertEqual(applicability["diseaseStage"], ["stage_ii", "stage_iii"])
        self.assertEqual(applicability["resectabilityStatus"], ["resected"])
        self.assertEqual(applicability["treatmentContext"], ["post_surgery"])

    def test_normalize_pubmed_v2_row_infers_consolidation_context_from_title(self):
        record = self.service._normalize_pubmed_v2_row(
            {
                "pmid": "28885881",
                "title": "Durvalumab after Chemoradiotherapy in Stage III Non-Small-Cell Lung Cancer.",
                "abstract": "Patients received durvalumab after chemoradiotherapy without progression.",
                "publicationYear": "2017",
                "publicationType": "Randomized Control Trial",
                "journalTitle": "NEJM",
                "evidenceType": "phase3_rct",
                "diseaseSetting": "unspecified",
                "histology": "unspecified",
                "lineOfTherapy": "unspecified",
                "diseaseStage": "",
                "resectabilityStatus": "",
                "treatmentContext": "",
                "biomarkers": "EGFR=unspecified,ALK=unspecified,ROS1=unspecified,PDL1Bucket=any",
                "interventionTags": '[\"chemotherapy\", \"consolidation\", \"therapy\"]',
                "outcomeTags": '[\"OS\", \"PFS\"]',
                "relevantN": "709",
            }
        )

        population = record["populationTags"]
        self.assertEqual(population["diseaseSetting"], "locally_advanced")
        self.assertEqual(population["lineOfTherapy"], "consolidation")
        self.assertEqual(population["diseaseStage"], "stage_iii")
        self.assertEqual(population["treatmentContext"], "post_chemoradiation")

    def test_resolve_source_path_uses_repo_root_for_relative_paths(self):
        resolved = self.service._resolve_source_path(
            dataset_kind="pubmed",
            path="datasets/pubmed/v.5/pubmed-NSCLC-set_2090_results_10_years_extracted.csv",
        )

        self.assertTrue(str(resolved).endswith("datasets/pubmed/v.5/pubmed-NSCLC-set_2090_results_10_years_extracted.csv"))

    def test_resolve_saved_source_path_maps_var_task_dataset_to_local_repo(self):
        resolved = self.service.resolve_saved_source_path(
            dataset_kind="pubmed",
            source_path="/var/task/datasets/pubmed/v.5/pubmed-NSCLC-set_2090_results_10_years_extracted.csv",
        )

        self.assertTrue(resolved.exists())
        self.assertTrue(str(resolved).endswith("datasets/pubmed/v.5/pubmed-NSCLC-set_2090_results_10_years_extracted.csv"))

    def test_load_normalized_records_from_saved_pubmed_source_returns_full_runtime_corpus(self):
        records = self.service.load_normalized_records_from_source(
            dataset_kind="pubmed",
            source_path="/var/task/datasets/pubmed/v.5/pubmed-NSCLC-set_2090_results_10_years_extracted.csv",
        )

        self.assertEqual(len(records), 2090)
        self.assertIn("populationTags", records[0])

    def test_ingest_esmo_replace_uses_replace_store(self):
        with patch("app.services.import_pipeline.corpus_store.replace_guideline_topics", return_value=2) as replace_mock, patch(
            "app.services.import_pipeline.corpus_store.merge_guideline_topics"
        ) as merge_mock:
            result = self.service._ingest(dataset_kind="esmo", batch_id="batch-esmo-replace", records=[{"topicId": "T1"}, {"topicId": "T2"}], mode="replace")

        replace_mock.assert_called_once()
        merge_mock.assert_not_called()
        self.assertEqual(result, {"processedCount": 2, "addedCount": 2, "updatedCount": 0})

    def test_ingest_esmo_append_uses_merge_store(self):
        with patch("app.services.import_pipeline.corpus_store.replace_guideline_topics") as replace_mock, patch(
            "app.services.import_pipeline.corpus_store.merge_guideline_topics",
            return_value={"processedCount": 2, "addedCount": 1, "updatedCount": 1},
        ) as merge_mock:
            result = self.service._ingest(dataset_kind="esmo", batch_id="batch-esmo-append", records=[{"topicId": "T1"}, {"topicId": "T2"}], mode="append")

        replace_mock.assert_not_called()
        merge_mock.assert_called_once()
        self.assertEqual(result, {"processedCount": 2, "addedCount": 1, "updatedCount": 1})


if __name__ == "__main__":
    unittest.main()
