"""Storage root models for cross-machine file references."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from supervisor.database import Base


class StorageRoot(Base):
    """Storage location definition for a project."""

    __tablename__ = "storage_roots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="storage_roots")
    mappings = relationship("StorageRootMapping", back_populates="storage_root", cascade="all, delete-orphan")
    raw_data_items = relationship("RawDataItem", back_populates="storage_root")

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_storage_name"),
    )

    def __repr__(self):
        return f"<StorageRoot(id={self.id}, name='{self.name}')>"


class StorageRootMapping(Base):
    """User-specific mapping from storage root to local path."""

    __tablename__ = "storage_root_mappings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    storage_root_id = Column(Integer, ForeignKey("storage_roots.id", ondelete="CASCADE"), nullable=False)
    local_mount_path = Column(String(1024), nullable=False)  # User's local path
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="storage_mappings")
    storage_root = relationship("StorageRoot", back_populates="mappings")

    __table_args__ = (
        UniqueConstraint("user_id", "storage_root_id", name="uq_user_storage"),
    )

    def __repr__(self):
        return f"<StorageRootMapping(user_id={self.user_id}, storage_root_id={self.storage_root_id})>"
