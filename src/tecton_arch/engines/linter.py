"""Quality Gate and Topological Graph Linter for Architecture-as-Code.

Enforces referential integrity, DAG acyclicity, lifecycle chronological consistency,
and technology governance policies.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any

from tecton_arch.dsl.parser import CompiledGraph
from tecton_arch.dsl.schema import TechnologyStatus
from tecton_arch.engines.lifecycle_validator import LifecycleValidator


class LintSeverity(str, Enum):
    """Severity classification of linting issues."""

    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass
class LintIssue:
    """Individual issue found during architecture graph validation."""

    severity: LintSeverity
    rule: str
    message: str
    entity_id: str | None = None
    file_origin: str | None = None


@dataclass
class LintReport:
    """Aggregated validation report from GraphLinter."""

    issues: list[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == LintSeverity.ERROR for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == LintSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == LintSeverity.WARNING)

    @property
    def is_valid(self) -> bool:
        return not self.has_errors

    def add_issue(
        self,
        severity: LintSeverity,
        rule: str,
        message: str,
        entity_id: str | None = None,
        file_origin: str | None = None,
    ) -> None:
        self.issues.append(
            LintIssue(
                severity=severity,
                rule=rule,
                message=message,
                entity_id=entity_id,
                file_origin=file_origin,
            )
        )


class GraphLinter:
    """Deterministic Quality Gate Linter for Enterprise Architecture Graphs."""

    def __init__(self) -> None:
        pass

    def lint(self, graph: CompiledGraph, as_of_date: date | None = None, *, require_owner: bool = False) -> LintReport:
        """Execute all architectural validation passes against the compiled graph."""
        report = LintReport()

        if require_owner:
            for system in graph.systems.values():
                if not system.owner or not system.owner.strip():
                    report.add_issue(
                        LintSeverity.ERROR, "MISSING_SYSTEM_OWNER",
                        "System must have an accountable owner", system.id,
                        graph.symbol_origins.get(system.id),
                    )

        self._check_duplicate_ids(graph, report)
        self._check_data_flow_diagrams(graph, report)
        self._check_referential_integrity(graph, report)
        self._check_capability_cycles(graph, report)
        self._check_dependency_cycles(graph, report)
        self._check_lifecycles(graph, report, as_of_date=as_of_date)
        self._check_technology_governance(graph, report, as_of_date=as_of_date)
        self._check_roadmap_governance(graph, report)

        return report

    def _check_duplicate_ids(self, graph: CompiledGraph, report: LintReport) -> None:
        for entity_id, orig1, orig2 in graph.duplicate_ids:
            report.add_issue(
                severity=LintSeverity.ERROR,
                rule="DUPLICATE_ID",
                message=f"Collision: entity ID '{entity_id}' is defined multiple times (found in '{orig1}' and '{orig2}')",
                entity_id=entity_id,
                file_origin=orig2,
            )

    def _check_data_flow_diagrams(self, graph: CompiledGraph, report: LintReport) -> None:
        for diagram in graph.data_flow_diagrams.values():
            origin = graph.symbol_origins.get(diagram.id)
            nodes = {node.id: node for node in diagram.nodes}
            ids = [item.id for item in [*diagram.nodes, *diagram.flows]]
            if len(set(ids)) != len(ids):
                report.add_issue(LintSeverity.ERROR, "DFD_DUPLICATE_ID", "Node and flow IDs must be unique within the diagram", diagram.id, origin)
            for node in diagram.nodes:
                if node.system_id and node.system_id not in graph.systems:
                    report.add_issue(LintSeverity.ERROR, "DFD_UNKNOWN_SYSTEM", f"Node '{node.id}' references unknown system '{node.system_id}'", diagram.id, origin)
            for flow in diagram.flows:
                source, target = nodes.get(flow.source_id), nodes.get(flow.target_id)
                if source is None or target is None:
                    report.add_issue(LintSeverity.ERROR, "DFD_UNKNOWN_ENDPOINT", f"Flow '{flow.id}' references an unknown node", diagram.id, origin)
                elif source.kind != "process" and target.kind != "process":
                    report.add_issue(LintSeverity.ERROR, "DFD_PROCESS_REQUIRED", f"Flow '{flow.id}' must connect to a process", diagram.id, origin)
                if flow.source_id == flow.target_id:
                    report.add_issue(LintSeverity.ERROR, "DFD_SELF_FLOW", f"Flow '{flow.id}' connects a node to itself", diagram.id, origin)
                for data_id in flow.data_objects:
                    if data_id not in graph.data_objects:
                        report.add_issue(LintSeverity.ERROR, "DFD_UNKNOWN_DATA_OBJECT", f"Flow '{flow.id}' references unknown data object '{data_id}'", diagram.id, origin)
            for node in diagram.nodes:
                if node.kind == "process" and (not any(f.source_id == node.id for f in diagram.flows) or not any(f.target_id == node.id for f in diagram.flows)):
                    report.add_issue(LintSeverity.WARNING, "DFD_UNBALANCED_PROCESS", f"Process '{node.id}' must have declared input and output flows", diagram.id, origin)

    def _check_referential_integrity(self, graph: CompiledGraph, report: LintReport) -> None:
        all_ids = graph.all_symbol_ids()

        # 1. Capability parent_id integrity
        for cap in graph.capabilities.values():
            origin = graph.symbol_origins.get(cap.id)
            if cap.parent_id and cap.parent_id not in graph.capabilities:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="REF_INTEGRITY_DANGLING_CAPABILITY_PARENT",
                    message=f"Parent capability '{cap.parent_id}' does not exist in capability catalog",
                    entity_id=cap.id,
                    file_origin=origin,
                )

        # 2. SoftwareSystem capabilities and technologies integrity
        has_tech_catalog = len(graph.technologies) > 0
        for sys in graph.systems.values():
            origin = graph.symbol_origins.get(sys.id)
            for cap_id in sys.capabilities:
                if cap_id not in graph.capabilities:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="REF_INTEGRITY_DANGLING_SYSTEM_CAPABILITY",
                        message=f"System '{sys.id}' references non-existent business capability '{cap_id}'",
                        entity_id=sys.id,
                        file_origin=origin,
                    )
            if has_tech_catalog:
                for tech_id in sys.technologies:
                    if tech_id not in graph.technologies:
                        report.add_issue(
                            severity=LintSeverity.ERROR,
                            rule="REF_INTEGRITY_DANGLING_SYSTEM_TECHNOLOGY",
                            message=f"System '{sys.id}' references non-existent technology '{tech_id}'",
                            entity_id=sys.id,
                            file_origin=origin,
                        )

        # 3. Container system_id and technology integrity
        for cnt in graph.containers.values():
            origin = graph.symbol_origins.get(cnt.id)
            if cnt.system_id not in graph.systems:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="REF_INTEGRITY_DANGLING_CONTAINER_SYSTEM",
                    message=f"Container '{cnt.id}' references non-existent parent system '{cnt.system_id}'",
                    entity_id=cnt.id,
                    file_origin=origin,
                )
            if has_tech_catalog and cnt.technology and cnt.technology not in graph.technologies:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="REF_INTEGRITY_DANGLING_CONTAINER_TECHNOLOGY",
                    message=f"Container '{cnt.id}' references non-existent technology '{cnt.technology}'",
                    entity_id=cnt.id,
                    file_origin=origin,
                )

        # 4. Interface and Data Object integrity
        has_data_catalog = len(graph.data_objects) > 0
        for iface in graph.interfaces.values():
            origin = graph.symbol_origins.get(iface.id)
            if iface.provider_system_id not in graph.systems:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="REF_INTEGRITY_DANGLING_INTERFACE_PROVIDER",
                    message=f"Interface '{iface.id}' references non-existent provider system '{iface.provider_system_id}'",
                    entity_id=iface.id,
                    file_origin=origin,
                )
            for consumer_id in iface.consumer_system_ids:
                if consumer_id not in graph.systems:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="REF_INTEGRITY_DANGLING_INTERFACE_CONSUMER",
                        message=f"Interface '{iface.id}' references non-existent consumer system '{consumer_id}'",
                        entity_id=iface.id,
                        file_origin=origin,
                    )
            if has_data_catalog:
                for d_id in iface.data_objects:
                    if d_id not in graph.data_objects:
                        report.add_issue(
                            severity=LintSeverity.ERROR,
                            rule="REF_INTEGRITY_DANGLING_INTERFACE_DATA_OBJECT",
                            message=f"Interface '{iface.id}' references non-existent data object '{d_id}'",
                            entity_id=iface.id,
                            file_origin=origin,
                        )

        # 5. Relationships endpoints integrity
        for rel in graph.relationships:
            if rel.source_id not in all_ids:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="REF_INTEGRITY_DANGLING_RELATIONSHIP_SOURCE",
                    message=f"Relationship source '{rel.source_id}' does not exist in architecture graph",
                    entity_id=rel.source_id,
                )
            if rel.target_id not in all_ids:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="REF_INTEGRITY_DANGLING_RELATIONSHIP_TARGET",
                    message=f"Relationship target '{rel.target_id}' does not exist in architecture graph",
                    entity_id=rel.target_id,
                )
            if has_data_catalog:
                for d_id in rel.data_objects:
                    if d_id not in graph.data_objects:
                        report.add_issue(
                            severity=LintSeverity.ERROR,
                            rule="REF_INTEGRITY_DANGLING_RELATIONSHIP_DATA_OBJECT",
                            message=f"Relationship '{rel.source_id}->{rel.target_id}' references non-existent data object '{d_id}'",
                            entity_id=rel.source_id,
                        )

    def _check_capability_cycles(self, graph: CompiledGraph, report: LintReport) -> None:
        """Verify that capability parent relationships form a strict Directed Acyclic Forest."""
        visited: set[str] = set()

        for cap_id, cap in graph.capabilities.items():
            if cap_id in visited:
                continue

            current_path: list[str] = []
            curr: str | None = cap_id
            seen_in_path: set[str] = set()

            while curr:
                if curr in seen_in_path:
                    # Found cycle
                    cycle_start = current_path.index(curr)
                    cycle_nodes = current_path[cycle_start:] + [curr]
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="CYCLE_DETECTED_CAPABILITY",
                        message=f"Cyclic capability hierarchy detected: {' -> '.join(cycle_nodes)}",
                        entity_id=cap_id,
                        file_origin=graph.symbol_origins.get(cap_id),
                    )
                    break

                if curr in visited:
                    break

                seen_in_path.add(curr)
                current_path.append(curr)

                parent = graph.capabilities.get(curr)
                curr = parent.parent_id if parent else None

            visited.update(seen_in_path)

    def _check_dependency_cycles(self, graph: CompiledGraph, report: LintReport) -> None:
        """Detect circular dependencies between architectural components."""
        # Build adjacency graph for directed dependency relations
        adj: dict[str, list[str]] = {}
        for rel in graph.relationships:
            if rel.relation_type in ("depends_on", "uses", "integrates_with"):
                adj.setdefault(rel.source_id, []).append(rel.target_id)

        # 0: unvisited, 1: visiting (in stack), 2: visited
        state: dict[str, int] = {}
        parent_map: dict[str, str] = {}
        reported_cycles: set[frozenset[str]] = set()

        def dfs(node: str, stack: list[str]) -> None:
            state[node] = 1
            stack.append(node)

            for neighbor in adj.get(node, []):
                if state.get(neighbor, 0) == 1:
                    # Cycle detected
                    idx = stack.index(neighbor)
                    cycle = stack[idx:] + [neighbor]
                    cycle_set = frozenset(cycle)
                    if cycle_set not in reported_cycles:
                        reported_cycles.add(cycle_set)
                        report.add_issue(
                            severity=LintSeverity.WARNING,
                            rule="CYCLE_DETECTED_DEPENDENCY",
                            message=f"Circular architectural dependency detected: {' -> '.join(cycle)}",
                            entity_id=node,
                        )
                elif state.get(neighbor, 0) == 0:
                    dfs(neighbor, stack)

            stack.pop()
            state[node] = 2

        for node in list(adj.keys()):
            if state.get(node, 0) == 0:
                dfs(node, [])

    def _check_lifecycles(
        self, graph: CompiledGraph, report: LintReport, as_of_date: date | None = None
    ) -> None:
        """Validate chronological lifecycle phase sequences."""
        apps = graph.get_applications()
        validator = LifecycleValidator()
        lc_report = validator.validate_all(apps, as_of_date=as_of_date)

        for issue in lc_report.issues:
            severity = LintSeverity.ERROR if issue.severity == "ERROR" else LintSeverity.WARNING
            origin = graph.symbol_origins.get(issue.application_id)
            report.add_issue(
                severity=severity,
                rule="LIFECYCLE_INCONSISTENCY",
                message=f"[{issue.application_name}] {issue.message}",
                entity_id=issue.application_id,
                file_origin=origin,
            )

    def _check_technology_governance(
        self, graph: CompiledGraph, report: LintReport, as_of_date: date | None = None
    ) -> None:
        """Verify technology radar statuses and EOL dates."""
        today = as_of_date or date.today()

        # Check EOL for technologies
        for tech in graph.technologies.values():
            origin = graph.symbol_origins.get(tech.id)
            if tech.eol_date and tech.eol_date < today:
                report.add_issue(
                    severity=LintSeverity.WARNING,
                    rule="TECHNOLOGY_EOL_EXPIRED",
                    message=f"Technology '{tech.name}' ({tech.id}) reached End of Life on {tech.eol_date}",
                    entity_id=tech.id,
                    file_origin=origin,
                )

        # Check system usage of prohibited/deprecated technologies
        for sys in graph.systems.values():
            origin = graph.symbol_origins.get(sys.id)
            for tech_id in sys.technologies:
                tech = graph.technologies.get(tech_id)
                if not tech:
                    continue
                if tech.status == TechnologyStatus.PROHIBITED:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="GOVERNANCE_PROHIBITED_TECH_USAGE",
                        message=f"System '{sys.name}' uses PROHIBITED technology '{tech.name}' ({tech.id})",
                        entity_id=sys.id,
                        file_origin=origin,
                    )
                elif tech.status == TechnologyStatus.DEPRECATED:
                    report.add_issue(
                        severity=LintSeverity.WARNING,
                        rule="GOVERNANCE_DEPRECATED_TECH_USAGE",
                        message=f"System '{sys.name}' uses DEPRECATED technology '{tech.name}' ({tech.id})",
                        entity_id=sys.id,
                        file_origin=origin,
                    )

    def _check_roadmap_governance(self, graph: CompiledGraph, report: LintReport) -> None:
        """Validate transformation roadmap plateaus and work packages."""
        # 1. Plateaus validation
        for plateau in graph.plateaus.values():
            origin = graph.symbol_origins.get(plateau.id)

            if plateau.previous_plateau_id:
                if plateau.previous_plateau_id not in graph.plateaus:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="REF_INTEGRITY_DANGLING_PLATEAU_PREDECESSOR",
                        message=f"Plateau '{plateau.id}' references non-existent previous plateau '{plateau.previous_plateau_id}'",
                        entity_id=plateau.id,
                        file_origin=origin,
                    )
                else:
                    pred = graph.plateaus[plateau.previous_plateau_id]
                    if plateau.target_date and pred.target_date and plateau.target_date < pred.target_date:
                        report.add_issue(
                            severity=LintSeverity.ERROR,
                            rule="LIFECYCLE_CHRONOLOGICAL_INVERSION",
                            message=f"Plateau '{plateau.id}' target date ({plateau.target_date}) is earlier than its predecessor '{pred.id}' ({pred.target_date})",
                            entity_id=plateau.id,
                            file_origin=origin,
                        )

            # Cycle detection in plateau predecessor chain
            visited = set()
            curr = plateau.id
            while curr:
                if curr in visited:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="ROADMAP_PLATEAU_CYCLE",
                        message=f"Circular predecessor dependency detected in plateau chain involving '{curr}'",
                        entity_id=plateau.id,
                        file_origin=origin,
                    )
                    break
                visited.add(curr)
                parent = graph.plateaus.get(curr)
                curr = parent.previous_plateau_id if parent else None

            # Verify system references
            for s_id in plateau.active_system_ids:
                if s_id not in graph.systems:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="REF_INTEGRITY_DANGLING_PLATEAU_SYSTEM",
                        message=f"Plateau '{plateau.id}' references non-existent active system '{s_id}'",
                        entity_id=plateau.id,
                        file_origin=origin,
                    )

            for s_id in plateau.decommissioned_system_ids:
                if s_id not in graph.systems:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="REF_INTEGRITY_DANGLING_PLATEAU_SYSTEM",
                        message=f"Plateau '{plateau.id}' references non-existent decommissioned system '{s_id}'",
                        entity_id=plateau.id,
                        file_origin=origin,
                    )

            overlap = set(plateau.active_system_ids) & set(plateau.decommissioned_system_ids)
            for s_id in overlap:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="ROADMAP_CONTRADICTORY_SYSTEM_STATE",
                    message=f"System '{s_id}' cannot be simultaneously active and decommissioned in plateau '{plateau.id}'",
                    entity_id=plateau.id,
                    file_origin=origin,
                )

        # 2. WorkPackages validation
        for wp in graph.work_packages.values():
            origin = graph.symbol_origins.get(wp.id)

            if wp.from_plateau_id and wp.from_plateau_id not in graph.plateaus:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="REF_INTEGRITY_DANGLING_WORK_PACKAGE_PLATEAU",
                    message=f"Work package '{wp.id}' references non-existent from_plateau '{wp.from_plateau_id}'",
                    entity_id=wp.id,
                    file_origin=origin,
                )

            if wp.to_plateau_id and wp.to_plateau_id not in graph.plateaus:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="REF_INTEGRITY_DANGLING_WORK_PACKAGE_PLATEAU",
                    message=f"Work package '{wp.id}' references non-existent to_plateau '{wp.to_plateau_id}'",
                    entity_id=wp.id,
                    file_origin=origin,
                )

            if wp.start_date and wp.target_date and wp.start_date > wp.target_date:
                report.add_issue(
                    severity=LintSeverity.ERROR,
                    rule="LIFECYCLE_CHRONOLOGICAL_INVERSION",
                    message=f"Work package '{wp.id}' start_date ({wp.start_date}) cannot be later than target_date ({wp.target_date})",
                    entity_id=wp.id,
                    file_origin=origin,
                )

            for s_id in wp.involved_system_ids:
                if s_id not in graph.systems:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="REF_INTEGRITY_DANGLING_WORK_PACKAGE_SYSTEM",
                        message=f"Work package '{wp.id}' references non-existent system '{s_id}'",
                        entity_id=wp.id,
                        file_origin=origin,
                    )

            for c_id in wp.realized_capability_ids:
                if c_id not in graph.capabilities:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="REF_INTEGRITY_DANGLING_WORK_PACKAGE_CAPABILITY",
                        message=f"Work package '{wp.id}' references non-existent capability '{c_id}'",
                        entity_id=wp.id,
                        file_origin=origin,
                    )

            for dep_id in wp.depends_on:
                if dep_id not in graph.work_packages:
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="REF_INTEGRITY_DANGLING_WORK_PACKAGE_DEPENDENCY",
                        message=f"Work package '{wp.id}' references non-existent dependency '{dep_id}'",
                        entity_id=wp.id,
                        file_origin=origin,
                    )

        # 3. Work package dependency cycle detection (DFS)
        wp_cycle_visited: set[str] = set()
        wp_cycle_stack: set[str] = set()

        def dfs_wp(node_id: str) -> bool:
            wp_cycle_visited.add(node_id)
            wp_cycle_stack.add(node_id)
            node = graph.work_packages.get(node_id)
            if node:
                for dep in node.depends_on:
                    if dep not in wp_cycle_visited:
                        if dfs_wp(dep):
                            return True
                    elif dep in wp_cycle_stack:
                        return True
            wp_cycle_stack.remove(node_id)
            return False

        for wp_id in graph.work_packages:
            if wp_id not in wp_cycle_visited:
                if dfs_wp(wp_id):
                    report.add_issue(
                        severity=LintSeverity.ERROR,
                        rule="ROADMAP_WORK_PACKAGE_CYCLE",
                        message=f"Circular dependency detected in work package graph involving '{wp_id}'",
                        entity_id=wp_id,
                        file_origin=graph.symbol_origins.get(wp_id),
                    )

