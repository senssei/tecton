"""Integration tests for GitRepositoryAdapter."""

from pathlib import Path
import pytest
from tecton.adapters.git_adapter import GitRepositoryAdapter
from tecton.core.models import TimeQuadrant


def test_git_adapter_loads_c4_workspace():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    adapter = GitRepositoryAdapter(workspace)

    apps = adapter.fetch_applications()
    assert len(apps) == 3

    app_ids = {a.id for a in apps}
    assert "sys-crm-core" in app_ids
    assert "sys-order-router" in app_ids
    assert "sys-legacy-billing" in app_ids

    crm = adapter.get_application("sys-crm-core")
    assert crm is not None
    assert crm.name == "Global CRM Platform"
    assert crm.time_classification == TimeQuadrant.INVEST
    assert "cap-order-capture" in crm.capabilities


def test_git_adapter_apply_patches_dry_run():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    adapter = GitRepositoryAdapter(workspace)

    patches = [
        {"op": "replace", "path": "/timeClassification", "value": "TOLERATE"}
    ]
    result = adapter.apply_patches("sys-crm-core", patches, dry_run=True)

    assert result["dry_run"] is True
    assert result["applied_count"] == 1

    # In dry-run, memory state should remain unchanged
    crm = adapter.get_application("sys-crm-core")
    assert crm is not None
    assert crm.time_classification == TimeQuadrant.INVEST


def test_git_adapter_apply_patches_persist_success(tmp_path: Path):
    manifest = tmp_path / "apps.yaml"
    manifest.write_text("""
systems:
  - id: sys-app1
    name: App One
    time_classification: INVEST
""", encoding="utf-8")

    adapter = GitRepositoryAdapter(tmp_path)
    patches = [{"op": "replace", "path": "/time_classification", "value": "MIGRATE"}]
    result = adapter.apply_patches("sys-app1", patches, dry_run=False)

    assert result["dry_run"] is False
    assert result["applied_count"] == 1
    assert "MIGRATE" in manifest.read_text(encoding="utf-8")


def test_git_adapter_apply_patches_persist_failure(tmp_path: Path):
    manifest = tmp_path / "apps.yaml"
    manifest.write_text("""
systems:
  - id: sys-app1
    name: App One
""", encoding="utf-8")

    adapter = GitRepositoryAdapter(tmp_path)
    # Patching a non-existent entity with dry_run=False
    patches = [{"op": "replace", "path": "/time_classification", "value": "MIGRATE"}]
    with pytest.raises(Exception):
        adapter.apply_patches("sys-unknown-id", patches, dry_run=False)
