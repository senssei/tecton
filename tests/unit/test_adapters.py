"""Unit tests for Repository Adapters."""

from datetime import date
from pathlib import Path
from tecton_arch.adapters.file_adapter import FileRepositoryAdapter
from tecton_arch.adapters.in_memory import InMemoryRepositoryAdapter
from tecton_arch.core.models import Application, Lifecycle, LifecyclePhase, TimeQuadrant


def test_in_memory_adapter_crud() -> None:
    adapter = InMemoryRepositoryAdapter()
    app = Application(id="a-1", name="App 1", functional_suitability=3.0)
    adapter.save_application(app)

    apps = adapter.fetch_applications()
    assert len(apps) == 1
    assert apps[0].name == "App 1"


def test_in_memory_adapter_patches_dry_run_and_apply() -> None:
    adapter = InMemoryRepositoryAdapter([
        Application(id="a-2", name="App 2", time_classification=TimeQuadrant.UNKNOWN)
    ])

    patch = [{"op": "replace", "path": "/timeClassification", "value": "INVEST"}]

    # Dry run
    res_dry = adapter.apply_patches("a-2", patch, dry_run=True)
    assert res_dry["dry_run"] is True
    assert adapter.get_application("a-2").time_classification == TimeQuadrant.UNKNOWN

    # Apply
    res_apply = adapter.apply_patches("a-2", patch, dry_run=False)
    assert res_apply["dry_run"] is False
    assert adapter.get_application("a-2").time_classification == TimeQuadrant.INVEST


def test_file_adapter_loads_fixture() -> None:
    fixture_path = Path("tests/fixtures/sample_applications.json")
    adapter = FileRepositoryAdapter(fixture_path)
    apps = adapter.fetch_applications()
    assert len(apps) >= 5
    app_names = [a.name for a in apps]
    assert "Global Salesforce CRM" in app_names
    assert "Mainframe Core Ledger" in app_names


def test_in_memory_adapter_preserves_explicit_current_phase_when_lifecycle_has_no_phases() -> None:
    app = Application(
        id="app-explicit",
        name="Explicit Phase App",
        current_phase=LifecyclePhase.ACTIVE,
        lifecycle=Lifecycle(phases=[]),
    )
    adapter = InMemoryRepositoryAdapter([app])
    target_date = date(2025, 1, 1)

    fetched = adapter.fetch_applications(as_of_date=target_date)
    assert len(fetched) == 1
    assert fetched[0].current_phase == LifecyclePhase.ACTIVE


def test_file_adapter_preserves_explicit_current_phase_when_lifecycle_has_no_phases(tmp_path: Path) -> None:
    manifest_file = tmp_path / "apps.yaml"
    manifest_file.write_text(
        """
        - id: app-yaml-explicit
          name: YAML Explicit App
          current_phase: active
          lifecycle:
            phases: []
        - id: app-yaml-string
          name: YAML String App
          lifecycle:
            as_string: active
            phases: []
        """,
        encoding="utf-8",
    )
    adapter = FileRepositoryAdapter(manifest_file)
    target_date = date(2025, 1, 1)

    fetched = adapter.fetch_applications(as_of_date=target_date)
    assert len(fetched) == 2
    assert fetched[0].current_phase == LifecyclePhase.ACTIVE
    assert fetched[1].current_phase == LifecyclePhase.ACTIVE


def test_application_phase_as_of_preserves_explicit_phase() -> None:
    app = Application(
        id="app-model",
        name="Model App",
        current_phase=LifecyclePhase.ACTIVE,
        lifecycle=Lifecycle(phases=[]),
    )
    assert app.phase_as_of(date(2025, 1, 1)) == LifecyclePhase.ACTIVE
