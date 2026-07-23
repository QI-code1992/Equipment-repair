"""Create TASK-005 knowledge lifecycle tables.

Revision ID: 0006_task005
Revises: 0005_task007
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_task005"
down_revision = "0005_task007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "file_objects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("object_key", sa.String(500), nullable=False, unique=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("scan_status", sa.String(16), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "knowledge_datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("ragflow_dataset_id", sa.String(100), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("knowledge_datasets.id"), nullable=False),
        sa.Column("object_storage_file_id", sa.String(36), sa.ForeignKey("file_objects.id"), nullable=False, unique=True),
        sa.Column("ragflow_document_id", sa.String(100), unique=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_documents_dataset_id", "knowledge_documents", ["dataset_id"])
    op.create_index("ix_knowledge_documents_status", "knowledge_documents", ["status"])
    op.create_table(
        "knowledge_citations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("knowledge_documents.id"), nullable=False),
        sa.Column("chunk_id", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("similarity", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_citations_document_id", "knowledge_citations", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_citations_document_id", table_name="knowledge_citations")
    op.drop_table("knowledge_citations")
    op.drop_index("ix_knowledge_documents_status", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_dataset_id", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
    op.drop_table("knowledge_datasets")
    op.drop_table("file_objects")
