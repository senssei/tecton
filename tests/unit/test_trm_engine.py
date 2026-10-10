"""Unit tests for Technology Risk & Obsolescence Management (TRM) Engine."""

from datetime import date, timedelta
from tecton.dsl.parser import C4EAMParser
from tecton.dsl.schema import TechnologyStatus
from tecton.engines.trm_engine import TRMEngine


def test_trm_engine_evaluate_technologies():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    content = f"""
    technologies:
      - id: tech-py
        name: Python 3.12
        category: runtime
        status: approved
      - id: tech-legacy
        name: Legacy DB
        category: database
        status: deprecated
        eol_date: {yesterday}
    systems:
      - id: sys-1
        name: Modern App
        technologies: [tech-py]
      - id: sys-2
        name: Legacy App
        technologies: [tech-legacy]
    """
    graph = C4EAMParser().parse_content(content)
    engine = TRMEngine()
    report = engine.evaluate_technologies(graph)

    assert report.total_technologies == 2
    assert report.approved_count == 1
    assert report.deprecated_count == 1
    assert report.eol_count == 1

    py_item = next(t for t in report.technologies if t.id == "tech-py")
    assert py_item.realizing_systems_count == 1
    assert py_item.is_eol is False

    legacy_item = next(t for t in report.technologies if t.id == "tech-legacy")
    assert legacy_item.realizing_systems_count == 1
    assert legacy_item.is_eol is True


def test_trm_engine_calculate_blast_radius():
    content = """
    technologies:
      - id: tech-vulnerable
        name: Vulnerable Driver
        status: prohibited
    systems:
      - id: sys-core
        name: Core Service
        business_criticality: MISSION_CRITICAL
        technologies: [tech-vulnerable]
        capabilities: [cap-orders]
      - id: sys-gateway
        name: API Gateway
        business_criticality: BUSINESS_CRITICAL
        capabilities: [cap-routing]
    relationships:
      - source_id: sys-gateway
        target_id: sys-core
        relation_type: depends_on
    """
    graph = C4EAMParser().parse_content(content)
    engine = TRMEngine()
    blast = engine.calculate_blast_radius("tech-vulnerable", graph)

    assert blast.technology_id == "tech-vulnerable"
    assert blast.status == TechnologyStatus.PROHIBITED
    assert blast.directly_affected_system_ids == ["sys-core"]
    assert blast.cascading_system_ids == ["sys-gateway"]
    assert set(blast.compromised_capability_ids) == {"cap-orders", "cap-routing"}
    assert blast.highest_criticality == "MISSION_CRITICAL"
    assert blast.risk_score >= 80.0
    assert blast.total_systems_impacted == 2
