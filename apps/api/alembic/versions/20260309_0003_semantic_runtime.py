"""Add semantic retrieval runtime tables.

Revision ID: 20260309_0003
Revises: 20260302_0002
Create Date: 2026-03-09 16:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260309_0003"
down_revision = "20260302_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_kind", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("source_title", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("import_batch_id", sa.String(length=128), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("histology_original", sa.String(length=128), nullable=True),
        sa.Column("histology_normalized", sa.String(length=64), nullable=False),
        sa.Column("histology_source", sa.String(length=64), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_source_documents_document_id", "source_documents", ["document_id"], unique=True)
    op.create_index("ix_source_documents_dataset_kind", "source_documents", ["dataset_kind"], unique=False)
    op.create_index("ix_source_documents_source_id", "source_documents", ["source_id"], unique=False)
    op.create_index("ix_source_documents_import_batch_id", "source_documents", ["import_batch_id"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chunk_id", sa.String(length=128), nullable=False),
        sa.Column("document_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_kind", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("topic_id", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("dense_vector", sa.JSON(), nullable=False),
        sa.Column("sparse_vector", sa.JSON(), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_document_chunks_chunk_id", "document_chunks", ["chunk_id"], unique=True)
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"], unique=False)
    op.create_index("ix_document_chunks_dataset_kind", "document_chunks", ["dataset_kind"], unique=False)
    op.create_index("ix_document_chunks_source_type", "document_chunks", ["source_type"], unique=False)
    op.create_index("ix_document_chunks_source_id", "document_chunks", ["source_id"], unique=False)
    op.create_index("ix_document_chunks_topic_id", "document_chunks", ["topic_id"], unique=False)

    op.create_table(
        "embedding_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_kind", sa.String(length=32), nullable=False),
        sa.Column("import_batch_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("vector_store", sa.String(length=64), nullable=False),
        sa.Column("retrieval_mode", sa.String(length=64), nullable=False),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("chunking_strategy_version", sa.String(length=128), nullable=False),
        sa.Column("document_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_embedding_jobs_job_id", "embedding_jobs", ["job_id"], unique=True)
    op.create_index("ix_embedding_jobs_dataset_kind", "embedding_jobs", ["dataset_kind"], unique=False)
    op.create_index("ix_embedding_jobs_import_batch_id", "embedding_jobs", ["import_batch_id"], unique=False)
    op.create_index("ix_embedding_jobs_status", "embedding_jobs", ["status"], unique=False)

    op.create_table(
        "projection_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("point_id", sa.String(length=128), nullable=False),
        sa.Column("chunk_id", sa.String(length=128), nullable=False),
        sa.Column("document_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_kind", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("topic_id", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("histology", sa.String(length=64), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_projection_points_point_id", "projection_points", ["point_id"], unique=True)
    op.create_index("ix_projection_points_chunk_id", "projection_points", ["chunk_id"], unique=False)
    op.create_index("ix_projection_points_document_id", "projection_points", ["document_id"], unique=False)
    op.create_index("ix_projection_points_dataset_kind", "projection_points", ["dataset_kind"], unique=False)
    op.create_index("ix_projection_points_source_type", "projection_points", ["source_type"], unique=False)
    op.create_index("ix_projection_points_source_id", "projection_points", ["source_id"], unique=False)
    op.create_index("ix_projection_points_topic_id", "projection_points", ["topic_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_projection_points_topic_id", table_name="projection_points")
    op.drop_index("ix_projection_points_source_id", table_name="projection_points")
    op.drop_index("ix_projection_points_source_type", table_name="projection_points")
    op.drop_index("ix_projection_points_dataset_kind", table_name="projection_points")
    op.drop_index("ix_projection_points_document_id", table_name="projection_points")
    op.drop_index("ix_projection_points_chunk_id", table_name="projection_points")
    op.drop_index("ix_projection_points_point_id", table_name="projection_points")
    op.drop_table("projection_points")

    op.drop_index("ix_embedding_jobs_status", table_name="embedding_jobs")
    op.drop_index("ix_embedding_jobs_import_batch_id", table_name="embedding_jobs")
    op.drop_index("ix_embedding_jobs_dataset_kind", table_name="embedding_jobs")
    op.drop_index("ix_embedding_jobs_job_id", table_name="embedding_jobs")
    op.drop_table("embedding_jobs")

    op.drop_index("ix_document_chunks_topic_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_source_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_source_type", table_name="document_chunks")
    op.drop_index("ix_document_chunks_dataset_kind", table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_chunk_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_source_documents_import_batch_id", table_name="source_documents")
    op.drop_index("ix_source_documents_source_id", table_name="source_documents")
    op.drop_index("ix_source_documents_dataset_kind", table_name="source_documents")
    op.drop_index("ix_source_documents_document_id", table_name="source_documents")
    op.drop_table("source_documents")
