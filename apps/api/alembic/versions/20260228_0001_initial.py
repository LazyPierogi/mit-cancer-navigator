"""Initial navigator schema.

Revision ID: 20260228_0001
Revises:
Create Date: 2026-02-28 18:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260228_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rulesets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("relevance_gate_rules", sa.JSON(), nullable=False),
        sa.Column("ers_tables", sa.JSON(), nullable=False),
        sa.Column("mapping_rubric", sa.JSON(), nullable=False),
        sa.Column("label_logic", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_rulesets_version", "rulesets", ["version"], unique=True)

    op.create_table(
        "safety_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("footer_key", sa.String(length=64), nullable=False),
        sa.Column("footer_copy", sa.Text(), nullable=False),
        sa.Column("uncertainty_copy", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_safety_templates_version", "safety_templates", ["version"], unique=True)

    op.create_table(
        "policy_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("safety_boundaries", sa.JSON(), nullable=False),
        sa.Column("hard_stops", sa.JSON(), nullable=False),
        sa.Column("soft_review_triggers", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_policy_snapshots_version", "policy_snapshots", ["version"], unique=True)

    op.create_table(
        "update_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("changed_component", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("before_after_summary", sa.JSON(), nullable=False),
        sa.Column("hard_stop_violations", sa.JSON(), nullable=False),
        sa.Column("soft_review_flags", sa.JSON(), nullable=False),
        sa.Column("reviewer_notes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "guideline_topics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("topic_id", sa.String(length=128), nullable=False),
        sa.Column("topic_title", sa.String(length=255), nullable=False),
        sa.Column("topic_applicability", sa.JSON(), nullable=False),
        sa.Column("topic_intervention_tags", sa.JSON(), nullable=False),
        sa.Column("guideline_stance", sa.String(length=64), nullable=False),
        sa.Column("stance_notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_guideline_topics_topic_id", "guideline_topics", ["topic_id"], unique=True)

    op.create_table(
        "evidence_studies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evidence_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("source_category", sa.String(length=64), nullable=True),
        sa.Column("normalized_payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_evidence_studies_evidence_id", "evidence_studies", ["evidence_id"], unique=True)

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("ruleset_version", sa.String(length=64), nullable=False),
        sa.Column("corpus_version", sa.String(length=64), nullable=False),
        sa.Column("input_schema_version", sa.String(length=64), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("run_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_analysis_runs_run_id", "analysis_runs", ["run_id"], unique=True)

    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("eval_run_id", sa.String(length=128), nullable=False),
        sa.Column("pack_id", sa.String(length=128), nullable=False),
        sa.Column("layer1_payload", sa.JSON(), nullable=False),
        sa.Column("layer2_metrics", sa.JSON(), nullable=False),
        sa.Column("notes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_eval_runs_eval_run_id", "eval_runs", ["eval_run_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_eval_runs_eval_run_id", table_name="eval_runs")
    op.drop_table("eval_runs")
    op.drop_index("ix_analysis_runs_run_id", table_name="analysis_runs")
    op.drop_table("analysis_runs")
    op.drop_index("ix_evidence_studies_evidence_id", table_name="evidence_studies")
    op.drop_table("evidence_studies")
    op.drop_index("ix_guideline_topics_topic_id", table_name="guideline_topics")
    op.drop_table("guideline_topics")
    op.drop_table("update_records")
    op.drop_index("ix_policy_snapshots_version", table_name="policy_snapshots")
    op.drop_table("policy_snapshots")
    op.drop_index("ix_safety_templates_version", table_name="safety_templates")
    op.drop_table("safety_templates")
    op.drop_index("ix_rulesets_version", table_name="rulesets")
    op.drop_table("rulesets")
