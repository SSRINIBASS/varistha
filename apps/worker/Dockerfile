FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/
COPY apps/worker/pyproject.toml apps/worker/
COPY packages/spec/pyproject.toml packages/spec/
COPY packages/sdk/pyproject.toml packages/sdk/
COPY packages/cli/pyproject.toml packages/cli/

RUN uv sync --package varistha-worker --no-dev --frozen

COPY apps/api/src/ apps/api/src/
COPY apps/worker/src/ apps/worker/src/
COPY packages/spec/src/ packages/spec/src/
COPY packages/sdk/src/ packages/sdk/src/

CMD ["uv", "run", "--package", "varistha-worker", "python", "-m", "src.worker"]
