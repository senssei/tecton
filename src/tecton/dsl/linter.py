"""Quality Gate and Topological Graph Linter for Architecture-as-Code.

Enforces referential integrity, DAG acyclicity, lifecycle chronological consistency,
and technology governance policies.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any

from tecton.dsl.parser import CompiledGraph
from tecton.dsl.schema import TechnologyStatus
from tecton.engines.lifecycle_validator import LifecycleValidator


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

    def lint(self, graph: CompiledGraph) -> LintReport:
        """Execute all architectural validation passes against the compiled graph."""
        report = LintReport()

        self._check_duplicate_ids(graph, report)
        self._check_referential_integrity(graph, report)
        self._check_capability_cycles(graph, report)
        self._check_dependency_cycles(graph, report)
        self._check_lifecycles(graph, report)
        self._check_technology_governance(graph, report)

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

    def _check_lifecycles(self, graph: CompiledGraph, report: LintReport) -> None:
        """Validate chronological lifecycle phase sequences."""
        apps = graph.get_applications()
        validator = LifecycleValidator()
        lc_report = validator.validate_all(apps)

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

    def _check_technology_governance(self, graph: CompiledGraph, report: LintReport) -> None:
        """Verify technology radar statuses and EOL dates."""
        today = date.today()

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
