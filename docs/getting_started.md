# 🚀 Getting started

## Install

Tecton requires Python 3.11+. The package name is `tecton-arch`, the import
namespace is `tecton_arch`, and the command is `tecton`.

The first release is being prepared. For now, install from a checkout:

```bash
git clone https://github.com/senssei/tecton.git
cd tecton
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
tecton --version
```

Once a release is published, use `python -m pip install tecton-arch` in a virtual
environment. On Windows PowerShell use `.venv\Scripts\Activate.ps1` instead
of `source`. Source installations include the example catalogs; wheels contain
the Python package, so create your own model or download the examples from GitHub.

## Explore the examples

The repository contains two independent workspaces:

- `examples/c4_eam_workspace`: a fictional business landscape covering all analytic domains.
- `examples/dogfood/tecton_c4_workspace`: the pilot catalog for Tecton itself.

Validate each workspace separately. Scanning their common parent combines them
into one graph and may create duplicate IDs or unintended analysis results.

```bash
tecton validate examples/c4_eam_workspace --format json
tecton validate examples/dogfood/tecton_c4_workspace --require-owner
tecton apm analyze --source examples/dogfood/tecton_c4_workspace
tecton bcm analyze --source examples/c4_eam_workspace
```

The business example intentionally includes technology risks and a dependency
cycle. Ordinary validation accepts warnings; `--strict` intentionally fails on
that example. The pilot is expected to pass without warnings.

## Create your own model

Create an `architecture` directory and save this as `architecture/catalog.yaml`:

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
    description: Order processing application
    owner: Commerce team
    current_phase: active
    functional_suitability: 4.5
    technical_suitability: 4.0
    capabilities: [cap-orders]
    technologies: [tech-python]
```

```bash
tecton validate architecture --require-owner
tecton apm analyze --source architecture
tecton export portal --source architecture -o dist/portal
```

Split collections into separate files when useful; references resolve across the
whole supplied workspace. IDs must remain stable when display names change.
See the [manifest reference](manifest_reference.md).

## Browse and refresh

```bash
tecton portal --source architecture
```

Open `http://127.0.0.1:8000/` or the API explorer at
`http://127.0.0.1:8000/docs`. Restart after editing manifests, or use the API's
`POST /api/v1/reload` endpoint. If `TECTON_API_TOKEN` is set, reload requires
that value in an `Authorization: Bearer ...` header; it does not protect read endpoints.
The currently accepted `--reload` CLI option does not implement file watching.

The exported HTML embeds a snapshot of the model. Re-export after changes.
Tailwind and Mermaid are loaded from CDNs; diagrams and full styling need network
access. CLI analysis and Mermaid source generation work on local files.

## Troubleshooting

- **No applications:** supply the architecture directory explicitly. APM defaults
  to a configured remote endpoint or an empty in-memory repository.
- **Unexpected entities or duplicate IDs:** point to one dedicated catalog directory,
  rather than the root of a repository containing multiple examples or fixtures.
- **A YAML file has no effect:** use a documented collection (`systems`, etc.) or
  explicit `kind`. Unknown fields are generally ignored by the Pydantic models.
- **Local server unavailable:** check the requested port and use `--port 8001`.
- **Changes disappear after `patch-time --apply` on a legacy file:** that adapter
  changes in-memory data only; see the [CLI reference](cli_reference.md).
