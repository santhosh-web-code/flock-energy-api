# Flock Energy - Urja Meter Ops API

A clean, modern, and documented REST API wrapper built over the legacy **Urja Meter Ops** portal.

---

## 1. Project Objective

The Urja Meter Ops portal is an internal web utility used by field and operations staff to query smart meters, navigate the electrical distribution hierarchy, and inspect consumption telemetry. However, the portal lacks a programmatic API, forcing internal product and analytics teams to manually copy and paste data from browser sessions.

This project delivers a robust, production-minded REST API service in front of the legacy portal, transforming raw, unstructured, or HTML-rendered upstream meter data into typed, clean, and reliable JSON resources.

> **Status Notice (Step 1 Baseline):**  
> This repository currently reflects **Step 1: Project Setup and Initial Architecture**. The core application structure, configuration management, health check endpoints, automated test suite, and OpenAPI schemas are implemented and fully verified. The legacy portal integration (`UrjaPortalClient`) is structured as an architectural placeholder, pending live empirical inspection of the upstream portal in Step 2.

---

## 2. Architecture & Directory Structure

The service follows a clean, decoupled layered architecture:

```
flock-energy-api/
├── app/
│   ├── __init__.py       # Package metadata and version definition
│   ├── main.py           # FastAPI application factory, lifespan hooks, and core routes
│   ├── client.py         # UrjaPortalClient abstraction (HTTPX async client wrapper)
│   ├── models.py         # Strongly typed Pydantic models (health schemas)
│   └── config.py         # Environment configuration using Pydantic & python-dotenv
├── tests/
│   ├── __init__.py       # Test package marker
│   └── test_health.py    # TestClient test suite for /health, /docs, and OpenAPI schema
├── .env.example          # Template environment file (no secrets committed)
├── .gitignore            # Git ignore rules for virtual environments, secrets, and caches
├── requirements.txt      # Pinned dependency definitions
├── README.md             # Project documentation and operational guide
├── PROTOCOL.md           # Upstream portal reverse-engineering investigation log
├── REFLECTION.md         # Engineering evaluation reflections
└── openapi.json          # Exported static OpenAPI 3.1.0 specification
```

### Architectural Highlights
- **FastAPI**: Asynchronous, high-performance web framework providing native OpenAPI and Swagger documentation.
- **HTTPX**: Modern asynchronous HTTP client featuring connection pooling, configurable timeouts, and safe lifecycle termination.
- **Pydantic**: Robust runtime data validation, schema enforcement, and serialization.
- **python-dotenv**: Environment isolation preventing hardcoded secrets and facilitating 12-factor application configuration.
- **pytest & FastAPI TestClient**: Automated testing ensuring stability and preventing regressions.

---

## 3. Getting Started (Windows Setup Guide)

### Prerequisites
- **Python 3.11+** (Verified compatible with Python 3.11 through 3.14 on 64-bit Windows)
- **Git**

### Step-by-Step Installation

1. **Clone or navigate to the repository:**
   ```powershell
   cd "c:\Users\santh\Flock-Energy API"
   ```

2. **Create a virtual environment:**
   ```powershell
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   * PowerShell:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   * Command Prompt (cmd):
     ```cmd
     .\.venv\Scripts\activate.bat
     ```

4. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 4. Configuration

The application reads configuration parameters from environment variables or a local `.env` file using `python-dotenv`.

Copy `.env.example` to create your local `.env`:
```powershell
Copy-Item .env.example .env
```

Open `.env` and configure your credentials:
```env
# Upstream Urja Meter Ops Portal
PORTAL_BASE_URL=https://urja-ops.flockenergy.tech
PORTAL_USERNAME=operator@urja.local
PORTAL_PASSWORD=your_secure_password_here

# Service Settings
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
```

> **Security Guardrail:** Never commit `.env` or any real portal credentials into Git. The `.gitignore` file is pre-configured to exclude all `.env*` files.

---

## 5. Running the Application

Start the local development server with auto-reload:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The application will bind to `http://127.0.0.1:8000`.

### Endpoints and Interactive Documentation
Once started, you can explore the service:
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) — Returns service status and metadata.
- **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — Interactive API playground.
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) — Clean alternative documentation reader.
- **OpenAPI Schema (JSON):** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) — Programmatic schema.

### Sample Request & Response
```bash
curl -X GET http://127.0.0.1:8000/health
```

Response (`HTTP 200 OK`):
```json
{
  "status": "ok",
  "version": "1.0.0",
  "service": "Flock Energy - Urja Meter Ops API"
}
```

---

## 6. Running the Test Suite

Run unit and integration tests using `pytest`:

```powershell
pytest -v
```

All health check, documentation accessibility, and schema integrity tests will execute with full verbose output.

---

## 7. Key Documentation Links

- **Protocol Investigation Log:** [`PROTOCOL.md`](./PROTOCOL.md) — Documenting upstream authentication, session management, discovered routes, and observed data quirks.
- **Engineering Reflection:** [`REFLECTION.md`](./REFLECTION.md) — The five reflective questions covering assumptions, challenges, trade-offs, and retrospectives.
- **Exported OpenAPI Specification:** [`openapi.json`](./openapi.json) — Static snapshot of the service's OpenAPI contract.

---

## 8. Architectural Notes & Decisions

### Assumptions Made
1. **Upstream Availability:** We assume the upstream portal is a legacy application with potential latency variances and rate limits; thus, asynchronous I/O and connection pooling via HTTPX are vital.
2. **Empirical Discovery Over Guesswork:** We make no premature assumptions about internal route paths or response schemas until the live portal is inspected in Step 2.
3. **Stateless Wrapper:** Downstream consumers interact with our API statelessly; session management with the upstream portal will be handled transparently within the client layer.

### Design Decisions & Trade-offs
- **Pydantic Settings vs. Raw os.environ:** We used Pydantic dataclass/BaseModel patterns in `app/config.py` with `@lru_cache` to provide typed defaults, test-time dependency injection, and deterministic configuration loading.
- **Explicit TestClient Tests:** We verified `/docs` and `/openapi.json` programmatically within the test suite to guarantee that API documentation never breaks silently during development.

### What Was Intentionally Left Out & Why
- **No Guessed Upstream Endpoints:** We deliberately avoided inventing `/meters`, `/consumption`, or mock schemas in Step 1. Premature modeling creates technical debt before upstream payloads are inspected.
- **No Database or Caching Layers:** Adding persistent storage or Redis at this foundational stage would be over-engineering. We maintain a lean, single-purpose service boundary.
- **No Docker or Complex Orchestration:** For Step 1, local virtual environment reproducibility and standard Python tooling keep the development loop fast and transparent.

### Future Improvements (With More Time)
- Upstream session pooling and proactive re-authentication with exponential backoff.
- In-memory or Redis caching with intelligent TTLs for static network hierarchy trees.
- Structured JSON logging and OpenTelemetry tracing for upstream request telemetry.
