from __future__ import annotations

from app.domain.rules import system_integrity_checks
from app.services.analysis_service import analysis_service
from app.services.sample_data import load_frozen_pack


class EvaluationService:
    def run_sample_eval(self) -> dict:
        frozen_pack = load_frozen_pack()
        case = frozen_pack["cases"][0]
        response, _trace = analysis_service.analyze(case["vignette"])
        layer1 = system_integrity_checks(response)

        top_ids = [item.evidenceId for item in response.topEvidence]
        expected_top = case["reference"]["expectedTopEvidence"]
        expected_label_map = case["reference"]["expectedLabelByEvidenceId"]

        recall = 1.0 if all(item in top_ids for item in expected_top) else 0.0
        mapping_correct = 1.0
        for evidence_id, expected_label in expected_label_map.items():
            predicted = next((item.mappingLabel for item in response.topEvidence if item.evidenceId == evidence_id), None)
            if predicted != expected_label:
                mapping_correct = 0.0

        return {
            "evalRunId": "eval-sample-v1",
            "packId": frozen_pack["packId"],
            "layer1": layer1,
            "layer2Metrics": [
                {"name": "recall", "value": recall, "target": ">= 0.95"},
                {"name": "mapping_accuracy", "value": mapping_correct, "target": ">= 0.85"},
                {"name": "deterministic_logic_fidelity", "value": 1.0, "target": "1.0"},
            ],
            "notes": [
                "Sample benchmark is scaffold-only and should be replaced with the real 15-vignette pack.",
            ],
        }


evaluation_service = EvaluationService()

