"""
Client module for interacting with the legacy Urja Meter Ops web portal.
Manages persistent HTTPX sessions, cookie-based authentication, and upstream requests.
"""

import asyncio
from typing import Any, Dict, Optional
import httpx


class PortalClientError(Exception):
    """Base exception for Urja portal client operations."""


class PortalConfigurationError(PortalClientError):
    """Raised when portal credentials or required configuration are missing."""


class PortalAuthenticationError(PortalClientError):
    """Raised when upstream authentication fails or credentials are invalid."""


class PortalTimeoutError(PortalClientError):
    """Raised when an upstream request times out."""


class PortalUpstreamError(PortalClientError):
    """Raised when the upstream portal returns 5xx or network connection fails."""


class PortalResponseError(PortalClientError):
    """Raised when the upstream portal returns malformed or unexpected response structure."""


class UrjaPortalClient:
    """
    HTTP client abstraction for the legacy Urja Meter Ops portal.

    Features:
    - Persistent HTTPX AsyncClient with automatic cookie management.
    - Handles JSON-body redirect login protocol and session cookie persistence.
    - Automatic session re-authentication with protection against infinite retry loops.
    - Robust error mapping (timeouts, 5xx, auth failures, malformed payloads).
    - Safe credential handling (never logged or exposed in string representations).
    """

    SESSION_COOKIE_NAME = "__Secure-better-auth.session_token"

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
            username: Operator email/username for authentication.
            password: Operator password for authentication (never logged).
            timeout: HTTP request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self._password = password
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._is_authenticated: bool = False
        self._auth_lock = asyncio.Lock()

    def __repr__(self) -> str:
        """Safe representation without exposing secrets."""
        return (
            f"<UrjaPortalClient base_url='{self.base_url}' "
            f"username='{self.username}' authenticated={self._is_authenticated}>"
        )

    async def get_client(self) -> httpx.AsyncClient:
        """
        Lazily initialize and return the underlying HTTPX AsyncClient.
        Maintains persistent cookies across requests.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url if self.base_url else None,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "User-Agent": "FlockEnergy-UrjaAPI/1.0",
                    "Accept": "application/json",
                },
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
        self._is_authenticated = False

    async def __aenter__(self) -> "UrjaPortalClient":
        """Async context manager entry."""
        await self.get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit ensuring clean resource shutdown."""
        await self.aclose()

    async def login(self) -> bool:
        """
        Authenticate against the legacy Urja Meter Ops portal.

        Protocol:
        - POST /login with JSON payload: {"email": username, "password": password}
        - Expects response with session cookie (__Secure-better-auth.session_token)
          and JSON body like {"type": "redirect", "status": 303, "location": "/meters"}
        """
        if not self.username or not self._password:
            raise PortalConfigurationError(
                "Upstream portal credentials are not configured. "
                "Set PORTAL_USERNAME and PORTAL_PASSWORD environment variables."
            )

        client = await self.get_client()
        login_url = f"{self.base_url}/login" if self.base_url else "/login"

        try:
            response = await client.post(
                login_url,
                json={"email": self.username, "password": self._password},
                headers={"Content-Type": "application/json"},
            )
        except httpx.TimeoutException as e:
            raise PortalTimeoutError(
                f"Upstream portal authentication timed out after {self.timeout}s"
            ) from e
        except httpx.RequestError as e:
            raise PortalUpstreamError(
                f"Connection error during upstream authentication: {str(e)}"
            ) from e

        # Handle authentication failure status
        if response.status_code in (401, 403):
            self._is_authenticated = False
            raise PortalAuthenticationError(
                "Upstream portal authentication rejected invalid credentials (401/403)."
            )

        if response.status_code >= 500:
            self._is_authenticated = False
            raise PortalUpstreamError(
                f"Upstream portal returned server error during login ({response.status_code})."
            )

        # Inspect response content and cookies
        try:
            body = response.json()
        except Exception as e:
            # If body is not JSON but status is success, check cookies
            body = {}

        # The portal returns {"type":"redirect","status":303,"location":"/meters"}
        is_redirect_json = isinstance(body, dict) and body.get("type") == "redirect"
        has_session_cookie = self.SESSION_COOKIE_NAME in client.cookies or any(
            c.name == self.SESSION_COOKIE_NAME for c in response.cookies.jar
        )

        if response.is_success or response.status_code == 303 or is_redirect_json or has_session_cookie:
            self._is_authenticated = True
            return True

        self._is_authenticated = False
        raise PortalAuthenticationError(
            f"Unexpected login response from upstream portal (status {response.status_code})."
        )

    async def ensure_authenticated(self) -> None:
        """
        Ensure the client is authenticated before making requests.
        Uses an asyncio Lock to avoid concurrent redundant logins.
        """
        if not self._is_authenticated:
            async with self._auth_lock:
                if not self._is_authenticated:
                    await self.login()

    async def get_meters(
        self,
        q: str = "",
        page: int = 1,
        _retry_auth: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve paginated meters from the legacy portal.

        Verified Upstream Endpoint:
        GET /portal/meters/search?q={q}&page={page}

        Response format:
        {"data": [...], "total": 403, "page": 1, "pageSize": 20}
        """
        await self.ensure_authenticated()
        client = await self.get_client()

        meters_url = (
            f"{self.base_url}/portal/meters/search"
            if self.base_url
            else "/portal/meters/search"
        )
        params = {"q": q, "page": page}

        try:
            response = await client.get(meters_url, params=params)
        except httpx.TimeoutException as e:
            raise PortalTimeoutError(
                f"Upstream portal request timed out after {self.timeout}s"
            ) from e
        except httpx.RequestError as e:
            raise PortalUpstreamError(
                f"Connection error querying upstream meters: {str(e)}"
            ) from e

        # Handle session expiration or unauthorized response
        if response.status_code in (401, 403):
            if _retry_auth:
                # Session may have expired - attempt re-authentication once
                self._is_authenticated = False
                await self.login()
                return await self.get_meters(q=q, page=page, _retry_auth=False)
            raise PortalAuthenticationError(
                "Upstream portal session expired and re-authentication failed."
            )

        # Check for unexpected upstream server errors
        if response.status_code >= 500:
            raise PortalUpstreamError(
                f"Upstream portal server error ({response.status_code}) while fetching meters."
            )

        if response.status_code != 200:
            raise PortalUpstreamError(
                f"Upstream portal returned unexpected status ({response.status_code}) while fetching meters."
            )

        # Parse JSON response
        try:
            payload = response.json()
        except Exception as e:
            raise PortalResponseError(
                "Upstream portal returned a non-JSON or malformed response."
            ) from e

        # Validate that the expected payload keys are present
        if not isinstance(payload, dict) or "data" not in payload:
            raise PortalResponseError(
                "Upstream portal response schema missing expected 'data' list."
            )

        return payload
