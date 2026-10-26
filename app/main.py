"""
Main FastAPI application entrypoint for Flock Energy - Urja Meter Ops API.
Provides service metadata, health check endpoint, and Swagger/OpenAPI documentation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import get_settings
from app.models import HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown hooks.
    Ensures safe resource allocation and teardown.
    """
    # Startup actions
    yield
    # Shutdown actions


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns the operational status, version, and identity of the Flock Energy API service.",
    tags=["Health & Status"],
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify that the service is running and responsive.
    """
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        service=settings.app_name,
    )
