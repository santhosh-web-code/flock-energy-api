"""
Data schemas and models for the Flock Energy API service.
Defines strongly typed Pydantic models for health checks, meter records, and pagination.
"""

from typing import List, Optional
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


class MeterRecord(BaseModel):
    """
    Representation of a single smart meter record from the Urja Meter Ops portal.
    Verified empirically via portal API inspection.
    """

    meter_id: str = Field(
        ...,
        alias="meterId",
        description="Unique identifier assigned to the meter",
        examples=["MTR-10023"],
    )
    serial_no: str = Field(
        ...,
        alias="serialNo",
        description="Manufacturer hardware serial number",
        examples=["SN-8839201"],
    )
    make: str = Field(
        ...,
        description="Manufacturer or brand of the meter",
        examples=["Secure Meters"],
    )
    phase_type: str = Field(
        ...,
        alias="phaseType",
        description="Electrical phase configuration (e.g., 1-phase, 3-phase)",
        examples=["1-phase"],
    )
    install_status: str = Field(
        ...,
        alias="installStatus",
        description="Operational installation status of the meter",
        examples=["installed"],
    )
    dt_code: Optional[str] = Field(
        default=None,
        alias="dtCode",
        description="Associated Distribution Transformer (DT) network code",
        examples=["DT-NORTH-04"],
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "meterId": "MTR-10023",
                    "serialNo": "SN-8839201",
                    "make": "Secure Meters",
                    "phaseType": "1-phase",
                    "installStatus": "installed",
                    "dtCode": "DT-NORTH-04",
                }
            ]
        },
    }


class MeterListResponse(BaseModel):
    """Paginated list response containing meter records and metadata."""

    data: List[MeterRecord] = Field(
        ...,
        description="List of smart meter records for the current page",
    )
    total: int = Field(
        ...,
        description="Total count of meters matching the search query",
        examples=[403],
    )
    page: int = Field(
        ...,
        description="Current page number (1-indexed)",
        examples=[1],
    )
    page_size: int = Field(
        ...,
        alias="pageSize",
        description="Number of records per page",
        examples=[20],
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "data": [
                        {
                            "meterId": "MTR-10023",
                            "serialNo": "SN-8839201",
                            "make": "Secure Meters",
                            "phaseType": "1-phase",
                            "installStatus": "installed",
                            "dtCode": "DT-NORTH-04",
                        }
                    ],
                    "total": 403,
                    "page": 1,
                    "pageSize": 20,
                }
            ]
        },
    }


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    detail: str = Field(
        ...,
        description="Human-readable description of the error",
        examples=["Upstream portal authentication failed"],
    )
    error_type: Optional[str] = Field(
        default=None,
        alias="errorType",
        description="Classification or category of the error",
        examples=["UpstreamAuthenticationError"],
    )

    model_config = {
        "populate_by_name": True,
    }
