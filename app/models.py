"""
Data schemas and models for the Flock Energy API service.
Initial models are strictly limited to core service responses.
Legacy meter/consumption models will only be added after inspecting the upstream portal.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema indicating service availability and metadata."""

    status: str = Field(
        ...,
        description="Current health status of the API service",
        examples=["ok"],
    )
    version: str = Field(
        ...,
        description="Running API version",
        examples=["1.0.0"],
    )
    service: str = Field(
        ...,
        description="Service name identifier",
        examples=["Flock Energy - Urja Meter Ops API"],
    )
