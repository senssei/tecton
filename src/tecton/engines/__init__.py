"""Deterministic Analytic Engines for Enterprise Architecture Intelligence."""

from tecton.engines.bcm_engine import BCMEngine, BCMReport, CapabilityCoverage, CapabilityHealth
from tecton.engines.diff_engine import ArchitectureDiffReport, ChangeType, DiffEngine, EntityDelta
from tecton.engines.lifecycle_validator import LifecycleIssue, LifecycleValidationReport, LifecycleValidator
from tecton.engines.lineage_engine import DataFlowEdge, DataLineageReport, LineageEngine
from tecton.engines.redundancy import RedundancyDetectionEngine
from tecton.engines.roadmap_engine import (
    PlateauComparison,
    PlateauState,
    RoadmapAnalysisReport,
    RoadmapEngine,
    TransitionalGap,
)
from tecton.engines.time_scoring import TimeScoringEngine
from tecton.engines.trm_engine import BlastRadiusReport, TechnologyRiskItem, TRMEngine, TRMReport

__all__ = [
    "ArchitectureDiffReport",
    "BCMEngine",
    "BCMReport",
    "BlastRadiusReport",
    "CapabilityCoverage",
    "CapabilityHealth",
    "ChangeType",
    "DataFlowEdge",
    "DataLineageReport",
    "DiffEngine",
    "EntityDelta",
    "LifecycleIssue",
    "LifecycleValidationReport",
    "LifecycleValidator",
    "LineageEngine",
    "PlateauComparison",
    "PlateauState",
    "RedundancyDetectionEngine",
    "RoadmapAnalysisReport",
    "RoadmapEngine",
    "TechnologyRiskItem",
    "TimeScoringEngine",
    "TransitionalGap",
    "TRMEngine",
    "TRMReport",
]
