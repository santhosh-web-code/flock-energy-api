# Urja Meter Ops - Portal Protocol & Reverse-Engineering Analysis

> **Status:** Empirically Verified Baseline (Chrome DevTools Inspection)  
> **Target Portal:** `https://urja-ops.flockenergy.tech`  
> **Auth Framework Identified:** Better-Auth (`__Secure-better-auth.session_token`)

---

## Executive Overview
This document records the empirical protocol analysis of the legacy **Urja Meter Ops** portal. It captures how the upstream system authenticates operators, maintains stateful sessions, and delivers meter data over internal JSON endpoints.

Through Chrome DevTools network analysis, we identified that the legacy portal functions as a single-page or hybrid application communicating with internal JSON endpoints rather than raw server-rendered HTML forms.

---

## 1. Authentication Protocol (Verified)

### Request Signature
* **Target URL:** `POST /login` (relative to portal root, e.g., `https://urja-ops.flockenergy.tech/login`)
* **Content-Type:** `application/json`
* **Request Payload:**
  ```json
  {
    "email": "operator@urja.local",
    "password": "<secure_password>"
  }
  ```

### Upstream Response Behavior
* **HTTP Status Code:** `200 OK` (or `303 See Other`)
* **Content-Type:** `application/json`
* **Response Body:**
  ```json
  {
    "type": "redirect",
    "status": 303,
    "location": "/meters"
  }
  ```
  > **Critical Observation:** The upstream service communicates navigation intent via a JSON body containing `{"type": "redirect", "status": 303, ...}` rather than relying solely on HTTP-level `Location` header redirection. HTTP clients must not confuse this JSON directive with an automatic HTTP redirect.

### Session Cookie
Upon successful credentials verification, the server sets a session cookie:
* **Cookie Name:** `__Secure-better-auth.session_token`
* **Attributes:**
  * `HttpOnly`: Yes (prevents client-side script access)
  * `Secure`: Yes (enforces HTTPS transmission)
  * `SameSite`: `Lax`
  * `Max-Age`: `3600` (1-hour session validity)

### Credential & Security Handling
* Credentials must be supplied exclusively through environment variables (`PORTAL_USERNAME` and `PORTAL_PASSWORD`).
* No credentials, passwords, or active session tokens are ever written to disk, committed to Git, or exposed in logs.

---

## 2. Session Management & Re-Authentication (Verified)

* **Session Lifetime:** The `Max-Age=3600` cookie expires after 60 minutes of inactivity.
* **State Persistence:** The wrapper client (`UrjaPortalClient`) encapsulates an `httpx.AsyncClient` with an active cookie jar, reusing `__Secure-better-auth.session_token` across subsequent calls.
* **Session Expiry Detection:** If an authenticated request returns an HTTP `401 Unauthorized`, `403 Forbidden`, or redirect indication, the client detects session invalidation.
* **Transparent Re-Authentication:** The client automatically re-authenticates via `POST /login` and retries the failed operation once. To prevent cascading failures or denial-of-service, retries are strictly bounded to a single attempt (`_retry_auth=False`).

---

## 3. Meter Search & Listing Endpoint (Verified)

### Request Specification
* **Target URL:** `GET /portal/meters/search`
* **Base Example:** `https://urja-ops.flockenergy.tech/portal/meters/search?q=&page=1`
* **Method:** `GET`
* **Query Parameters:**
  * `q` *(string, optional)*: Search keyword (matches meter ID, serial number, or DT code).
  * `page` *(integer, default 1)*: 1-indexed pagination number.
* **Authentication:** Requires `__Secure-better-auth.session_token` cookie.

### Verified Response Structure
* **Status:** `200 OK`
* **Content-Type:** `application/json`
* **Observed Baseline (First Page):**
  * `total`: `403` records
  * `page`: `1`
  * `pageSize`: `20` records per page
* **Response Schema:**
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
      }
    ],
    "total": 403,
    "page": 1,
    "pageSize": 20
  }
  ```

### Verified Field Definitions
| Field | Type | Description | Example |
|---|---|---|---|
| `meterId` | `string` | Unique internal system identifier for the meter | `"MTR-10023"` |
| `serialNo` | `string` | Hardware manufacturer serial number | `"SN-8839201"` |
| `make` | `string` | Manufacturer brand name | `"Secure Meters"` |
| `phaseType` | `string` | Electrical connection phase (e.g., 1-phase, 3-phase) | `"1-phase"` |
| `installStatus` | `string` | Deployment/operational state | `"installed"` |
| `dtCode` | `string` (nullable) | Associated Distribution Transformer code | `"DT-NORTH-04"` |

---

## 4. Unverified & Unknown Endpoints (Omissions)

To preserve engineering integrity and adhere to the strict requirement of **never fabricating upstream behavior**, the following endpoints were deliberately **omitted from the API implementation**:

1. **Meter Detail Endpoint (`GET /api/v1/meters/{meter_id}`):**  
   * **Status:** *UNVERIFIED / NOT IMPLEMENTED*.  
   * **Reasoning:** Network inspection did not verify an explicit individual detail route (such as `/portal/meters/{id}`). While exact-match filtering can be achieved via `GET /portal/meters/search?q={meter_id}`, creating a dedicated detail route with guessed semantics would violate architectural safety.
2. **Meter Consumption & Telemetry (`GET /api/v1/meters/{meter_id}/consumption`):**  
   * **Status:** *UNVERIFIED / NOT IMPLEMENTED*.  
   * **Reasoning:** No consumption telemetry endpoint, time-series schema, or interval data URL was observed in the verified traffic. The wrapper does not guess schema fields (e.g., kWh, voltage, timestamps).
3. **Distribution Network Hierarchy:**  
   * **Status:** *UNVERIFIED / NOT IMPLEMENTED*.  
   * **Reasoning:** Although `dtCode` appears on meter records, an explicit network tree endpoint (Substations -> Feeders -> DTs) has not been confirmed.

---

## 5. Data Anomalies & Integration Considerations

* **Search Semantics:** The `q` parameter performs partial or exact substring matching on both serial numbers and meter IDs upstream.
* **Pagination Bounds:** Upstream page size appears fixed at 20 items per page (`pageSize: 20`).
* **Error Semantics:** Non-authenticated calls to `/portal/meters/search` return 401/403 or redirect to `/login`. Our wrapper catches this and re-authenticates automatically.
