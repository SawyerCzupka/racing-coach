"""Business logic for waitlist feature."""

import logging

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from racing_coach_server.waitlist.models import WaitlistEntry

logger = logging.getLogger(__name__)


class WaitlistService:
    """Service for managing waitlist signups."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add_signup(
        self,
        email: str,
        feedback: str | None = None,
        source: str | None = None,
        ip_address: str | None = None,
    ) -> WaitlistEntry:
        """
        Add a new waitlist signup.

        Args:
            email: Email address to add
            feedback: Optional feedback/comments from user
            source: Optional source identifier (e.g., "landing", "blog")
            ip_address: Optional IP address for rate limiting

        Returns:
            The created WaitlistEntry

        Raises:
            ValueError: If email already exists on waitlist
        """
        entry = WaitlistEntry(
            email=email.lower().strip(),
            feedback=feedback.strip() if feedback else None,
            source=source,
            ip_address=ip_address,
        )

        try:
            self.db.add(entry)
            await self.db.flush()
            logger.info("Added email to waitlist: %s", email)
            return entry
        except IntegrityError as e:
            await self.db.rollback()
            logger.info("Email already on waitlist: %s", email)
            raise ValueError("Email already on waitlist") from e

    async def get_entry_by_email(self, email: str) -> WaitlistEntry | None:
        """Get a waitlist entry by email."""
        result = await self.db.execute(
            select(WaitlistEntry).where(WaitlistEntry.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_all_entries(
        self, limit: int = 100, offset: int = 0
    ) -> tuple[list[WaitlistEntry], int]:
        """
        Get all waitlist entries (for admin).

        Returns:
            Tuple of (entries, total_count)
        """
        # Get total count
        count_result = await self.db.execute(select(func.count(WaitlistEntry.id)))
        total = count_result.scalar_one()

        # Get paginated entries
        result = await self.db.execute(
            select(WaitlistEntry)
            .order_by(WaitlistEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        entries = list(result.scalars().all())

        return entries, total
