# 🛠️ CLI reference

Run `tecton --help` and `tecton COMMAND --help` for exact options. All examples
below run from a source checkout. Installed wheels need paths to your own catalog.

## Sources and configuration

For graph commands, `--source` selects a YAML/JSON manifest or a workspace
containing manifests. Omitting it usually selects the current directory.
Use dedicated catalog directories. `validate` takes a positional path instead.

APM has a different source resolver: a directory uses `GitRepositoryAdapter`;
a file uses the legacy application-list adapter. APM file inputs should be a
list or an `applications`/`data` collection, such as
`examples/dogfood/tecton_landscape.json`. A single C4/EAM `systems` file should
instead be supplied through its containing directory for APM.

APM commands accept `--config`. Configuration searches the supplied path, then
`tecton.yaml`, `.tecton.yaml`, `tecton.yml` in the working directory. The first
readable mapping is used; invalid YAML is currently skipped. Environment values
for `TECTON_API_URL`, `TECTON_API_TOKEN`, `TECTON_WORKSPACE`,
`TECTON_DRY_RUN`, `TECTON_TIME_BUSINESS_THRESHOLD` and
`TECTON_TIME_TECHNICAL_THRESHOLD` override loaded values. Workspace selection is
stored in config but is not sent by the current GraphQL adapter. Graph commands
through `TectonApp` use default analysis settings; they do not load APM config.

## ✅ Validation

```bash
tecton validate examples/dogfood/tecton_c4_workspace --require-owner --format json
tecton lint examples/dogfood/tecton_c4_workspace
tecton validate examples/c4_eam_workspace --strict
```

`lint` aliases `validate`. `--require-owner` requires a nonblank owner on every
system, not on child components. `--strict` makes all warnings fail the gate.
JSON reports include `valid`, file count, error/warning counts and issue details.

Exit codes: `0` means no errors (and no warnings in strict mode); `1` means
validation/parsing failure; `2` normally indicates CLI usage errors. A valid but
empty workspace is accepted. Validation does not enforce coverage of all capabilities.

## 📊 Analysis commands

| Domain | Commands | Example |
| --- | --- | --- |
| APM | `list`, `analyze`, `export-matrix`, `patch-time` | `tecton apm analyze --source examples/c4_eam_workspace` |
| BCM | `tree`, `analyze`, `heatmap` | `tecton bcm heatmap --source examples/c4_eam_workspace` |
| TRM | `list`, `blast-radius`, `export-radar` | `tecton trm blast-radius tech-legacy-solaris --source examples/c4_eam_workspace` |
| Data | `list`, `interfaces`, `lineage`, `export-lineage` | `tecton data lineage do-customer-profile --source examples/c4_eam_workspace` |
| Roadmap | `list`, `analyze`, `compare`, `export-gantt` | `tecton roadmap compare plateau-2026-as-is plateau-2027-target --source examples/c4_eam_workspace` |

APM report export supports `--format mermaid` or `--format markdown` and `-o`.
Analysis commands report findings; their success exit code does not imply a
risk-free model. Use `validate` or `diff --fail-on-risk` for explicit gates.

## 🔎 Semantic diff

```bash
tecton diff examples/c4_eam_workspace examples/dogfood/tecton_c4_workspace --format json
tecton diff examples/c4_eam_workspace examples/dogfood/tecton_c4_workspace --format pr-comment -o review.md
```

`--fail-on-risk` returns `1` for newly introduced linter errors or newly unmapped
capabilities. It is a regression check, not a replacement for full validation.
`pr-comment` writes report text; it does not post to GitHub.

`tecton diff main HEAD` is also supported when running inside a dedicated
architecture Git repository. Revision comparison scans each archived tree;
it has no workspace-subpath option. In this project's multi-example repository,
compare explicit workspace directories to avoid combining unrelated models.
`HEAD` means committed files; use `WORKTREE` to request uncommitted state.
Time-sensitive checks use the current date, not each commit's historical date.

## 🌐 Portal and API

```bash
tecton portal --source examples/dogfood/tecton_c4_workspace
tecton serve --source examples/dogfood/tecton_c4_workspace --host 127.0.0.1 --port 8000
tecton export portal --source examples/dogfood/tecton_c4_workspace -o dist/portal
```

`portal` aliases `serve`; both run the same FastAPI app. `--reload` is currently
accepted but has no effect. The server has read endpoints and a reload action,
not catalog-editing forms. API reload optionally checks `TECTON_API_TOKEN`;
read endpoints have no authentication. The UI currently sends no reload token.
Use the default localhost binding for local exploration.

## 🔌 Interchange

```bash
tecton export backstage --source examples/c4_eam_workspace -o dist/catalog-info.yaml
tecton export archimate --source examples/c4_eam_workspace -o dist/model.xml
tecton export archi --source examples/c4_eam_workspace -o dist/model.archimate
tecton import backstage dist/catalog-info.yaml -o dist/imported-backstage
tecton import archimate dist/model.xml -o dist/imported-archimate
```

`export archimate --format archi` also selects native Archi XML. Connectors map
supported entities and preserve IDs through project-specific annotations or
properties. They do not guarantee lossless preservation of every field or schema
conformance for arbitrary input. Review imported models and run validation.

## 💾 Repository mutations

```bash
tecton apm patch-time --source examples/dogfood/tecton_c4_workspace
```

This previews TIME patches. `--apply` explicitly enables persistence for Git
workspaces and the configured GraphQL endpoint. Git persistence currently handles
TIME classification in a `systems` collection or root list and atomically replaces
one file at a time. It is not a general JSON Patch or multi-file transaction engine;
YAML comments/formatting are not preserved. Multi-document patch persistence is
not supported. The legacy file adapter changes memory until `save_to_disk()` is
called programmatically; the CLI does not call it.

There is no `--dry-run` CLI option for `patch-time`: simulation is the default,
controlled by the absence of `--apply`. The config `dry_run` setting does not
override this command's flag. Import/export commands write output paths directly
and do not share this patch-simulation policy.
