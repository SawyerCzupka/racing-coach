"""Pydantic schemas for waitlist API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class WaitlistSignupRequest(BaseModel):
    """Request model for waitlist signup."""

    email: EmailStr
    feedback: str | None = Field(None, max_length=2000)
    source: str | None = Field(None, max_length=50)


class WaitlistSignupResponse(BaseModel):
    """Response model for successful waitlist signup."""

    message: str = "Thanks for signing up! We'll be in touch."
    email: str


class WaitlistEntryResponse(BaseModel):
    """Response model for a waitlist entry (admin view)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    feedback: str | None
    source: str | None
    ip_address: str | None
    created_at: datetime


class WaitlistListResponse(BaseModel):
    """Response model for listing waitlist entries."""

    entries: list[WaitlistEntryResponse]
    total: int
