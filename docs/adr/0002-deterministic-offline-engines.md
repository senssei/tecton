# ADR 0002: Local analytical engines

- **Status:** Accepted
- **Date:** 2026-10-10

## Context

Catalog analysis should run locally and in CI without browser automation or a
live remote EAM account.

## Decision

Implement TIME scoring, pairwise weighted-Jaccard overlap detection, lifecycle
checks and other graph analysis in Python over in-memory models. Keep algorithms
and configurable thresholds visible in code and verify them with offline tests.

## Consequences and limits

The same input, configuration and evaluation date should produce equivalent
results. Date control is currently partial: selected APIs accept `as_of_date`,
but inference, roadmap and diff still use current dates. Results are not uniformly
immutable. Pairwise overlap is quadratic; no enterprise-scale latency guarantee
has been benchmarked. See [quality attributes](../05_attribute_driven_design.md).
