from __future__ import annotations


class GovernanceService:
    def policy(self) -> dict:
        return {
            "scope": "NSCLC treatment evidence only",
            "frozenLabelVocabulary": ["aligned", "guideline_silent", "conflict"],
            "hardStops": [
                "recommendation language",
                "approval or allowance claims",
                "increased misclassification beyond threshold",
                "removed uncertainty disclosures",
            ],
            "softReviewTriggers": [
                "relevance shifts",
                "mapping shifts",
                "new evidence without prior context loss",
            ],
            "safetyBoundaries": [
                "not diagnosis",
                "not prescribing",
                "not replacing clinician judgment",
                "not exhaustive evidence coverage",
                "no inference beyond provided inputs",
            ],
        }


governance_service = GovernanceService()

