"""Fixtures for runtime tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import shared.db.models  # noqa: F401  # pyright: ignore[reportUnusedImport]
from httpx import ASGITransport, AsyncClient
from main import app
from runtime.mock import MockRuntime
from runtime.router import get_runtime
from shared.db.base import Base
from shared.db.session import get_db_session
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@pytest.fixture
def mock_runtime() -> MockRuntime:
    """Provide a mock runtime instance."""
    return MockRuntime()


@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Provide an isolated in-memory SQLite engine with fresh schema."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def session_factory(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Provide a sessionmaker connected to the test database."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a direct DB session for unit tests."""
    async with session_factory() as session:
        yield session


@pytest.fixture
async def async_client(
    test_engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
    mock_runtime: MockRuntime,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient with an isolated in-memory SQLite database and MockRuntime."""

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_get_db_session
    app.dependency_overrides[get_runtime] = lambda: mock_runtime

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
