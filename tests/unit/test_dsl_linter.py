"""Unit tests for GraphLinter and architectural quality gates."""

from datetime import date
import pytest
from tecton_arch.engines.linter import GraphLinter, LintSeverity
from tecton_arch.dsl.parser import C4EAMParser


def test_linter_passes_on_valid_graph():
    content = """
    capabilities:
      - id: cap-root
        name: Root Capability
        level: L1
      - id: cap-child
        name: Child Capability
        level: L2
        parent_id: cap-root
    systems:
      - id: sys-app
        name: Core Application
        capabilities: [cap-child]
    """
    graph = C4EAMParser().parse_content(content)
    report = GraphLinter().lint(graph)

    assert report.is_valid is True
    assert report.error_count == 0
    assert report.warning_count == 0


def test_linter_detects_dangling_capability_parent():
    content = """
    capabilities:
      - id: cap-child
        name: Child
        parent_id: cap-non-existent
    """
    graph = C4EAMParser().parse_content(content)
    report = GraphLinter().lint(graph)

    assert report.is_valid is False
    assert report.error_count == 1
    assert report.issues[0].rule == "REF_INTEGRITY_DANGLING_CAPABILITY_PARENT"


def test_linter_detects_dangling_system_capability():
    content = """
    capabilities:
      - id: cap-known
        name: Known Capability
    systems:
      - id: sys-app
        name: Application
        capabilities: [cap-ghost]
    """
    graph = C4EAMParser().parse_content(content)
    report = GraphLinter().lint(graph)

    assert report.is_valid is False
    assert report.error_count == 1
    assert report.issues[0].rule == "REF_INTEGRITY_DANGLING_SYSTEM_CAPABILITY"


def test_linter_detects_dangling_container_system():
    content = """
    containers:
      - id: cnt-web
        name: Web Frontend
        system_id: sys-missing
    """
    graph = C4EAMParser().parse_content(content)
    report = GraphLinter().lint(graph)

    assert report.is_valid is False
    assert report.error_count == 1
    assert report.issues[0].rule == "REF_INTEGRITY_DANGLING_CONTAINER_SYSTEM"


def test_linter_detects_dangling_relationship_endpoints():
    content = """
    systems:
      - id: sys-real
        name: Real System
    relationships:
      - source_id: sys-real
        target_id: sys-fake
      - source_id: sys-ghost
        target_id: sys-real
    """
    graph = C4EAMParser().parse_content(content)
    report = GraphLinter().lint(graph)

    assert report.is_valid is False
    assert report.error_count == 2
    rules = [i.rule for i in report.issues]
    assert "REF_INTEGRITY_DANGLING_RELATIONSHIP_TARGET" in rules
    assert "REF_INTEGRITY_DANGLING_RELATIONSHIP_SOURCE" in rules


def test_linter_detects_capability_hierarchy_cycle():
    content = """
    capabilities:
      - id: cap-a
        name: Capability A
        parent_id: cap-b
      - id: cap-b
        name: Capability B
        parent_id: cap-a
    """
    graph = C4EAMParser().parse_content(content)
    report = GraphLinter().lint(graph)

    assert report.is_valid is False
    rules = [i.rule for i in report.issues]
    assert "CYCLE_DETECTED_CAPABILITY" in rules


def test_linter_detects_duplicate_id_collision():
    content = """
    systems:
      - id: id-conflict
        name: System 1
      - id: id-conflict
        name: System 2
    """
    graph = C4EAMParser().parse_content(content)
    report = GraphLinter().lint(graph)

    assert report.is_valid is False
    assert any(i.rule == "DUPLICATE_ID" for i in report.issues)


def test_linter_detects_prohibited_technology_usage():
    content = """
    technologies:
      - id: tech-banned
        name: Banned Library
        status: prohibited
    systems:
      - id: sys-violator
        name: Violating System
        technologies: [tech-banned]
    """
    graph = C4EAMParser().parse_content(content)
    report = GraphLinter().lint(graph)

    assert report.is_valid is False
    assert any(i.rule == "GOVERNANCE_PROHIBITED_TECH_USAGE" for i in report.issues)


def test_linter_detects_circular_system_dependencies_as_warning():
    content = """
    systems:
      - id: sys-svc-a
        name: Service A
      - id: sys-svc-b
        name: Service B
    relationships:
      - source_id: sys-svc-a
        target_id: sys-svc-b
        relation_type: depends_on
      - source_id: sys-svc-b
        target_id: sys-svc-a
        relation_type: depends_on
    """
    graph = C4EAMParser().parse_content(content)
    report = GraphLinter().lint(graph)

    assert report.is_valid is True  # Warning doesn't make report invalid by default
    assert report.warning_count >= 1
    assert any(i.rule == "CYCLE_DETECTED_DEPENDENCY" for i in report.issues)


def test_linter_lifecycle_deterministic_with_as_of_date(monkeypatch):
    content = """
    systems:
      - id: sys-legacy
        name: Legacy System
        lifecycle:
          phases:
            - phase: active
              start_date: 2020-01-01
            - phase: endOfLife
              start_date: 2030-01-01
    """
    graph = C4EAMParser().parse_content(content)
    target_date = date(2035, 1, 1)

    class FakeDate2025(date):
        @classmethod
        def today(cls):
            return date(2025, 1, 1)

    monkeypatch.setattr("tecton_arch.core.models.date", FakeDate2025)
    report_2025 = GraphLinter().lint(graph, as_of_date=target_date)

    class FakeDate2035(date):
        @classmethod
        def today(cls):
            return date(2035, 1, 1)

    monkeypatch.setattr("tecton_arch.core.models.date", FakeDate2035)
    report_2035 = GraphLinter().lint(graph, as_of_date=target_date)

    # Lint results must be identical regardless of system clock
    assert report_2025.warning_count == report_2035.warning_count
    assert report_2025.error_count == report_2035.error_count
    assert [i.rule for i in report_2025.issues] == [i.rule for i in report_2035.issues]
    # As of 2035 the app is endOfLife, so no spurious warning about active past EOL
    assert not any(i.rule == "LIFECYCLE_INCONSISTENCY" for i in report_2025.issues)
