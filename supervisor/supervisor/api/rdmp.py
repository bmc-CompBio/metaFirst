"""RDMP template and version management API."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from supervisor.database import get_db
from supervisor.models.user import User
from supervisor.models.rdmp import RDMPTemplate, RDMPTemplateVersion, RDMPVersion
from supervisor.schemas.rdmp import (
    RDMPTemplate as RDMPTemplateSchema,
    RDMPTemplateCreate,
    RDMPTemplateVersion as RDMPTemplateVersionSchema,
    RDMPTemplateVersionCreate,
    RDMPVersion as RDMPVersionSchema,
    RDMPVersionCreate,
)
from supervisor.api.deps import get_current_active_user
from supervisor.services.rdmp_service import validate_rdmp_schema, get_current_rdmp

router = APIRouter()


# RDMP Templates

@router.get("/templates", response_model=list[RDMPTemplateSchema])
def list_templates(db: Annotated[Session, Depends(get_db)]):
    """List all RDMP templates."""
    templates = db.query(RDMPTemplate).all()
    return templates


@router.post("/templates", response_model=RDMPTemplateSchema, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: RDMPTemplateCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create a new RDMP template with initial version."""
    # Validate RDMP schema
    is_valid, errors = validate_rdmp_schema(template_data.template_json.model_dump())
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid RDMP schema", "errors": errors}
        )

    # Create template
    template = RDMPTemplate(
        name=template_data.name,
        description=template_data.description
    )
    db.add(template)
    db.flush()

    # Create initial version
    version = RDMPTemplateVersion(
        template_id=template.id,
        version_int=1,
        created_by=current_user.id,
        template_json=template_data.template_json.model_dump()
    )
    db.add(version)
    db.commit()
    db.refresh(template)

    return template


@router.get("/templates/{template_id}/versions", response_model=list[RDMPTemplateVersionSchema])
def list_template_versions(
    template_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """List all versions of an RDMP template."""
    versions = (
        db.query(RDMPTemplateVersion)
        .filter(RDMPTemplateVersion.template_id == template_id)
        .order_by(RDMPTemplateVersion.version_int.desc())
        .all()
    )
    return versions


@router.post("/templates/{template_id}/versions", response_model=RDMPTemplateVersionSchema, status_code=status.HTTP_201_CREATED)
def create_template_version(
    template_id: int,
    version_data: RDMPTemplateVersionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create a new version of an RDMP template."""
    # Check template exists
    template = db.query(RDMPTemplate).filter(RDMPTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Validate RDMP schema
    is_valid, errors = validate_rdmp_schema(version_data.template_json.model_dump())
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid RDMP schema", "errors": errors}
        )

    # Get next version number
    latest_version = (
        db.query(RDMPTemplateVersion)
        .filter(RDMPTemplateVersion.template_id == template_id)
        .order_by(RDMPTemplateVersion.version_int.desc())
        .first()
    )
    next_version_int = (latest_version.version_int + 1) if latest_version else 1

    # Create version
    version = RDMPTemplateVersion(
        template_id=template_id,
        version_int=next_version_int,
        created_by=current_user.id,
        template_json=version_data.template_json.model_dump()
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    return version


# Project RDMP Versions

@router.get("/projects/{project_id}/rdmp", response_model=RDMPVersionSchema)
def get_project_rdmp(
    project_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Get current RDMP for a project."""
    rdmp = get_current_rdmp(db, project_id)
    if not rdmp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No RDMP found for project")
    return rdmp


@router.get("/projects/{project_id}/rdmp/versions", response_model=list[RDMPVersionSchema])
def list_project_rdmp_versions(
    project_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """List all RDMP versions for a project."""
    versions = (
        db.query(RDMPVersion)
        .filter(RDMPVersion.project_id == project_id)
        .order_by(RDMPVersion.version_int.desc())
        .all()
    )
    return versions


@router.post("/projects/{project_id}/rdmp", response_model=RDMPVersionSchema, status_code=status.HTTP_201_CREATED)
def create_project_rdmp_version(
    project_id: int,
    rdmp_data: RDMPVersionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create a new RDMP version for a project."""
    # Validate RDMP schema
    is_valid, errors = validate_rdmp_schema(rdmp_data.rdmp_json.model_dump())
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid RDMP schema", "errors": errors}
        )

    # Get next version number
    latest_version = (
        db.query(RDMPVersion)
        .filter(RDMPVersion.project_id == project_id)
        .order_by(RDMPVersion.version_int.desc())
        .first()
    )
    next_version_int = (latest_version.version_int + 1) if latest_version else 1

    # Create version
    version = RDMPVersion(
        project_id=project_id,
        version_int=next_version_int,
        created_by=current_user.id,
        rdmp_json=rdmp_data.rdmp_json.model_dump(),
        provenance_json=rdmp_data.provenance_json
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    return version
