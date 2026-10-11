"""Dogfooding Test: Verifies Tecton auditing its own internal architecture."""

from pathlib import Path
from tecton_arch.adapters.file_adapter import FileRepositoryAdapter
from tecton_arch.core.models import TimeQuadrant
from tecton_arch.exporters.mermaid import MermaidExporter
from tecton_arch.services.apm_service import APMService


def test_dogfood_tecton_self_governance() -> None:
    dogfood_path = Path("examples/dogfood/tecton_landscape.json")
    assert dogfood_path.exists(), "Dogfood landscape model must exist"

    repo = FileRepositoryAdapter(dogfood_path)
    service = APMService(repo)

    result = service.analyze()

    # Tecton landscape contains 7 internal components
    assert len(result.applications) == 7

    # Verify that strategic core modules are classified as INVEST
    assert result.time_classifications["tecton-cli"] == TimeQuadrant.INVEST
    assert result.time_classifications["tecton-engine-time"] == TimeQuadrant.INVEST
    assert result.time_classifications["tecton-engine-redundancy"] == TimeQuadrant.INVEST
    assert result.time_classifications["tecton-engine-lifecycle"] == TimeQuadrant.INVEST

    # Verify that the deprecated prototype script is classified as ELIMINATE
    assert result.time_classifications["tecton-legacy-script"] == TimeQuadrant.ELIMINATE

    # Verify lifecycle validity (Tecton's internal architecture is well-ordered)
    assert result.lifecycle_report.error_count == 0

    # Verify that living Mermaid diagram renders Tecton's own components
    mermaid_chart = MermaidExporter.to_time_quadrant_chart(result.applications, title="Tecton Internal Architecture TIME Matrix")
    assert "quadrantChart" in mermaid_chart
    assert "Tecton Unified CLI Toolchain:" in mermaid_chart
    assert "Tecton TIME Scoring Engine:" in mermaid_chart


def test_dogfood_tecton_c4_workspace() -> None:
    """Verifies that Tecton's self-architecture passes the C4-Extended DSL Quality Gate."""
    from tecton_arch.adapters.git_adapter import GitRepositoryAdapter
    from tecton_arch.engines.linter import GraphLinter
    from tecton_arch.dsl.parser import C4EAMParser

    c4_workspace = Path("examples/dogfood/tecton_c4_workspace")
    assert c4_workspace.exists(), "Tecton C4 dogfood workspace must exist"

    # 1. Validate graph integrity via Quality Gate
    parser = C4EAMParser()
    graph = parser.parse_directory(c4_workspace)
    report = GraphLinter().lint(graph)

    assert report.is_valid is True
    assert report.error_count == 0
    assert report.warning_count == 0
    assert len(graph.systems) == 1
    assert len(graph.containers) == 15
    assert graph.systems["sys-tecton"].owner == "Tecton maintainers"
    assert len(graph.capabilities) == 10
    assert len(graph.relationships) == 9

    # 2. Ingest via GitRepositoryAdapter and analyze APM
    repo = GitRepositoryAdapter(c4_workspace)
    service = APMService(repo)
    result = service.analyze()

    assert len(result.applications) == 1
    assert all(q == TimeQuadrant.INVEST for q in result.time_classifications.values())
