# Engineering Take-Home Reflection

This document contains candidate reflections on the design, implementation, and problem-solving process for the Flock Energy Urja Meter Ops API take-home project.

---

### 1. What assumptions did you make?

*[Candidate to complete during/after project implementation]*

*Guiding prompts:*
- Assumptions made regarding the legacy portal stability, concurrency, and rate limiting.
- Assumptions about downstream consumer requirements (e.g., REST vs. streaming, freshness tolerances).
- Assumptions regarding data types, timezone handling (e.g., IST vs. UTC), and missing/null values.

---

### 2. Which part was the most difficult, and how did you get unstuck?

*[Candidate to complete during/after project implementation]*

*Guiding prompts:*
- Unraveling complex upstream flows (e.g., authentication redirects, hidden form tokens, irregular HTML DOM structures, session persistence).
- Debugging techniques applied (e.g., HTTP inspection, logging, isolating unit tests).

---

### 3. If you had another day, what would you improve?

*[Candidate to complete during/after project implementation]*

*Guiding prompts:*
- Caching and cache invalidation strategies (e.g., Redis or in-memory TTL caching for meter metadata).
- Background polling, bulk scraping, or asynchronous job queues for high-volume readings.
- Resiliency enhancements (exponential backoff, circuit breaking, retry policies).
- Modern web explorer/visualization layer.

---

### 4. What mistake did you make while solving this (there's always one)?

*[Candidate to complete during/after project implementation]*

*Guiding prompts:*
- An early architectural assumption that had to be refactored.
- A subtle parsing bug, session handling edge-case, or performance bottleneck encountered.

---

### 5. If you were reviewing your own submission, what would you criticise?

*[Candidate to complete during/after project implementation]*

*Guiding prompts:*
- Potential architectural shortcuts taken to respect time constraints.
- Areas where test coverage or edge-case handling could be deeper.
- Observability and metrics instrumentation.
