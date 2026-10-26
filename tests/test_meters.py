"""
Automated unit and integration tests for UrjaPortalClient and /api/v1/meters endpoint.
All tests use mocked HTTPX transports and dependency injection — no live portal dependency.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.client import (
    PortalAuthenticationError,
    PortalConfigurationError,
    PortalResponseError,
    PortalTimeoutError,
    PortalUpstreamError,
    UrjaPortalClient,
)
from app.main import app, get_portal_client


# Sample verified test payload matching the Urja portal structure
SAMPLE_METER_PAYLOAD = {
    "data": [
        {
            "meterId": "MTR-10023",
            "serialNo": "SN-8839201",
            "make": "Secure Meters",
            "phaseType": "1-phase",
            "installStatus": "installed",
            "dtCode": "DT-NORTH-04",
        },
        {
            "meterId": "MTR-10024",
            "serialNo": "SN-8839202",
            "make": "Schneider",
            "phaseType": "3-phase",
            "installStatus": "installed",
            "dtCode": "DT-SOUTH-01",
        },
    ],
    "total": 403,
    "page": 1,
    "pageSize": 20,
}


# =====================================================================
# UrjaPortalClient Unit Tests (MockTransport)
# =====================================================================

@pytest.mark.asyncio
async def test_client_login_success():
    """Verify login handles the JSON redirect response and saves session token."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/login"
        assert request.method == "POST"
        return httpx.Response(
            status_code=200,
            json={"type": "redirect", "status": 303, "location": "/meters"},
            headers={
                "Set-Cookie": "__Secure-better-auth.session_token=test_token_abc123; Path=/; HttpOnly; Secure"
            },
        )

    transport = httpx.MockTransport(handler)
    client = UrjaPortalClient(
        base_url="https://test-portal.local",
        username="operator@urja.local",
        password="test-password",
    )
    # Inject mock transport into client
    client._client = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
    )

    result = await client.login()
    assert result is True
    assert client._is_authenticated is True
    await client.aclose()


@pytest.mark.asyncio
async def test_client_login_invalid_credentials():
    """Verify 401 response raises PortalAuthenticationError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            json={"error": "Invalid email or password"},
        )

    transport = httpx.MockTransport(handler)
    client = UrjaPortalClient(
        base_url="https://test-portal.local",
        username="wrong@urja.local",
        password="wrong-password",
    )
    client._client = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
    )

    with pytest.raises(PortalAuthenticationError) as exc_info:
        await client.login()
    assert "rejected invalid credentials" in str(exc_info.value)
    assert client._is_authenticated is False
    await client.aclose()


@pytest.mark.asyncio
async def test_client_login_missing_credentials():
    """Verify missing username/password raises PortalConfigurationError."""
    client = UrjaPortalClient(base_url="https://test-portal.local", username="", password="")
    with pytest.raises(PortalConfigurationError):
        await client.login()


@pytest.mark.asyncio
async def test_client_get_meters_success():
    """Verify get_meters fetches and returns parsed meter records."""
    call_count = {"login": 0, "meters": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/login":
            call_count["login"] += 1
            return httpx.Response(
                status_code=200,
                json={"type": "redirect", "status": 303, "location": "/meters"},
                headers={"Set-Cookie": "__Secure-better-auth.session_token=tok; Path=/"},
            )
        if request.url.path == "/portal/meters/search":
            call_count["meters"] += 1
            assert request.url.params["q"] == "SN-883"
            assert request.url.params["page"] == "2"
            return httpx.Response(status_code=200, json=SAMPLE_METER_PAYLOAD)
        return httpx.Response(status_code=404)

    transport = httpx.MockTransport(handler)
    client = UrjaPortalClient(
        base_url="https://test-portal.local",
        username="operator@urja.local",
        password="test-password",
    )
    client._client = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
    )

    result = await client.get_meters(q="SN-883", page=2)
    assert call_count["login"] == 1
    assert call_count["meters"] == 1
    assert len(result["data"]) == 2
    assert result["total"] == 403
    await client.aclose()


@pytest.mark.asyncio
async def test_client_session_expiry_triggers_reauth():
    """Verify client re-authenticates once if session expires (401 on search)."""
    search_attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal search_attempts
        if request.url.path == "/login":
            return httpx.Response(
                status_code=200,
                json={"type": "redirect", "status": 303, "location": "/meters"},
                headers={"Set-Cookie": "__Secure-better-auth.session_token=new_tok; Path=/"},
            )
        if request.url.path == "/portal/meters/search":
            search_attempts += 1
            if search_attempts == 1:
                # First attempt: session expired
                return httpx.Response(status_code=401, json={"error": "Session expired"})
            # Second attempt: after re-auth, succeed
            return httpx.Response(status_code=200, json=SAMPLE_METER_PAYLOAD)
        return httpx.Response(status_code=404)

    transport = httpx.MockTransport(handler)
    client = UrjaPortalClient(
        base_url="https://test-portal.local",
        username="operator@urja.local",
        password="test-password",
    )
    client._client = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
    )
    # Assume pre-authenticated
    client._is_authenticated = True

    result = await client.get_meters()
    assert search_attempts == 2
    assert len(result["data"]) == 2
    await client.aclose()


@pytest.mark.asyncio
async def test_client_timeout_handling():
    """Verify timeout translates to PortalTimeoutError."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Connection timed out", request=request)

    transport = httpx.MockTransport(handler)
    client = UrjaPortalClient(
        base_url="https://test-portal.local",
        username="operator@urja.local",
        password="test-password",
    )
    client._client = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
    )
    client._is_authenticated = True

    with pytest.raises(PortalTimeoutError):
        await client.get_meters()
    await client.aclose()


