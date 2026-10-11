"""Technology Risk & Obsolescence Management (TRM) Engine.

Evaluates tech radar standards, tracks End-of-Life (EOL) obsolescence milestones,
and computes transitive blast radius propagation across the architectural graph.
"""

from collections import deque
from datetime import date
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from tecton.core.models import Application
from tecton.dsl.parser import CompiledGraph
from tecton.dsl.schema import TechnologyDef, TechnologyStatus


class CriticalityLevel(str, Enum):
    """Normalized enterprise criticality levels."""

    MISSION_CRITICAL = "MISSION_CRITICAL"
    BUSINESS_CRITICAL = "BUSINESS_CRITICAL"
    OPERATIONAL = "OPERATIONAL"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    UNKNOWN = "UNKNOWN"


class TechnologyRiskItem(BaseModel):
    """Assessed risk profile for a single technology asset."""

    id: str
    name: str
    category: str | None = None
    status: TechnologyStatus
    eol_date: date | None = None
    is_eol: bool = False
    days_to_eol: int | None = None
    realizing_systems_count: int = 0
    realizing_systems: list[str] = Field(default_factory=list)


class BlastRadiusReport(BaseModel):
    """Detailed blast radius assessment when a technology fails or reaches EOL."""

    technology_id: str
    technology_name: str
    status: TechnologyStatus
    eol_date: date | None = None
    is_eol: bool = False
    directly_affected_system_ids: list[str] = Field(default_factory=list)
    directly_affected_system_names: list[str] = Field(default_factory=list)
    cascading_system_ids: list[str] = Field(default_factory=list)
    cascading_system_names: list[str] = Field(default_factory=list)
    compromised_capability_ids: list[str] = Field(default_factory=list)
    highest_criticality: str = "UNKNOWN"
    total_systems_impacted: int = 0
    risk_score: float = Field(ge=0.0, le=100.0)
    summary: str


class TRMReport(BaseModel):
    """Aggregated portfolio technology risk report."""

    total_technologies: int
    approved_count: int
    deprecated_count: int
    prohibited_count: int
    eol_count: int
    technologies: list[TechnologyRiskItem] = Field(default_factory=list)


