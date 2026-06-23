"""Harden public table RLS and role grants.

Revision ID: 20260623_0005
Revises: 20260401_0004
Create Date: 2026-06-23 12:00:00
"""

from alembic import op


revision = "20260623_0005"
down_revision = "20260401_0004"
branch_labels = None
depends_on = None


APP_TABLES = (
    "analysis_runs",
    "document_chunks",
    "embedding_jobs",
    "eval_runs",
    "evidence_studies",
    "guideline_topics",
    "import_batches",
    "policy_snapshots",
    "projection_points",
    "rulesets",
    "safety_templates",
    "source_documents",
    "update_records",
)


def upgrade() -> None:
    for table_name in APP_TABLES:
        op.execute(f"ALTER TABLE IF EXISTS public.{table_name} ENABLE ROW LEVEL SECURITY")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM anon;
                REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM anon;
                EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon';
                EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon';
            END IF;

            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM authenticated;
                REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM authenticated;
                EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM authenticated';
                EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM authenticated';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Security hardening is intentionally not reversed automatically.
    pass
