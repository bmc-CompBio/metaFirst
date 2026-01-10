"""Pending ingest model for browser-based file registration."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from supervisor.database import Base
import enum


class IngestStatus(str, enum.Enum):
    """Status of a pending ingest."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PendingIngest(Base):
    """Pending file ingest awaiting user action in browser UI."""

    __tablename__ = "pending_ingests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    storage_root_id = Column(Integer, ForeignKey("storage_roots.id", ondelete="CASCADE"), nullable=False)
    relative_path = Column(String(2048), nullable=False)
    inferred_sample_identifier = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_hash_sha256 = Column(String(64), nullable=True)
    status = Column(String(20), default=IngestStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    raw_data_item_id = Column(Integer, ForeignKey("raw_data_items.id"), nullable=True)

    # Relationships
    project = relationship("Project")
    storage_root = relationship("StorageRoot")
    creator = relationship("User")
    raw_data_item = relationship("RawDataItem")

    def __repr__(self):
        return f"<PendingIngest(id={self.id}, path='{self.relative_path}', status='{self.status}')>"
