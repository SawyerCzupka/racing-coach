"""FastAPI route handlers for waitlist."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from racing_coach_server.auth.dependencies import CurrentUserDep
from racing_coach_server.database.dependencies import AsyncSessionDep
from racing_coach_server.database.engine import transactional_session
from racing_coach_server.waitlist.schemas import (
    WaitlistEntryResponse,
    WaitlistListResponse,
    WaitlistSignupRequest,
    WaitlistSignupResponse,
)
from racing_coach_server.waitlist.service import WaitlistService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_waitlist_service(db: AsyncSessionDep) -> WaitlistService:
    """Dependency for WaitlistService."""
    return WaitlistService(db)


WaitlistServiceDep = Annotated[WaitlistService, Depends(get_waitlist_service)]


@router.post(
    "",
    response_model=WaitlistSignupResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["waitlist"],
    operation_id="joinWaitlist",
)
async def join_waitlist(
    request_body: WaitlistSignupRequest,
    request: Request,
    db: AsyncSessionDep,
    waitlist_service: WaitlistServiceDep,
) -> WaitlistSignupResponse:
    """
    Add email to waitlist.

    Public endpoint - no authentication required.
    Accepts optional feedback for product discovery.
    """
    ip_address = request.client.host if request.client else None

    try:
        async with transactional_session(db):
            entry = await waitlist_service.add_signup(
                email=request_body.email,
                feedback=request_body.feedback,
                source=request_body.source,
                ip_address=ip_address,
            )
            return WaitlistSignupResponse(email=entry.email)
    except ValueError:
        # Email already exists - return success anyway to not leak info
        return WaitlistSignupResponse(email=request_body.email)


@router.get(
    "",
    response_model=WaitlistListResponse,
    tags=["waitlist", "admin"],
    operation_id="listWaitlistEntries",
)
async def list_waitlist_entries(
    current_user: CurrentUserDep,
    waitlist_service: WaitlistServiceDep,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> WaitlistListResponse:
    """
    List all waitlist entries.

    Admin-only endpoint.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    entries, total = await waitlist_service.get_all_entries(limit=limit, offset=offset)

    return WaitlistListResponse(
        entries=[
            WaitlistEntryResponse(
                id=str(e.id),
                email=e.email,
                feedback=e.feedback,
                source=e.source,
                ip_address=e.ip_address,
                created_at=e.created_at,
            )
            for e in entries
        ],
        total=total,
    )
