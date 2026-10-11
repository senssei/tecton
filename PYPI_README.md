# Tecton 🏛️

**Enterprise architecture as code: a Git catalog, validation CLI and read-only portal.**

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-green)
![Status: alpha](https://img.shields.io/badge/status-alpha-orange)

Tecton reads YAML/JSON architecture manifests and compiles them into an in-memory
graph. It validates references, evaluates application portfolios, and exports
Mermaid diagrams, Markdown reports and an HTML portal.

**Distribution:** `tecton-arch` · **Import:** `tecton_arch` · **CLI:** `tecton`

This project is independent of the unrelated `tecton` package on PyPI.
Use a separate virtual environment for this CLI to avoid command-name conflicts.

## 🚀 Install

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install tecton-arch
tecton --version
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## 📚 Create a catalog

Save this as `architecture/catalog.yaml`:

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
tecton export portal --source architecture -o portal
tecton portal --source architecture
```

Open `portal/index.html` for the exported view, or `http://127.0.0.1:8000/`
for the local server. The catalog remains editable YAML, with Git providing
version history and reviewed changes.

## ✨ Features

- ✅ Graph checks: duplicate IDs, references, capability hierarchies and lifecycle consistency.
- 📊 Application portfolio: TIME classification and weighted Jaccard overlap detection.
- 🧭 Capability coverage, technology impact, declared data lineage and transformation roadmaps.
- 🔎 Semantic model diff for directory snapshots or Git revisions.
- 🌐 Read-only portal and Mermaid/Markdown exports.
- 🔌 Backstage and ArchiMate interchange for supported entity mappings.

## 🐍 Python use

```python
from tecton_arch.application import TectonApp

catalog = TectonApp("architecture")
report = catalog.validate(require_owner=True)
print(report.model_dump())
```

## ⚠️ Alpha limits

Analysis depends on manually declared metadata. It does not discover deployed
systems, scan dependencies for vulnerabilities, or prove regulatory compliance.
Dependency cycles produce warnings; `validate --strict` promotes warnings to a
failing gate. The HTML export embeds data but uses CDN-hosted Tailwind/Mermaid
assets for full styling and diagrams. Repository patching is dry-run by default;
file imports and exports write their requested output paths.

## 📖 Links

- [Source and issues](https://github.com/senssei/tecton)
- [User guides](https://github.com/senssei/tecton/tree/main/docs)
- [CLI reference](https://github.com/senssei/tecton/blob/main/docs/cli_reference.md)
- [Apache-2.0 license](https://github.com/senssei/tecton/blob/main/LICENSE)
