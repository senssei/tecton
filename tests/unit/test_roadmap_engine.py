"""Unit tests for Architecture Transformation Roadmapping Engine and Plateaus."""

from datetime import date
import pytest

from tecton_arch.engines.linter import GraphLinter, LintSeverity
from tecton_arch.dsl.parser import C4EAMParser, CompiledGraph
from tecton_arch.dsl.schema import (
    BusinessCapabilityDef,
    PlateauDef,
    SoftwareSystemDef,
    TechnologyDef,
    TechnologyStatus,
    WorkPackageDef,
    WorkPackageStatus,
)
from tecton_arch.engines.roadmap_engine import RoadmapEngine


@pytest.fixture
def sample_roadmap_graph() -> CompiledGraph:
    yaml_content = """
capabilities:
  - id: cap-orders
    name: Order Processing
    level: L1
  - id: cap-billing
    name: Billing Operations
    level: L1

technologies:
  - id: tech-modern-pg
    name: PostgreSQL 16
    status: approved
  - id: tech-old-solaris
    name: Solaris 10
    status: deprecated

systems:
  - id: sys-crm
    name: Modern CRM
    capabilities: [cap-orders]
    technologies: [tech-modern-pg]
  - id: sys-legacy
    name: Old Mainframe
    capabilities: [cap-billing]
    technologies: [tech-old-solaris]
  - id: sys-cloud-billing
    name: Cloud Billing Engine
    capabilities: [cap-billing]
    technologies: [tech-modern-pg]

plateaus:
  - id: plat-as-is
    name: Baseline As-Is
    target_date: 2026-01-01
    active_system_ids: [sys-crm, sys-legacy]

  - id: plat-transition
    name: Transition Hybrid
    target_date: 2026-06-01
    previous_plateau_id: plat-as-is
    active_system_ids: [sys-crm]
    decommissioned_system_ids: [sys-legacy]

  - id: plat-to-be
    name: Target Cloud Architecture
    target_date: 2027-01-01
    previous_plateau_id: plat-transition
    active_system_ids: [sys-crm, sys-cloud-billing]

work_packages:
  - id: wp-1
    name: Migrate CRM
    status: COMPLETED
    start_date: 2025-06-01
    target_date: 2025-12-31
    involved_system_ids: [sys-crm]
  - id: wp-2
    name: Deploy Cloud Billing
    status: IN_PROGRESS
    start_date: 2026-06-01
    target_date: 2026-12-31
    depends_on: [wp-1]
    involved_system_ids: [sys-cloud-billing]
    realized_capability_ids: [cap-billing]
"""
    return C4EAMParser().parse_content(yaml_content)


def test_roadmap_engine_ordered_plateaus(sample_roadmap_graph: CompiledGraph):
    engine = RoadmapEngine(sample_roadmap_graph)
    ordered = engine.get_ordered_plateaus()
    assert len(ordered) == 3
    assert [p.id for p in ordered] == ["plat-as-is", "plat-transition", "plat-to-be"]


def test_roadmap_engine_evaluate_plateau_states(sample_roadmap_graph: CompiledGraph):
    engine = RoadmapEngine(sample_roadmap_graph)

    # 1. As-Is
    s1 = engine.evaluate_plateau_state("plat-as-is")
    assert s1.active_system_ids == ["sys-crm", "sys-legacy"]
    assert "cap-billing" in s1.covered_capability_ids
    assert "cap-orders" in s1.covered_capability_ids
    assert s1.deprecated_or_eol_techs_in_use == ["tech-old-solaris"]

    # 2. Transition (gap created!)
    s2 = engine.evaluate_plateau_state("plat-transition")
    assert s2.active_system_ids == ["sys-crm"]
    assert "cap-orders" in s2.covered_capability_ids
    assert "cap-billing" in s2.uncovered_capability_ids
    assert s2.deprecated_or_eol_techs_in_use == []

    # 3. To-Be (gap closed with modern tech!)
    s3 = engine.evaluate_plateau_state("plat-to-be")
    assert s3.active_system_ids == ["sys-cloud-billing", "sys-crm"]
    assert "cap-billing" in s3.covered_capability_ids
    assert s3.deprecated_or_eol_techs_in_use == []


def test_roadmap_engine_detects_transitional_gaps(sample_roadmap_graph: CompiledGraph):
    engine = RoadmapEngine(sample_roadmap_graph)
    report = engine.analyze_roadmap()
    assert report.total_plateaus == 3
    assert report.total_work_packages == 2
    assert len(report.transitional_gaps) == 1

    gap = report.transitional_gaps[0]
    assert gap.from_plateau_id == "plat-as-is"
    assert gap.to_plateau_id == "plat-transition"
    assert gap.capability_id == "cap-billing"
    assert gap.decommissioned_system_ids == ["sys-legacy"]


def test_roadmap_engine_compare_as_is_vs_to_be(sample_roadmap_graph: CompiledGraph):
    engine = RoadmapEngine(sample_roadmap_graph)
    comp = engine.compare_plateaus("plat-as-is", "plat-to-be")

    assert comp.from_plateau_id == "plat-as-is"
    assert comp.to_plateau_id == "plat-to-be"
    assert comp.added_system_ids == ["sys-cloud-billing"]
    assert comp.decommissioned_system_ids == ["sys-legacy"]
    assert comp.retained_system_ids == ["sys-crm"]
    assert comp.eliminated_obsolete_technologies == ["tech-old-solaris"]
    assert comp.tech_debt_reduction_count == 1
    assert comp.net_capability_gain == 0  # Replaced 1 with 1


def test_roadmap_engine_export_gantt_mermaid(sample_roadmap_graph: CompiledGraph):
    engine = RoadmapEngine(sample_roadmap_graph)
    gantt = engine.export_gantt_mermaid()
    assert "gantt" in gantt
    assert "section Plateaus" in gantt
    assert "Baseline As-Is :milestone, plat-as-is, 2026-01-01, 0d" in gantt
    assert "section Work Packages" in gantt
    assert "Migrate CRM :done, wp-1, 2025-06-01, 2025-12-31" in gantt
    assert "Deploy Cloud Billing :active, wp-2, after wp-1" in gantt


def test_linter_detects_roadmap_cycle_and_dangling_refs():
    bad_yaml = """
plateaus:
  - id: plat-a
    name: Plateau A
    target_date: 2027-01-01
    previous_plateau_id: plat-b
  - id: plat-b
    name: Plateau B
    target_date: 2026-01-01
    previous_plateau_id: plat-a
  - id: plat-c
    name: Plateau C
    previous_plateau_id: non-existent-plat
    active_system_ids: [non-existent-sys]

work_packages:
  - id: wp-cycle-1
    name: WP Cycle 1
    depends_on: [wp-cycle-2]
    involved_system_ids: [ghost-sys]
  - id: wp-cycle-2
    name: WP Cycle 2
    depends_on: [wp-cycle-1]
"""
    graph = C4EAMParser().parse_content(bad_yaml)
    report = GraphLinter().lint(graph)
    assert not report.is_valid

    rules = {i.rule for i in report.issues}
    assert "ROADMAP_PLATEAU_CYCLE" in rules
    assert "REF_INTEGRITY_DANGLING_PLATEAU_PREDECESSOR" in rules
    assert "REF_INTEGRITY_DANGLING_PLATEAU_SYSTEM" in rules
    assert "ROADMAP_WORK_PACKAGE_CYCLE" in rules
    assert "REF_INTEGRITY_DANGLING_WORK_PACKAGE_SYSTEM" in rules
