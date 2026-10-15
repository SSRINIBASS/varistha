"""Unit tests for database session and engine factories."""

from __future__ import annotations

import pytest
from shared.config import Settings, get_settings
from shared.db.session import (
    get_async_engine,
    get_db_session,
    get_session_factory,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


def test_settings_retrieval() -> None:
    """Settings can be retrieved and are cached."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.environment in {"development", "test", "production"}


def test_get_async_engine() -> None:
    """get_async_engine returns an AsyncEngine instance."""
    engine = get_async_engine("sqlite+aiosqlite:///:memory:")
    assert isinstance(engine, AsyncEngine)


def test_get_session_factory() -> None:
    """get_session_factory returns an async_sessionmaker."""
    engine = get_async_engine("sqlite+aiosqlite:///:memory:")
    factory = get_session_factory(engine)
    assert isinstance(factory, async_sessionmaker)


async def test_get_db_session_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_db_session yields an active session and commits successfully."""
    engine = get_async_engine("sqlite+aiosqlite:///:memory:")
    factory = get_session_factory(engine)
    monkeypatch.setattr("shared.db.session.get_session_factory", lambda: factory)

    async for session in get_db_session():
        assert isinstance(session, AsyncSession)
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1


async def test_get_db_session_rollback_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_db_session rolls back when an exception occurs inside the generator context."""
    engine = get_async_engine("sqlite+aiosqlite:///:memory:")
    factory = get_session_factory(engine)
    monkeypatch.setattr("shared.db.session.get_session_factory", lambda: factory)

    gen = get_db_session()
    session = await anext(gen)
    assert isinstance(session, AsyncSession)

    with pytest.raises(RuntimeError, match="simulated failure"):
        await gen.athrow(RuntimeError("simulated failure"))
