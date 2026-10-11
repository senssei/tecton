"""Verify built artifacts contain the intended namespace, license and source material."""

from email.parser import Parser
from pathlib import Path
import tarfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    wheels = list((ROOT / "dist").glob("*.whl"))
    sdists = list((ROOT / "dist").glob("*.tar.gz"))
    assert len(wheels) == len(sdists) == 1, "Use a clean dist directory with one release"
    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()
        assert "tecton_arch/__init__.py" in names
        assert "tecton_arch/portal/template.py" in names
        for asset in ("d3-7.9.0.min.js", "D3-LICENSE", "radar.js", "radar.css", "dfd.js", "roadmap.js", "lineage.js"):
            assert "tecton_arch/portal/assets/" + asset in names
        assert not any(name.startswith("tecton/") for name in names)
        metadata_path = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = Parser().parsestr(archive.read(metadata_path).decode())
        assert metadata["Name"] == project["name"] == "tecton-arch"
        assert metadata["Version"] == project["version"]
        assert metadata["License-Expression"] == "Apache-2.0"
        assert metadata["Requires-Python"] == ">=3.11"
        assert metadata["Description-Content-Type"] == "text/markdown"
        for file in ("LICENSE", "NOTICE"):
            assert any(name.endswith(".dist-info/licenses/" + file) for name in names)
        entries = archive.read(next(name for name in names if name.endswith(".dist-info/entry_points.txt"))).decode()
        assert "tecton = tecton_arch.cli.main:app" in entries
    with tarfile.open(sdists[0]) as archive:
        members = archive.getnames()
        for suffix in ("/LICENSE", "/NOTICE", "/PYPI_README.md", "/docs/manifest_reference.md",
                       "/docs/assets/tecton-mark.svg", "/examples/dogfood/tecton_c4_workspace/systems.yaml",
                       "/tests/integration/test_eam_pilot.py", "/scripts/smoke_installed.py"):
            assert any(name.endswith(suffix) for name in members), f"Missing sdist file: {suffix}"
    print(f"Distribution OK: {wheels[0].name}, {sdists[0].name}")


if __name__ == "__main__":
    main()
