"""Semantic Architecture Diff Engine for GitOps & Evolution Tracking.

Compares two compiled architectural graphs (e.g. As-Is vs To-Be, or Git base vs head revision)
to detect entity changes, metric shifts, newly introduced gaps, and quality regressions.
"""

from datetime import date
from collections import Counter
import hashlib
import json
from typing import Any
from pydantic import BaseModel, Field

from tecton_arch.core.models import ChangeType
from tecton_arch.dsl.parser import CompiledGraph
from tecton_arch.engines.bcm_engine import BCMEngine


class EntityDelta(BaseModel):
    """Detailed change delta for an architectural entity."""

    entity_id: str
    entity_type: str  # system, capability, container, technology, relationship
    change_type: ChangeType
    name: str | None = None
    snapshot: dict[str, Any] | None = None
    field_changes: dict[str, tuple[Any, Any]] = Field(default_factory=dict)  # field -> (old, new)


class ArchitectureDiffReport(BaseModel):
    """Comprehensive semantic delta report between two architecture states."""

    as_of_date: date | None = None
    config_fingerprint: str | None = None
    analysis_changes: dict[str, Any] = Field(default_factory=dict)
    configuration_changes: dict[str, Any] = Field(default_factory=dict)
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
        return bool(self.deltas or self.new_risk_issues or self.new_capability_gaps or self.configuration_changes)


def canonical(value, field="", metadata=False):
    from tecton_arch.dsl.references import SET_FIELDS
    if isinstance(value, dict):
        return {key: canonical(item, key, metadata or key == "metadata") for key, item in sorted(value.items())}
    if isinstance(value, list):
        items = [canonical(item, metadata=metadata) for item in value]
        if not metadata and field in SET_FIELDS:
            return sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
        if not metadata and field in ("nodes", "flows"):
            return {item["id"]: item for item in items}
        return items
    return value


def changed_fields(old, new, prefix=""):
    changes = {}
    for key in sorted(old.keys() | new.keys()):
        path = f"{prefix}.{key}" if prefix else key
        a, b = old.get(key), new.get(key)
        if a == b:
            continue
        if isinstance(a, dict) and isinstance(b, dict):
            changes.update(changed_fields(a, b, path))
        else:
            changes[path] = (a, b)
    return changes


class DiffEngine:
    def __init__(self):
        from tecton_arch.engines.linter import GraphLinter
        self.linter = GraphLinter()

    def compare(self, base_graph, head_graph, base_ref="base", head_ref="head", as_of_date=None, config=None):
        from tecton_arch.core.config import TectonConfig
        from tecton_arch.dsl.references import COLLECTIONS
        from tecton_arch.services.bcm_service import BCMService
        config = config or TectonConfig()
        target = as_of_date or date.today()
        deltas = []
        for collection, kind in COLLECTIONS.items():
            old, new = getattr(base_graph, collection), getattr(head_graph, collection)
            for entity_id in sorted(old.keys() | new.keys()):
                a, b = old.get(entity_id), new.get(entity_id)
                if a is None or b is None:
                    entity = b if b is not None else a
                    deltas.append(EntityDelta(entity_id=entity_id, entity_type=kind, change_type=ChangeType.ADDED if a is None else ChangeType.REMOVED, name=entity.name, snapshot=entity.model_dump(mode="json")))
                else:
                    changes = changed_fields(canonical(a.model_dump(mode="json")), canonical(b.model_dump(mode="json")))
                    if changes:
                        deltas.append(EntityDelta(entity_id=entity_id, entity_type=kind, change_type=ChangeType.MODIFIED, name=b.name, field_changes=changes))
        def records(graph):
            return Counter(json.dumps(canonical(r.model_dump(mode="json")), sort_keys=True) for r in graph.relationships)
        old, new = records(base_graph), records(head_graph)
        for difference, change in ((new-old, ChangeType.ADDED), (old-new, ChangeType.REMOVED)):
            for record, count in sorted(difference.items()):
                data = json.loads(record)
                for _ in range(count):
                    identity = f"{data['source_id']} -> {data['target_id']} ({data['relation_type']})"
                    deltas.append(EntityDelta(entity_id=identity, entity_type="relationship", change_type=change, name=identity, snapshot=data))
        base_report = self.linter.lint(base_graph, as_of_date=target, config=config)
        head_report = self.linter.lint(head_graph, as_of_date=target, config=config)
        def issue_key(i):
            return (i.rule, i.entity_id, i.message, i.severity.value)
        base_keys = {issue_key(i) for i in base_report.issues}
        risks = [{"severity": i.severity.value, "rule": i.rule, "entity_id": i.entity_id, "message": i.message} for i in head_report.issues if issue_key(i) not in base_keys]
        summaries = {}
        for label, graph in (("base", base_graph), ("head", head_graph)):
            try:
                report = BCMService(graph, config=config).analyze(target)
                summaries[label] = {"capability_gaps": report.orphaned_capabilities, "coverage_percentage": report.coverage_percentage, "aggregation_status": report.aggregation_status, "issues": report.issues}
            except ValueError as exc:
                summaries[label] = {"capability_gaps": [], "assessment_status": "unavailable", "reason": str(exc)}
        gaps = sorted(set(summaries["head"]["capability_gaps"])-set(summaries["base"]["capability_gaps"]))
        # Fingerprint only analysis settings; never leak repository credentials.
        public_config = config.model_dump(mode="json", exclude={"repository"})
        fingerprint = hashlib.sha256(json.dumps(public_config, sort_keys=True).encode()).hexdigest()
        return ArchitectureDiffReport(base_ref=base_ref, head_ref=head_ref, as_of_date=target, config_fingerprint=fingerprint, analysis_changes=summaries, deltas=deltas, new_risk_issues=risks, new_capability_gaps=gaps)
