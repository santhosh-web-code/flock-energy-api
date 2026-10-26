"""
Configuration management for the Flock Energy API service.
Reads environment variables with fallback defaults and supports easy test overrides.
"""

from functools import lru_cache
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


class Settings(BaseModel):
    """Application and legacy portal configuration settings."""

    app_name: str = Field(
        default="Flock Energy - Urja Meter Ops API",
        description="Application title displayed in OpenAPI documentation",
    )
    app_version: str = Field(
        default="1.0.0",
        description="Current semantic version of the service",
    )
    app_description: str = Field(
        default="Clean, documented REST API wrapper around the Urja Meter Ops legacy portal.",
        description="Application overview displayed in OpenAPI documentation",
    )
    app_env: str = Field(
        default_factory=lambda: os.getenv("APP_ENV", "development"),
        description="Operating environment (development, test, production)",
    )

    # Legacy portal connection settings - never hardcoded
    portal_base_url: str = Field(
        default_factory=lambda: os.getenv("PORTAL_BASE_URL", ""),
        description="Base URL for the legacy Urja Meter Ops portal",
    )
    portal_username: str = Field(
        default_factory=lambda: os.getenv("PORTAL_USERNAME", ""),
        description="Username for authenticating against the legacy portal",
    )
    portal_password: str = Field(
        default_factory=lambda: os.getenv("PORTAL_PASSWORD", ""),
        description="Password for authenticating against the legacy portal",
    )

    model_config = {
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor.
    Can be overridden or cleared (get_settings.cache_clear()) during testing.
    """
    return Settings()
