# 🧭 Capability catalog

This catalog describes Tecton's implementation, not a certified EAM standard
or complete TOGAF/ArchiMate conformance. The [manifest reference](manifest_reference.md)
describes the current metamodel.

## Implemented

| Area | Available capability | Important boundary |
| --- | --- | --- |
| Catalog | Systems, components, capabilities, technologies, interfaces, data objects, plateaus and work packages | No separate provider or organizational-unit entities |
| Ownership | Optional system owner; pilot can require it | Optional owner directory and review policies; no RACI workflow |
| APM | TIME, suitability fields, lifecycle checks, pairwise overlap findings | No inferred business suitability or actual cost savings calculation |
| BCM | Hierarchy display, direct realization coverage, gaps, hotspots and TIME-derived health | Leaf coverage and cost aggregation; no maturity roll-up or exclusive leading-system rule |
| TRM | Declared technology statuses/EOL and direct/cascading dependency impact | No live vendor catalog enrichment or vulnerability scanning |
| Data | Declared objects/interfaces and graph-based lineage/risk heuristics | No technical contract parser or compliance certification |
| Roadmap | Plateaus, work packages, comparison and Gantt source | Date/dependency/resource/budget checks; no timestamp reconstruction or automatic rescheduling |
| Review | Validation and semantic graph diff | Git text merge remains separate from semantic validation |
| Reporting | Mermaid, Markdown, static/dynamic HTML portal | Bundled offline assets; no live external CMS or multi-tenant portal backend |
| Interchange | Backstage and ArchiMate/Archi import/export | Supported mappings only; no universal lossless interchange guarantee |
| Remote APM | GraphQL application fetch/TIME patch adapter | Endpoint-specific schema; not complete central-EAM synchronization |
| Validation | Integrity checks, strict schema typo rejection (`extra='forbid'`), scoped discovery (`tecton.yaml`), and empty workspace detection | Supported metamodel only; does not infer missing business attributes |

## Future ideas

- Automated discovery and OpenAPI/AsyncAPI/Protobuf ingestion.
- Maturity aggregation and richer realization roles.
- Owner surveys, editing forms and in-app approval workflows.
- In-place transactional multi-file graph changes.
- Persistent query cache and incremental graph compilation.
- Broader EAM/CMDB connectors and organization-wide Git-catalog operation.
- Natural-language exploration or AI enrichment, if justified by a user need.


These are candidates, not commitments or CLI commands. A new capability should
include source-of-truth ownership, failure behavior and validation evidence
before being described as available.

Review freshness, owner policies, full semantic diff, subtree coverage, decimal
costs, business cases and resource/budget feasibility are implemented. See
[catalog review and planning](catalog_planning.md) for their exact limits.
