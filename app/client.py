"""
Client module for interacting with the legacy Urja Meter Ops web portal.

NOTE ON STEP 1 ARCHITECTURE:
This is an architectural placeholder for the UrjaPortalClient. Upstream authentication,
session cookie handling, HTML parsing, and meter extraction endpoints are intentionally
deferred until Step 2, when the live portal behavior and network traffic are inspected.
"""

from typing import Optional
import httpx


class UrjaPortalClient:
    """
    HTTP client abstraction for the legacy Urja Meter Ops portal.

    Provides a clean interface for asynchronous HTTP interactions with configurable
    timeouts and resource cleanup.
    """

    def __init__(
        self,
        base_url: str,
        username: str = "",
        password: str = "",
        timeout: float = 15.0,
    ) -> None:
        """
        Initialize the portal client.

        Args:
            base_url: Base URL of the Urja Meter Ops portal.
            username: Username for portal authentication (never logged).
            password: Password for portal authentication (never logged).
            timeout: HTTP request timeout in seconds (default: 15.0).
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self._password = password
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """
        Lazily initialize and return the underlying HTTPX AsyncClient.
        Re-instantiates if the client was previously closed.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url if self.base_url else None,
                timeout=httpx.Timeout(self.timeout),
                headers={"User-Agent": "FlockEnergy-UrjaAPI/1.0 (Integration Client)"},
                follow_redirects=True,
            )
        return self._client

    async def aclose(self) -> None:
        """
        Safely terminate the underlying HTTPX AsyncClient session
        and release active connection pools.
        """
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "UrjaPortalClient":
        """Async context manager entry."""
        await self.get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit ensuring clean resource shutdown."""
        await self.aclose()
