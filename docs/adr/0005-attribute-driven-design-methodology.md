# ADR 0005: Quality-attribute design review

- **Status:** Accepted
- **Date:** 2026-10-10

## Context

Feature additions should preserve testability, clear dependency boundaries,
reviewable data and explicit write behavior.

## Decision

Use an attribute-driven review discipline for significant changes: state the
scenario, affected quality attributes, tactics and verification. Record lasting
choices in ADRs and distinguish targets from measured implementation evidence.

## Consequences and limits

Architecture reviews gain traceable rationale. Notes need maintenance as code
changes. Performance goals and organizational usability require representative
measurements; small examples do not establish production SLOs. See the
[quality-attribute notes](../05_attribute_driven_design.md).
