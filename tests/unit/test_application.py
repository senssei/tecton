from datetime import date
from pathlib import Path
import json
import pytest

from tecton_arch.adapters.file_adapter import FileRepositoryAdapter
from tecton_arch.adapters.in_memory import InMemoryRepositoryAdapter
from tecton_arch.core.models import Application
from tecton_arch.dsl.parser import C4EAMParser

from tecton_arch.application import (
    ExportError,
    TectonApp,
    Workspace,
    WorkspaceNotFoundError,
)


@pytest.fixture
def dogfood_workspace_path() -> Path:
    return Path(__file__).parents[2] / "examples" / "dogfood" / "tecton_c4_workspace"


@pytest.fixture
def eam_workspace_path() -> Path:
    return Path(__file__).parents[2] / "examples" / "c4_eam_workspace"


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

    # 4. Markdown Executive Report
    res_md = app.export("markdown")
    assert res_md.format == "markdown"
    assert "Portfolio Executive Summary" in res_md.content

    # 5. Unknown format raises ExportError
    with pytest.raises(ExportError, match="Unsupported export format"):
        app.export("unsupported-format-xyz")


def test_tecton_app_facade_export_gantt_with_as_of_date(eam_workspace_path: Path):
    app = TectonApp(eam_workspace_path, as_of_date=date(2025, 1, 1))

    # Via TectonApp.as_of_date
    res_gantt = app.export("mermaid", options={"diagram_type": "roadmap-gantt"})
    assert res_gantt.format == "mermaid"
    assert "Evaluation Date :milestone, eval_date, 2025-01-01, 0d" in res_gantt.content

    # Via direct options as_of_date string
    res_gantt_opts = app.export(
        "mermaid",
        options={"diagram_type": "roadmap-gantt", "as_of_date": "2024-05-01"},
    )
    assert "Evaluation Date :milestone, eval_date, 2024-05-01, 0d" in res_gantt_opts.content


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


@pytest.mark.parametrize("repository_kind", ["memory", "file"])
def test_application_listing_without_graph(repository_kind, tmp_path):
    application = Application(
        id="app-demo", name="Demo", functional_suitability=5,
        technical_suitability=5, tags=["pilot"],
        metadata={"owner": "Team", "description": "Example", "technologies": ["python"]},
    )
    if repository_kind == "file":
        path = tmp_path / "applications.json"
        path.write_text(json.dumps([application.model_dump(mode="json")]), encoding="utf-8")
        adapter = FileRepositoryAdapter(path)
    else:
        adapter = InMemoryRepositoryAdapter([application])
    workspace = Workspace(adapter)
    assert workspace.optional_graph is None
    with pytest.raises(AttributeError):
        _ = workspace.graph
    listed = TectonApp(workspace).apm_applications()
    assert len(listed) == 1
    assert listed[0]["components"] == []
    assert listed[0]["time_classification"] == "INVEST"
    assert listed[0]["owner"] == "Team"
    assert listed[0]["description"] == "Example"
    assert listed[0]["technologies"] == ["python"]
    assert listed[0]["tags"] == ["pilot"]


def test_application_components_grouped_and_sorted():
    graph = C4EAMParser().parse_content("""
systems:
  - {id: app-a, name: A}
  - {id: app-b, name: B}
  - {id: app-c, name: C}
containers:
  - {id: z, name: Z, system_id: app-a, description: Last}
  - {id: b, name: B component, system_id: app-b}
  - {id: a, name: A component, system_id: app-a}
""")
    workspace = Workspace.from_graph(graph)
    assert workspace.optional_graph is graph
    listed = TectonApp(workspace).apm_applications()
    assert [c["id"] for c in listed[0]["components"]] == ["a", "z"]
    assert listed[0]["components"][1]["description"] == "Last"
    assert [c["id"] for c in listed[1]["components"]] == ["b"]
    assert listed[2]["components"] == []


@pytest.mark.parametrize("error_type", [ValueError, AttributeError])
def test_application_listing_propagates_graph_loading_errors(error_type):
    class BrokenGraphAdapter(InMemoryRepositoryAdapter):
        @property
        def graph(self):
            raise error_type("Graph loading failed")

    workspace = Workspace(BrokenGraphAdapter([Application(id="demo", name="Demo")]))
    with pytest.raises(error_type, match="Graph loading failed"):
        TectonApp(workspace).apm_applications()


def test_radar_static_and_rest_data_match(dogfood_workspace_path):
    app = TectonApp(dogfood_workspace_path)
    assert app.trm_evaluation()['technologies'] == app.portal_snapshot()['technologies']
    technology = next(t for t in app.trm_evaluation()['technologies'] if t['id'] == 'tech-python-312')
    assert technology['realizing_systems_count'] == len(technology['realizing_system_details'])
    assert technology['realizing_system_details'][0]['owner'] == 'Tecton maintainers'
    assert 'eol_date' in technology and 'is_eol' in technology


def test_tecton_app_temporal_determinism():
    graph = C4EAMParser().parse_content("""
technologies:
  - id: tech-test
    name: Test Tech
    status: approved
    eol_date: 2026-06-01

systems:
  - id: sys-test
    name: Test System
    owner: Architects
    technologies: [tech-test]
    lifecycle:
      phases:
        - phase: plan
          start_date: 2025-01-01
        - phase: active
          start_date: 2026-01-01
        - phase: endOfLife
          start_date: 2026-12-31
""")
    ws = Workspace.from_graph(graph)

    # Eval 2025-06-01 (phase is plan, tech not EOL)
    app_2025 = TectonApp(ws, as_of_date=date(2025, 6, 1))
    overview_2025 = app_2025.overview()
    assert overview_2025.as_of_date == "2025-06-01"
    assert overview_2025.technologies_past_eol == 0
    apps_2025 = app_2025.apm_applications()
    assert apps_2025[0]["current_phase"] == "plan"

    # Eval 2026-08-01 (phase is active, tech is past EOL)
    app_2026 = TectonApp(ws, as_of_date=date(2026, 8, 1))
    overview_2026 = app_2026.overview()
    assert overview_2026.as_of_date == "2026-08-01"
    assert overview_2026.technologies_past_eol == 1
    apps_2026 = app_2026.apm_applications()
    assert apps_2026[0]["current_phase"] == "active"

    snapshot = app_2026.portal_snapshot()
    assert snapshot["as_of_date"] == "2026-08-01"


