"""RDMP (Research Data Management Plan) schemas."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class RDMPRole(BaseModel):
    """RDMP role definition."""

    name: str
    permissions: dict[str, bool]


class RDMPField(BaseModel):
    """RDMP field definition."""

    key: str
    label: str
    type: str  # string, number, date, categorical
    required: bool = False
    allowed_values: list[str] | None = None
    visibility: str = "collaborators"  # private, collaborators, public_index


class RDMPIngestionRules(BaseModel):
    """RDMP ingestion rules."""

    file_patterns: list[str] = []
    prompts: list[str] = []


class RDMPJSON(BaseModel):
    """RDMP JSON structure."""

    roles: list[RDMPRole]
    fields: list[RDMPField]
    ingestion_rules: RDMPIngestionRules = Field(default_factory=RDMPIngestionRules)


class RDMPTemplateBase(BaseModel):
    """Base RDMP template schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class RDMPTemplateCreate(RDMPTemplateBase):
    """RDMP template creation schema."""

    template_json: RDMPJSON


class RDMPTemplate(RDMPTemplateBase):
    """RDMP template response schema."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RDMPTemplateVersionCreate(BaseModel):
    """RDMP template version creation schema."""

    template_json: RDMPJSON


class RDMPTemplateVersion(BaseModel):
    """RDMP template version response schema."""

    id: int
    template_id: int
    version_int: int
    created_at: datetime
    created_by: int
    template_json: dict[str, Any]

    class Config:
        from_attributes = True


class RDMPVersionCreate(BaseModel):
    """Project RDMP version creation schema."""

    rdmp_json: RDMPJSON
    provenance_json: dict[str, Any] | None = None


class RDMPVersion(BaseModel):
    """Project RDMP version response schema."""

    id: int
    project_id: int
    version_int: int
    created_at: datetime
    created_by: int
    rdmp_json: dict[str, Any]
    provenance_json: dict[str, Any] | None

    class Config:
        from_attributes = True
