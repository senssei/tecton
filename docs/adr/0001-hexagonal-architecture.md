# ADR 0001: Hexagonal Architecture (Ports and Adapters) for Repository Decoupling

* **Status:** Accepted
* **Date:** 2026-10-10
* **Deciders:** Solution Architecture Team
* **Consulted:** Tecton Core Contributors

---

## Context
Enterprise Architecture Management (EAM) ecosystems typically force clients to bind directly to proprietary SDKs or specific vendor APIs (e.g., GraphQL schemas, REST CMDB models). This tight coupling introduces severe friction:
1. Analytical and governance logic becomes difficult or impossible to test offline.
2. Migrating between repositories or supporting local file formats requires major codebase rewrites.
3. CI/CD pipelines cannot run lightweight validation without full network access and remote API credentials.

## Decision
We adopt **Hexagonal Architecture (Ports and Adapters)** as the foundational architectural pattern for Tecton:
* The **Domain Layer** (`tecton.core.models`, `tecton.engines`) contains pure business logic and analytical algorithms with zero dependencies on external protocols, network libraries, or vendor schemas.
* Communication with external storage or remote graph services is mediated strictly via the `ArchitectureRepositoryPort` protocol interface.
* Specific infrastructure implementations (`GraphQLRepositoryAdapter`, `FileRepositoryAdapter`, `InMemoryRepositoryAdapter`) reside in the **Adapters Layer** (`tecton.adapters`), implementing the port contract without leaking infrastructure details into the core.

## Consequences

### Positive
* **100% Offline Capability:** Enables full unit, integration, and CLI testing using in-memory and local file adapters without network or credentials.
* **Extensibility:** New repository backends (e.g., Ardoq, Git-based YAML repositories, Neo4j, ServiceNow) can be added as isolated adapters without touching any existing analytic engine.
* **Maintainability:** Clear boundary separation minimizes unintended side effects and enforces strict dependency direction (dependencies point inward).

### Negative / Trade-offs
* Requires maintaining mapping boilerplate between external DTOs and internal `Application` domain models.
* Introduces interface indirection through Python `typing.Protocol`.
