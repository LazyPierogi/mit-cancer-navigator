import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACK_PATH = ROOT / "datasets" / "vignettes" / "frozen_pack.curated.json"


class FrozenBenchmarkPackTest(unittest.TestCase):
    def test_canonical_pack_matches_expected_distribution(self):
        payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
        cases = payload["cases"]

        self.assertEqual(payload["packId"], "frozen-pack-canonical-v2")
        self.assertEqual(len(cases), 15)

        categories: dict[str, int] = {}
        labels: dict[str, int] = {}
        quantitative_goldens = 0

        for case in cases:
            categories[case["category"]] = categories.get(case["category"], 0) + 1
            reference = case.get("reference") or {}
            label = reference.get("expectedPrimaryLabel")
            if label:
                labels[label] = labels.get(label, 0) + 1
            if label and reference.get("expectedTopEvidence"):
                quantitative_goldens += 1
            self.assertTrue(case["caseLabel"])
            self.assertTrue(case["detail"])
            self.assertTrue(case["clinicalQuestion"])
            self.assertGreaterEqual(len(reference.get("expectedTopEvidence", [])), 1)
            self.assertGreaterEqual(len(reference.get("expectedLabelByEvidenceId", {})), 1)

        self.assertEqual(
            categories,
            {
                "targeted": 5,
                "immunotherapy": 4,
                "progression_second_line": 3,
                "early_consolidation_adjuvant": 2,
                "edge_case": 1,
            },
        )
        self.assertEqual(
            labels,
            {
                "aligned": 11,
                "guideline_silent": 2,
                "conflict": 2,
            },
        )
        self.assertEqual(quantitative_goldens, 15)


if __name__ == "__main__":
    unittest.main()
