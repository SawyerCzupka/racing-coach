"""CLI commands for admin user management."""

import asyncio
from dataclasses import dataclass
from typing import Annotated

import typer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from racing_coach_server.auth.models import User
from racing_coach_server.config import settings

app = typer.Typer(help="Racing Coach admin management CLI")


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create a fresh async session factory for CLI usage.

    This avoids event loop conflicts by creating a new engine each time
    rather than reusing the global one from database.engine.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@dataclass
class UserInfo:
    """Simple dataclass to hold user info outside of session."""

    email: str
    display_name: str | None
    is_admin: bool


async def _get_user_by_email(email: str) -> UserInfo | None:
    """Get a user by email address."""
    factory = _get_session_factory()
    async with factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            return UserInfo(
                email=user.email, display_name=user.display_name, is_admin=user.is_admin
            )
        return None


async def _set_admin_status(email: str, is_admin: bool) -> bool:
    """Set the admin status for a user. Returns True if successful."""
    factory = _get_session_factory()
    async with factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.is_admin = is_admin
            await session.commit()
            return True
        return False


async def _list_admin_users() -> list[UserInfo]:
    """List all admin users."""
    factory = _get_session_factory()
    async with factory() as session:
        result = await session.execute(select(User).where(User.is_admin == True))  # noqa: E712
        users = result.scalars().all()
        return [
            UserInfo(email=u.email, display_name=u.display_name, is_admin=u.is_admin) for u in users
        ]


@app.command()
def promote(
    email: Annotated[str, typer.Argument(help="Email address of the user to promote")],
) -> None:
    """Promote a user to admin status."""
    user = asyncio.run(_get_user_by_email(email))
    if not user:
        typer.echo(f"Error: User with email '{email}' not found.", err=True)
        raise typer.Exit(1)

    if user.is_admin:
        typer.echo(f"User '{email}' is already an admin.")
        return

    asyncio.run(_set_admin_status(email, is_admin=True))
    typer.echo(f"Successfully promoted '{email}' to admin.")


@app.command()
def demote(
    email: Annotated[str, typer.Argument(help="Email address of the user to demote")],
) -> None:
    """Remove admin status from a user."""
    user = asyncio.run(_get_user_by_email(email))
    if not user:
        typer.echo(f"Error: User with email '{email}' not found.", err=True)
        raise typer.Exit(1)

    if not user.is_admin:
        typer.echo(f"User '{email}' is not an admin.")
        return

    asyncio.run(_set_admin_status(email, is_admin=False))
    typer.echo(f"Successfully demoted '{email}' from admin.")


@app.command(name="list")
def list_admins() -> None:
    """List all admin users."""
    admins = asyncio.run(_list_admin_users())

    if not admins:
        typer.echo("No admin users found.")
        return

    typer.echo(f"Admin users ({len(admins)}):")
    for admin in admins:
        display = admin.display_name or "(no display name)"
        typer.echo(f"  - {admin.email} ({display})")


if __name__ == "__main__":
    app()
