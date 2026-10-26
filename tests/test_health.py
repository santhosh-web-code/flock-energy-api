"""
Automated tests for health check and API documentation endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_status_code():
    """Verify that GET /health returns HTTP 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_body():
    """Verify that GET /health returns the expected JSON payload schema."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert data["service"] == "Flock Energy - Urja Meter Ops API"


def test_docs_endpoint_available():
    """Verify that Swagger UI documentation is accessible at /docs."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_available():
    """Verify that OpenAPI schema JSON is served at /openapi.json."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Flock Energy - Urja Meter Ops API"
    assert schema["info"]["version"] == "1.0.0"
    assert "/health" in schema["paths"]
