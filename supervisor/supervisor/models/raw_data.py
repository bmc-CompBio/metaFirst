"""Raw data reference and path change tracking models."""

from sqlalchemy import Column, Integer, String, BigInteger, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from supervisor.database import Base


class RawDataItem(Base):
    """Raw data file reference (storage root + relative path)."""

    __tablename__ = "raw_data_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sample_id = Column(Integer, ForeignKey("samples.id", ondelete="SET NULL"), nullable=True)
    storage_root_id = Column(Integer, ForeignKey("storage_roots.id"), nullable=False)
    relative_path = Column(String(2048), nullable=False)  # Path within storage root
    storage_owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    file_hash_sha256 = Column(String(64), nullable=True)  # Optional integrity check
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="raw_data_items")
    sample = relationship("Sample", back_populates="raw_data_items")
    storage_root = relationship("StorageRoot", back_populates="raw_data_items")
    storage_owner = relationship("User", foreign_keys=[storage_owner_user_id])
    creator = relationship("User", foreign_keys=[created_by])
    path_changes = relationship("PathChange", back_populates="raw_data_item", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("storage_root_id", "relative_path", name="uq_storage_path"),
        Index("ix_raw_data_sample", "sample_id"),
        Index("ix_raw_data_project", "project_id"),
    )

    def __repr__(self):
        return f"<RawDataItem(id={self.id}, path='{self.relative_path}')>"


class PathChange(Base):
    """Audit trail for raw data path changes."""

    __tablename__ = "path_changes"

    id = Column(Integer, primary_key=True, index=True)
    raw_data_item_id = Column(Integer, ForeignKey("raw_data_items.id", ondelete="CASCADE"), nullable=False)
    old_storage_root_id = Column(Integer, ForeignKey("storage_roots.id"), nullable=False)
    old_relative_path = Column(String(2048), nullable=False)
    new_storage_root_id = Column(Integer, ForeignKey("storage_roots.id"), nullable=False)
    new_relative_path = Column(String(2048), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=True)

    # Relationships
    raw_data_item = relationship("RawDataItem", back_populates="path_changes")
    old_storage_root = relationship("StorageRoot", foreign_keys=[old_storage_root_id])
    new_storage_root = relationship("StorageRoot", foreign_keys=[new_storage_root_id])
    changer = relationship("User")

    __table_args__ = (
        Index("ix_path_changes_item", "raw_data_item_id", "changed_at"),
    )

    def __repr__(self):
        return f"<PathChange(id={self.id}, raw_data_item_id={self.raw_data_item_id})>"
