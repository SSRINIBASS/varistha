FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy workspace files
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/
COPY apps/worker/pyproject.toml apps/worker/
COPY packages/spec/pyproject.toml packages/spec/
COPY packages/sdk/pyproject.toml packages/sdk/
COPY packages/cli/pyproject.toml packages/cli/

# Install dependencies (no dev dependencies in production)
RUN uv sync --package varistha-api --no-dev --frozen

# Copy application source
COPY apps/api/src/ apps/api/src/
COPY packages/spec/src/ packages/spec/src/
COPY packages/sdk/src/ packages/sdk/src/

ENV PYTHONPATH="/app/apps/api/src:/app/packages/spec/src:/app/packages/sdk/src"

EXPOSE 8000

CMD ["uv", "run", "--package", "varistha-api", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
