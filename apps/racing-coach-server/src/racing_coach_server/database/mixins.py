"""Database model mixins for common functionality."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column


class TimestampMixin(MappedAsDataclass):
    """Mixin providing created_at and updated_at timestamp columns.

    Note: Fields use init=False so they don't require constructor args.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )
