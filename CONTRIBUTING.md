# 🤝 Contributing

Tecton is an alpha architecture-as-code tool. Prefer focused changes with clear
examples, documented behavior and tests for meaningful new logic.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,release]'
python -m pytest
python scripts/check_docs.py
python -m build
python -m twine check --strict dist/*.whl dist/*.tar.gz
python scripts/check_distribution.py
```

Use Python 3.11+; CI exercises 3.11 and 3.14. On Windows activate with
`.venv\Scripts\Activate.ps1`. The CLI remains `tecton`; Python imports use
`tecton_arch`. Install this project into its own environment.

## What to include in a PR

Explain the problem, resulting behavior and validation. Update user-facing
references when changing CLI arguments or model fields. For a significant
architectural choice, add an [ADR](docs/adr/README.md). Do not describe proposed
functions as implemented or claim performance without a reproducible benchmark.

Keep delivery free of direct imports from engines, connectors and the DSL parser;
coordinate through application methods or services. The DSL must not import
engines. `tests/unit/test_architecture.py` enforces these selected boundaries.

## Catalog changes

The canonical pilot is `examples/dogfood/tecton_c4_workspace`. Preserve IDs when
changing display names. Every system needs an owner in the pilot; descriptions
and current lifecycle are maintained by review convention. Components inherit
product ownership/lifecycle by convention.

```bash
tecton validate examples/dogfood/tecton_c4_workspace --require-owner --format json
python -m pytest tests/integration/test_eam_pilot.py tests/integration/test_dogfood.py
```

Deleting a node requires updating its references in the same PR. Validate the
latest merged state, not only the original branch. Generated portal output stays
in ignored `dist/` and CI artifacts. The fictional business example intentionally
includes warnings; do not suppress useful checks merely to make `--strict` pass.

## Issues and conduct

Use the bug/feature templates for reproducible reports. Avoid publishing real
enterprise inventories, credentials or customer data. Be respectful and explain
technical disagreements with evidence. Follow [security reporting guidance](SECURITY.md)
for potentially sensitive vulnerabilities.

Contributions are accepted under [Apache-2.0](LICENSE). Include attribution and
license information when adding third-party material. New vendor asset bundles
must retain their original notices and licenses.
