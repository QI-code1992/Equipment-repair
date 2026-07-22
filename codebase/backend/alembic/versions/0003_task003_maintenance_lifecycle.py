"""Add the TASK-003 maintenance lifecycle schema.

Downgrade is destructive: all TASK-003 fault, work-order, maintenance, diagnosis,
and historical-case data is removed. TASK-002 tables and data remain intact.

Revision ID: 0003_task003
Revises: 0002
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_task003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fault_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number", sa.String(100), nullable=False),
        sa.Column("equipment_id", sa.String(36), nullable=False),
        sa.Column("organization_snapshot", sa.JSON(), nullable=False),
        sa.Column("urgency", sa.String(30), nullable=False),
        sa.Column("symptom", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("possible_location", sa.String(300)),
        sa.Column("description", sa.Text()),
        sa.Column("attachment_refs", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(14), nullable=False),
        sa.Column("submitter_id", sa.String(36), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('PENDING_ACCEPT', 'IN_REPAIR', 'PROCESSED')",
            name="ck_fault_reports_status",
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"], ["equipment.id"], name="fk_fault_reports_equipment_id"
        ),
        sa.ForeignKeyConstraint(
            ["submitter_id"], ["users.id"], name="fk_fault_reports_submitter_id"
        ),
        sa.UniqueConstraint("number", name="uq_fault_reports_number"),
    )
    op.create_index(
        "ix_fault_reports_equipment_id", "fault_reports", ["equipment_id"]
    )
    op.create_index("ix_fault_reports_status", "fault_reports", ["status"])

    op.create_table(
        "diagnosis_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("fault_report_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(15), nullable=False),
        sa.Column("allowed_prefill", sa.JSON()),
        sa.Column("read_only_summary", sa.JSON()),
        sa.Column("adopted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'DIAGNOSIS_READY')",
            name="ck_diagnosis_drafts_status",
        ),
        sa.ForeignKeyConstraint(
            ["fault_report_id"],
            ["fault_reports.id"],
            name="fk_diagnosis_drafts_fault_report_id",
        ),
    )
    op.create_index(
        "ix_diagnosis_drafts_fault_report_id",
        "diagnosis_drafts",
        ["fault_report_id"],
    )

    op.create_table(
        "work_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number", sa.String(100), nullable=False),
        sa.Column("fault_report_id", sa.String(36), nullable=False),
        sa.Column("equipment_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(18), nullable=False),
        sa.Column("repairer_user_id", sa.String(36)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("pending_inspection_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PENDING_ACCEPT', 'IN_REPAIR', "
            "'PENDING_INSPECTION', 'COMPLETED')",
            name="ck_work_orders_status",
        ),
        sa.ForeignKeyConstraint(
            ["fault_report_id"],
            ["fault_reports.id"],
            name="fk_work_orders_fault_report_id",
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"], ["equipment.id"], name="fk_work_orders_equipment_id"
        ),
        sa.ForeignKeyConstraint(
            ["repairer_user_id"],
            ["users.id"],
            name="fk_work_orders_repairer_user_id",
        ),
        sa.UniqueConstraint("number", name="uq_work_orders_number"),
        sa.UniqueConstraint(
            "fault_report_id", name="uq_work_orders_fault_report_id"
        ),
    )
    op.create_index("ix_work_orders_equipment_id", "work_orders", ["equipment_id"])
    op.create_index("ix_work_orders_status", "work_orders", ["status"])

    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("work_order_id", sa.String(36), nullable=False),
        sa.Column("start_mode", sa.String(7), nullable=False),
        sa.Column("diagnosis_draft_id", sa.String(36)),
        sa.Column("diagnosis_prefill", sa.JSON()),
        sa.Column("ai_summary", sa.JSON()),
        sa.Column("actual_cause", sa.Text()),
        sa.Column("actual_solution", sa.Text()),
        sa.Column("repair_result", sa.Text()),
        sa.Column("parts_replacement_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "start_mode IN ('DIRECT', 'ADOPTED')",
            name="ck_maintenance_records_start_mode",
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["work_orders.id"],
            name="fk_maintenance_records_work_order_id",
        ),
        sa.ForeignKeyConstraint(
            ["diagnosis_draft_id"],
            ["diagnosis_drafts.id"],
            name="fk_maintenance_records_diagnosis_draft_id",
        ),
        sa.UniqueConstraint(
            "work_order_id", name="uq_maintenance_records_work_order_id"
        ),
        sa.UniqueConstraint(
            "diagnosis_draft_id",
            name="uq_maintenance_records_diagnosis_draft_id",
        ),
    )

    op.create_table(
        "historical_repair_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_work_order_id", sa.String(36), nullable=False),
        sa.Column("source_fault_report_id", sa.String(36), nullable=False),
        sa.Column("equipment_id", sa.String(36), nullable=False),
        sa.Column("equipment_type", sa.String(100), nullable=False),
        sa.Column("equipment_model", sa.String(200), nullable=False),
        sa.Column("symptom", sa.Text(), nullable=False),
        sa.Column("actual_cause", sa.Text(), nullable=False),
        sa.Column("actual_solution", sa.Text(), nullable=False),
        sa.Column("repair_result", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_work_order_id"],
            ["work_orders.id"],
            name="fk_historical_repair_cases_source_work_order_id",
        ),
        sa.ForeignKeyConstraint(
            ["source_fault_report_id"],
            ["fault_reports.id"],
            name="fk_historical_repair_cases_source_fault_report_id",
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["equipment.id"],
            name="fk_historical_repair_cases_equipment_id",
        ),
        sa.UniqueConstraint(
            "source_work_order_id",
            name="uq_historical_repair_cases_source_work_order_id",
        ),
    )
    op.create_index(
        "ix_historical_repair_cases_source_fault_report_id",
        "historical_repair_cases",
        ["source_fault_report_id"],
    )
    op.create_index(
        "ix_historical_repair_cases_equipment_id",
        "historical_repair_cases",
        ["equipment_id"],
    )


def downgrade() -> None:
    op.drop_table("historical_repair_cases")
    op.drop_table("maintenance_records")
    op.drop_table("work_orders")
    op.drop_table("diagnosis_drafts")
    op.drop_table("fault_reports")