@pytest.mark.asyncio
async def test_client_upstream_server_error():
    """Verify 500 response raises PortalUpstreamError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    client = UrjaPortalClient(
        base_url="https://test-portal.local",
        username="operator@urja.local",
        password="test-password",
    )
    client._client = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
    )
    client._is_authenticated = True

    with pytest.raises(PortalUpstreamError):
        await client.get_meters()
    await client.aclose()


@pytest.mark.asyncio
async def test_client_malformed_response():
    """Verify invalid structure raises PortalResponseError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, json={"unexpectedKey": []})

    transport = httpx.MockTransport(handler)
    client = UrjaPortalClient(
        base_url="https://test-portal.local",
        username="operator@urja.local",
        password="test-password",
    )
    client._client = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
    )
    client._is_authenticated = True

    with pytest.raises(PortalResponseError):
        await client.get_meters()
    await client.aclose()


# =====================================================================
# FastAPI Route Integration Tests (TestClient)
# =====================================================================

class MockPortalClient:
    """Mock client for testing route handling and error mapping."""

    def __init__(self, mode: str = "success"):
        self.mode = mode

    async def get_meters(self, q: str = "", page: int = 1):
        if self.mode == "success":
            return SAMPLE_METER_PAYLOAD
        if self.mode == "auth_error":
            raise PortalAuthenticationError("Upstream authentication rejected")
        if self.mode == "timeout":
            raise PortalTimeoutError("Upstream request timed out after 15.0s")
        if self.mode == "server_error":
            raise PortalUpstreamError("Upstream portal returned 500")
        if self.mode == "malformed":
            raise PortalResponseError("Upstream returned invalid payload")
        raise RuntimeError("Unknown mode")


def test_api_get_meters_success():
    """Verify GET /api/v1/meters returns 200 with typed meter list."""
    app.dependency_overrides[get_portal_client] = lambda: MockPortalClient("success")
    test_client = TestClient(app)

    response = test_client.get("/api/v1/meters?q=SN-883&page=1")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 2
    assert data["total"] == 403
    assert data["page"] == 1
    assert data["pageSize"] == 20

    first_meter = data["data"][0]
    assert first_meter["meterId"] == "MTR-10023"
    assert first_meter["serialNo"] == "SN-8839201"
    assert first_meter["make"] == "Secure Meters"
    assert first_meter["phaseType"] == "1-phase"
    assert first_meter["installStatus"] == "installed"
    assert first_meter["dtCode"] == "DT-NORTH-04"

    app.dependency_overrides.clear()


def test_api_get_meters_auth_failure_returns_502():
    """Verify upstream auth failure maps to HTTP 502 Bad Gateway."""
    app.dependency_overrides[get_portal_client] = lambda: MockPortalClient("auth_error")
    test_client = TestClient(app)

    response = test_client.get("/api/v1/meters")
    assert response.status_code == 502
    data = response.json()
    assert data["errorType"] == "PortalAuthenticationError"
    assert "authentication rejected" in data["detail"]

    app.dependency_overrides.clear()


def test_api_get_meters_timeout_returns_504():
    """Verify upstream timeout maps to HTTP 504 Gateway Timeout."""
    app.dependency_overrides[get_portal_client] = lambda: MockPortalClient("timeout")
    test_client = TestClient(app)

    response = test_client.get("/api/v1/meters")
    assert response.status_code == 504
    data = response.json()
    assert data["errorType"] == "PortalTimeoutError"
    assert "timed out" in data["detail"]

    app.dependency_overrides.clear()


def test_api_get_meters_upstream_server_error_returns_502():
    """Verify upstream 5xx maps to HTTP 502 Bad Gateway."""
    app.dependency_overrides[get_portal_client] = lambda: MockPortalClient("server_error")
    test_client = TestClient(app)

    response = test_client.get("/api/v1/meters")
    assert response.status_code == 502
    data = response.json()
    assert data["errorType"] == "PortalUpstreamError"

    app.dependency_overrides.clear()


def test_api_get_meters_malformed_response_returns_502():
    """Verify upstream malformed payload maps to HTTP 502 Bad Gateway."""
    app.dependency_overrides[get_portal_client] = lambda: MockPortalClient("malformed")
    test_client = TestClient(app)

    response = test_client.get("/api/v1/meters")
    assert response.status_code == 502
    data = response.json()
    assert data["errorType"] == "PortalResponseError"

    app.dependency_overrides.clear()
