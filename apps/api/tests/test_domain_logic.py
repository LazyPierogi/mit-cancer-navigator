import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.contracts import Biomarkers, ClinicalModifiers, EvidenceRecord, GuidelineTopic, PopulationTags, TopicApplicability, VignetteInput
from app.domain.rules import analyze_records, compute_ers, relevance_gate, structured_facets_count, tag_overlap, topic_applies


def make_evidence(**kwargs) -> EvidenceRecord:
    return EvidenceRecord(abstract=None, journalTitle=None, **kwargs)


class DomainLogicTest(unittest.TestCase):
    def setUp(self):
        self.vignette = VignetteInput(
            cancerType="NSCLC",
            diseaseSetting="metastatic",
            histology="adenocarcinoma",
            performanceStatus="1",
            biomarkers=Biomarkers(EGFR="no", ALK="no", ROS1="no", PDL1Bucket="ge50"),
            lineOfTherapy="first_line",
        )
        self.topic = GuidelineTopic(
            topicId="T1",
            topicTitle="PD-1 first line",
            topicApplicability=TopicApplicability(
                diseaseSetting=["metastatic"],
                histology=["adenocarcinoma"],
                biomarkerConditions=["all_negative(EGFR,ALK,ROS1)", "PDL1Bucket>=ge50"],
                lineOfTherapy=["first_line"],
            ),
            topicInterventionTags=["PD-1", "pembrolizumab"],
            guidelineStance="recommend",
        )

    def test_relevance_gate_rejects_biomarker_mismatch(self):
        evidence = make_evidence(
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
                lineOfTherapy="first_line",
            ),
            interventionTags=["EGFR"],
            outcomeTags=["OS"],
        )
        passed, reasons = relevance_gate(self.vignette, evidence)
        self.assertFalse(passed)
        self.assertIn("biomarker_mismatch:EGFR", reasons)

    def test_ers_matches_expected_breakdown(self):
        evidence = make_evidence(
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
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1", "pembrolizumab"],
            outcomeTags=["OS", "PFS"],
        )
        breakdown = compute_ers(evidence, 2026)
        self.assertEqual(breakdown.evidenceStrength, 28)
        self.assertEqual(breakdown.datasetRobustness, 25)
        self.assertEqual(breakdown.sourceCredibility, 20)
        self.assertEqual(breakdown.recency, 15)
        self.assertEqual(breakdown.total, 88)

    def test_analyze_records_emits_top_evidence(self):
        evidence = make_evidence(
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
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1", "pembrolizumab"],
            outcomeTags=["OS", "PFS"],
        )
        response, trace = analyze_records(
            self.vignette,
            [evidence],
            [self.topic],
            current_year=2026,
            input_schema_version="vignette-v2",
            ruleset_version="mvp-2026-02-28",
            corpus_version="sample-v1",
            safety_footer_key="safety-v1",
        )
        self.assertEqual(len(response.topEvidence), 1)
        self.assertEqual(response.topEvidence[0].mappingLabel, "aligned")
        self.assertEqual(trace["topEvidenceCount"], 1)

    def test_topic_applies_supports_bucket_ranges_and_any_positive(self):
        driver_positive_topic = GuidelineTopic(
            topicId="T2",
            topicTitle="Driver-positive targeted therapy",
            topicApplicability=TopicApplicability(
                diseaseSetting=["metastatic"],
                histology=["non_squamous"],
                biomarkerConditions=["any_positive(EGFR,ALK,ROS1,BRAF,RET,MET,EGFRExon20ins,KRAS,NTRK,HER2)"],
                lineOfTherapy=["first_line"],
            ),
            topicInterventionTags=["EGFR"],
            guidelineStance="recommend",
        )
        driver_positive_vignette = VignetteInput(
            cancerType="NSCLC",
            diseaseSetting="metastatic",
            histology="adenocarcinoma",
            performanceStatus="1",
            biomarkers=Biomarkers(EGFR="yes", ALK="no", ROS1="no", PDL1Bucket="1to49"),
            lineOfTherapy="first_line",
        )
        pdl1_range_topic = GuidelineTopic(
            topicId="T3",
            topicTitle="PD-L1 >=1% checkpoint option",
            topicApplicability=TopicApplicability(
                diseaseSetting=["metastatic"],
                histology=["adenocarcinoma"],
                biomarkerConditions=["PDL1Bucket>=1to49"],
                lineOfTherapy=["first_line"],
            ),
            topicInterventionTags=["PD-1"],
            guidelineStance="recommend",
        )

        self.assertTrue(topic_applies(driver_positive_vignette, driver_positive_topic))
        self.assertTrue(topic_applies(driver_positive_vignette, pdl1_range_topic))

    def test_relevance_gate_checks_line_of_therapy(self):
        evidence = make_evidence(
            evidenceId="E3",
            title="Second-line trial",
            publicationYear=2025,
            evidenceType="phase3_rct",
            relevantN=400,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="second_line",
            ),
            interventionTags=["PD-1"],
            outcomeTags=["OS"],
        )

        passed, reasons = relevance_gate(self.vignette, evidence)
        self.assertFalse(passed)
        self.assertIn("line_of_therapy_mismatch", reasons)

    def test_unspecified_evidence_type_goes_to_manual_review(self):
        evidence = make_evidence(
            evidenceId="E4",
            title="Study type unresolved",
            publicationYear=2025,
            evidenceType="unspecified",
            relevantN=120,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1", "pembrolizumab"],
            outcomeTags=["OS"],
        )

        response, trace = analyze_records(
            self.vignette,
            [evidence],
            [self.topic],
            current_year=2026,
            input_schema_version="vignette-v2",
            ruleset_version="mvp-2026-02-28",
            corpus_version="sample-v1",
            safety_footer_key="safety-v1",
        )

        self.assertEqual(len(response.topEvidence), 0)
        self.assertEqual(len(response.manualReviewEvidence), 1)
        self.assertEqual(response.manualReviewEvidence[0].classificationStatus, "manual_review_required")
        self.assertEqual(response.manualReviewEvidence[0].manualReviewReason, "evidence_type_unspecified")
        self.assertFalse(response.manualReviewEvidence[0].potentialConflict)
        self.assertEqual(trace["manualReviewCount"], 1)

    def test_unspecified_evidence_type_can_be_flagged_as_potential_conflict(self):
        conflict_topic = GuidelineTopic(
            topicId="T5",
            topicTitle="PD-1 monotherapy not advised",
            topicApplicability=TopicApplicability(
                diseaseSetting=["metastatic"],
                histology=["adenocarcinoma"],
                biomarkerConditions=["all_negative(EGFR,ALK,ROS1)", "PDL1Bucket>=ge50"],
                lineOfTherapy=["first_line"],
            ),
            topicInterventionTags=["PD-1", "pembrolizumab"],
            guidelineStance="do_not_recommend",
        )
        evidence = make_evidence(
            evidenceId="E4B",
            title="Study type unresolved with matched conservative topic",
            publicationYear=2025,
            evidenceType="unspecified",
            relevantN=120,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1", "pembrolizumab"],
            outcomeTags=["OS"],
        )

        response, _trace = analyze_records(
            self.vignette,
            [evidence],
            [conflict_topic],
            current_year=2026,
            input_schema_version="vignette-v2",
            ruleset_version="mvp-2026-02-28",
            corpus_version="sample-v1",
            safety_footer_key="safety-v1",
        )

        self.assertEqual(len(response.manualReviewEvidence), 1)
        self.assertTrue(response.manualReviewEvidence[0].potentialConflict)
        self.assertEqual(response.manualReviewEvidence[0].mappingLabel, "conflict")
        self.assertIn("possible conflict with a matched do-not-recommend guideline topic", response.manualReviewEvidence[0].applicabilityNote)

    def test_relevance_gate_allows_unspecified_setting_and_histology(self):
        evidence = make_evidence(
            evidenceId="E5",
            title="Broad NSCLC cohort",
            publicationYear=2025,
            evidenceType="systematic_review",
            relevantN=180,
            sourceCategory="specialty_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="unspecified",
                histology="unspecified",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "unspecified"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1"],
            outcomeTags=["OS"],
        )

        passed, reasons = relevance_gate(self.vignette, evidence)
        self.assertTrue(passed)
        self.assertEqual(reasons, [])

    def test_tag_overlap_normalizes_targeted_synonyms(self):
        egfr_topic = GuidelineTopic(
            topicId="T4",
            topicTitle="EGFR targeted therapy",
            topicApplicability=TopicApplicability(
                diseaseSetting=["metastatic"],
                histology=["non_squamous"],
                biomarkerConditions=["any_positive(EGFR)"],
                lineOfTherapy=["first_line"],
            ),
            topicInterventionTags=["egfr", "tki", "targeted"],
            guidelineStance="recommend",
        )
        evidence = make_evidence(
            evidenceId="E11",
            title="EGFR TKI trial",
            publicationYear=2025,
            evidenceType="phase3_rct",
            relevantN=320,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="non_squamous",
                biomarkers={"EGFR": "yes"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["egfr-tki"],
            outcomeTags=["PFS"],
        )

        self.assertGreater(tag_overlap(evidence, egfr_topic), 0)

    def test_topic_applies_blocks_ps2_topics_for_ps1_patient(self):
        ps2_topic = GuidelineTopic(
            topicId="T5",
            topicTitle="PS 2: platinum-doublet chemotherapy",
            topicApplicability=TopicApplicability(
                diseaseSetting=["metastatic"],
                histology=["all_nsclc"],
                biomarkerConditions=[],
                lineOfTherapy=["first_line"],
            ),
            topicInterventionTags=["platinum-doublet", "chemotherapy"],
            guidelineStance="recommend",
        )

        self.assertFalse(topic_applies(self.vignette, ps2_topic))

    def test_sparse_records_are_excluded_from_primary_ranking(self):
        sparse_evidence = make_evidence(
            evidenceId="E12",
            title="Barely structured cohort",
            publicationYear=2025,
            evidenceType="phase3_rct",
            relevantN=400,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="unspecified",
                histology="unspecified",
                biomarkers={"EGFR": "unspecified", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified"},
                lineOfTherapy="unspecified",
            ),
            interventionTags=["pd1"],
            outcomeTags=["OS"],
        )

        self.assertEqual(structured_facets_count(sparse_evidence), 0)

        response, trace = analyze_records(
            self.vignette,
            [sparse_evidence],
            [self.topic],
            current_year=2026,
            input_schema_version="vignette-v2",
            ruleset_version="mvp-2026-02-28",
            corpus_version="sample-v1",
            safety_footer_key="safety-v1",
        )

        self.assertEqual(len(response.topEvidence), 0)
        self.assertEqual(len(response.secondaryReferences), 1)
        self.assertIn("insufficient_structured_cohort_metadata", response.secondaryReferences[0].exclusionReasons[0])
        self.assertEqual(trace["topEvidenceCount"], 0)

    def test_structured_facets_count_includes_stage_and_treatment_context(self):
        evidence = make_evidence(
            evidenceId="E12b",
            title="Stage III consolidation cohort",
            publicationYear=2025,
            evidenceType="phase3_rct",
            relevantN=400,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="unspecified",
                diseaseStage="stage_iii",
                histology="unspecified",
                biomarkers={"EGFR": "unspecified", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified"},
                lineOfTherapy="consolidation",
                resectabilityStatus="unresectable",
                treatmentContext="post_chemoradiation",
            ),
            interventionTags=["consolidation"],
            outcomeTags=["OS"],
        )

        self.assertEqual(structured_facets_count(evidence), 4)

    def test_dataset_robustness_uses_new_bands_and_null_default(self):
        low_n = make_evidence(
            evidenceId="E6",
            title="Small cohort",
            publicationYear=2025,
            evidenceType="phase2_rct",
            relevantN=18,
            sourceCategory="specialty_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1"],
            outcomeTags=["OS"],
        )
        unknown_n = make_evidence(
            evidenceId="E7",
            title="Unknown sample size",
            publicationYear=2025,
            evidenceType="systematic_review",
            relevantN=None,
            sourceCategory=None,
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1"],
            outcomeTags=["OS"],
        )

        self.assertEqual(compute_ers(low_n, 2026).datasetRobustness, 4)
        self.assertEqual(compute_ers(unknown_n, 2026).datasetRobustness, 6)
        self.assertEqual(compute_ers(unknown_n, 2026).sourceCredibility, 6)

    def test_topic_applies_respects_stage_resectability_and_context(self):
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
        )
        topic = GuidelineTopic(
            topicId="T-stage3",
            topicTitle="Stage III consolidation",
            topicApplicability=TopicApplicability(
                diseaseSetting=["locally_advanced"],
                histology=["non_squamous"],
                biomarkerConditions=["all_negative(EGFR,ALK,ROS1)"],
                lineOfTherapy=["consolidation"],
                diseaseStage=["stage_iii"],
                resectabilityStatus=["unresectable"],
                treatmentContext=["post_chemoradiation"],
            ),
            topicInterventionTags=["durvalumab"],
            guidelineStance="recommend",
        )

        self.assertTrue(topic_applies(vignette, topic))

    def test_relevance_gate_checks_brain_metastases_context(self):
        vignette = VignetteInput(
            cancerType="NSCLC",
            diseaseSetting="metastatic",
            diseaseStage="stage_iv",
            histology="adenocarcinoma",
            performanceStatus="1",
            biomarkers=Biomarkers(EGFR="no", ALK="yes", ROS1="no", PDL1Bucket="unspecified"),
            lineOfTherapy="first_line",
            treatmentContext="treatment_naive",
            clinicalModifiers=ClinicalModifiers(brainMetastases="yes"),
        )
        evidence = make_evidence(
            evidenceId="E-stage-mismatch",
            title="ALK systemic-only study",
            publicationYear=2025,
            evidenceType="systematic_review",
            relevantN=250,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                diseaseStage="stage_iv",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "yes", "ROS1": "no", "PDL1Bucket": "unspecified"},
                lineOfTherapy="first_line",
                treatmentContext="treatment_naive",
                brainMetastases="no",
            ),
            interventionTags=["alk-targeted"],
            outcomeTags=["PFS"],
        )

        passed, reasons = relevance_gate(vignette, evidence)
        self.assertFalse(passed)
        self.assertIn("brain_metastases_mismatch", reasons)

    def test_relevance_gate_ignores_unspecified_new_facets(self):
        evidence = make_evidence(
            evidenceId="E-unspecified",
            title="Broad population study",
            publicationYear=2025,
            evidenceType="systematic_review",
            relevantN=180,
            sourceCategory="specialty_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                diseaseStage="unspecified",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="first_line",
                resectabilityStatus="unspecified",
                treatmentContext="unspecified",
                brainMetastases="unspecified",
            ),
            interventionTags=["pd1"],
            outcomeTags=["OS"],
        )

        passed, reasons = relevance_gate(self.vignette, evidence)
        self.assertTrue(passed)
        self.assertEqual(reasons, [])

    def test_recency_uses_new_three_band_scale(self):
        newest = make_evidence(
            evidenceId="E8",
            title="Fresh trial",
            publicationYear=2026,
            evidenceType="phase3_rct",
            relevantN=300,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1"],
            outcomeTags=["OS"],
        )
        mid = make_evidence(
            evidenceId="E9",
            title="Recent review",
            publicationYear=2023,
            evidenceType="systematic_review",
            relevantN=300,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1"],
            outcomeTags=["OS"],
        )
        old = make_evidence(
            evidenceId="E10",
            title="Old evidence",
            publicationYear=2018,
            evidenceType="retrospective",
            relevantN=300,
            sourceCategory="industry_whitepaper",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["PD-1"],
            outcomeTags=["OS"],
        )

        self.assertEqual(compute_ers(newest, 2026).recency, 15)
        self.assertEqual(compute_ers(mid, 2026).recency, 12)
        self.assertEqual(compute_ers(old, 2026).recency, 8)

    def test_semantic_topic_hint_can_promote_guideline_silent_to_aligned(self):
        evidence = make_evidence(
            evidenceId="E12",
            title="Checkpoint trial with weak manual tags",
            publicationYear=2025,
            evidenceType="phase3_rct",
            relevantN=280,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="adenocarcinoma",
                biomarkers={"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
                lineOfTherapy="first_line",
            ),
            interventionTags=["therapy"],
            outcomeTags=["OS"],
        )

        response, _trace = analyze_records(
            self.vignette,
            [evidence],
            [self.topic],
            current_year=2026,
            input_schema_version="vignette-v2",
            ruleset_version="mvp-2026-02-28",
            corpus_version="sample-v1",
            safety_footer_key="safety-v1",
            semantic_topic_hints={"E12": "T1"},
            semantic_evidence_scores={"E12": 0.42},
            semantic_rescue_ids={"E12"},
        )

        self.assertEqual(len(response.topEvidence), 1)
        self.assertEqual(response.topEvidence[0].mappingLabel, "aligned")
        self.assertEqual(response.topEvidence[0].mappedTopicId, "T1")

    def test_semantic_rescue_can_reinclude_sparse_record(self):
        sparse_evidence = make_evidence(
            evidenceId="E13",
            title="Sparse but relevant review",
            publicationYear=2024,
            evidenceType="systematic_review",
            relevantN=220,
            sourceCategory="high_impact_journal",
            populationTags=PopulationTags(
                disease="NSCLC",
                diseaseSetting="metastatic",
                histology="unspecified",
                biomarkers={"EGFR": "unspecified", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified"},
                lineOfTherapy="unspecified",
            ),
            interventionTags=["PD-1", "pembrolizumab"],
            outcomeTags=["OS"],
        )

        baseline_response, _ = analyze_records(
            self.vignette,
            [sparse_evidence],
            [self.topic],
            current_year=2026,
            input_schema_version="vignette-v2",
            ruleset_version="mvp-2026-02-28",
            corpus_version="sample-v1",
            safety_footer_key="safety-v1",
        )
        rescued_response, rescued_trace = analyze_records(
            self.vignette,
            [sparse_evidence],
            [self.topic],
            current_year=2026,
            input_schema_version="vignette-v2",
            ruleset_version="mvp-2026-02-28",
            corpus_version="sample-v1",
            safety_footer_key="safety-v1",
            semantic_topic_hints={"E13": "T1"},
            semantic_evidence_scores={"E13": 0.33},
            semantic_rescue_ids={"E13"},
        )

        self.assertEqual(len(baseline_response.topEvidence), 0)
        self.assertEqual(len(rescued_response.topEvidence), 1)
        self.assertIn("semantic_rescue_sparse_metadata:E13", rescued_trace["uncertaintyFlags"])


if __name__ == "__main__":
    unittest.main()
