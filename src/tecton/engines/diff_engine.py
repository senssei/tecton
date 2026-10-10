"""Semantic Architecture Diff Engine for GitOps & Evolution Tracking.

Compares two compiled architectural graphs (e.g. As-Is vs To-Be, or Git base vs head revision)
to detect entity changes, metric shifts, newly introduced gaps, and quality regressions.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from tecton.dsl.parser import CompiledGraph
from tecton.engines.bcm_engine import BCMEngine


class ChangeType(str, Enum):
    """Classification of an architectural delta."""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"


class EntityDelta(BaseModel):
    """Detailed change delta for an architectural entity."""

    entity_id: str
    entity_type: str  # system, capability, container, technology, relationship
    change_type: ChangeType
    name: str | None = None
    field_changes: dict[str, tuple[Any, Any]] = Field(default_factory=dict)  # field -> (old, new)


class ArchitectureDiffReport(BaseModel):
    """Comprehensive semantic delta report between two architecture states."""

    base_ref: str = "base"
    head_ref: str = "head"
    deltas: list[EntityDelta] = Field(default_factory=list)
    new_risk_issues: list[dict[str, Any]] = Field(default_factory=list)
    new_capability_gaps: list[str] = Field(default_factory=list)

    @property
    def added_count(self) -> int:
        return sum(1 for d in self.deltas if d.change_type == ChangeType.ADDED)

    @property
    def removed_count(self) -> int:
        return sum(1 for d in self.deltas if d.change_type == ChangeType.REMOVED)

    @property
    def modified_count(self) -> int:
        return sum(1 for d in self.deltas if d.change_type == ChangeType.MODIFIED)

    @property
    def has_breaking_changes(self) -> bool:
        """True if any error regressions or unmapped capability gaps were introduced."""
        has_error_risks = any(r.get("severity") == "ERROR" for r in self.new_risk_issues)
        return has_error_risks or len(self.new_capability_gaps) > 0

    @property
    def has_changes(self) -> bool:
        return len(self.deltas) > 0 or len(self.new_risk_issues) > 0


class DiffEngine:
    """Deterministic comparison engine computing architectural graph diffs."""

    def __init__(self) -> None:
        from tecton.dsl.linter import GraphLinter
        self.linter = GraphLinter()
        self.bcm_engine = BCMEngine()

    def compare(
        self,
        base_graph: CompiledGraph,
        head_graph: CompiledGraph,
        base_ref: str = "base",
        head_ref: str = "head",
    ) -> ArchitectureDiffReport:
        """Compute semantic diff between base and head architectural states."""
        deltas: list[EntityDelta] = []

        self._diff_capabilities(base_graph, head_graph, deltas)
        self._diff_systems(base_graph, head_graph, deltas)
        self._diff_technologies(base_graph, head_graph, deltas)
        self._diff_relationships(base_graph, head_graph, deltas)

        # Detect new risk regressions introduced in head
        new_risks = self._detect_risk_regressions(base_graph, head_graph)

        # Detect newly introduced capability gaps
        new_gaps = self._detect_gap_regressions(base_graph, head_graph)

        return ArchitectureDiffReport(
            base_ref=base_ref,
            head_ref=head_ref,
            deltas=deltas,
            new_risk_issues=new_risks,
            new_capability_gaps=new_gaps,
        )

    def _diff_capabilities(
        self, base: CompiledGraph, head: CompiledGraph, deltas: list[EntityDelta]
    ) -> None:
        base_ids = set(base.capabilities.keys())
        head_ids = set(head.capabilities.keys())

        for c_id in sorted(head_ids - base_ids):
            c = head.capabilities[c_id]
            deltas.append(
                EntityDelta(
                    entity_id=c_id,
                    entity_type="capability",
                    change_type=ChangeType.ADDED,
                    name=c.name,
                )
            )

        for c_id in sorted(base_ids - head_ids):
            c = base.capabilities[c_id]
            deltas.append(
                EntityDelta(
                    entity_id=c_id,
                    entity_type="capability",
                    change_type=ChangeType.REMOVED,
                    name=c.name,
                )
            )

        for c_id in sorted(base_ids & head_ids):
            c_base = base.capabilities[c_id]
            c_head = head.capabilities[c_id]
            field_changes: dict[str, tuple[Any, Any]] = {}
            if c_base.name != c_head.name:
                field_changes["name"] = (c_base.name, c_head.name)
            if c_base.parent_id != c_head.parent_id:
                field_changes["parent_id"] = (c_base.parent_id, c_head.parent_id)
            if c_base.level != c_head.level:
                field_changes["level"] = (c_base.level, c_head.level)

            if field_changes:
                deltas.append(
                    EntityDelta(
                        entity_id=c_id,
                        entity_type="capability",
                        change_type=ChangeType.MODIFIED,
                        name=c_head.name,
                        field_changes=field_changes,
                    )
                )

    def _diff_systems(
        self, base: CompiledGraph, head: CompiledGraph, deltas: list[EntityDelta]
    ) -> None:
        base_ids = set(base.systems.keys())
        head_ids = set(head.systems.keys())

        for s_id in sorted(head_ids - base_ids):
            s = head.systems[s_id]
            deltas.append(
                EntityDelta(
                    entity_id=s_id,
                    entity_type="system",
                    change_type=ChangeType.ADDED,
                    name=s.name,
                )
            )

        for s_id in sorted(base_ids - head_ids):
            s = base.systems[s_id]
            deltas.append(
                EntityDelta(
                    entity_id=s_id,
                    entity_type="system",
                    change_type=ChangeType.REMOVED,
                    name=s.name,
                )
            )

        for s_id in sorted(base_ids & head_ids):
            s_base = base.systems[s_id]
            s_head = head.systems[s_id]
            field_changes: dict[str, tuple[Any, Any]] = {}

            if s_base.name != s_head.name:
                field_changes["name"] = (s_base.name, s_head.name)
            if s_base.time_classification != s_head.time_classification:
                field_changes["time_classification"] = (
                    s_base.time_classification.value,
                    s_head.time_classification.value,
                )
            if s_base.business_criticality != s_head.business_criticality:
                field_changes["business_criticality"] = (
                    s_base.business_criticality,
                    s_head.business_criticality,
                )
            if set(s_base.capabilities) != set(s_head.capabilities):
                field_changes["capabilities"] = (s_base.capabilities, s_head.capabilities)
            if set(s_base.technologies) != set(s_head.technologies):
                field_changes["technologies"] = (s_base.technologies, s_head.technologies)

            if field_changes:
                deltas.append(
                    EntityDelta(
                        entity_id=s_id,
                        entity_type="system",
                        change_type=ChangeType.MODIFIED,
                        name=s_head.name,
                        field_changes=field_changes,
                    )
                )

    def _diff_technologies(
        self, base: CompiledGraph, head: CompiledGraph, deltas: list[EntityDelta]
    ) -> None:
        base_ids = set(base.technologies.keys())
        head_ids = set(head.technologies.keys())

        for t_id in sorted(head_ids - base_ids):
            t = head.technologies[t_id]
            deltas.append(
                EntityDelta(
                    entity_id=t_id,
                    entity_type="technology",
                    change_type=ChangeType.ADDED,
                    name=t.name,
                )
            )

        for t_id in sorted(base_ids - head_ids):
            t = base.technologies[t_id]
            deltas.append(
                EntityDelta(
                    entity_id=t_id,
                    entity_type="technology",
                    change_type=ChangeType.REMOVED,
                    name=t.name,
                )
            )

        for t_id in sorted(base_ids & head_ids):
            t_base = base.technologies[t_id]
            t_head = head.technologies[t_id]
            field_changes: dict[str, tuple[Any, Any]] = {}

            if t_base.status != t_head.status:
                field_changes["status"] = (t_base.status.value, t_head.status.value)
            if t_base.eol_date != t_head.eol_date:
                field_changes["eol_date"] = (str(t_base.eol_date), str(t_head.eol_date))

            if field_changes:
                deltas.append(
                    EntityDelta(
                        entity_id=t_id,
                        entity_type="technology",
                        change_type=ChangeType.MODIFIED,
                        name=t_head.name,
                        field_changes=field_changes,
                    )
                )

    def _diff_relationships(
        self, base: CompiledGraph, head: CompiledGraph, deltas: list[EntityDelta]
    ) -> None:
        def rel_key(r: Any) -> tuple[str, str, str]:
            return (r.source_id, r.target_id, r.relation_type)

        base_rels = {rel_key(r): r for r in base.relationships}
        head_rels = {rel_key(r): r for r in head.relationships}

        for key in sorted(set(head_rels.keys()) - set(base_rels.keys())):
            r = head_rels[key]
            rel_id = f"{r.source_id} -> {r.target_id} ({r.relation_type})"
            deltas.append(
                EntityDelta(
                    entity_id=rel_id,
                    entity_type="relationship",
                    change_type=ChangeType.ADDED,
                    name=rel_id,
                )
            )

        for key in sorted(set(base_rels.keys()) - set(head_rels.keys())):
            r = base_rels[key]
            rel_id = f"{r.source_id} -> {r.target_id} ({r.relation_type})"
            deltas.append(
                EntityDelta(
                    entity_id=rel_id,
                    entity_type="relationship",
                    change_type=ChangeType.REMOVED,
                    name=rel_id,
                )
            )

    def _detect_risk_regressions(
        self, base: CompiledGraph, head: CompiledGraph
    ) -> list[dict[str, Any]]:
        base_report = self.linter.lint(base)
        head_report = self.linter.lint(head)

        def issue_key(issue: Any) -> tuple[str, str, str]:
            return (issue.rule, str(issue.entity_id), issue.message)

        base_keys = {issue_key(i) for i in base_report.issues}
        new_issues: list[dict[str, Any]] = []

        for issue in head_report.issues:
            if issue_key(issue) not in base_keys:
                new_issues.append({
                    "severity": issue.severity.value,
                    "rule": issue.rule,
                    "entity_id": issue.entity_id,
                    "message": issue.message,
                })

        return new_issues

    def _detect_gap_regressions(
        self, base: CompiledGraph, head: CompiledGraph
    ) -> list[str]:
        base_bcm = self.bcm_engine.analyze(base.capabilities, base.get_applications())
        head_bcm = self.bcm_engine.analyze(head.capabilities, head.get_applications())

        base_orphans = set(base_bcm.orphaned_capabilities)
        head_orphans = set(head_bcm.orphaned_capabilities)

        # Gaps that are in head but were mapped in base
        return sorted(list(head_orphans - base_orphans))
