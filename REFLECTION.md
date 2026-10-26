# Engineering Take-Home Reflection

This document contains reflections on the design, implementation, and problem-solving process for the Flock Energy Urja Meter Ops API take-home project.

---

### 1. What assumptions did you make?

* **Authentication & Session Persistence:** We assumed the legacy portal relies strictly on the `__Secure-better-auth.session_token` cookie for authenticating internal requests, with a typical 60-minute validity window (`Max-Age=3600`). Rather than re-authenticating on every downstream request, we assumed that maintaining a persistent, cookie-aware client session and lazily re-authenticating upon encountering a 401/403 status is the most resilient, respectful approach to interacting with the legacy portal.
* **JSON Directive vs. HTTP Redirect:** We observed that `POST /login` returns an `application/json` payload containing navigation directives (`{"type":"redirect","status":303,"location":"/meters"}`). We assumed the upstream backend is an API-first or hybrid framework (Better-Auth) rather than a traditional server-rendered HTML form.
* **Never Fabricate Unverified Schemas:** We assumed that delivering a smaller, 100% verified API surface is far superior to guessing or mocking `/meters/{id}` or `/meters/{id}/consumption` endpoints. Without verified upstream network contracts, fabricating telemetry or detail schemas would create misleading abstractions.
* **Stateless Consumer Interface:** We assumed that downstream data and product teams require a clean, stateless REST API. All stateful session management, cookie synchronization, and error translation must remain encapsulated inside the API service.

> **Candidate Personalization:**  
> *[Optional: Add any specific assumptions you made regarding downstream consumer latency tolerance, expected query volume, or network reliability.]*

---

### 2. Which part was the most difficult, and how did you get unstuck?

* **The Challenge:** The most nuanced part was diagnosing the upstream authentication handshake. Standard legacy portals typically employ either standard HTTP redirects (`Location` header on a 302/303 response) or HTML form posts with hidden CSRF tokens. Urja Meter Ops, however, returned an HTTP response with a JSON payload indicating a redirect (`{"type": "redirect", "status": 303, "location": "/meters"}`) alongside a `Set-Cookie` header containing `__Secure-better-auth.session_token`.
* **Getting Unstuck:** Rather than making assumptions in code, we relied on empirical verification via Chrome DevTools Network inspection. By isolating the exact request payload (`{"email": ..., "password": ...}`) and observing the response headers, we realized that HTTPX's default redirect follower needed to be paired with cookie jar inspection. Once the session token was confirmed in the cookie jar, we validated the session against `GET /portal/meters/search?q=&page=1`, confirming that the session was active and authorized.

> **Candidate Personalization:**  
> *[Optional: Share any personal moment during the inspection or debugging phase where you had to test a hypothesis or overcome an unexpected hurdle.]*

---

### 3. If you had another day, what would you improve?

1. **Caching & Upstream Protection:** The legacy portal is an ageing internal system with 403 meters. Adding an in-memory TTL cache (e.g. Cachetools) or Redis for `GET /api/v1/meters` would dramatically decrease load on the legacy portal and provide sub-millisecond response times for frequently repeated queries.
2. **Reverse-Engineering Consumption & Details:** Given more time, we would dig deeper into the frontend client bundles or simulate operational user actions in the portal to capture how meter detail views and historical telemetry (kWh consumption) are requested over the wire.
3. **Background Sync / Local Index Layer:** Because the total dataset is relatively small (403 records across ~21 pages), we could build a lightweight background sync worker that proactively synchronizes all meters into a local SQLite/DuckDB database on a periodic schedule (e.g., every 15 minutes). This would enable instant full-text search, multi-attribute filtering, and spatial queries without touching the legacy portal synchronously.
4. **Resiliency & Circuit Breaking:** Implement circuit breaker patterns (e.g., via `tenacity` or `pybreaker`) to gracefully handle upstream outages, and add distributed session sharing so multiple Uvicorn workers share a single upstream session token.

> **Candidate Personalization:**  
> *[Optional: Note which of these improvements aligns most with your personal engineering strengths, e.g. distributed systems, database indexing, or developer experience.]*

---

### 4. What mistake did you make while solving this (there's always one)?

* **Initial Assumption of HTML Scraping:** Initially, seeing a legacy portal utility named "Urja Meter Ops", our default mental model prepared for scraping server-rendered HTML tables using BeautifulSoup4 and parsing CSRF tokens from hidden `<input>` elements. We had even included BeautifulSoup4 in `requirements.txt` in Step 1.
* **Correction:** When empirical network traffic was inspected in DevTools, we discovered the portal actually exposes internal JSON endpoints (`/portal/meters/search`). We pivoted immediately to consuming the clean JSON response rather than introducing brittle HTML scrapers. Leaving BeautifulSoup4 in `requirements.txt` remains harmless for future scraping needs, but recognizing early that we did not need HTML DOM traversal kept the client clean and fast.

> **Candidate Personalization:**  
> *[Optional: Mention any small syntax mistake, command line typo, or test assertion quirk you encountered and resolved during your session.]*

---

### 5. If you were reviewing your own submission, what would you criticise?

1. **Scope Omission of Detail & Consumption:** A reviewer might notice that `GET /api/v1/meters/{id}` and `GET /api/v1/meters/{id}/consumption` are not implemented. While this was an intentional, principled choice to avoid fabricating unverified endpoints, a production-grade utility wrapper would ideally expose meter consumption telemetry.
2. **In-Memory Session Storage per Process:** The `UrjaPortalClient` maintains session cookies in memory within the process instance. If deployed across multiple worker processes (e.g., `uvicorn --workers 4`), each worker logs in independently. A shared Redis or database token cache would be more efficient at scale.
3. **Single Upstream Credentials:** The wrapper currently uses a single operator credential pool from environment variables. If different downstream users needed role-based access or audit logging on the upstream portal, a credential-delegation or multi-tenant approach would be required.

> **Candidate Personalization:**  
> *[Optional: Add any thoughts on your personal coding style, documentation conciseness, or test organization.]*
