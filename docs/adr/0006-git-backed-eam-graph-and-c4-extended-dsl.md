# ADR 0006: Git-backed EAM workspaces

- **Status:** Accepted
- **Date:** 2026-10-10

## Context

Versioned architecture files enable reviewed changes, but Git text merges do not
understand graph references, duplicate identity or capability hierarchy cycles.

## Decision

Use a typed YAML/JSON metamodel inspired by C4 and extended with EAM entities.
Git is the source of truth for Git-backed workspaces. Run `tecton validate` on
the merged model before accepting catalog changes. Refer to the
[manifest reference](../manifest_reference.md) for supported entities and severities.

## Consequences and limits

Local graphs have versioned inputs and can be checked before merge. Blocking
invalid main-branch states requires configured branch protection and fresh merged
checks. Dependency cycles are warnings by default. There is no single-leading-system
rule, persistent compiled cache or automatic ID-renaming CLI. Stable IDs and
reviewed reference changes are the current convention.

The [pilot](../08_git_eam_pilot.md) evaluates Git on Tecton's own model.
Organization-wide central EAM adoption remains open; external adapters remain supported.
