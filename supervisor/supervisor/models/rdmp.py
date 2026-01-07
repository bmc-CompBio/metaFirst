"""RDMP (Research Data Management Plan) models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from supervisor.database import Base


class RDMPTemplate(Base):
    """RDMP template - reusable RDMP definitions."""

    __tablename__ = "rdmp_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    versions = relationship("RDMPTemplateVersion", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RDMPTemplate(id={self.id}, name='{self.name}')>"


class RDMPTemplateVersion(Base):
    """Versioned RDMP template."""

    __tablename__ = "rdmp_template_versions"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("rdmp_templates.id", ondelete="CASCADE"), nullable=False)
    version_int = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_json = Column(JSON, nullable=False)  # Full RDMP structure

    # Relationships
    template = relationship("RDMPTemplate", back_populates="versions")
    creator = relationship("User")

    __table_args__ = (
        UniqueConstraint("template_id", "version_int", name="uq_template_version"),
        Index("ix_template_latest", "template_id", "version_int"),
    )

    def __repr__(self):
        return f"<RDMPTemplateVersion(template_id={self.template_id}, version={self.version_int})>"


class RDMPVersion(Base):
    """Project-specific RDMP version (append-only)."""

    __tablename__ = "rdmp_versions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    version_int = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    rdmp_json = Column(JSON, nullable=False)  # Active RDMP for project
    provenance_json = Column(JSON, nullable=True)  # Template reference, changes, parameters

    # Relationships
    project = relationship("Project", back_populates="rdmp_versions")
    creator = relationship("User")
    releases = relationship("Release", back_populates="rdmp_version")

    __table_args__ = (
        UniqueConstraint("project_id", "version_int", name="uq_project_rdmp_version"),
        Index("ix_project_rdmp_latest", "project_id", "version_int"),
    )

    def __repr__(self):
        return f"<RDMPVersion(project_id={self.project_id}, version={self.version_int})>"
