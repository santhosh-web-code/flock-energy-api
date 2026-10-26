# Flock Energy - Urja Meter Ops API

A production-minded, clean, and documented REST API wrapper built over the legacy **Urja Meter Ops** portal.

---

## 1. Project Objective

Electricity distribution utilities rely on the internal **Urja Meter Ops** web portal to inspect smart meters, locate them in the distribution network, and monitor telemetry. However, the legacy portal lacks an official programmatic API, leaving internal engineering, product, and analytics teams dependent on manual browser navigation and copy-pasting.

This service acts as a transparent, robust REST API adapter in front of the Urja Meter Ops portal:
- Authenticates securely against the legacy portal using operator credentials.
- Manages stateful session cookies (`__Secure-better-auth.session_token`) across requests.
- Handles transparent session re-authentication and upstream errors.
- Exposes typed, documented, and paginated JSON endpoints (`/api/v1/meters`).
- Protects downstream consumers from legacy upstream quirks.

---

## 2. Architecture & Design

The application follows a decoupled, layered architecture:

```
flock-energy-api/
├── app/
│   ├── __init__.py       # Package metadata and version definition
│   ├── main.py           # FastAPI application, route handlers, exception mapping, lifespan
│   ├── client.py         # UrjaPortalClient: persistent HTTPX client, cookie jar, auth & retries
│   ├── models.py         # Pydantic schemas: HealthResponse, MeterRecord, MeterListResponse, ErrorResponse
│   └── config.py         # Settings loaded from environment variables with python-dotenv
├── tests/
│   ├── __init__.py       # Test package marker
│   ├── test_health.py    # Health check, Swagger docs, and OpenAPI schema tests
│   └── test_meters.py    # Unit & integration tests with mocked HTTPX transports (17 total tests)
├── .env.example          # Environment variables template with placeholders (no secrets committed)
├── .gitignore            # Git ignore rules for virtual environments, secrets, and caches
├── requirements.txt      # Pinned dependency definitions
├── README.md             # Project documentation and operational guide
├── PROTOCOL.md           # Empirical reverse-engineering findings and protocol analysis
├── REFLECTION.md         # Five candidate reflection questions and design retrospective
└── openapi.json          # Exported static OpenAPI 3.1.0 specification
```

### Architectural Highlights
- **FastAPI**: Provides high-performance asynchronous request handling and automated OpenAPI/Swagger documentation.
- **HTTPX Persistent Session**: Uses `httpx.AsyncClient` with a persistent cookie jar, enabling transparent transmission of the `__Secure-better-auth.session_token` cookie across operations.
- **Pydantic Validation**: All upstream data is validated against strongly typed Pydantic models with field aliasing (`meterId` <-> `meter_id`, `serialNo` <-> `serial_no`, etc.).
- **Decoupled Upstream Adapter**: The `UrjaPortalClient` is fully separated from FastAPI route handlers and injected via FastAPI's `Depends` system, making it easy to mock during automated testing.
- **Bounded Re-Authentication**: When an expired session returns 401/403, the client automatically re-authenticates once and retries the call. Retries are strictly bounded (`_retry_auth=False`) to prevent infinite loops.

---

## 3. Getting Started (Windows Setup Guide)

### Prerequisites
- **Python 3.11+** (Verified with Python 3.13 and 3.14 on 64-bit Windows)
- **Git**

### Installation Steps

1. **Navigate to the project root:**
   ```powershell
   cd "c:\Users\santh\Flock-Energy API"
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(If using Command Prompt `cmd`: `.\.venv\Scripts\activate.bat`)*

3. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 4. Configuration & Security

The service reads configuration parameters from environment variables or a local `.env` file using `python-dotenv`.

Copy `.env.example` to create your local `.env`:
```powershell
Copy-Item .env.example .env
```

Set your configuration values in `.env`:
```env
# Upstream Urja Meter Ops Portal
PORTAL_BASE_URL=https://urja-ops.flockenergy.tech
PORTAL_USERNAME=operator@urja.local
PORTAL_PASSWORD=your_actual_password_here
PORTAL_TIMEOUT_SECONDS=15.0

# Service Settings
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
```

> **Security Guardrail:** Credentials must only be configured in `.env` or system environment variables. Never commit `.env` to Git. The project `.gitignore` strictly ignores `.env*` files.

---

## 5. Running the Service

Start the local Uvicorn development server:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The service will be accessible at `http://127.0.0.1:8000`.

### Interactive API Documentation
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — Test endpoints directly in your browser.
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) — Clean documentation viewer.
- **OpenAPI Schema (JSON):** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 6. API Endpoints & Usage

### 1. Health Check
* **Path:** `GET /health`
* **Purpose:** Service liveness and version verification.
* **Curl Example:**
  ```bash
  curl -X GET http://127.0.0.1:8000/health
  ```
* **Response (`200 OK`):**
  ```json
  {
    "status": "ok",
    "version": "1.0.0",
    "service": "Flock Energy - Urja Meter Ops API"
  }
  ```

---

