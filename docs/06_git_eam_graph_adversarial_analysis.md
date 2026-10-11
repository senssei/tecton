# 🔎 Git-backed graph risks

Git stores versioned files. The architecture model is a graph spanning those
files. A conflict-free text merge does not imply a consistent graph.

## Risks and current defenses

| Risk | Current defense | Remaining limit |
| --- | --- | --- |
| Deleted entity leaves references | Graph linter checks endpoints and entity references | Checks only the supplied workspace; some catalog-dependent checks require catalog entries |
| Two valid branches combine into an invalid graph | CI checks PR synthetic merge commits and merge groups | Branch protection/up-to-date checks must be configured in GitHub |
| Duplicate IDs across files/types | Global symbol registry reports duplicates | No distributed namespace federation |
| Capability hierarchy cycle | Validation error | No automatic graph repair |
| Architectural dependency cycle | Warning for `depends_on`, `uses`, `integrates_with` | Default pilot allows warnings; `--strict` blocks them |
| Name-based ID changes | Stable-ID convention and reviewed reference edits | No rename CLI or alias/refactoring engine |
| Too many files or broad scan | Dedicated catalog path and ignored build/hidden paths | Heuristic ingestion remains; no configurable manifest glob scope |
| Cold graph loading | In-memory symbol and adjacency indexes | No on-disk compiled cache; no published scale/latency benchmark |
| Text rewrite during persistence | Single-file temporary write and atomic replacement | TIME-only persistence; comments/formatting and multi-file atomicity not preserved |

## Concurrent-change example

Branch A removes a currently unreferenced component. Branch B adds a dependency
to that component. Each passes against the original main branch; their combination
contains a dangling reference. Another case is two branches introducing the same
ID in different files. Both can merge textually without a conflict.

The [pilot acceptance tests](../tests/integration/test_eam_pilot.py) construct
these combined states and require validation to fail. Required checks must run
again after updating the PR branch or in a merge queue.

## Practical repository design

Keep one catalog workspace with shared capability/technology vocabularies.
Split manifests by domain or responsibility when that improves review. Avoid
combining independent example catalogs. Keep generated portal output outside
source manifests and do not version it as a second source of truth.

Git history is content-addressed and reviewable, but can be rewritten. Audit
retention, access rules, backups and protected branches are operational choices,
not properties guaranteed by Git or the linter alone.

This schema uses C4-inspired concepts plus EAM fields. It does not implement
Structurizr syntax, UUID/slug aliasing, mandatory DAGs for every relation,
exclusive realization cardinality or full graph database semantics.