class TRMEngine:
    """Deterministic analytics engine for Technology Obsolescence & Risk Propagation."""

    def __init__(self) -> None:
        pass

    def evaluate_technologies(self, graph: CompiledGraph, as_of_date: date | None = None) -> TRMReport:
        """Assess overall technology catalog and calculate usage stats."""
        today = as_of_date or date.today()
        items: list[TechnologyRiskItem] = []

        approved = 0
        deprecated = 0
        prohibited = 0
        eol_count = 0

        # Map technology usage across all systems
        tech_to_systems: dict[str, list[str]] = {t_id: [] for t_id in graph.technologies.keys()}
        for sys in graph.systems.values():
            for t_id in sys.technologies:
                if t_id in tech_to_systems:
                    tech_to_systems[t_id].append(sys.name)

        for t_id, tech in sorted(graph.technologies.items(), key=lambda x: x[1].name):
            is_eol = False
            days_to_eol = None
            if tech.eol_date:
                days_to_eol = (tech.eol_date - today).days
                if tech.eol_date < today:
                    is_eol = True
                    eol_count += 1

            if tech.status == TechnologyStatus.APPROVED:
                approved += 1
            elif tech.status == TechnologyStatus.DEPRECATED:
                deprecated += 1
            elif tech.status == TechnologyStatus.PROHIBITED:
                prohibited += 1

            systems_using = tech_to_systems.get(t_id, [])

            items.append(
                TechnologyRiskItem(
                    id=t_id,
                    name=tech.name,
                    category=tech.category,
                    status=tech.status,
                    eol_date=tech.eol_date,
                    is_eol=is_eol,
                    days_to_eol=days_to_eol,
                    realizing_systems_count=len(systems_using),
                    realizing_systems=systems_using,
                )
            )

        return TRMReport(
            total_technologies=len(graph.technologies),
            approved_count=approved,
            deprecated_count=deprecated,
            prohibited_count=prohibited,
            eol_count=eol_count,
            technologies=items,
        )

    def calculate_blast_radius(
        self, technology_id: str, graph: CompiledGraph, as_of_date: date | None = None
    ) -> BlastRadiusReport:
        """Trace direct and cascading transitive dependency blast radius of a technology."""
        tech = graph.technologies.get(technology_id)
        if not tech:
            raise KeyError(f"Technology '{technology_id}' not found in architecture catalog")

        today = as_of_date or date.today()
        is_eol = bool(tech.eol_date and tech.eol_date < today)

        # 1. Directly affected systems
        directly_affected_systems = [
            sys for sys in graph.systems.values() if technology_id in sys.technologies
        ]
        direct_ids = {sys.id for sys in directly_affected_systems}
        direct_names = [sys.name for sys in directly_affected_systems]

        # 2. Cascading dependent systems via incoming dependency relationships
        # If A is directly affected and B depends on A (rel.source_id == B, rel.target_id == A),
        # then B is transitively compromised.
        cascading_ids: set[str] = set()
        queue = deque(direct_ids)
        visited = set(direct_ids)

        while queue:
            current_id = queue.popleft()
            # Incoming relationships point to current_id as target
            for rel in graph.incoming_relationships(current_id):
                if rel.relation_type in ("depends_on", "uses", "integrates_with"):
                    dep_sys_id = rel.source_id
                    if dep_sys_id in graph.systems and dep_sys_id not in visited:
                        visited.add(dep_sys_id)
                        cascading_ids.add(dep_sys_id)
                        queue.append(dep_sys_id)

        cascading_names = [graph.systems[s_id].name for s_id in sorted(cascading_ids)]

        # 3. Compromised business capabilities
        all_impacted_systems = [graph.systems[s_id] for s_id in visited]
        compromised_caps: set[str] = set()
        for sys in all_impacted_systems:
            compromised_caps.update(sys.capabilities)

        # 4. Highest business criticality
        criticality_ranks = {
            "MISSION_CRITICAL": 4,
            "BUSINESS_CRITICAL": 3,
            "OPERATIONAL": 2,
            "ADMINISTRATIVE": 1,
        }
        highest_crit = "UNKNOWN"
        max_rank = 0
        for sys in all_impacted_systems:
            crit = (sys.business_criticality or "").upper().replace(" ", "_")
            rank = criticality_ranks.get(crit, 0)
            if rank > max_rank:
                max_rank = rank
                highest_crit = crit

        # 5. Risk score (0.0 to 100.0)
        base_weight = 10.0
        if is_eol:
            base_weight += 30.0
        if tech.status == TechnologyStatus.PROHIBITED:
            base_weight += 40.0
        elif tech.status == TechnologyStatus.DEPRECATED:
            base_weight += 20.0

        sys_factor = min(len(all_impacted_systems) * 5.0, 30.0)
        crit_factor = max_rank * 5.0
        risk_score = min(base_weight + sys_factor + crit_factor, 100.0)

        total_impacted = len(all_impacted_systems)
        summary = (
            f"Technology '{tech.name}' ({tech.id}) impacts {len(direct_ids)} direct systems "
            f"and {len(cascading_ids)} cascading systems, compromising {len(compromised_caps)} "
            f"business capabilities (highest criticality: {highest_crit})."
        )

        return BlastRadiusReport(
            technology_id=tech.id,
            technology_name=tech.name,
            status=tech.status,
            eol_date=tech.eol_date,
            is_eol=is_eol,
            directly_affected_system_ids=sorted(direct_ids),
            directly_affected_system_names=direct_names,
            cascading_system_ids=sorted(cascading_ids),
            cascading_system_names=cascading_names,
            compromised_capability_ids=sorted(compromised_caps),
            highest_criticality=highest_crit,
            total_systems_impacted=total_impacted,
            risk_score=round(risk_score, 1),
            summary=summary,
        )
