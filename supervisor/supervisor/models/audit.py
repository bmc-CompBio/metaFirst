"""Audit log model for tracking all state changes."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from supervisor.database import Base


class AuditLog(Base):
    """Audit trail for all state changes."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, etc.
    target_type = Column(String(100), nullable=False)  # Sample, RawDataItem, etc.
    target_id = Column(Integer, nullable=False)
    before_json = Column(JSON, nullable=True)  # State before change
    after_json = Column(JSON, nullable=True)  # State after change
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    source_device = Column(String(255), nullable=True)  # Device identifier

    # Relationships
    project = relationship("Project", back_populates="audit_logs")
    actor = relationship("User", back_populates="audit_logs", foreign_keys=[actor_user_id])

    __table_args__ = (
        Index("ix_audit_project_time", "project_id", "timestamp"),
        Index("ix_audit_target", "target_type", "target_id"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action_type}', target='{self.target_type}:{self.target_id}')>"
