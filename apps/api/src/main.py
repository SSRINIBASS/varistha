"""Varistha Control Plane API — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from governance.router import router as governance_router
from identity.router import router as identity_router
from observability.router import router as observability_router
from plugins.router import router as plugins_router
from registry.router import router as registry_router
from runtime.router import router as runtime_router

app = FastAPI(
    title="Varistha Control Plane",
    description=(
        "Self-hostable control plane to build, run, monitor and govern "
        "AI agents (AI employees) for startups."
    ),
    version="0.1.0",
    license_info={"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(registry_router)
app.include_router(runtime_router)
app.include_router(observability_router)
app.include_router(governance_router)
app.include_router(plugins_router)
app.include_router(identity_router)


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
