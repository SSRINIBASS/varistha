"""Integration test for Alembic database migrations."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_migrations_upgrade_and_downgrade(tmp_path: Path) -> None:
    """Alembic migrations upgrade to head, downgrade to base, and re-upgrade cleanly."""
    db_file = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    api_dir = Path(__file__).resolve().parents[3]
    alembic_ini_path = api_dir / "alembic.ini"
    alembic_script_path = api_dir / "alembic"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    alembic_cfg.set_main_option("script_location", str(alembic_script_path))

    # 1. Upgrade to head
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "agents" in table_names
    assert "agent_versions" in table_names
    assert "runs" in table_names
    assert "spans" in table_names
    assert "alembic_version" in table_names

    # Check columns on agents table
    columns = {c["name"] for c in inspector.get_columns("agents")}
    assert {
        "id",
        "name",
        "description",
        "owner",
        "stage",
        "current_version",
        "created_at",
        "updated_at",
    }.issubset(columns)

    # 2. Downgrade to base
    command.downgrade(alembic_cfg, "base")
    inspector = inspect(engine)
    tables_after_downgrade = set(inspector.get_table_names())

    assert "agents" not in tables_after_downgrade
    assert "agent_versions" not in tables_after_downgrade
    assert "runs" not in tables_after_downgrade
    assert "spans" not in tables_after_downgrade

    # 3. Upgrade back to head to verify idempotency
    command.upgrade(alembic_cfg, "head")
    inspector = inspect(engine)
    assert "agents" in inspector.get_table_names()

    engine.dispose()


def test_alembic_async_url_migrations(tmp_path: Path) -> None:
    """Alembic migrations execute correctly when configured with an async engine URL."""
    db_file = tmp_path / "test_async_migration.db"
    async_db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    sync_db_url = f"sqlite:///{db_file.as_posix()}"

    api_dir = Path(__file__).resolve().parents[3]
    alembic_ini_path = api_dir / "alembic.ini"
    alembic_script_path = api_dir / "alembic"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", async_db_url)
    alembic_cfg.set_main_option("script_location", str(alembic_script_path))

    # Upgrade to head using async engine path
    command.upgrade(alembic_cfg, "head")

    # Verify tables created
    engine = create_engine(sync_db_url)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "agents" in table_names
    assert "agent_versions" in table_names
    assert "runs" in table_names
    assert "spans" in table_names

    # Downgrade to base using async engine path
    command.downgrade(alembic_cfg, "base")
    inspector = inspect(engine)
    assert "agents" not in set(inspector.get_table_names())

    engine.dispose()
