# Guide: Database Schema & Alembic Migrations

## 1. Architecture Overview

Varistha uses **SQLAlchemy 2.0 (asyncio)** with PostgreSQL 16 (+pgvector) in production and `aiosqlite` for in-memory testing.

- **Base Class**: `shared.db.base.Base` (subclassing `DeclarativeBase`).
- **Timestamps**: `shared.db.base.TimestampMixin` provides timezone-aware UTC `created_at` and `updated_at`.
- **Primary Keys**: Standard UUIDv4 via `sqlalchemy.Uuid`.
- **JSON Storage**: `JSON().with_variant(JSONB, "postgresql")` ensures native PostgreSQL JSONB support while maintaining SQLite test compatibility.
- **Relationships**: Configured with `lazy="selectin"` to guarantee safe asynchronous loading without `MissingGreenlet` errors.

---

## 2. Core Entities

```
+--------------------+            1:N           +--------------------+
|       Agent        |------------------------->|    AgentVersion    |
| (name, stage, ...) |                          | (spec snapshot)    |
+--------------------+                          +--------------------+
          |                                               |
          | 1:N                                           | 1:N
          v                                               v
+--------------------+            1:N           +--------------------+
|        Run         |------------------------->|        Span        |
| (status, cost, ...) |                          | (trace_id, span_id)|
+--------------------+                          +--------------------+
```

---

## 3. Creating & Running Migrations

Alembic configuration is housed in `apps/api/`:
- Configuration: `apps/api/alembic.ini`
- Environment: `apps/api/alembic/env.py` (automatically detects sync vs. async connection URLs)
- Versions: `apps/api/alembic/versions/`

### Apply migrations:
```bash
cd apps/api
uv run alembic upgrade head
```

### Rollback the last migration:
```bash
cd apps/api
uv run alembic downgrade -1
```

### Create a new migration:
```bash
cd apps/api
uv run alembic revision -m "add_table_or_column"
```

---

## 4. Testing Migrations & DB Models

Unit tests execute asynchronously against SQLite in-memory without needing a running Postgres container:
```bash
uv run pytest apps/api/src/shared/tests/test_db_models.py
uv run pytest apps/api/src/shared/tests/test_migrations.py
```
