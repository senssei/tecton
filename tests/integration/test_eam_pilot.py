"""Pilot acceptance checks use disposable workspaces, never the canonical catalog."""

import json
import shutil
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from tecton_arch.application.app import TectonApp
from tecton_arch.cli.main import app
from tecton_arch.dsl.schema import SoftwareSystemDef
from tecton_arch.portal.builder import PortalBuilder

CATALOG = Path(__file__).parents[2] / "examples/dogfood/tecton_c4_workspace"
runner = CliRunner()


@pytest.fixture
def workspace(tmp_path):
    target = tmp_path / "catalog"
    shutil.copytree(CATALOG, target)
    return target


def write_manifest(workspace, name, data):
    (workspace / name).write_text(yaml.safe_dump(data), encoding="utf-8")


def validate(workspace, require_owner=True):
    args = ["validate", str(workspace), "--format", "json"]
    if require_owner:
        args.append("--require-owner")
    result = runner.invoke(app, args)
    return result.exit_code, json.loads(result.output)


def test_owner_is_optional_for_existing_manifests(tmp_path):
    assert SoftwareSystemDef(id="old", name="Existing system").owner is None
    write_manifest(tmp_path, "old.yaml", {"systems": [{"id": "old", "name": "Existing system"}]})
    assert validate(tmp_path, require_owner=False)[0] == 0
    code, report = validate(tmp_path)
    assert code == 1
    assert report["issues"][0]["rule"] == "MISSING_SYSTEM_OWNER"


@pytest.mark.parametrize("owner", [None, "", "   "])
def test_missing_owner_blocks_pilot(workspace, owner):
    path = workspace / "systems.yaml"
    manifest = yaml.safe_load(path.read_text())
    manifest["systems"][0]["owner"] = owner
    write_manifest(workspace, path.name, manifest)
    assert validate(workspace)[0] == 1


def test_component_add_owner_change_and_atomic_removal(workspace, tmp_path):
    assert validate(workspace)[0] == 0
    added = {"id": "component-pilot", "name": "Pilot component", "system_id": "sys-tecton"}
    write_manifest(workspace, "new-component.yaml", {"containers": [added]})
    write_manifest(workspace, "new-edge.yaml", {"relationships": [{
        "source_id": "sys-tecton-cli", "target_id": "component-pilot",
    }]})
    assert validate(workspace)[0] == 0
    product = yaml.safe_load((workspace / "systems.yaml").read_text())
    product["systems"][0]["owner"] = "Pilot architecture team"
    write_manifest(workspace, "systems.yaml", product)
    application = TectonApp(workspace)
    assert validate(workspace)[0] == 0
    assert application.apm_applications()[0]["owner"] == "Pilot architecture team"
    snapshot = application.portal_snapshot()
    assert snapshot["applications"][0]["owner"] == "Pilot architecture team"
    assert added["id"] in {c["id"] for c in snapshot["applications"][0]["components"]}
    html = PortalBuilder.export_portal(application, tmp_path / "portal").read_text()
    assert "Pilot architecture team" in html
    assert "Pilot component" in html
    assert "escapeHtml(app.owner" in html
    (workspace / "new-component.yaml").unlink()
    assert validate(workspace)[0] == 1
    (workspace / "new-edge.yaml").unlink()
    assert validate(workspace)[0] == 0


def test_duplicate_ids_after_combining_changes_block_merge(workspace):
    component = {"id": "component-shared", "name": "New component", "system_id": "sys-tecton"}
    write_manifest(workspace, "branch-a.yaml", {"containers": [component]})
    assert validate(workspace)[0] == 0
    (workspace / "branch-a.yaml").unlink()
    write_manifest(workspace, "branch-b.yaml", {"containers": [component]})
    assert validate(workspace)[0] == 0
    write_manifest(workspace, "branch-a.yaml", {"containers": [component]})
    code, report = validate(workspace)
    assert code == 1
    assert any(i["rule"] == "DUPLICATE_ID" for i in report["issues"])


def test_valid_parallel_changes_can_create_dangling_reference(workspace):
    components = yaml.safe_load((workspace / "components.yaml").read_text())
    removed_id = "sys-tecton-connectors"
    # Branch A deletes an unreferenced component; valid alone.
    components["containers"] = [c for c in components["containers"] if c["id"] != removed_id]
    write_manifest(workspace, "components.yaml", components)
    assert validate(workspace)[0] == 0
    # Branch B adds an edge to the original component; valid alone.
    shutil.copyfile(CATALOG / "components.yaml", workspace / "components.yaml")
    write_manifest(workspace, "branch-b.yaml", {"relationships": [{
        "source_id": "sys-tecton-cli", "target_id": removed_id,
    }]})
    assert validate(workspace)[0] == 0
    # Their textually clean combination must fail validation.
    write_manifest(workspace, "components.yaml", components)
    assert validate(workspace)[0] == 1
