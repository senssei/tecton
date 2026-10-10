"""Unit tests for semantic architecture DiffEngine."""

from tecton.dsl.parser import C4EAMParser
from tecton.engines.diff_engine import ChangeType, DiffEngine


def test_diff_engine_entity_additions_and_removals():
    base_content = """
    capabilities:
      - id: cap-1
        name: Capability One
    systems:
      - id: sys-1
        name: System One
        capabilities: [cap-1]
    """

    head_content = """
    capabilities:
      - id: cap-1
        name: Capability One Renamed
      - id: cap-2
        name: Capability Two
    systems:
      - id: sys-2
        name: System Two
        capabilities: [cap-2]
    """

    parser = C4EAMParser()
    base_graph = parser.parse_content(base_content)
    head_graph = parser.parse_content(head_content)

    engine = DiffEngine()
    report = engine.compare(base_graph, head_graph)

    assert report.added_count == 2  # cap-2, sys-2
    assert report.removed_count == 1  # sys-1
    assert report.modified_count == 1  # cap-1 name changed

    # Verify field change details on cap-1
    cap_mod = next(d for d in report.deltas if d.entity_id == "cap-1")
    assert cap_mod.change_type == ChangeType.MODIFIED
    assert "name" in cap_mod.field_changes
    assert cap_mod.field_changes["name"] == ("Capability One", "Capability One Renamed")


def test_diff_engine_detects_new_risk_regressions():
    base_content = """
    systems:
      - id: sys-clean
        name: Clean System
    """

    # Head introduces a dangling pointer to a non-existent capability
    head_content = """
    systems:
      - id: sys-clean
        name: Clean System
      - id: sys-broken
        name: Broken System
        capabilities: [cap-non-existent]
    """

    parser = C4EAMParser()
    base_graph = parser.parse_content(base_content)
    head_graph = parser.parse_content(head_content)

    engine = DiffEngine()
    report = engine.compare(base_graph, head_graph)

    assert len(report.new_risk_issues) >= 1
    assert any(r["rule"] == "REF_INTEGRITY_DANGLING_SYSTEM_CAPABILITY" for r in report.new_risk_issues)
    assert report.has_breaking_changes is True


def test_diff_engine_detects_capability_gap_regressions():
    base_content = """
    capabilities:
      - id: cap-critical
        name: Mission Critical Cap
    systems:
      - id: sys-realizer
        name: Realizer System
        capabilities: [cap-critical]
    """

    # Head removes the system, turning cap-critical into an unmapped gap!
    head_content = """
    capabilities:
      - id: cap-critical
        name: Mission Critical Cap
    systems: []
    """

    parser = C4EAMParser()
    base_graph = parser.parse_content(base_content)
    head_graph = parser.parse_content(head_content)

    engine = DiffEngine()
    report = engine.compare(base_graph, head_graph)

    assert "cap-critical" in report.new_capability_gaps
    assert report.has_breaking_changes is True
