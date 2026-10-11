# 🔌 Repository boundaries and integration assumptions

An architecture repository stores a declared model. Tecton adds validation,
analysis and reporting around that model. Whether a remote product also offers
these capabilities depends on its actual API, license and configuration; this
project does not claim they are absent across the EAM market.

## Responsibilities

| Concern | Tecton responsibility | Input or integration responsibility |
| --- | --- | --- |
| Inventory | Parse known manifests and normalize applications | Supply accurate IDs, names, owners and relationships |
| Portfolio | Evaluate TIME and pairwise overlap | Define suitability scores, thresholds and capability mappings |
| Capabilities | Hierarchy, direct realization coverage, gaps and health | Supply capability taxonomy and system mappings |
| Technology | Declared EOL/status checks and dependency impact | Maintain catalog dates and adoption links |
| Data | Traverse declared interfaces/relationships and flag modeled risks | Describe actual flows, classifications and processing attributes |
| Transformation | Compare declared plateaus and work packages | Keep schedules and membership lists current |
| Reporting | Generate Mermaid, Markdown, HTML and interchange files | Host and review outputs; configure viewers and access |

## Current adapters

- `GitRepositoryAdapter`: reads a local file/directory and persists supported
  TIME patches to source manifests. It does not clone, commit or push Git.
- `FileRepositoryAdapter`: reads legacy JSON/YAML application lists. Patches
  affect memory; `save_to_disk()` is an explicit Python operation.
- `InMemoryRepositoryAdapter`: local application test doubles and simulations.
- `GraphQLRepositoryAdapter`: uses `allFactSheets` and `updateFactSheet` operations.
  Its fields and mutation input must match the target endpoint. Its
  `save_application()` currently returns its argument without a remote create.

The GraphQL adapter is not a complete graph workspace adapter. General
`TectonApp` graph use cases need a compiled graph; the application-list repository
port alone does not supply all entity collections. Remote calls are not exercised
against a live service by the shipped test suite.

## Failure modes to account for

Stale source data yields stale analysis. Schema and referential checks catch
structural problems, not undisclosed systems or incorrect ownership. Import/export
mapping may discard unsupported fields. A remote mutation can partially succeed
before a later application patch fails; bulk synchronization is not transactional.

No production guarantee follows from a passing offline test suite. Evaluate a
new endpoint with snapshots, dry-run patches, explicitly checked mappings and
controlled credentials before enabling real updates.

## Deferred integrations

OpenAPI, AsyncAPI, Protobuf, infrastructure discovery, CMDB synchronization,
webhook ingestion, stakeholder surveys and generic graph database backends are
not implemented. The [capability catalog](04_eam_capabilities_catalog.md) separates
these ideas from current behavior.
