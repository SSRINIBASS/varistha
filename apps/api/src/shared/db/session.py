"""Database engine and session management."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from shared.config import get_settings
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import Pool

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@event.listens_for(Pool, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """Enable foreign key support for SQLite connections."""
    if hasattr(dbapi_connection, "_connection") and hasattr(dbapi_connection._connection, "_conn"):
        with contextlib.suppress(Exception):
            dbapi_connection._connection._conn.execute("PRAGMA foreign_keys=ON")
    elif hasattr(dbapi_connection, "cursor"):
        with contextlib.suppress(Exception):
            cursor = dbapi_connection.cursor()
            if not hasattr(cursor, "__await__"):
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()


def get_async_engine(database_url: str | None = None) -> AsyncEngine:
    """Create and return an async SQLAlchemy engine."""
    url = database_url or get_settings().database_url
    return create_async_engine(
        url,
        echo=False,
        future=True,
    )


def get_session_factory(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Create and return an async session maker."""
    eng = engine or get_async_engine()
    return async_sessionmaker(
        bind=eng,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
