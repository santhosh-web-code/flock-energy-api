# Urja Meter Ops - Portal Protocol & Reverse-Engineering Analysis

> **Status:** Pending Investigation (Step 1 Baseline)  
> **Last Updated:** Initial Scaffolding  
> **Target Portal:** `https://urja-ops.flockenergy.tech`  
> **Target Role:** Operator (`operator@urja.local`)

---

## Executive Overview
This document records the empirical protocol analysis of the legacy **Urja Meter Ops** portal. It outlines how the upstream system authenticates users, maintains operational sessions, structures its internal routing/payloads, and handles meter data.

As of Step 1, all integration specifics remain strictly marked as **Pending Investigation** to adhere to the design constraint of not inventing upstream behavior or accessing the live portal prior to empirical network inspection in Step 2.

---

## 1. Authentication Protocol

* **Mechanism:** *[Pending Investigation]* (e.g., standard form-urlencoded POST `/login`, Bearer token exchange, OAuth2, or HTTP Basic Auth).
* **Request Signature:**
  * URL: *[To be captured]*
  * HTTP Method: *[To be captured]*
  * Form / Body Fields: *[To be captured]*
  * Content-Type: *[To be captured]*
* **CSRF / Security Tokens:** *[Pending Investigation]* (Presence of anti-CSRF hidden inputs or verification cookies).
* **Failure Responses:** *[Pending Investigation]* (HTTP status codes, redirect behaviors, or error message selectors for invalid credentials).

---

## 2. Session Management & State Persistence

* **Session Token Type:** *[Pending Investigation]* (e.g., `sessionid`, `JSESSIONID`, JWT cookie, or header tokens).
* **Persistence Mechanism:** *[Pending Investigation]* (Cookie jar persistence via `httpx.AsyncClient` or custom header injection).
* **Session Lifecycle & Expiry:** *[Pending Investigation]* (Idle timeout duration, absolute expiry, automatic renewal semantics).
* **Re-authentication Triggers:** *[Pending Investigation]* (How the client detects an expired session and safely re-authenticates without interrupting consumer requests).

---

## 3. Discovered Endpoints & Route Map

| Legacy Path / Action | HTTP Method | Expected Query / Body | Upstream Purpose | Upstream Content Type |
|----------------------|-------------|-----------------------|------------------|-----------------------|
| *Pending*            | *Pending*   | *Pending*             | Meter search     | *Pending*             |
| *Pending*            | *Pending*   | *Pending*             | Meter details    | *Pending*             |
| *Pending*            | *Pending*   | *Pending*             | Hierarchy view   | *Pending*             |
| *Pending*            | *Pending*   | *Pending*             | Telemetry/readings| *Pending*            |

---

## 4. Response Formats & Payload Extraction

* **Data Format:** *[Pending Investigation]* (Server-side rendered HTML, client-side rendered JSON API, embedded scripts, or CSV export).
* **HTML Parsing Strategy (if applicable):**
  * Target DOM Selectors: *[Pending Investigation]*
  * Parser: `BeautifulSoup4` with `lxml` / `html.parser`.
* **API Payloads (if JSON endpoints exist):**
  * Raw schemas vs. cleaned Pydantic models: *[Pending Investigation]*.

---

## 5. Data Anomalies & Quirks

* **Character Encoding:** *[Pending Investigation]* (UTF-8, ISO-8859-1, etc.).
* **Timestamp & Timezone Formats:** *[Pending Investigation]* (UTC vs. Indian Standard Time / local timezone, presence of DST).
* **Missing / Inconsistent Data:** *[Pending Investigation]* (Handling of disconnected meters, zero-consumption values, null fields).
* **Rate Limits & Concurrency Quirks:** *[Pending Investigation]* (Upstream throttling limits, 429 status codes, or connection drops).

---

## 6. Unresolved Questions

1. Does the portal expose an undocumented internal JSON API used by frontend scripts, or is all data purely HTML tables?
2. Does the authentication flow require multi-step redirects or hidden token pre-fetching?
3. How deep does the network hierarchy go (e.g., Substation -> Feeder -> Transformer -> Meter), and can it be queried incrementally?
4. Are historical meter readings paginated or delivered as bulk downloads?
