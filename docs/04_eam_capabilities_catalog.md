# 🧭 Capability catalog

This catalog describes Tecton's implementation, not a certified EAM standard
or complete TOGAF/ArchiMate conformance. The [manifest reference](manifest_reference.md)
describes the current metamodel.

## Implemented

| Area | Available capability | Important boundary |
| --- | --- | --- |
| Catalog | Systems, components, capabilities, technologies, interfaces, data objects, plateaus and work packages | No separate provider or organizational-unit entities |
| Ownership | Optional system owner; pilot can require it | No RACI workflow or owner directory |
| APM | TIME, suitability fields, lifecycle checks, pairwise overlap findings | No inferred business suitability or actual cost savings calculation |
| BCM | Hierarchy display, direct realization coverage, gaps, hotspots and TIME-derived health | No financial/maturity roll-up or exclusive leading-system rule |
| TRM | Declared technology statuses/EOL and direct/cascading dependency impact | No live vendor catalog enrichment or vulnerability scanning |
| Data | Declared objects/interfaces and graph-based lineage/risk heuristics | No technical contract parser or compliance certification |
| Roadmap | Plateaus, work packages, comparison and Gantt source | No arbitrary timestamp reconstruction or initiative collision solver |
| Review | Validation and semantic graph diff | Git text merge remains separate from semantic validation |
| Reporting | Mermaid, Markdown, static/dynamic HTML portal | Full portal styling and diagrams use CDN assets |
| Interchange | Backstage and ArchiMate/Archi import/export | Supported mappings only; no universal lossless interchange guarantee |
| Remote APM | GraphQL application fetch/TIME patch adapter | Endpoint-specific schema; not complete central-EAM synchronization |

## Future ideas

- Scoped manifest configuration and stricter rejection of unknown fields.
- Automated discovery and OpenAPI/AsyncAPI/Protobuf ingestion.
- Cost/maturity aggregation and explicit realization roles.
- Owner surveys, freshness checks, editing forms and approval workflows.
- ID-refactoring commands and safe multi-file graph changes.
- Full offline portal asset bundling and persistent query cache.
- Broader EAM/CMDB connectors and organization-wide Git-catalog operation.
- Natural-language exploration or AI enrichment, if justified by a user need.

These are candidates, not commitments or CLI commands. A new capability should
include source-of-truth ownership, failure behavior and validation evidence
before being described as available.
