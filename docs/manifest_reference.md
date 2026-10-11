# 🗂️ Manifest reference

The Python definitions in [schema.py](../src/tecton_arch/dsl/schema.py) are the
source of truth. This is a project-specific YAML/JSON metamodel inspired by C4;
it is not Structurizr DSL and does not implement the full ArchiMate metamodel.

## Collections

A file can contain any subset of the following top-level lists. A workspace
combines entries across files; YAML multi-document input is supported for reading.

| Collection | Required fields | Selected optional fields |
| --- | --- | --- |
| `systems` | `id`, `name` | `description`, `owner`, suitability scores, lifecycle, capabilities, technologies, user groups, tags, metadata |
| `containers` | `id`, `name`, `system_id` | `description`, `technology` (catalog ID) |
| `capabilities` | `id`, `name` | `description`, `level`, `parent_id` |
| `technologies` | `id`, `name` | `category`, `status`, `eol_date`, description |
| `relationships` | `source_id`, `target_id` | `relation_type`, `technology` (protocol label), `data_objects`, description |
| `data_objects` | `id`, `name` | classification, PII/regulatory flags, description, owner |
| `interfaces` | `id`, `name`, `provider_system_id` | consumer IDs, protocol, data object IDs, description |
| `plateaus` | `id`, `name` | target date, previous plateau, active/decommissioned system IDs |
| `work_packages` | `id`, `name` | dates, status, owner, plateau links, system/capability IDs, prerequisites |

For the pilot, `containers` holds logical implementation components of one
product. These are not claimed to be independently deployed C4 containers.
Only `systems` become applications in portfolio analysis. Child components
inherit the product's ownership/lifecycle by pilot convention, not through
separate component fields.

## Minimal connected model

```yaml
capabilities:
  - id: cap-orders
    name: Order management
    level: L1
technologies:
  - id: tech-python
    name: Python
    category: runtime
    status: approved
systems:
  - id: sys-orders
    name: Orders
    owner: Commerce team
    description: Order processing application
    current_phase: active
    capabilities: [cap-orders]
    technologies: [tech-python]
containers:
  - id: component-orders-api
    name: Orders API
    system_id: sys-orders
    technology: tech-python
relationships:
  - source_id: component-orders-api
    target_id: sys-orders
    relation_type: uses
```

## IDs and references

Entity IDs share a global namespace across collections. Use stable, readable IDs;
kebab-case is a convention, not a schema-enforced format. Changing a display name
should preserve the ID. Renaming IDs or deleting entities requires updating every
reference in the same reviewed change. There is no automatic rename/refactor CLI.
Relationships have no standalone ID in this schema.

A system's `capabilities` list drives BCM realization analysis; use that list
rather than expecting an arbitrary `realizes` relationship to populate coverage.
A relationship is directed from source to target. Dependency-cycle checks cover
`depends_on`, `uses` and `integrates_with`. `relation_type` accepts arbitrary strings;
the schema does not enforce a closed vocabulary or single-leading-system cardinality.

The graph linter checks cross-references. Technology checks depend on a nonempty
technology catalog; define that catalog when using technology IDs. Use one
workspace rather than relying on reference resolution across separate CLI calls.

## Scores, enums and dates

- Suitability scores are numbers from `1.0` through `5.0`; missing values yield
  `UNKNOWN` in calculated TIME classification.
- TIME values: `INVEST`, `TOLERATE`, `MIGRATE`, `ELIMINATE`, `UNKNOWN`.
- Lifecycle values: `plan`, `phaseIn`, `active`, `phaseOut`, `endOfLife`.
- Technology status: `approved`, `under_evaluation`, `deprecated`, `prohibited`.
- Data classification: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED_PII`, `PCI_DSS`.
- Work-package status: `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`.
- Dates use ISO `YYYY-MM-DD`; lifecycle schedules use `lifecycle.phases` entries
  with `phase` and `start_date`.

`current_phase` can be explicit or inferred from the lifecycle and today's date.
Some analysis APIs accept `as_of_date`; a global historical date is not exposed
by the CLI. Unknown model fields are generally ignored, so validation is not a
strict typo detector. `level` is a free string; L1/L2/L3 are conventions.

## Discovery and validation severity

The loader reads `.yaml`, `.yml` and `.json`, skips hidden paths and common build,
virtual-environment and dependency directories, and supports explicit `kind` for
individual entities. It also retains heuristic detection of entity-like mappings.
Prefer a dedicated catalog path; do not expect arbitrary repository JSON to be safe
from heuristic ingestion.

Duplicate IDs, dangling references and capability hierarchy cycles are errors.
Dependency cycles and some date/technology findings are warnings. `--strict`
blocks warnings; `--require-owner` rejects missing or whitespace-only system
owners. It does not require system descriptions or lifecycle phases globally.
