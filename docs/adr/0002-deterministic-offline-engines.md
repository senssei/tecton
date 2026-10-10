# ADR 0002: Deterministic In-Memory Analytic Engines

* **Status:** Accepted
* **Date:** 2026-10-10
* **Deciders:** Solution Architecture Team
* **Consulted:** Tecton Core Contributors

---

## Context
Standard EAM repository APIs are passive storage systems (CRUD over entities and relations). Advanced business capabilities like Gartner TIME model scoring, functional redundancy clustering, and lifecycle chronological validation are missing from repository APIs and trapped inside proprietary web browser front-ends.

Organizations attempting to automate architectural governance in CI/CD pipelines need fast, deterministic, reproducible evaluations without browser automation or external server calls.

## Decision
We implement independent, deterministic analytical engines in Python:
1. `TimeScoringEngine`: Maps functional and technical suitability scores to Gartner TIME quadrants using configurable mathematical thresholds.
2. `RedundancyDetectionEngine`: Evaluates pairwise functional similarity using weighted Jaccard metrics across capability sets and organizational user groups:
   $$J(A_1, A_2) = w_c \cdot \frac{|C_1 \cap C_2|}{|C_1 \cup C_2|} + w_u \cdot \frac{|U_1 \cap U_2|}{|U_1 \cup U_2|}$$
3. `LifecycleValidator`: Enforces chronological validity across standard lifecycle phases (`plan` < `phaseIn` < `active` < `phaseOut` < `endOfLife`).

All engines operate on in-memory collections of pure domain models and produce immutable evaluation results.

## Consequences

### Positive
* **Deterministic Results:** Evaluations yield identical, mathematically reproducible results across local developer machines, CI/CD containers, and cloud environments.
* **Ultra-Low Latency:** Processing thousands of entities executes in milliseconds, avoiding network roundtrips and SaaS rate limits.
* **Testability:** Pure functions and deterministic engines make testing trivial and robust.

### Negative / Trade-offs
* Requires local memory footprint proportional to the number of applications in the portfolio (typically negligible for enterprise software portfolios of 1,000–50,000 systems).
* Pairwise redundancy comparison is $O(N^2)$, which may require spatial partitioning or approximate indexing for portfolios exceeding 100,000 entities.
