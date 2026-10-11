"""Reject publication from a tag that does not match the checked-out version."""

import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
tag = sys.argv[1]
assert tag == "v" + project["version"], "Release tag must equal v + project version"
expected = subprocess.check_output(["git", "rev-parse", f"{tag}^{{commit}}"], cwd=ROOT, text=True).strip()
actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
assert expected == actual, "Checkout must match the tagged commit"
from tecton_arch import __version__
assert __version__ == project["version"], "Installed/source version must match release metadata"
print(f"Release tag OK: {tag}")
