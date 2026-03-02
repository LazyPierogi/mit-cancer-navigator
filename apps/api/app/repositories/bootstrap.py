from __future__ import annotations

from sqlalchemy import inspect, select, text
from sqlalchemy.exc import OperationalError

from app.config.settings import settings
from app.repositories.db import Base, SessionLocal, engine
from app.repositories.models import PolicySnapshotModel, RulesetModel, SafetyTemplateModel


def _ensure_runtime_schema_extensions() -> None:
    inspector = inspect(engine)

    with engine.begin() as connection:
        guideline_columns = {column["name"] for column in inspector.get_columns("guideline_topics")}
        if "import_batch_id" not in guideline_columns:
            try:
                connection.execute(text("ALTER TABLE guideline_topics ADD COLUMN import_batch_id VARCHAR(128)"))
            except OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        if "prerequisites" not in guideline_columns:
            try:
                connection.execute(text("ALTER TABLE guideline_topics ADD COLUMN prerequisites JSON NOT NULL DEFAULT '[]'"))
            except OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_guideline_topics_import_batch_id ON guideline_topics (import_batch_id)"))

        evidence_columns = {column["name"] for column in inspector.get_columns("evidence_studies")}
        if "import_batch_id" not in evidence_columns:
            try:
                connection.execute(text("ALTER TABLE evidence_studies ADD COLUMN import_batch_id VARCHAR(128)"))
            except OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_evidence_studies_import_batch_id ON evidence_studies (import_batch_id)"))


def bootstrap_database() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_runtime_schema_extensions()

    with SessionLocal() as session:
        ruleset = session.execute(select(RulesetModel).where(RulesetModel.version == settings.ruleset_version)).scalar_one_or_none()
        if ruleset is None:
            session.add(
                RulesetModel(
                    version=settings.ruleset_version,
                    relevance_gate_rules={
                        "disease": "NSCLC only",
                        "setting": "exact or mixed",
                        "histology": "exact, non_squamous family, or mixed/all_nsclc",
                        "line_of_therapy": "exact or mixed or unspecified",
                        "biomarkers": "exact, unspecified, or rule-expression match",
                    },
                    ers_tables={
                        "evidenceStrength": {
                            "guideline": 20,
                            "systematic_review": 18,
                            "phase3_rct": 16,
                            "phase2_rct": 13,
                            "prospective_obs": 10,
                            "retrospective": 6,
                            "case_series": 2,
                            "expert_opinion": 2,
                        },
                        "threshold": 30,
                    },
                    mapping_rubric={
                        "topicMatch": "applicability rules + intervention tag overlap",
                        "tieBreak": "more specific biomarker rule wins",
                    },
                    label_logic={
                        "aligned": "recommend or conditional + supporting evidence",
                        "conflict": "do_not_recommend + evidence suggests benefit",
                        "guideline_silent": "not_covered or no topic match",
                    },
                )
            )

        template = session.execute(
            select(SafetyTemplateModel).where(SafetyTemplateModel.version == settings.safety_template_version)
        ).scalar_one_or_none()
        if template is None:
            session.add(
                SafetyTemplateModel(
                    version=settings.safety_template_version,
                    footer_key=settings.safety_template_version,
                    footer_copy=(
                        "This tool does not diagnose, prescribe, or replace clinician judgment. "
                        "It summarizes evidence relative to guideline topics and may be incomplete."
                    ),
                    uncertainty_copy="Missing inputs or weak topic matches are surfaced explicitly as uncertainty.",
                )
            )

        policy = session.execute(select(PolicySnapshotModel).where(PolicySnapshotModel.version == "policy-v1")).scalar_one_or_none()
        if policy is None:
            session.add(
                PolicySnapshotModel(
                    version="policy-v1",
                    safety_boundaries=[
                        "not diagnosis",
                        "not prescribing",
                        "not replacing clinician judgment",
                        "not exhaustive evidence coverage",
                        "no inference beyond provided inputs",
                    ],
                    hard_stops=[
                        "recommendation language",
                        "approval or allowance claims",
                        "increased misclassification beyond threshold",
                        "removed uncertainty disclosures",
                    ],
                    soft_review_triggers=[
                        "relevance shifts",
                        "mapping shifts",
                        "new evidence without prior context loss",
                    ],
                )
            )

        session.commit()
