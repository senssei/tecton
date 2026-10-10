"""Unit tests for Repository Adapters."""

from pathlib import Path
from tecton.adapters.file_adapter import FileRepositoryAdapter
from tecton.adapters.in_memory import InMemoryRepositoryAdapter
from tecton.core.models import Application, TimeQuadrant


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
