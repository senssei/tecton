# ADR 0006: Git-Backed EAM Graph Repository via C4-Extended DSL and Quality Gates

* **Status:** Accepted
* **Date:** 2026-10-10
* **Deciders:** Solution Architecture Team
* **Consulted:** Tecton Core Contributors

---

## Context
While traditional EAM tools store graph data in proprietary cloud databases, treating enterprise architecture as code requires versioning the architecture directly within Git. 

However, mapping a Directed Labeled Property Graph (DLPG) onto Git text files introduces severe adversarial risks:
1. **Dangling Edges:** Silently merging entity deletions without removing inbound relationship pointers.
2. **Topological Merge Conflicts:** Textual auto-merges that introduce illegal dependency cycles or multi-master leadership states.
3. **C4 Metamodel Mismatch:** Standard C4/Structurizr DSL only models runtime software components and lacks enterprise strategic primitives (Business Capabilities, Gartner TIME scoring, Obsolescence EOL dates).

## Decision
1. **Git as Single Source of Truth (Pure GitOps):** All architecture definitions originate in Git and are governed via Pull Requests.
2. **C4-Extended EAM Schema:** We adopt a typed YAML/JSON DSL expanding the C4 model concepts (`systems`, `containers`, `relationships`) with enterprise governance primitives:
   * `capabilities:` (Hierarchical business capabilities L1–L3).
   * `systems:` (Extended with TIME metrics, lifecycles, criticality, and tech stacks).
   * `relationships:` (Explicit typed directed edges).
3. **Mandatory Pre-Merge Quality Gate (`tecton validate`):** We mandate an automated CI/CD linter that asserts 100% referential integrity (zero dangling pointers), topological acyclicity where required, and schema adherence before PR merges.

## Consequences

### Positive
* **Cryptographic Version Control:** Complete, immutable audit history of every architectural change with standard Git blaming and commit tagging.
* **True GitOps & Developer Experience:** Architects and engineers collaborate in Pull Requests using familiar code review tools instead of web portal permission gates.
* **Corrupted Graph Prevention:** The pre-merge linter mathematically prevents broken pointers and illegal cycles from contaminating `main`.

### Negative / Trade-offs
* Querying the graph requires in-memory compilation and schema hydration upon cold starts.
* Renaming entities requires atomic refactoring across referencing files (mitigated via `tecton refactor rename`).
