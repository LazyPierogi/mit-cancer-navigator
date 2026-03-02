from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.repositories.db import Base


class RulesetModel(Base):
    __tablename__ = "rulesets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    relevance_gate_rules: Mapped[dict] = mapped_column(JSON)
    ers_tables: Mapped[dict] = mapped_column(JSON)
    mapping_rubric: Mapped[dict] = mapped_column(JSON)
    label_logic: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SafetyTemplateModel(Base):
    __tablename__ = "safety_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    footer_key: Mapped[str] = mapped_column(String(64))
    footer_copy: Mapped[str] = mapped_column(Text)
    uncertainty_copy: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PolicySnapshotModel(Base):
    __tablename__ = "policy_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    safety_boundaries: Mapped[list] = mapped_column(JSON)
    hard_stops: Mapped[list] = mapped_column(JSON)
    soft_review_triggers: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UpdateRecordModel(Base):
    __tablename__ = "update_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    changed_component: Mapped[str] = mapped_column(String(128))
    reason: Mapped[str] = mapped_column(Text)
    before_after_summary: Mapped[dict] = mapped_column(JSON)
    hard_stop_violations: Mapped[list] = mapped_column(JSON)
    soft_review_flags: Mapped[list] = mapped_column(JSON)
    reviewer_notes: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GuidelineTopicRecord(Base):
    __tablename__ = "guideline_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    import_batch_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    topic_title: Mapped[str] = mapped_column(String(255))
    topic_applicability: Mapped[dict] = mapped_column(JSON)
    topic_intervention_tags: Mapped[list] = mapped_column(JSON)
    guideline_stance: Mapped[str] = mapped_column(String(64))
    stance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)


class EvidenceStudyRecord(Base):
    __tablename__ = "evidence_studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    import_batch_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(64))
    source_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    normalized_payload: Mapped[dict] = mapped_column(JSON)


class AnalysisRunRecord(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    ruleset_version: Mapped[str] = mapped_column(String(64))
    corpus_version: Mapped[str] = mapped_column(String(64))
    input_schema_version: Mapped[str] = mapped_column(String(64))
    trace_id: Mapped[str] = mapped_column(String(128))
    run_payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvalRunRecord(Base):
    __tablename__ = "eval_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    eval_run_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    pack_id: Mapped[str] = mapped_column(String(128))
    layer1_payload: Mapped[dict] = mapped_column(JSON)
    layer2_metrics: Mapped[list] = mapped_column(JSON)
    notes: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ImportBatchRecord(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    dataset_kind: Mapped[str] = mapped_column(String(32), index=True)
    dataset_shape: Mapped[str] = mapped_column(String(32))
    source_path: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), index=True)
    record_count: Mapped[int] = mapped_column(Integer)
    imported_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    validation_payload: Mapped[dict] = mapped_column(JSON)
    notes: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
