"""Exercise an installed wheel from a temporary directory, outside the source tree."""

import json
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import tecton_arch
from tecton_arch.application import TectonApp
from tecton_arch.server.app import create_app

ROOT = Path(__file__).resolve().parents[1]
assert not Path(tecton_arch.__file__).resolve().is_relative_to(ROOT / "src"), "Install a wheel, not an editable checkout"
assert tecton_arch.__version__ == version("tecton-arch")
entrypoint = Path(sys.executable).parent / ("tecton.exe" if sys.platform == "win32" else "tecton")
assert entrypoint.is_file(), "Missing installed console command"
with tempfile.TemporaryDirectory() as folder:
    cwd = Path(folder)
    workspace = cwd / "architecture"
    workspace.mkdir()
    (workspace / "catalog.yaml").write_text(
        "systems:\n  - id: sys-wheel\n    name: Wheel smoke\n    owner: Test team\n    current_phase: active\n",
        encoding="utf-8",
    )
    def run(*args):
        return subprocess.check_output([str(entrypoint), *args], cwd=cwd, text=True, timeout=30)
    assert tecton_arch.__version__ in run("--version")
    report = json.loads(run("validate", str(workspace), "--require-owner", "--format", "json"))
    assert report["valid"]
    run("apm", "analyze", "--source", str(workspace))
    run("export", "portal", "--source", str(workspace), "-o", str(cwd / "portal"))
    portal_html = (cwd / "portal/index.html").read_text()
    assert "Wheel smoke" in portal_html
    assert "Tailwind Labs" in portal_html
    assert "Knut Sveidqvist" in portal_html
    assert TectonApp(workspace).apm_applications()[0]["owner"] == "Test team"
    assert "/api/v1/apm/applications" in create_app(workspace).openapi()["paths"]
print("Installed wheel OK: import, version, CLI, validation, analysis, portal and API schema")
