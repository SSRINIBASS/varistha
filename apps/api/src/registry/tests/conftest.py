"""Fixtures for registry API integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import shared.db.models  # noqa: F401  # pyright: ignore[reportUnusedImport]
from httpx import ASGITransport, AsyncClient
from main import app
from shared.db.base import Base
from shared.db.session import get_db_session
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient with an isolated in-memory SQLite database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
