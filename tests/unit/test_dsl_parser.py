"""Unit tests for C4-Extended EAM DSL parser and graph compiler."""

from pathlib import Path
import pytest
from tecton.dsl.parser import C4EAMParser, SymbolTable
from tecton.dsl.schema import (
    BusinessCapabilityDef,
    ContainerDef,
    RelationshipDef,
    SoftwareSystemDef,
    TechnologyDef,
)


def test_parser_single_document_content():
    content = """
    capabilities:
      - id: cap-1
        name: Capability One
        level: L1
    systems:
      - id: sys-1
        name: System One
        functional_suitability: 4.0
        technical_suitability: 4.0
        capabilities: [cap-1]
    technologies:
      - id: tech-1
        name: Tech One
        category: runtime
    relationships:
      - source_id: sys-1
        target_id: sys-1
        relation_type: self_call
    """
    parser = C4EAMParser()
    graph = parser.parse_content(content)

    assert len(graph.capabilities) == 1
    assert "cap-1" in graph.capabilities
    assert len(graph.systems) == 1
    assert "sys-1" in graph.systems
    assert len(graph.technologies) == 1
    assert "tech-1" in graph.technologies
    assert len(graph.relationships) == 1

    apps = graph.get_applications()
    assert len(apps) == 1
    assert apps[0].id == "sys-1"
    assert apps[0].name == "System One"


def test_parser_symbol_collision_detection():
    content = """
    systems:
      - id: dup-id
        name: System First
      - id: dup-id
        name: System Second
    """
    parser = C4EAMParser()
    graph = parser.parse_content(content, file_origin="test_file.yaml")

    assert len(graph.duplicate_ids) == 1
    dup_id, orig1, orig2 = graph.duplicate_ids[0]
    assert dup_id == "dup-id"


def test_parser_directory_c4_workspace():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    parser = C4EAMParser()
    graph = parser.parse_directory(workspace)

    assert len(graph.files_parsed) == 7
    assert len(graph.capabilities) >= 6
    assert len(graph.systems) == 3
    assert len(graph.technologies) >= 4
    assert len(graph.relationships) == 2
    assert len(graph.data_objects) == 3
    assert len(graph.interfaces) == 2
    assert len(graph.plateaus) == 2
    assert len(graph.work_packages) == 2

    # Verify relationship index
    outgoing = graph.outgoing_relationships("sys-crm-core")
    assert len(outgoing) == 1
    assert outgoing[0].target_id == "sys-order-router"

    incoming = graph.incoming_relationships("sys-order-router")
    assert len(incoming) == 1
    assert incoming[0].source_id == "sys-crm-core"


def test_parser_invalid_syntax_raises_value_error():
    parser = C4EAMParser()
    with pytest.raises(ValueError, match="YAML/JSON syntax error"):
        parser.parse_content(": this is invalid [yaml:")


def test_parser_ignores_non_architecture_files_and_build_dirs(tmp_path):
    # Valid architecture file
    (tmp_path / "systems.yaml").write_text(
        "systems:\n  - id: sys-valid\n    name: Valid System\n",
        encoding="utf-8",
    )
    # Ignored directory
    nm_dir = tmp_path / "node_modules" / "some_pkg"
    nm_dir.mkdir(parents=True)
    (nm_dir / "package.json").write_text('{"name": "ignored", "id": "ignored"}', encoding="utf-8")

    # Generic file without architectural attributes or system ID prefix
    (tmp_path / "ci_config.yaml").write_text(
        "id: generic-job\nname: build-step\nother_key: 123\n",
        encoding="utf-8",
    )

    parser = C4EAMParser()
    graph = parser.parse_directory(tmp_path)

    assert "sys-valid" in graph.systems
    assert "ignored" not in graph.systems
    assert "generic-job" not in graph.systems

