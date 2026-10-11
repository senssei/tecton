# 🏛️ Architecture decision records

Accepted means the decision guides this project; it does not imply every future
consequence or extension has already been implemented.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-hexagonal-architecture.md) | Repository adapters and dependency boundaries | Accepted |
| [0002](0002-deterministic-offline-engines.md) | Local analytical engines | Accepted; time control remains partial |
| [0003](0003-safety-first-mutation-policy.md) | Dry-run repository patches | Accepted; output-file generation excluded |
| [0004](0004-sovereign-mermaid-visualizations.md) | Mermaid/Markdown outputs | Accepted; visual rendering needs a viewer |
| [0005](0005-attribute-driven-design-methodology.md) | Quality-attribute review discipline | Accepted |
| [0006](0006-git-backed-eam-graph-and-c4-extended-dsl.md) | Git-backed workspace model and validation | Accepted; central organization-wide adoption open |
| [0007](0007-git-eam-catalog-pilot.md) | Pilot on Tecton's own architecture | Accepted |

Create a new numbered ADR when changing a lasting decision. Include context,
the chosen behavior, alternatives/trade-offs and implementation limits. Update
this index and cross-link the affected user guide.
