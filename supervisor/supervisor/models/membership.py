"""Membership model - links users to projects with roles."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from supervisor.database import Base


class Membership(Base):
    """Project membership with role assignment."""

    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_name = Column(String(100), nullable=False)  # Must match RDMP role
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="memberships")
    user = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
        Index("ix_membership_project_user", "project_id", "user_id"),
    )

    def __repr__(self):
        return f"<Membership(project_id={self.project_id}, user_id={self.user_id}, role='{self.role_name}')>"
