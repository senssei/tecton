# ADR 0001: Repository adapters and architectural boundaries

- **Status:** Accepted
- **Date:** 2026-10-10

## Context

Portfolio analysis should be testable with local data and avoid dependence on
one remote API's field names or network behavior.

## Decision

Keep core models and analytical engines separate from repository I/O. Use
`ArchitectureRepositoryPort` for application fetching/saving/patching, with
in-memory, file, Git-workspace and GraphQL adapters. Delivery packages delegate
to application methods or services. Enforce selected import boundaries with an AST test.

## Consequences and limits

Adapters isolate endpoint mappings and support offline tests. Graph-oriented
use cases still share concrete `CompiledGraph` types and require graph-capable
sources; the application repository port alone does not expose the whole EAM
metamodel. Additional backends may therefore need graph contracts as well as
application mapping. See the [implemented architecture](../03_baseline_architecture.md).
