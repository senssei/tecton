"""Business Capability Management (BCM) Engine.

Evaluates capability realization coverage, identifies architectural blind spots (gaps),
detects overprovisioned capability hotspots, and aggregates health indicators.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from tecton.core.models import Application, TimeQuadrant
from tecton.dsl.schema import BusinessCapabilityDef


class CapabilityHealth(str, Enum):
    """Aggregate health status of a business capability based on realizing systems."""

    HEALTHY = "HEALTHY"        # Dominated by INVEST / TOLERATE systems
    TOLERABLE = "TOLERABLE"    # Mixed or TOLERATE systems
    AT_RISK = "AT_RISK"        # Dominated by ELIMINATE / MIGRATE systems or expired lifecycles
    UNMAPPED = "UNMAPPED"      # 0 realizing systems (Blind spot / Gap)
    UNKNOWN = "UNKNOWN"        # Realizing systems lack TIME evaluation


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


class BCMReport(BaseModel):
    """Comprehensive Business Capability Management assessment report."""

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
