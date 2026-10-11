"""Core Domain Models for Tecton Enterprise Architecture Intelligence Engine."""

from datetime import date
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TimeQuadrant(str, Enum):
    """Gartner TIME Framework classification quadrants."""

    INVEST = "INVEST"
    TOLERATE = "TOLERATE"
    MIGRATE = "MIGRATE"
    ELIMINATE = "ELIMINATE"
    UNKNOWN = "UNKNOWN"


class CapabilityHealth(str, Enum):
    """Aggregate health status of a business capability based on realizing systems."""

    HEALTHY = "HEALTHY"        # Dominated by INVEST / TOLERATE systems
    TOLERABLE = "TOLERABLE"    # Mixed or TOLERATE systems
    AT_RISK = "AT_RISK"        # Dominated by ELIMINATE / MIGRATE systems or expired lifecycles
    UNMAPPED = "UNMAPPED"      # 0 realizing systems (Blind spot / Gap)
    UNKNOWN = "UNKNOWN"        # Realizing systems lack TIME evaluation


class ChangeType(str, Enum):
    """Classification of an architectural delta."""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"


class LifecyclePhase(str, Enum):
    """Standard Enterprise Architecture lifecycle phases."""

    PLAN = "plan"
    PHASE_IN = "phaseIn"
    ACTIVE = "active"
    PHASE_OUT = "phaseOut"
    END_OF_LIFE = "endOfLife"


class LifecyclePhaseDate(BaseModel):
    """Phase transition timestamp in lifecycle."""

    phase: LifecyclePhase
    start_date: date

    model_config = ConfigDict(frozen=True, extra="forbid")


class Lifecycle(BaseModel):
    """Lifecycle history and phases of an architectural entity."""

    model_config = ConfigDict(extra="forbid")

    as_string: str | None = None
    phases: list[LifecyclePhaseDate] = Field(default_factory=list)

    def phase_as_of(self, as_of_date: date | None = None) -> LifecyclePhase | None:
        """Derive active lifecycle phase based on a target evaluation date (defaults to date.today())."""
        if not self.phases:
            return None
        target = as_of_date or date.today()
        sorted_phases = sorted(self.phases, key=lambda p: p.start_date)
        active: LifecyclePhase | None = None
        for p in sorted_phases:
            if p.start_date <= target:
                active = p.phase
        return active or sorted_phases[0].phase

    @property
    def current_phase(self) -> LifecyclePhase | None:
        """Derive active lifecycle phase based on today's date if phases are present."""
        return self.phase_as_of()


class Application(BaseModel):
    """Core domain model representing an Application in the IT landscape."""

    id: str
    name: str
    business_criticality: str | None = None
    functional_suitability: float | None = Field(default=None, ge=1.0, le=5.0)
    technical_suitability: float | None = Field(default=None, ge=1.0, le=5.0)
    time_classification: TimeQuadrant = TimeQuadrant.UNKNOWN
    current_phase: LifecyclePhase | None = None
    lifecycle: Lifecycle | None = None
    capabilities: list[str] = Field(default_factory=list)
    user_groups: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def phase_as_of(self, as_of_date: date | None = None) -> LifecyclePhase | None:
        """Derive active lifecycle phase as of a target date."""
        if self.lifecycle:
            return self.lifecycle.phase_as_of(as_of_date)
        return self.current_phase

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Application name must not be empty")
        return v.strip()


class RedundancyCluster(BaseModel):
    """Cluster of applications exhibiting high functional redundancy."""

    cluster_id: str
    application_ids: list[str]
    application_names: list[str]
    similarity_score: float = Field(ge=0.0, le=1.0)
    shared_capabilities: list[str] = Field(default_factory=list)
    shared_user_groups: list[str] = Field(default_factory=list)
    recommendation: str


class TimeConfig(BaseModel):
    """Configuration thresholds for the TIME evaluation engine."""

    business_threshold: float = Field(default=3.5, ge=1.0, le=5.0)
    technical_threshold: float = Field(default=3.5, ge=1.0, le=5.0)


class RedundancyConfig(BaseModel):
    """Configuration weights and threshold for redundancy clustering."""

    capability_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    user_group_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    similarity_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
