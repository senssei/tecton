# 🏛️ Product vision

Tecton helps architects and engineers maintain an architecture catalog as
reviewable data. A model in Git can be validated before merging, analyzed locally,
and published as reports or a read-only portal.

## Users and value

- **Architects:** maintain applications, capabilities, dependencies and transformation scenarios.
- **Tech leads:** own catalog entries and review changes alongside engineering work.
- **Platform teams:** run model checks in CI and export snapshots for shared documentation.
- **Portfolio stakeholders:** read coverage, suitability and technology-impact reports.

The value is explicit rules, versioned inputs and repeatable local analysis.
These functions complement an existing EAM repository or support a lightweight
Git catalog. They do not depend on claims that commercial EAM APIs lack analytics.

## Current product

Version 0.1.0 is an alpha Python modular monolith. It provides a CLI, Python
application facade, local REST API, manifest parser, graph validation, analytic
engines and report/export adapters. See the [capability catalog](04_eam_capabilities_catalog.md)
for the implemented feature boundary.

Local engines consume supplied metadata. A remote GraphQL adapter demonstrates
application querying and TIME patches for a particular `allFactSheets` schema;
it is not a universal EAM client or evidence of tested production vendor support.

## Git as a central EAM catalog

The [pilot](08_git_eam_pilot.md) makes Git authoritative for Tecton's own model.
Maintainers edit YAML, another person reviews the PR, CI validates the merged
graph, and the portal exposes the accepted snapshot.

Choosing Git as the organization-wide EAM source of truth remains open. The
pilot must first show that ownership, update effort and reviewer workflow work
in practice; a real business domain must then test organizational adoption.

## Future directions

Automatic discovery from code, OpenAPI/AsyncAPI ingestion, editing forms and broader remote integrations are future work.
ID refactoring to isolated catalogs and bundled offline portals are implemented. They are not shipped features.

Tecton currently uses deterministic heuristics rather than an LLM. Suitability
scores and risk labels are decision inputs, not objective measurements of all
architectural quality or evidence of legal compliance.
