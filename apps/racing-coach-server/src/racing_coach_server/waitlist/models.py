"""SQLAlchemy models for the waitlist feature."""

import uuid
from datetime import datetime

from sqlalchemy import Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from racing_coach_server.database.base import Base


class WaitlistEntry(Base):
    """Model representing a waitlist signup."""

    __tablename__ = "waitlist_entry"

    # Required fields (no defaults) come first
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Optional fields with defaults
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, default=None)

    # Primary key with default_factory
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default_factory=uuid.uuid4
    )

    # Server-defaulted timestamp
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), init=False
    )

    __table_args__ = (
        Index("idx_waitlist_email", "email"),
        Index("idx_waitlist_created_at", "created_at"),
    )
