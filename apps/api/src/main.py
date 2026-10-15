"""Varistha Control Plane API — FastAPI application entry point."""

from fastapi import FastAPI
from registry.router import router as registry_router

app = FastAPI(
    title="Varistha Control Plane",
    description=(
        "Self-hostable control plane to build, run, monitor and govern "
        "AI agents (AI employees) for startups."
    ),
    version="0.1.0",
    license_info={"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
)

app.include_router(registry_router)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Return API health status."""
    return {"status": "healthy", "service": "varistha-api"}


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    """Return API root information."""
    return {
        "name": "Varistha Control Plane API",
        "version": "0.1.0",
        "docs": "/docs",
    }
