"""Release model for freezing project snapshots."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from supervisor.database import Base


class Release(Base):
    """Frozen snapshot of project state."""

    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    release_tag = Column(String(100), nullable=False)  # e.g., "v1.0", "2024-Q1"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    rdmp_version_id = Column(Integer, ForeignKey("rdmp_versions.id"), nullable=False)
    parent_release_id = Column(Integer, ForeignKey("releases.id"), nullable=True)  # For corrections
    description = Column(Text, nullable=True)
    snapshot_json = Column(JSON, nullable=False)  # Full denormalized snapshot

    # Relationships
    project = relationship("Project", back_populates="releases")
    creator = relationship("User")
    rdmp_version = relationship("RDMPVersion", back_populates="releases")
    parent_release = relationship("Release", remote_side=[id], backref="corrections")

    __table_args__ = (
        UniqueConstraint("project_id", "release_tag", name="uq_project_release"),
        Index("ix_release_project", "project_id", "created_at"),
    )

    def __repr__(self):
        return f"<Release(id={self.id}, tag='{self.release_tag}')>"
