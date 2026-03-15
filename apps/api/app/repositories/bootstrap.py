from __future__ import annotations

from threading import Lock

from sqlalchemy import inspect, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import settings
from app.repositories.db import Base, SessionLocal, engine
from app.repositories.models import PolicySnapshotModel, RulesetModel, SafetyTemplateModel

_BOOTSTRAP_LOCK = Lock()
_BOOTSTRAP_COMPLETE = False
_POSTGRES_REQUIRED_TABLES = {
    "rulesets",
    "safety_templates",
    "policy_snapshots",
    "guideline_topics",
    "evidence_studies",
    "source_documents",
    "document_chunks",
    "projection_points",
    "import_batches",
    "analysis_runs",
    "eval_runs",
    "embedding_jobs",
}
_POSTGRES_REQUIRED_COLUMNS = {
    "guideline_topics": {"import_batch_id", "topic_title", "prerequisites"},
    "evidence_studies": {"import_batch_id", "title"},
    "source_documents": {"source_title"},
    "document_chunks": {"title"},
    "projection_points": {"title", "label"},
}


def _ensure_runtime_schema_extensions() -> None:
    with engine.begin() as connection:
        if connection.dialect.name != "sqlite":
            for statement in (
                "ALTER TABLE guideline_topics ALTER COLUMN topic_title TYPE TEXT",
                "ALTER TABLE evidence_studies ALTER COLUMN title TYPE TEXT",
                "ALTER TABLE source_documents ALTER COLUMN source_title TYPE TEXT",
                "ALTER TABLE document_chunks ALTER COLUMN title TYPE TEXT",
                "ALTER TABLE projection_points ALTER COLUMN title TYPE TEXT",
                "ALTER TABLE projection_points ALTER COLUMN label TYPE TEXT",
            ):
                try:
                    with connection.begin_nested():
                        connection.execute(text(statement))
                except SQLAlchemyError:
                    pass
            return

        inspector = inspect(connection)

        guideline_columns = {column["name"] for column in inspector.get_columns("guideline_topics")}
        if "import_batch_id" not in guideline_columns:
            try:
                connection.execute(text("ALTER TABLE guideline_topics ADD COLUMN import_batch_id VARCHAR(128)"))
            except SQLAlchemyError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        if "prerequisites" not in guideline_columns:
            try:
                connection.execute(text("ALTER TABLE guideline_topics ADD COLUMN prerequisites JSON NOT NULL DEFAULT '[]'"))
            except SQLAlchemyError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_guideline_topics_import_batch_id ON guideline_topics (import_batch_id)"))

        evidence_columns = {column["name"] for column in inspector.get_columns("evidence_studies")}
        if "import_batch_id" not in evidence_columns:
            try:
                connection.execute(text("ALTER TABLE evidence_studies ADD COLUMN import_batch_id VARCHAR(128)"))
            except SQLAlchemyError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_evidence_studies_import_batch_id ON evidence_studies (import_batch_id)"))


def _postgres_runtime_schema_ready() -> bool:
    try:
        with engine.connect() as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()")
                )
            }
            if not _POSTGRES_REQUIRED_TABLES.issubset(tables):
                return False

            column_rows = connection.execute(
                text(
                    "SELECT table_name, column_name "
                    "FROM information_schema.columns "
                    "WHERE table_schema = current_schema() "
                    "AND table_name IN ('guideline_topics', 'evidence_studies', 'source_documents', 'document_chunks', 'projection_points')"
                )
            )
            columns_by_table: dict[str, set[str]] = {}
            for table_name, column_name in column_rows:
                columns_by_table.setdefault(str(table_name), set()).add(str(column_name))

            for table_name, required_columns in _POSTGRES_REQUIRED_COLUMNS.items():
                if not required_columns.issubset(columns_by_table.get(table_name, set())):
                    return False
        return True
    except SQLAlchemyError:
        return False


def bootstrap_database() -> None:
    global _BOOTSTRAP_COMPLETE
    if _BOOTSTRAP_COMPLETE:
        return

    with _BOOTSTRAP_LOCK:
        if _BOOTSTRAP_COMPLETE:
            return

        requires_schema_bootstrap = True
        if not settings.database_url.startswith("sqlite"):
            requires_schema_bootstrap = not _postgres_runtime_schema_ready()

        if requires_schema_bootstrap:
            Base.metadata.create_all(bind=engine)
            _ensure_runtime_schema_extensions()

        with SessionLocal() as session:
            ruleset = session.execute(
                select(RulesetModel).where(RulesetModel.version == settings.ruleset_version)
            ).scalar_one_or_none()
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
                                "guideline": 35,
                                "systematic_review": 35,
                                "phase3_rct": 28,
                                "phase2_rct": 20,
                                "prospective_obs": 12,
                                "retrospective": 8,
                                "case_series": 6,
                                "expert_opinion": 6,
                                "unspecified": 6,
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

            policy = session.execute(
                select(PolicySnapshotModel).where(PolicySnapshotModel.version == "policy-v1")
            ).scalar_one_or_none()
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
        _BOOTSTRAP_COMPLETE = True
