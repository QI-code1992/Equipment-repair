from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class FaultStatus(StrEnum):
    PENDING_ACCEPT = "PENDING_ACCEPT"
    IN_REPAIR = "IN_REPAIR"
    PROCESSED = "PROCESSED"


class WorkOrderStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_ACCEPT = "PENDING_ACCEPT"
    IN_REPAIR = "IN_REPAIR"
    PENDING_INSPECTION = "PENDING_INSPECTION"
    COMPLETED = "COMPLETED"


class RepairStartMode(StrEnum):
    DIRECT = "DIRECT"
    ADOPTED = "ADOPTED"


class DiagnosisDraftStatus(StrEnum):
    DRAFT = "DRAFT"
    DIAGNOSIS_READY = "DIAGNOSIS_READY"


class FaultReport(Base):
    __tablename__ = "fault_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id"), nullable=False, index=True
    )
    organization_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False
    )
    urgency: Mapped[str] = mapped_column(String(30), nullable=False)
    symptom: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    possible_location: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    attachment_refs: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    status: Mapped[FaultStatus] = mapped_column(
        Enum(FaultStatus, native_enum=False),
        nullable=False,
        default=FaultStatus.PENDING_ACCEPT,
        index=True,
    )
    submitter_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class DiagnosisDraft(Base):
    __tablename__ = "diagnosis_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    fault_report_id: Mapped[str] = mapped_column(
        ForeignKey("fault_reports.id"), nullable=False, index=True
    )
    status: Mapped[DiagnosisDraftStatus] = mapped_column(
        Enum(DiagnosisDraftStatus, native_enum=False),
        nullable=False,
        default=DiagnosisDraftStatus.DRAFT,
    )
    allowed_prefill: Mapped[dict[str, object] | None] = mapped_column(JSON)
    read_only_summary: Mapped[dict[str, object] | None] = mapped_column(JSON)
    adopted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    fault_report_id: Mapped[str] = mapped_column(
        ForeignKey("fault_reports.id"), unique=True, nullable=False
    )
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id"), nullable=False, index=True
    )
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus, native_enum=False),
        nullable=False,
        default=WorkOrderStatus.DRAFT,
        index=True,
    )
    repairer_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pending_inspection_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    work_order_id: Mapped[str] = mapped_column(
        ForeignKey("work_orders.id"), unique=True, nullable=False
    )
    start_mode: Mapped[RepairStartMode] = mapped_column(
        Enum(RepairStartMode, native_enum=False), nullable=False
    )
    diagnosis_draft_id: Mapped[str | None] = mapped_column(
        ForeignKey("diagnosis_drafts.id"), unique=True
    )
    diagnosis_prefill: Mapped[dict[str, object] | None] = mapped_column(JSON)
    ai_summary: Mapped[dict[str, object] | None] = mapped_column(JSON)
    actual_cause: Mapped[str | None] = mapped_column(Text)
    actual_solution: Mapped[str | None] = mapped_column(Text)
    repair_result: Mapped[str | None] = mapped_column(Text)
    parts_replacement_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class HistoricalRepairCase(Base):
    __tablename__ = "historical_repair_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_work_order_id: Mapped[str] = mapped_column(
        ForeignKey("work_orders.id"), unique=True, nullable=False
    )
    source_fault_report_id: Mapped[str] = mapped_column(
        ForeignKey("fault_reports.id"), nullable=False, index=True
    )
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id"), nullable=False, index=True
    )
    equipment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    equipment_model: Mapped[str] = mapped_column(String(200), nullable=False)
    symptom: Mapped[str] = mapped_column(Text, nullable=False)
    actual_cause: Mapped[str] = mapped_column(Text, nullable=False)
    actual_solution: Mapped[str] = mapped_column(Text, nullable=False)
    repair_result: Mapped[str] = mapped_column(Text, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
