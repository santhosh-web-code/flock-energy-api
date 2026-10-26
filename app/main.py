"""
Main FastAPI application entrypoint for Flock Energy - Urja Meter Ops API.
Provides service metadata, health check endpoint, meter search/pagination,
and Swagger/OpenAPI documentation.
"""

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import Depends, FastAPI, Query, status
from fastapi.responses import JSONResponse

from app.client import (
    PortalAuthenticationError,
    PortalConfigurationError,
    PortalResponseError,
    PortalTimeoutError,
    PortalUpstreamError,
    UrjaPortalClient,
)
from app.config import Settings, get_settings
from app.models import ErrorResponse, HealthResponse, MeterListResponse

settings = get_settings()

_portal_client: Optional[UrjaPortalClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown hooks.
    Ensures safe resource allocation and teardown of the persistent HTTP client.
    """
    global _portal_client
    current_settings = get_settings()
    _portal_client = UrjaPortalClient(
        base_url=current_settings.portal_base_url,
        username=current_settings.portal_username,
        password=current_settings.portal_password,
        timeout=current_settings.portal_timeout_seconds,
    )
    yield
    if _portal_client is not None:
        await _portal_client.aclose()
        _portal_client = None


def get_portal_client(
    current_settings: Settings = Depends(get_settings),
) -> UrjaPortalClient:
    """
    FastAPI dependency returning the UrjaPortalClient instance.
    Can be easily overridden in tests via app.dependency_overrides[get_portal_client].
    """
    global _portal_client
    if _portal_client is None:
        _portal_client = UrjaPortalClient(
            base_url=current_settings.portal_base_url,
            username=current_settings.portal_username,
            password=current_settings.portal_password,
            timeout=current_settings.portal_timeout_seconds,
        )
    return _portal_client


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    responses={
        502: {
            "model": ErrorResponse,
            "description": "Bad Gateway - Upstream portal error or authentication failure",
        },
        504: {
            "model": ErrorResponse,
            "description": "Gateway Timeout - Upstream portal request timed out",
        },
    },
)


@app.exception_handler(PortalAuthenticationError)
async def portal_auth_error_handler(request, exc: PortalAuthenticationError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "errorType": "PortalAuthenticationError"},
    )


@app.exception_handler(PortalConfigurationError)
async def portal_config_error_handler(request, exc: PortalConfigurationError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc), "errorType": "PortalConfigurationError"},
    )


@app.exception_handler(PortalTimeoutError)
async def portal_timeout_error_handler(request, exc: PortalTimeoutError):
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"detail": str(exc), "errorType": "PortalTimeoutError"},
    )


@app.exception_handler(PortalResponseError)
async def portal_response_error_handler(request, exc: PortalResponseError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "errorType": "PortalResponseError"},
    )


@app.exception_handler(PortalUpstreamError)
async def portal_upstream_error_handler(request, exc: PortalUpstreamError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "errorType": "PortalUpstreamError"},
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


@app.get(
    "/api/v1/meters",
    response_model=MeterListResponse,
    summary="List and Search Smart Meters",
    description=(
        "Retrieves a paginated list of smart meters from the Urja Meter Ops legacy portal. "
        "Supports optional keyword search filtering and pagination."
    ),
    tags=["Meters"],
)
async def list_meters(
    q: str = Query(
        default="",
        description="Search term to filter meters (e.g., serial number or meter ID)",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number to retrieve (1-indexed)",
    ),
    portal_client: UrjaPortalClient = Depends(get_portal_client),
) -> MeterListResponse:
    """
    Fetch meters from the legacy portal via the UrjaPortalClient.
    """
    raw_response = await portal_client.get_meters(q=q, page=page)
    return MeterListResponse.model_validate(raw_response)
