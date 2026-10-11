# 🎯 Quality attributes and design drivers

The project uses attribute-driven design as a review discipline: define the
quality scenario, select a tactic, and record verification evidence. This document
is a working design note, not a certification of ADD process compliance.

## Scenarios and evidence

| Attribute | Scenario / tactic | Current evidence or limit |
| --- | --- | --- |
| Testability | Local models can be evaluated without a live EAM account; use file/in-memory adapters | Offline unit and integration tests; remote calls mocked |
| Modifiability | Keep analytic rules independent of endpoint-specific HTTP/GraphQL code | Repository port and AST boundary test; graph coupling remains concrete |
| Safety | Preview repository classification changes before persistence | `patch-time` simulates unless `--apply`; imports/exports write output files |
| Integrity | Reject duplicate IDs and broken references before merging | Graph linter plus required merged-state CI check, when branch rules are configured |
| Reproducibility | Evaluate the same metadata, settings and date consistently | Selected date-injection APIs; CLI, roadmap and lifecycle inference still use current dates |
| Interoperability | Export inspectable text and supported ecosystem mappings | Mermaid/Markdown and connector tests; arbitrary field round-trip is not guaranteed |
| Performance | Keep catalog loading and common analysis practical in CI | In-memory indexes; pairwise overlap is quadratic; no established throughput benchmark |
| Usability | Maintainers review text; other users browse a generated snapshot | YAML/PR pilot, read-only portal and documented owner conventions |

## Targets requiring measurement

Cold parsing, validation, memory usage, portal generation and overlap detection
need representative benchmark datasets before any latency or scale claim is
published. Record dataset size, runtime, hardware, Python/dependency versions and
fixed evaluation date. Small example tests do not establish enterprise-scale SLOs.

## Design constraints

Python 3.11+, Pydantic schemas, Typer CLI, local graph execution and explicit
adapter boundaries keep the alpha implementation straightforward. The current
portal uses CDN-hosted assets. Preserving full document formatting, distributed
transactions and persistent graph indexing are not implemented constraints.

## Change review

For substantial changes, specify the user scenario, inputs/outputs, failure
behavior and affected quality attributes. Check the [architecture review](07_architectural_adversarial_analysis.md)
and add an [ADR](adr/README.md) when the change alters a lasting architectural
choice. Tests must verify behavior rather than merely repeat the implementation.
