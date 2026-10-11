# 🛠️ Architecture review and remaining limitations

Reviewed against the current source on 2026-10-11. This replaces the initial
refactoring snapshot, which described startup/import failures that have since
been resolved. It is an engineering assessment, not a production readiness certification.

## Resolved or materially improved

| Finding | Current state | Evidence |
| --- | --- | --- |
| Deleted DSL-linter imports blocked startup | Callers use the engine linter through application/services | CLI/API/portal integration tests |
| Delivery imported engines/connectors/parser directly | AST-enforced import boundaries cover delivery and DSL, including relative imports | `tests/unit/test_architecture.py` |
| Architecture test merely observed violations | Test asserts zero violations and is included in CI | Same fitness test and workflows |
| Git patches mutated memory before failed disk writes | Supported TIME patches replace a file before reloading graph/storage | Git adapter failure/persistence tests |
| Workspace only accepted a filesystem path | It also accepts a compiled graph or repository object | Application facade tests |
| Broad parsing included generated/hidden content | Hidden and common build/dependency paths are excluded | Parser unit tests |
| Static/live portal application payloads diverged | Shared application serialization includes owners and child components | Pilot/portal tests |
| Portal loaded external network assets | Bundled offline assets include D3 7.9.0, Mermaid 10.9.8, and Tailwind CSS 3.4.17 runtime with zero CDN requests | Browser offline tests (`tests/browser/test_radar.py`) and distribution checks |
| Partial time determinism | Global `as_of_date` temporal evaluation injected across domain models (`phase_as_of`), engines, application DTOs, CLI subcommands (`validate`, `trm`, `apm`, `roadmap`, `export portal`), and REST API | `tests/unit/test_roadmap_engine.py`, `tests/unit/test_application.py`, `tests/integration/test_server.py`, `test_validate_cli.py`, `test_trm_cli.py`, `test_roadmap_cli.py` |
| Discovery and schema strictness | Manifest discovery is scoped via `tecton.yaml` (`include`/`exclude`), configuration files are excluded from manifests, empty workspaces trigger `EMPTY_WORKSPACE` (error in strict mode), and unknown entity fields are strictly rejected (`extra="forbid"`) | `tests/unit/test_dsl_parser.py`, `tests/integration/test_validate_cli.py` |

These changes do not eliminate all coupling, mutation or ingestion risks.

## Remaining limits

1. **Concrete graph coupling.** Services/engines use `CompiledGraph`, and an
   application-only repository does not supply a complete EAM graph. Facade
   methods mix typed DTOs and dictionaries.
2. **Persistence boundaries.** Supported writes are TIME updates in certain
   manifest layouts. Replacement is atomic for one file; a later reload failure
   or multiple updates do not have a transactional rollback guarantee. General
   JSON Patch semantics, concurrent-write locking and formatting preservation
   are not provided.
3. **Local API access.** Read endpoints are unauthenticated. Optional token
   checking applies only to reload. `--reload` currently has no file-watching
   effect. Production hosting needs external access controls and a refresh plan.
4. **Interchange coverage.** Connectors map supported entities and preserve IDs
   through annotations/properties. Field-complete round trips, external XSD
   validation and arbitrary tool compatibility are not established.

## Follow-up order

Broaden persistence only with explicit patch contracts, validation-before-write
and failure tests. Benchmark representative data before stating latency or scale
guarantees.


## Review procedure

Run unit/integration tests, the AST boundary check, documentation smoke checks
and a wheel-install smoke test. Check changed interfaces against the
[manifest](manifest_reference.md) and [CLI](cli_reference.md) references. Use the
[pilot](08_git_eam_pilot.md) to test model maintenance separately from engine correctness.
