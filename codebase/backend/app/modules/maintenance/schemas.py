from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.maintenance.models import RepairStartMode


class AttachmentRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_key: str = Field(min_length=1, max_length=500)
    filename: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=0, le=100 * 1024 * 1024)
    content_type: str = Field(min_length=1, max_length=255)


class FaultReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    equipment_id: str = Field(min_length=1, max_length=36)
    urgency: str = Field(min_length=1, max_length=30)
    symptom: str = Field(min_length=1, max_length=4000)
    occurred_at: datetime
    possible_location: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=10000)
    attachment_refs: list[AttachmentRef] = Field(default_factory=list)


class StartRepairRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: RepairStartMode
    diagnosis_draft_id: str | None = Field(default=None, min_length=1, max_length=36)

    @model_validator(mode="after")
    def validate_diagnosis_reference(self) -> "StartRepairRequest":
        if self.mode is RepairStartMode.DIRECT and self.diagnosis_draft_id is not None:
            raise ValueError("DIRECT start forbids diagnosis_draft_id")
        if self.mode is RepairStartMode.ADOPTED and self.diagnosis_draft_id is None:
            raise ValueError("ADOPTED start requires diagnosis_draft_id")
        return self


class RepairResultRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    actual_cause: str = Field(min_length=1, max_length=10000)
    actual_solution: str = Field(min_length=1, max_length=10000)
    repair_result: str = Field(min_length=1, max_length=10000)
    parts_replacement_notes: str | None = Field(default=None, max_length=10000)


class SimilarCaseQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    equipment_type: str | None = Field(default=None, min_length=1, max_length=100)
    equipment_model: str | None = Field(default=None, min_length=1, max_length=200)
    symptom: str | None = Field(default=None, min_length=1, max_length=4000)
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def require_filter(self) -> "SimilarCaseQuery":
        if not any((self.equipment_type, self.equipment_model, self.symptom)):
            raise ValueError("at least one similar-case filter is required")
        return self
