"""Architectural boundary fitness tests enforcing hexagonal layer separation.

Rules:
1. Delivery layer (`cli`, `server`, `portal`) must NOT import directly from:
   - `tecton_arch.engines`
   - `tecton_arch.connectors`
   - `tecton_arch.dsl.parser`
   Delivery must coordinate use cases via `tecton_arch.application` (or `tecton_arch.core`).
2. Domain / DSL layer (`tecton_arch.dsl`) must NOT import from `tecton_arch.engines`.
"""

import ast
import os
from pathlib import Path
from typing import NamedTuple


class ImportViolation(NamedTuple):
    file_path: str
    line_number: int
    imported_module: str
    violation_type: str


def scan_architecture_violations(src_dir: Path | None = None) -> list[ImportViolation]:
    """Scan source code AST for hexagonal and delivery boundary violations, resolving relative imports."""
    if src_dir is None:
        src_dir = Path(__file__).parents[2] / "src" / "tecton_arch"

    violations: list[ImportViolation] = []

    for root, _, files in os.walk(src_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = Path(root) / f
            rel = path.relative_to(src_dir)
            module_parts = rel.parts
            layer = module_parts[0]

            # Determine package tuple for resolving relative imports
            if f == "__init__.py":
                pkg_parts = ("tecton_arch",) + module_parts[:-1]
            else:
                pkg_parts = ("tecton_arch",) + module_parts[:-1]

            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                imported_modules: list[str] = []
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        # Relative import resolution
                        cutoff = len(pkg_parts) - (node.level - 1)
                        base_parts = pkg_parts[:cutoff] if cutoff > 0 else ("tecton_arch",)
                        if node.module:
                            resolved = ".".join(base_parts) + "." + node.module
                        else:
                            resolved = ".".join(base_parts)
                        imported_modules.append(resolved)
                    elif node.module:
                        imported_modules.append(node.module)

                for imported in imported_modules:
                    # Rule 1: Delivery layer isolation
                    if layer in ("cli", "server", "portal"):
                        for forbidden in ("tecton_arch.engines", "tecton_arch.connectors", "tecton_arch.dsl.parser"):
                            if imported == forbidden or imported.startswith(forbidden + "."):
                                violations.append(
                                    ImportViolation(
                                        file_path=str(rel),
                                        line_number=node.lineno,
                                        imported_module=imported,
                                        violation_type="delivery_layer_bypass",
                                    )
                                )

                    # Rule 2: DSL must not depend on engines
                    if layer == "dsl":
                        if imported == "tecton_arch.engines" or imported.startswith("tecton_arch.engines."):
                            violations.append(
                                ImportViolation(
                                    file_path=str(rel),
                                    line_number=node.lineno,
                                    imported_module=imported,
                                    violation_type="dsl_depends_on_engines",
                                )
                            )

    return violations


def test_architecture_violations_report():
    """Strict architectural boundary gate: enforces 0 hexagonal layer violations."""
    violations = scan_architecture_violations()
    assert len(violations) == 0, f"Found {len(violations)} architectural violations: {violations}"