### 2. List & Search Smart Meters
* **Path:** `GET /api/v1/meters`
* **Query Parameters:**
  * `q` *(string, optional, default="")*: Search keyword to filter meters by serial number, meter ID, or DT code.
  * `page` *(integer, optional, default=1)*: 1-indexed page number to retrieve.
* **Curl Examples:**

  **Retrieve first page of meters:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/meters?page=1"
  ```

  **Search meters by serial number or ID:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/meters?q=SN-883&page=1"
  ```

* **Response (`200 OK`):**
  ```json
  {
    "data": [
      {
        "meterId": "MTR-10023",
        "serialNo": "SN-8839201",
        "make": "Secure Meters",
        "phaseType": "1-phase",
        "installStatus": "installed",
        "dtCode": "DT-NORTH-04"
      },
      {
        "meterId": "MTR-10024",
        "serialNo": "SN-8839202",
        "make": "Schneider",
        "phaseType": "3-phase",
        "installStatus": "installed",
        "dtCode": "DT-SOUTH-01"
      }
    ],
    "total": 403,
    "page": 1,
    "pageSize": 20
  }
  ```

---

### 3. Error Responses & Status Codes

| Status Code | Scenario | Sample Response |
|---|---|---|
| `502 Bad Gateway` | Upstream authentication rejected or portal returned 5xx | `{"detail": "Upstream portal authentication rejected invalid credentials (401/403).", "errorType": "PortalAuthenticationError"}` |
| `504 Gateway Timeout` | Upstream portal request exceeded timeout threshold | `{"detail": "Upstream portal request timed out after 15.0s", "errorType": "PortalTimeoutError"}` |
| `500 Internal Server Error` | Required environment variables missing | `{"detail": "Upstream portal credentials are not configured...", "errorType": "PortalConfigurationError"}` |
| `422 Unprocessable Entity` | Invalid query parameter (e.g. `page=0`) | FastApi standard validation error |

---

## 7. Automated Test Suite

The test suite validates both unit-level client behavior and API route handling using **mocked HTTPX transports** (`httpx.MockTransport`) and FastAPI dependency overrides. The tests run completely offline without contacting the live portal.

Run tests:
```powershell
pytest -v
```

### Test Coverage Highlights (17 Tests)
- `tests/test_health.py`:
  - Health check HTTP status and response payload
  - Swagger UI accessibility (`/docs`)
  - OpenAPI schema validity (`/openapi.json`)
- `tests/test_meters.py`:
  - Successful login handling and session cookie extraction
  - Authentication failure on invalid credentials (401)
  - Missing credentials configuration error
  - Successful paginated meter search and filtering
  - Transparent session expiry handling (re-authenticating on 401 and retrying)
  - Upstream request timeout translation to HTTP 504
  - Upstream 500 error translation to HTTP 502
  - Malformed upstream JSON payload translation to HTTP 502
  - FastAPI integration tests for `/api/v1/meters` query params and error mapping

---

## 8. Design Decisions & Omissions

### Assumptions Made
1. **Internal JSON API**: Empirical inspection revealed the portal communicates via internal JSON endpoints (`/portal/meters/search`) rather than server-rendered HTML forms. We leveraged this directly to provide fast, structured data extraction.
2. **Session Persistence**: The upstream auth framework relies on `__Secure-better-auth.session_token` with an expiration window of 3600 seconds. Maintaining an in-memory cookie jar prevents redundant logins and avoids overwhelming the upstream portal.
3. **Stateless Wrapper**: Downstream consumers interact with our API in a stateless manner; our adapter manages the stateful authentication lifecycle under the hood.

### What Was Intentionally Left Out & Why
- **Meter Detail Endpoint (`GET /api/v1/meters/{id}`)**: No dedicated upstream detail endpoint was observed in DevTools network inspection. While search query filtering (`?q={id}`) can locate specific meters, fabricating a dedicated `/meters/{id}` endpoint with assumed semantics was avoided.
- **Meter Consumption Telemetry (`GET /api/v1/meters/{id}/consumption`)**: Network inspection did not reveal any confirmed consumption or time-series telemetry URL in the verified traffic. Rather than inventing fake schemas (kWh, timestamps, voltage), we omitted this endpoint to preserve data integrity.
- **Database & Caching Layer**: To keep the initial architecture minimal and maintainable, no external database or Redis cache was added.

### Future Improvements (With More Time)
1. **Caching Layer**: Add Redis or in-memory TTL caching for meter searches to minimize upstream load.
2. **Background Sync Worker**: Implement a lightweight background worker to periodically synchronize all 403 meters into a local queryable store (e.g., SQLite / DuckDB) for instant multi-field searching.
3. **Consumption Protocol Discovery**: Deep-dive into client-side JavaScript bundles to identify how the legacy portal renders consumption graphs.
4. **Shared Distributed Session**: Store session tokens in a shared cache to support multi-worker deployments (`uvicorn --workers 4`).

---

## 9. Key Documentation Deliverables

- **Protocol & Reverse Engineering Log:** [`PROTOCOL.md`](./PROTOCOL.md)
- **Candidate Reflection & Five Questions:** [`REFLECTION.md`](./REFLECTION.md)
- **Exported OpenAPI 3.1.0 Specification:** [`openapi.json`](./openapi.json)
