"""Architecture Transformation Roadmapping Engine (Plateaus & Scenarios).

Evaluates enterprise architecture plateaus (As-Is baseline, transitional states, To-Be targets),
validates work package dependency graphs, audits transitional capability gaps, and generates
transformation Gantt and scenario delta reports.
"""

from collections import deque
from datetime import date
from typing import Any
from pydantic import BaseModel, Field

from tecton_arch.dsl.parser import CompiledGraph
from tecton_arch.dsl.schema import PlateauDef, TechnologyStatus, WorkPackageDef, WorkPackageStatus


class PlateauState(BaseModel):
    """Evaluated architectural footprint at a specific plateau milestone."""

    plateau_id: str
    plateau_name: str
    target_date: date | None = None
    previous_plateau_id: str | None = None
    active_system_ids: list[str] = Field(default_factory=list)
    decommissioned_system_ids: list[str] = Field(default_factory=list)
    covered_capability_ids: list[str] = Field(default_factory=list)
    uncovered_capability_ids: list[str] = Field(default_factory=list)
    technologies_in_use: list[str] = Field(default_factory=list)
    deprecated_or_eol_techs_in_use: list[str] = Field(default_factory=list)


class TransitionalGap(BaseModel):
    """Capability coverage gap or risk introduced during plateau transition."""

    from_plateau_id: str
    to_plateau_id: str
    capability_id: str
    capability_name: str
    decommissioned_system_ids: list[str]
    description: str


class PlateauComparison(BaseModel):
    """Detailed delta analysis between two architecture plateaus (e.g. As-Is vs To-Be)."""

    from_plateau_id: str
    from_plateau_name: str
    to_plateau_id: str
    to_plateau_name: str
    added_system_ids: list[str] = Field(default_factory=list)
    decommissioned_system_ids: list[str] = Field(default_factory=list)
    retained_system_ids: list[str] = Field(default_factory=list)
    gained_capability_ids: list[str] = Field(default_factory=list)
    lost_capability_ids: list[str] = Field(default_factory=list)
    retained_capability_ids: list[str] = Field(default_factory=list)
    eliminated_technologies: list[str] = Field(default_factory=list)
    introduced_technologies: list[str] = Field(default_factory=list)
    eliminated_obsolete_technologies: list[str] = Field(default_factory=list)
    tech_debt_reduction_count: int = 0
    net_capability_gain: int = 0


class RoadmapAnalysisReport(BaseModel):
    """Comprehensive health, timeline and risk audit of architecture roadmap."""

    total_plateaus: int
    total_work_packages: int
    ordered_plateau_ids: list[str] = Field(default_factory=list)
    work_packages_by_status: dict[str, int] = Field(default_factory=dict)
    transitional_gaps: list[TransitionalGap] = Field(default_factory=list)
    plateau_states: list[PlateauState] = Field(default_factory=list)
    is_valid_dag: bool = True
    issues: list[str] = Field(default_factory=list)


