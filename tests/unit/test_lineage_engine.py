"""Unit tests for LineageEngine and data compliance rules."""

import pytest
from tecton.core.models import TimeQuadrant
from tecton.dsl.parser import CompiledGraph, SymbolTable
from tecton.dsl.schema import (
    DataClassification,
    DataObjectDef,
    InterfaceDef,
    RelationshipDef,
    SoftwareSystemDef,
    TechnologyDef,
    TechnologyStatus,
)
from tecton.engines.lineage_engine import LineageEngine


@pytest.fixture
def sample_graph() -> CompiledGraph:
    """Constructs a test graph with systems, interfaces, tech, and data objects."""
    table = SymbolTable()

    # Data objects
    table.data_objects["do-pii"] = DataObjectDef(
        id="do-pii",
        name="Customer PII",
        classification=DataClassification.RESTRICTED_PII,
        owner="Privacy Team",
    )
    table.data_objects["do-internal"] = DataObjectDef(
        id="do-internal",
        name="Operational Logs",
        classification=DataClassification.INTERNAL,
        owner="Infra Team",
    )

    # Technologies
    table.technologies["tech-approved"] = TechnologyDef(
        id="tech-approved",
        name="Modern DB",
        category="database",
        status=TechnologyStatus.APPROVED,
    )
    table.technologies["tech-prohibited"] = TechnologyDef(
        id="tech-prohibited",
        name="Legacy Protocol",
        category="protocol",
        status=TechnologyStatus.PROHIBITED,
    )

    # Systems
    table.systems["sys-sender"] = SoftwareSystemDef(
        id="sys-sender",
        name="Sender Service",
        functional_suitability=4.5,
        technical_suitability=4.5,
        time_classification=TimeQuadrant.INVEST,
        technologies=["tech-approved"],
    )
    table.systems["sys-receiver-eliminate"] = SoftwareSystemDef(
        id="sys-receiver-eliminate",
        name="Decommission Monolith",
        functional_suitability=2.0,
        technical_suitability=1.5,
        time_classification=TimeQuadrant.ELIMINATE,
        technologies=["tech-prohibited"],
    )

    # Interface
    table.interfaces["iface-transfer"] = InterfaceDef(
        id="iface-transfer",
        name="PII Transfer Stream",
        protocol="Kafka",
        provider_system_id="sys-sender",
        consumer_system_ids=["sys-receiver-eliminate"],
        data_objects=["do-pii", "do-internal"],
    )

    # Direct relationship
    table.relationships.append(
        RelationshipDef(
            source_id="sys-sender",
            target_id="sys-receiver-eliminate",
            relation_type="data_flow",
            technology="gRPC",
            data_objects=["do-pii"],
        )
    )

    return CompiledGraph(table)


def test_lineage_trace_missing_data_object(sample_graph: CompiledGraph):
    engine = LineageEngine()
    with pytest.raises(KeyError, match="not found"):
        engine.trace_lineage("non-existent-do", sample_graph)


def test_lineage_trace_producers_consumers_edges(sample_graph: CompiledGraph):
    engine = LineageEngine()
    report = engine.trace_lineage("do-pii", sample_graph)

    assert report.data_object_id == "do-pii"
    assert report.data_object_name == "Customer PII"
    assert report.classification == DataClassification.RESTRICTED_PII
    assert report.producers == ["sys-sender"]
    assert report.consumers == ["sys-receiver-eliminate"]
    assert report.participating_systems == ["sys-receiver-eliminate", "sys-sender"]

    # 1 edge from interface, 1 edge from relationship
    assert len(report.flow_edges) == 2
    protocols = {e.protocol for e in report.flow_edges}
    assert "Kafka" in protocols
    assert "gRPC" in protocols


def test_lineage_compliance_violations_on_sensitive_data(sample_graph: CompiledGraph):
    engine = LineageEngine()
    report = engine.trace_lineage("do-pii", sample_graph)

    assert not report.is_compliant
    assert report.risk_count == 3

    rule_names = {r["rule"] for r in report.compliance_risks}
    assert "COMPLIANCE_SENSITIVE_DATA_ON_ELIMINATE_SYSTEM" in rule_names
    assert "COMPLIANCE_UNAPPROVED_TECH_HANDLING_PII" in rule_names
    assert "COMPLIANCE_HIGH_TECH_DEBT_HANDLING_PII" in rule_names

    # Verify severity
    crit_risks = [r for r in report.compliance_risks if r["severity"] == "CRITICAL"]
    assert len(crit_risks) == 1
    assert crit_risks[0]["rule"] == "COMPLIANCE_UNAPPROVED_TECH_HANDLING_PII"


def test_lineage_non_sensitive_data_has_no_compliance_risks(sample_graph: CompiledGraph):
    engine = LineageEngine()
    report = engine.trace_lineage("do-internal", sample_graph)

    # Even though flowing to an ELIMINATE system, non-sensitive data does not trigger PII/PCI audits
    assert report.is_compliant
    assert report.risk_count == 0
    assert len(report.flow_edges) == 1
