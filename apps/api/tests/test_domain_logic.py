import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.contracts import Biomarkers, EvidenceRecord, GuidelineTopic, PopulationTags, TopicApplicability, VignetteInput
from app.domain.rules import analyze_records, compute_ers, relevance_gate


class DomainLogicTest(unittest.TestCase):
    def setUp(self):
        self.vignette = VignetteInput(
            cancerType="NSCLC",
            diseaseSetting="metastatic",
            histology="adenocarcinoma",
            performanceStatus="1",
            biomarkers=Biomarkers(EGFR="no", ALK="no", ROS1="no", PDL1Bucket="ge50"),
        )
        self.topic = GuidelineTopic(
            topicId="T1",
            topicTitle="PD-1 first line",
            topicApplicability=TopicApplicability(
                diseaseSetting=["metastatic"],
                histology=["adenocarcinoma"],
                biomarkerConditions=["EGFR=no", "ALK=no", "ROS1=no", "PDL1Bucket=ge50"],
            ),
            topicInterventionTags=["PD-1", "pembrolizumab"],
            guidelineStance="recommend",
        )

    def test_relevance_gate_rejects_biomarker_mismatch(self):
        evidence = EvidenceRecord(
            evidenceId="E1",
            title="EGFR study",
            publicationYear=2024,
            evidenceType="systematic_review",
            relevantN=300,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="all_nsclc",
                biomarkers={"EGFR": "yes"},
            ),
            interventionTags=["EGFR"],
            outcomeTags=["OS"],
        )
        passed, reasons = relevance_gate(self.vignette, evidence)
        self.assertFalse(passed)
        self.assertIn("biomarker_mismatch:EGFR", reasons)

    def test_ers_matches_expected_breakdown(self):
        evidence = EvidenceRecord(
            evidenceId="E2",
            title="PD-1 study",
            publicationYear=2025,
            evidenceType="phase3_rct",
            relevantN=642,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
            ),
            interventionTags=["PD-1", "pembrolizumab"],
            outcomeTags=["OS", "PFS"],
        )
        breakdown = compute_ers(evidence, 2026)
        self.assertEqual(breakdown.evidenceStrength, 16)
        self.assertEqual(breakdown.datasetRobustness, 15)
        self.assertEqual(breakdown.sourceCredibility, 12)
        self.assertEqual(breakdown.recency, 10)
        self.assertEqual(breakdown.total, 53)

    def test_analyze_records_emits_top_evidence(self):
        evidence = EvidenceRecord(
            evidenceId="E2",
            title="PD-1 study",
            publicationYear=2025,
            evidenceType="phase3_rct",
            relevantN=642,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
            ),
            interventionTags=["PD-1", "pembrolizumab"],
            outcomeTags=["OS", "PFS"],
        )
        response, trace = analyze_records(
            self.vignette,
            [evidence],
            [self.topic],
            current_year=2026,
            ruleset_version="mvp-2026-02-28",
            corpus_version="sample-v1",
            safety_footer_key="safety-v1",
        )
        self.assertEqual(len(response.topEvidence), 1)
        self.assertEqual(response.topEvidence[0].mappingLabel, "aligned")
        self.assertEqual(trace["topEvidenceCount"], 1)


if __name__ == "__main__":
    unittest.main()
