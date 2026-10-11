"""Business Capability Management (BCM) Engine.

Evaluates capability realization coverage, identifies architectural blind spots (gaps),
detects overprovisioned capability hotspots, and aggregates health indicators.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from tecton_arch.core.models import Application, CapabilityHealth, TimeQuadrant
from tecton_arch.dsl.schema import BusinessCapabilityDef


class CapabilityCoverage(BaseModel):
    """Realization mapping and health metrics for an individual business capability."""

    capability_id: str
    name: str
    level: str | None = None
    parent_id: str | None = None
    realizing_system_ids: list[str] = Field(default_factory=list)
    realizing_system_names: list[str] = Field(default_factory=list)
    health: CapabilityHealth = CapabilityHealth.UNMAPPED
    time_distribution: dict[str, int] = Field(default_factory=dict)
    description: str | None = None
    aggregated_system_ids: list[str] = Field(default_factory=list)
    leaf_coverage_percentage: float = 0
    weighted_leaf_coverage_percentage: float = 0
    annual_costs: dict[str, Any] = Field(default_factory=dict)


class BCMReport(BaseModel):
    """Comprehensive Business Capability Management assessment report."""

    aggregation_status: str = "available"
    issues: list[str] = Field(default_factory=list)
    total_capabilities: int
    mapped_capabilities: int
    orphaned_capabilities: list[str] = Field(default_factory=list)  # Gaps / 0 systems
    overprovisioned_capabilities: list[str] = Field(default_factory=list)  # Hotspots (> 2 systems)
    coverages: dict[str, CapabilityCoverage] = Field(default_factory=dict)

    @property
    def coverage_percentage(self) -> float:
        """Percentage of business capabilities realized by at least one system."""
        if self.total_capabilities == 0:
            return 100.0
        return (self.mapped_capabilities / self.total_capabilities) * 100.0


class BCMEngine:
    """Deterministic analytics engine for Business Capability Architecture."""

    def __init__(self, hotspot_threshold: int = 3) -> None:
        self.hotspot_threshold = hotspot_threshold

    def analyze(
        self,
        capabilities: dict[str, BusinessCapabilityDef] | list[BusinessCapabilityDef],
        applications: list[Application],
    ) -> BCMReport:
        """Evaluate realization mapping, gap blind spots, and health across all capabilities."""
        if isinstance(capabilities, list):
            caps_map = {c.id: c for c in capabilities}
        else:
            caps_map = capabilities

        coverages: dict[str, CapabilityCoverage] = {}
        orphaned: list[str] = []
        overprovisioned: list[str] = []

        # Index applications by capability
        cap_to_apps: dict[str, list[Application]] = {c_id: [] for c_id in caps_map.keys()}
        for app in applications:
            for cap_id in app.capabilities:
                if cap_id in cap_to_apps:
                    cap_to_apps[cap_id].append(app)

        mapped_count = 0

        for c_id, cap in caps_map.items():
            realizing = cap_to_apps.get(c_id, [])
            system_ids = [a.id for a in realizing]
            system_names = [a.name for a in realizing]

            # Calculate TIME distribution
            time_counts: dict[str, int] = {}
            for a in realizing:
                q = a.time_classification.value
                time_counts[q] = time_counts.get(q, 0) + 1

            # Determine aggregate health
            health = self._derive_health(realizing)

            coverage = CapabilityCoverage(
                capability_id=c_id,
                name=cap.name,
                level=cap.level,
                parent_id=cap.parent_id,
                realizing_system_ids=system_ids,
                realizing_system_names=system_names,
                health=health,
                time_distribution=time_counts,
                description=cap.description,
            )
            coverages[c_id] = coverage

            if len(realizing) == 0:
                orphaned.append(c_id)
            else:
                mapped_count += 1

            if len(realizing) >= self.hotspot_threshold:
                overprovisioned.append(c_id)

        # Aggregate independently of direct coverage. Detect cycles before traversing.
        children = {cid: sorted(c.id for c in caps_map.values() if c.parent_id == cid) for cid in caps_map}
        cache = {}
        def descendants(cid, visiting):
            if cid in visiting:
                raise ValueError("Capability hierarchy cycle prevents aggregation")
            if cid in cache:
                return cache[cid]
            result = {cid}
            for child in children[cid]:
                result.update(descendants(child, visiting | {cid}))
            cache[cid] = result
            return result
        for cid, coverage in coverages.items():
            try:
                subtree = descendants(cid, set())
            except ValueError as exc:
                return BCMReport(total_capabilities=len(caps_map), mapped_capabilities=mapped_count, orphaned_capabilities=orphaned, overprovisioned_capabilities=overprovisioned, coverages=coverages, aggregation_status="unavailable", issues=[str(exc)])
            leaves = sorted(c for c in subtree if not children[c])
            covered = [c for c in leaves if coverages[c].realizing_system_ids]
            coverage.aggregated_system_ids = sorted({s for c in subtree for s in coverages[c].realizing_system_ids})
            coverage.leaf_coverage_percentage = len(covered) / len(leaves) * 100
            coverage.weighted_leaf_coverage_percentage = sum(caps_map[c].importance for c in covered) / sum(caps_map[c].importance for c in leaves) * 100
            from decimal import Decimal
            totals, missing = {}, []
            for app in applications:
                if app.id not in coverage.aggregated_system_ids:
                    continue
                cost = app.metadata.get("annual_cost")
                if cost:
                    totals[cost["currency"]] = totals.get(cost["currency"], Decimal(0)) + Decimal(cost["amount"])
                else:
                    missing.append(app.id)
            coverage.annual_costs = {"totals_by_currency": {c: str(v) for c, v in sorted(totals.items())}, "missing_system_ids": sorted(missing), "complete": not missing}

        return BCMReport(
            total_capabilities=len(caps_map),
            mapped_capabilities=mapped_count,
            orphaned_capabilities=orphaned,
            overprovisioned_capabilities=overprovisioned,
            coverages=coverages,
        )

    def _derive_health(self, realizing: list[Application]) -> CapabilityHealth:
        """Derive overall capability health based on realizing applications."""
        if not realizing:
            return CapabilityHealth.UNMAPPED

        invest_count = sum(1 for a in realizing if a.time_classification == TimeQuadrant.INVEST)
        tolerate_count = sum(1 for a in realizing if a.time_classification == TimeQuadrant.TOLERATE)
        eliminate_count = sum(1 for a in realizing if a.time_classification == TimeQuadrant.ELIMINATE)
        migrate_count = sum(1 for a in realizing if a.time_classification == TimeQuadrant.MIGRATE)
        unknown_count = sum(1 for a in realizing if a.time_classification == TimeQuadrant.UNKNOWN)

        total = len(realizing)
        if unknown_count == total:
            return CapabilityHealth.UNKNOWN

        # If more than half the realizing apps are marked for elimination or migration, capability is AT_RISK
        if (eliminate_count + migrate_count) / total >= 0.5:
            return CapabilityHealth.AT_RISK

        # If at least one app is INVEST and no eliminate, capability is HEALTHY
        if invest_count > 0 and eliminate_count == 0:
            return CapabilityHealth.HEALTHY

        return CapabilityHealth.TOLERABLE