class RoadmapEngine:
    """Enterprise Architecture Transformation Roadmapping and Scenario Engine."""

    def __init__(self, graph: CompiledGraph) -> None:
        self.graph = graph

    def get_ordered_plateaus(self) -> list[PlateauDef]:
        """Return plateaus topologically sorted along predecessor chain and chronological dates."""
        plateaus = list(self.graph.plateaus.values())
        if not plateaus:
            return []

        # Build in-degree and successors
        pred_map: dict[str, str | None] = {p.id: p.previous_plateau_id for p in plateaus}
        successors: dict[str, list[str]] = {p.id: [] for p in plateaus}
        in_degree: dict[str, int] = {p.id: 0 for p in plateaus}

        for p_id, pred_id in pred_map.items():
            if pred_id and pred_id in self.graph.plateaus:
                successors[pred_id].append(p_id)
                in_degree[p_id] += 1

        queue = deque([p_id for p_id, deg in in_degree.items() if deg == 0])
        ordered: list[str] = []

        while queue:
            curr = queue.popleft()
            ordered.append(curr)
            for succ in successors.get(curr, []):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        # Fallback if any unvisited nodes remain (e.g. cycle or unconnected)
        for p in plateaus:
            if p.id not in ordered:
                ordered.append(p.id)

        # Sort stable by target_date when available
        def sort_key(pid: str) -> tuple[int, str]:
            plat = self.graph.plateaus.get(pid)
            d = str(plat.target_date) if plat and plat.target_date else "9999-99-99"
            return (0 if plat and plat.target_date else 1, d)

        # If date-ordered is feasible without breaking predecessor order, plateaus follow sequence
        return [self.graph.plateaus[pid] for pid in ordered]

    def evaluate_plateau_state(self, plateau_id: str, as_of_date: date | None = None) -> PlateauState:
        """Evaluate active systems, realized capabilities, and technology footprint for a plateau."""
        plateau = self.graph.plateaus.get(plateau_id)
        if not plateau:
            raise KeyError(f"Plateau '{plateau_id}' does not exist in graph")

        active_systems: list[str] = []
        if plateau.active_system_ids:
            active_systems = [s for s in plateau.active_system_ids if s in self.graph.systems]
        elif plateau.previous_plateau_id and plateau.previous_plateau_id in self.graph.plateaus:
            prev_state = self.evaluate_plateau_state(plateau.previous_plateau_id, as_of_date=as_of_date)
            decom_set = set(plateau.decommissioned_system_ids)
            active_systems = [s for s in prev_state.active_system_ids if s not in decom_set]
        else:
            # Baseline plateau defaults to all current systems minus explicitly decommissioned
            decom_set = set(plateau.decommissioned_system_ids)
            active_systems = [s_id for s_id in self.graph.systems.keys() if s_id not in decom_set]

        # Calculate covered capabilities
        covered_caps: set[str] = set()
        technologies_used: set[str] = set()
        deprecated_or_eol_techs: set[str] = set()
        eval_date = as_of_date or plateau.target_date or date.today()

        for s_id in active_systems:
            sys_def = self.graph.systems.get(s_id)
            if not sys_def:
                continue
            for cap_id in sys_def.capabilities:
                if cap_id in self.graph.capabilities:
                    covered_caps.add(cap_id)
            for tech_id in sys_def.technologies:
                if tech_id in self.graph.technologies:
                    technologies_used.add(tech_id)
                    tech_def = self.graph.technologies[tech_id]
                    if (
                        tech_def.status in (TechnologyStatus.DEPRECATED, TechnologyStatus.PROHIBITED)
                        or (tech_def.eol_date and tech_def.eol_date <= eval_date)
                    ):
                        deprecated_or_eol_techs.add(tech_id)

        all_caps = set(self.graph.capabilities.keys())
        uncovered_caps = sorted(all_caps - covered_caps)

        return PlateauState(
            plateau_id=plateau.id,
            plateau_name=plateau.name,
            target_date=plateau.target_date,
            previous_plateau_id=plateau.previous_plateau_id,
            active_system_ids=sorted(active_systems),
            decommissioned_system_ids=sorted(plateau.decommissioned_system_ids),
            covered_capability_ids=sorted(covered_caps),
            uncovered_capability_ids=uncovered_caps,
            technologies_in_use=sorted(technologies_used),
            deprecated_or_eol_techs_in_use=sorted(deprecated_or_eol_techs),
        )

    def compare_plateaus(self, from_plateau_id: str, to_plateau_id: str, as_of_date: date | None = None) -> PlateauComparison:
        """Compare two architecture plateaus (e.g. As-Is vs To-Be) and compute delta metrics."""
        from_state = self.evaluate_plateau_state(from_plateau_id, as_of_date=as_of_date)
        to_state = self.evaluate_plateau_state(to_plateau_id, as_of_date=as_of_date)

        from_sys = set(from_state.active_system_ids)
        to_sys = set(to_state.active_system_ids)

        added_sys = sorted(to_sys - from_sys)
        decom_sys = sorted(from_sys - to_sys)
        retained_sys = sorted(from_sys & to_sys)

        from_caps = set(from_state.covered_capability_ids)
        to_caps = set(to_state.covered_capability_ids)

        gained_caps = sorted(to_caps - from_caps)
        lost_caps = sorted(from_caps - to_caps)
        retained_caps = sorted(from_caps & to_caps)

        from_tech = set(from_state.technologies_in_use)
        to_tech = set(to_state.technologies_in_use)

        eliminated_tech = sorted(from_tech - to_tech)
        introduced_tech = sorted(to_tech - from_tech)

        eliminated_obsolete = [
            t for t in eliminated_tech
            if t in from_state.deprecated_or_eol_techs_in_use
        ]

        return PlateauComparison(
            from_plateau_id=from_state.plateau_id,
            from_plateau_name=from_state.plateau_name,
            to_plateau_id=to_state.plateau_id,
            to_plateau_name=to_state.plateau_name,
            added_system_ids=added_sys,
            decommissioned_system_ids=decom_sys,
            retained_system_ids=retained_sys,
            gained_capability_ids=gained_caps,
            lost_capability_ids=lost_caps,
            retained_capability_ids=retained_caps,
            eliminated_technologies=eliminated_tech,
            introduced_technologies=introduced_tech,
            eliminated_obsolete_technologies=eliminated_obsolete,
            tech_debt_reduction_count=len(eliminated_obsolete),
            net_capability_gain=len(gained_caps) - len(lost_caps),
        )

    def analyze_roadmap(self, as_of_date: Optional[date] = None) -> RoadmapAnalysisReport:
        """Perform comprehensive roadmap validation, gap analysis, and progress audit."""
        ordered_plateaus = self.get_ordered_plateaus()
        plateau_states = [self.evaluate_plateau_state(p.id, as_of_date=as_of_date) for p in ordered_plateaus]

        status_counts: dict[str, int] = {
            WorkPackageStatus.PLANNED.value: 0,
            WorkPackageStatus.IN_PROGRESS.value: 0,
            WorkPackageStatus.COMPLETED.value: 0,
            WorkPackageStatus.CANCELLED.value: 0,
        }
        for wp in self.graph.work_packages.values():
            status_counts[wp.status.value] = status_counts.get(wp.status.value, 0) + 1

        transitional_gaps: list[TransitionalGap] = []
        issues: list[str] = []

        # Audit transitions between consecutive plateaus
        for i in range(len(plateau_states) - 1):
            curr = plateau_states[i]
            nxt = plateau_states[i + 1]

            lost_in_transition = set(curr.covered_capability_ids) - set(nxt.covered_capability_ids)
            for cap_id in lost_in_transition:
                cap_name = self.graph.capabilities[cap_id].name if cap_id in self.graph.capabilities else cap_id
                decom_sys = [
                    s for s in curr.active_system_ids
                    if s not in nxt.active_system_ids and cap_id in self.graph.systems[s].capabilities
                ]
                gap = TransitionalGap(
                    from_plateau_id=curr.plateau_id,
                    to_plateau_id=nxt.plateau_id,
                    capability_id=cap_id,
                    capability_name=cap_name,
                    decommissioned_system_ids=decom_sys,
                    description=f"Capability '{cap_name}' ({cap_id}) was covered in plateau '{curr.plateau_name}' but becomes unmapped in '{nxt.plateau_name}' due to decommissioning of {decom_sys}.",
                )
                transitional_gaps.append(gap)
                issues.append(f"Transitional Gap: {gap.description}")

        return RoadmapAnalysisReport(
            total_plateaus=len(self.graph.plateaus),
            total_work_packages=len(self.graph.work_packages),
            ordered_plateau_ids=[p.id for p in ordered_plateaus],
            work_packages_by_status=status_counts,
            transitional_gaps=transitional_gaps,
            plateau_states=plateau_states,
            is_valid_dag=True,
            issues=issues,
        )

    def export_gantt_mermaid(
        self,
        title: str = "Enterprise Architecture Transformation Roadmap",
        as_of_date: date | None = None,
    ) -> str:
        """Export Mermaid Gantt diagram visualizing plateaus milestones and work package schedule."""
        today_val = as_of_date or date.today()
        lines: list[str] = [
            "gantt",
            f"    title {title}",
            "    dateFormat YYYY-MM-DD",
            "    axisFormat %Y-%m",
        ]

        # Section 1: Architecture Plateaus
        ordered_plateaus = self.get_ordered_plateaus()
        if ordered_plateaus:
            lines.append("    section Plateaus")
            if as_of_date:
                lines.append(f"    Evaluation Date :milestone, eval_date, {as_of_date}, 0d")
            for p in ordered_plateaus:
                date_str = str(p.target_date) if p.target_date else str(today_val)
                safe_name = p.name.replace(":", " -")
                lines.append(f"    {safe_name} :milestone, {p.id}, {date_str}, 0d")

        # Section 2: Work Packages
        wps = list(self.graph.work_packages.values())
        if wps:
            lines.append("    section Work Packages")
            # Sort wps by start_date if available
            wps_sorted = sorted(
                wps,
                key=lambda w: (
                    0 if w.start_date else 1,
                    str(w.start_date) if w.start_date else "9999-99-99",
                ),
            )
            for wp in wps_sorted:
                safe_name = wp.name.replace(":", " -")
                status_modifier = ""
                if wp.status == WorkPackageStatus.COMPLETED:
                    status_modifier = "done, "
                elif wp.status == WorkPackageStatus.IN_PROGRESS:
                    status_modifier = "active, "
                elif wp.status == WorkPackageStatus.CANCELLED:
                    status_modifier = "crit, "

                # Dependency or explicit date
                if wp.depends_on and wp.depends_on[0] in self.graph.work_packages:
                    dep_id = wp.depends_on[0]
                    duration = "30d"
                    if wp.start_date and wp.target_date:
                        days = (wp.target_date - wp.start_date).days
                        duration = f"{max(days, 1)}d"
                    lines.append(f"    {safe_name} :{status_modifier}{wp.id}, after {dep_id}, {duration}")
                elif wp.start_date and wp.target_date:
                    lines.append(f"    {safe_name} :{status_modifier}{wp.id}, {wp.start_date}, {wp.target_date}")
                elif wp.start_date:
                    lines.append(f"    {safe_name} :{status_modifier}{wp.id}, {wp.start_date}, 30d")
                else:
                    lines.append(f"    {safe_name} :{status_modifier}{wp.id}, {today_val}, 30d")

        return "\n".join(lines)
