"""Add import batch metadata and corpus provenance fields.

Revision ID: 20260302_0002
Revises: 20260228_0001
Create Date: 2026-03-02 14:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260302_0002"
down_revision = "20260228_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_kind", sa.String(length=32), nullable=False),
        sa.Column("dataset_shape", sa.String(length=32), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("validation_payload", sa.JSON(), nullable=False),
        sa.Column("notes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_import_batches_batch_id", "import_batches", ["batch_id"], unique=True)
    op.create_index("ix_import_batches_dataset_kind", "import_batches", ["dataset_kind"], unique=False)
    op.create_index("ix_import_batches_status", "import_batches", ["status"], unique=False)

    op.add_column("guideline_topics", sa.Column("import_batch_id", sa.String(length=128), nullable=True))
    op.add_column("guideline_topics", sa.Column("prerequisites", sa.JSON(), nullable=False, server_default="[]"))
    op.create_index("ix_guideline_topics_import_batch_id", "guideline_topics", ["import_batch_id"], unique=False)

    op.add_column("evidence_studies", sa.Column("import_batch_id", sa.String(length=128), nullable=True))
    op.create_index("ix_evidence_studies_import_batch_id", "evidence_studies", ["import_batch_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_evidence_studies_import_batch_id", table_name="evidence_studies")
    op.drop_column("evidence_studies", "import_batch_id")

    op.drop_index("ix_guideline_topics_import_batch_id", table_name="guideline_topics")
    op.drop_column("guideline_topics", "prerequisites")
    op.drop_column("guideline_topics", "import_batch_id")

    op.drop_index("ix_import_batches_status", table_name="import_batches")
    op.drop_index("ix_import_batches_dataset_kind", table_name="import_batches")
    op.drop_index("ix_import_batches_batch_id", table_name="import_batches")
    op.drop_table("import_batches")
