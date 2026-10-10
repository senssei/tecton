# ADR 0003: Safety-First Mutation Policy with Mandatory Dry-Run Default

* **Status:** Accepted
* **Date:** 2026-10-10
* **Deciders:** Solution Architecture Team
* **Consulted:** Tecton Core Contributors

---

## Context
Enterprise architecture repositories store mission-critical IT landscape data. Automated scripts and integration tools that perform write mutations (such as updating TIME classifications, retiring systems, or altering dependencies) pose severe operational risks if executed inadvertently or with incorrect parameters.

Unintended bulk updates in production EAM repositories can corrupt governance records, trigger false alerts, and overwrite historical audits.

## Decision
We establish a strict **Safety-First Mutation Policy** across all Tecton layers:
1. Every service method and CLI command that mutates repository state defaults unconditionally to `dry_run = True`.
2. In `--dry-run` mode, the engine evaluates the required changes, formats the exact RFC 6902-compliant JSON Patch operations (`add`, `replace`, `remove`), and returns a detailed preview without executing network writes or disk changes.
3. Actual state modification requires an explicit user opt-in via the `--apply` flag.

## Consequences

### Positive
* **Zero-Risk Inadvertent Writes:** Running `tecton apm patch-time` can never accidentally modify production data.
* **Audit Transparency:** Users and automated pipelines receive full previews of planned mutations before commitment.
* **CI/CD Compatibility:** Automated pipelines can run `tecton apm patch-time` in PR checks to generate diff comments without write permissions.

### Negative / Trade-offs
* Users must supply an extra flag (`--apply`) when they explicitly desire write operations.
