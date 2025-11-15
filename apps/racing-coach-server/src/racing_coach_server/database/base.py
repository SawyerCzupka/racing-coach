"""Database base configuration for SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(MappedAsDataclass, DeclarativeBase):
    """Base class for all SQLAlchemy models with dataclass integration."""
