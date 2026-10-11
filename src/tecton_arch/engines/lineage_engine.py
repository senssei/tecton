"""Data Lineage & Interface Flow Traversal Engine.

Traces end-to-end data trajectory across application interfaces and evaluates
compliance risks for sensitive and regulated data objects (GDPR/PII/PCI-DSS).
"""

from typing import Any
from pydantic import BaseModel, Field

from tecton_arch.core.models import TimeQuadrant
from tecton_arch.dsl.parser import CompiledGraph
from tecton_arch.dsl.schema import DataClassification, DataObjectDef, TechnologyStatus


class DataFlowEdge(BaseModel):
    """Directed transmission edge of a data object between two software systems."""

    source_system_id: str
    source_system_name: str
    target_system_id: str
    target_system_name: str
    protocol: str = "REST"
    channel_name: str = ""


class DataLineageReport(BaseModel):
    """Declared lineage risk assessment. is_compliant is a deprecated compatibility property."""

    data_object_id: str
    data_object_name: str
    classification: DataClassification
    assessment_status: str = "no_modeled_flows"
    owner: str | None = None
    producers: list[str] = Field(default_factory=list)
    consumers: list[str] = Field(default_factory=list)
    participating_systems: list[str] = Field(default_factory=list)
    flow_edges: list[DataFlowEdge] = Field(default_factory=list)
    compliance_risks: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        return len(self.compliance_risks) == 0

    @property
    def risk_count(self) -> int:
        return len(self.compliance_risks)


class LineageEngine:
    """Deterministic graph traversal engine for data flows and compliance governance."""

    def __init__(self) -> None:
        pass

    def trace_lineage(self, data_object_id: str, graph: CompiledGraph, as_of_date=None, config=None) -> DataLineageReport:
        """Trace the end-to-end flow trajectory of a data object across system interfaces."""
        data_obj = graph.data_objects.get(data_object_id)
        if not data_obj:
            raise KeyError(f"Data object '{data_object_id}' not found in architecture catalog")

        flow_edges: list[DataFlowEdge] = []
        source_nodes: set[str] = set()
        target_nodes: set[str] = set()

        # 1. Inspect explicit interfaces carrying this data object
        for iface in graph.interfaces.values():
            if data_object_id in iface.data_objects:
                provider_sys = graph.systems.get(iface.provider_system_id)
                provider_name = provider_sys.name if provider_sys else iface.provider_system_id
                source_nodes.add(iface.provider_system_id)

                for consumer_id in iface.consumer_system_ids:
                    target_sys = graph.systems.get(consumer_id)
                    target_name = target_sys.name if target_sys else consumer_id
                    target_nodes.add(consumer_id)

                    flow_edges.append(
                        DataFlowEdge(
                            source_system_id=iface.provider_system_id,
                            source_system_name=provider_name,
                            target_system_id=consumer_id,
                            target_system_name=target_name,
                            protocol=iface.protocol,
                            channel_name=iface.name,
                        )
                    )

        # 2. Inspect relationships tagged with this data object
        for rel in graph.relationships:
            if data_object_id in rel.data_objects:
                src_sys = graph.systems.get(rel.source_id)
                dst_sys = graph.systems.get(rel.target_id)
                src_name = src_sys.name if src_sys else rel.source_id
                dst_name = dst_sys.name if dst_sys else rel.target_id

                source_nodes.add(rel.source_id)
                target_nodes.add(rel.target_id)

                flow_edges.append(
                    DataFlowEdge(
                        source_system_id=rel.source_id,
                        source_system_name=src_name,
                        target_system_id=rel.target_id,
                        target_system_name=dst_name,
                        protocol=rel.technology or "Relationship",
                        channel_name=f"{rel.relation_type} ({rel.technology or 'direct'})",
                    )
                )

        participating = sorted(list(source_nodes | target_nodes))
        # Pure producers: sources that are never consumers in this flow
        producers = sorted(list(source_nodes - target_nodes)) or sorted(list(source_nodes))
        consumers = sorted(list(target_nodes))

        # 3. Privacy & Compliance Invariants
        compliance_risks = self._audit_compliance(data_obj, participating, graph, as_of_date, config)

        return DataLineageReport(
            assessment_status="no_modeled_flows" if not flow_edges else "risks_detected" if compliance_risks else "no_detected_risks",
            data_object_id=data_obj.id,
            data_object_name=data_obj.name,
            classification=data_obj.classification,
            owner=data_obj.owner,
            producers=producers,
            consumers=consumers,
            participating_systems=participating,
            flow_edges=flow_edges,
            compliance_risks=compliance_risks,
        )

    def _audit_compliance(
        self, data_obj: DataObjectDef, system_ids: list[str], graph: CompiledGraph, as_of_date=None, config=None
    ) -> list[dict[str, Any]]:
        """Verify privacy and security invariants for sensitive data objects."""
        risks: list[dict[str, Any]] = []

        is_sensitive = data_obj.classification in (
            DataClassification.RESTRICTED_PII,
            DataClassification.PCI_DSS,
            DataClassification.CONFIDENTIAL,
        )

        if not is_sensitive:
            return risks

        from tecton_arch.services.assessment import evaluate_applications
        evaluated = {a.id: a for a in evaluate_applications(graph.get_applications(as_of_date=as_of_date), config, as_of_date)}
        for s_id in system_ids:
            sys = graph.systems.get(s_id)
            if not sys:
                continue

            # Invariant 1: Sensitive data must not flow to an ELIMINATE system
            if evaluated[s_id].time_classification == TimeQuadrant.ELIMINATE:
                risks.append({
                    "severity": "HIGH",
                    "rule": "COMPLIANCE_SENSITIVE_DATA_ON_ELIMINATE_SYSTEM",
                    "system_id": sys.id,
                    "system_name": sys.name,
                    "message": (
                        f"Sensitive data '{data_obj.name}' ({data_obj.classification.value}) "
                        f"flows into system '{sys.name}', which is slated for ELIMINATION."
                    ),
                })

            # Invariant 2: Sensitive data must not be hosted on deprecated/prohibited tech
            for t_id in sys.technologies:
                tech = graph.technologies.get(t_id)
                if not tech:
                    continue
                if tech.status in (TechnologyStatus.PROHIBITED, TechnologyStatus.DEPRECATED):
                    risks.append({
                        "severity": "CRITICAL" if tech.status == TechnologyStatus.PROHIBITED else "MEDIUM",
                        "rule": "COMPLIANCE_UNAPPROVED_TECH_HANDLING_PII",
                        "system_id": sys.id,
                        "system_name": sys.name,
                        "message": (
                            f"System '{sys.name}' processing '{data_obj.name}' relies on "
                            f"{tech.status.value.upper()} technology '{tech.name}' ({tech.id})."
                        ),
                    })

            # Invariant 3: High technical debt warning
            if sys.technical_suitability is not None and sys.technical_suitability < 2.5:
                risks.append({
                    "severity": "MEDIUM",
                    "rule": "COMPLIANCE_HIGH_TECH_DEBT_HANDLING_PII",
                    "system_id": sys.id,
                    "system_name": sys.name,
                    "message": (
                        f"System '{sys.name}' handling '{data_obj.name}' has low technical "
                        f"suitability ({sys.technical_suitability:.1f}/5.0)."
                    ),
                })

        return risks
