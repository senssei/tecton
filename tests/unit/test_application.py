"""Unit tests for Tecton application layer, Workspace, and TectonApp facade."""

from pathlib import Path
import pytest

from tecton.application import (
    ExportError,
    TectonApp,
    Workspace,
    WorkspaceNotFoundError,
)


@pytest.fixture
def dogfood_workspace_path() -> Path:
    return Path(__file__).parents[2] / "examples" / "dogfood" / "tecton_c4_workspace"


def test_workspace_initialization_and_reload(dogfood_workspace_path: Path):
    ws = Workspace(dogfood_workspace_path)
    assert ws.path == dogfood_workspace_path.resolve()
    assert len(ws.graph.systems) > 0
    assert len(ws.graph.capabilities) > 0

    reloaded_graph = ws.reload()
    assert len(reloaded_graph.systems) == len(ws.graph.systems)


def test_workspace_raises_on_missing_path(tmp_path: Path):
    missing_dir = tmp_path / "does_not_exist"
    with pytest.raises(WorkspaceNotFoundError):
        Workspace(missing_dir)


def test_tecton_app_facade_health_and_overview(dogfood_workspace_path: Path):
    app = TectonApp(dogfood_workspace_path)
    health = app.health()
    assert health.status == "ok"
    assert health.applications > 0

    overview = app.overview()
    assert overview.total_applications == health.applications
    assert overview.quality_gate_valid is True


def test_tecton_app_facade_validate(dogfood_workspace_path: Path):
    app = TectonApp(dogfood_workspace_path)
    report = app.validate(strict=False)
    assert report.valid is True
    assert isinstance(report.issues, list)


def test_tecton_app_facade_export_formats(dogfood_workspace_path: Path):
    app = TectonApp(dogfood_workspace_path)

    # 1. ArchiMate Open Exchange
    res_exchange = app.export("exchange")
    assert res_exchange.format == "exchange"
    assert "Tecton Architecture Model" in res_exchange.content
    assert res_exchange.media_type == "application/xml"

    # Alias "archimate"
    res_alias = app.export("archimate")
    assert res_alias.format == "exchange"

    # 2. Archi Native format
    res_archi = app.export("archi")
    assert res_archi.format == "archi"
    assert "http://www.archimatetool.com/archimate" in res_archi.content

    # 3. Backstage
    res_backstage = app.export("backstage")
    assert res_backstage.format == "backstage"
    assert "backstage.io/v1alpha1" in res_backstage.content

    # 4. Unknown format raises ExportError
    with pytest.raises(ExportError, match="Unsupported export format"):
        app.export("unsupported-format-xyz")


def test_tecton_app_facade_portal_snapshot(dogfood_workspace_path: Path):
    app = TectonApp(dogfood_workspace_path)
    snapshot = app.portal_snapshot()
    assert "overview" in snapshot
    assert "validation" in snapshot
    assert "applications" in snapshot
    assert "capabilities" in snapshot
    assert "diagrams" in snapshot
    assert "backstage_yaml" in snapshot
    assert "archimate_xml" in snapshot
    assert "archi_native_xml" in snapshot
