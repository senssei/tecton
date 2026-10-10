"""C4-Extended Enterprise Architecture DSL Schemas (Pydantic v2).

Defines the declarative Architecture-as-Code schema bridging C4 structural models
with Enterprise Architecture Portfolio Management (capabilities, TIME scores, lifecycles).
"""

from datetime import date
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

from tecton.core.models import (
    Application,
    Lifecycle,
    LifecyclePhase,
    LifecyclePhaseDate,
    TimeQuadrant,
)


class TechnologyStatus(str, Enum):
    """Technology lifecycle status in enterprise radar."""

    APPROVED = "approved"
    UNDER_EVALUATION = "under_evaluation"
    DEPRECATED = "deprecated"
    PROHIBITED = "prohibited"


class BusinessCapabilityDef(BaseModel):
    """Business Capability representing what an organization does."""

    id: str
    name: str
    level: str | None = Field(default=None, description="Hierarchy level (e.g., L1, L2, L3)")
    parent_id: str | None = Field(default=None, description="Slug ID of parent capability")
    description: str | None = None

    @field_validator("id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Capability id must not be empty")
        return clean


class TechnologyDef(BaseModel):
    """Technology or standard evaluated in enterprise architecture tech radar."""

    id: str
    name: str
    category: str | None = Field(default=None, description="Category (e.g. runtime, database, framework, cloud)")
    status: TechnologyStatus = TechnologyStatus.APPROVED
    eol_date: date | None = Field(default=None, description="End of life date")
    description: str | None = None

    @field_validator("id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Technology id must not be empty")
        return clean


class ContainerDef(BaseModel):
    """C4 Container representing deployable application component."""

    id: str
    name: str
    system_id: str = Field(description="Slug ID of parent Software System")
    technology: str | None = Field(default=None, description="Technology used by container")
    description: str | None = None

    @field_validator("id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Container id must not be empty")
        return clean


class RelationshipDef(BaseModel):
    """Directed architectural relationship between two entities."""

    source_id: str = Field(description="Slug ID of source entity")
    target_id: str = Field(description="Slug ID of target entity")
    relation_type: str = Field(default="depends_on", description="Relationship semantics (e.g., depends_on, realizes, integrates_with, uses)")
    technology: str | None = Field(default=None, description="Integration protocol or tech")
    description: str | None = None

    @field_validator("source_id", "target_id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Relationship endpoint ID must not be empty")
        return clean


class SoftwareSystemDef(BaseModel):
    """C4 Software System extended with EAM portfolio properties."""

    id: str
    name: str
    description: str | None = None
    business_criticality: str | None = None
    functional_suitability: float | None = Field(default=None, ge=1.0, le=5.0)
    technical_suitability: float | None = Field(default=None, ge=1.0, le=5.0)
    time_classification: TimeQuadrant = TimeQuadrant.UNKNOWN
    current_phase: LifecyclePhase | None = None
    lifecycle: Lifecycle | None = None
    capabilities: list[str] = Field(default_factory=list, description="IDs of realized capabilities")
    user_groups: list[str] = Field(default_factory=list, description="User groups utilizing the system")
    technologies: list[str] = Field(default_factory=list, description="IDs of utilized technologies")
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("System id must not be empty")
        return clean

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("System name must not be empty")
        return clean

    def to_application(self) -> Application:
        """Convert SoftwareSystemDef into core Application domain model."""
        return Application(
            id=self.id,
            name=self.name,
            business_criticality=self.business_criticality,
            functional_suitability=self.functional_suitability,
            technical_suitability=self.technical_suitability,
            time_classification=self.time_classification,
            current_phase=self.current_phase or (self.lifecycle.current_phase if self.lifecycle else None),
            lifecycle=self.lifecycle,
            capabilities=self.capabilities,
            user_groups=self.user_groups,
            tags=self.tags,
            metadata={
                **self.metadata,
                "technologies": self.technologies,
                "description": self.description,
            },
        )


class C4EAMManifest(BaseModel):
    """Root or grouped manifest document representing architecture entities."""

    capabilities: list[BusinessCapabilityDef] = Field(default_factory=list)
    systems: list[SoftwareSystemDef] = Field(default_factory=list)
    containers: list[ContainerDef] = Field(default_factory=list)
    relationships: list[RelationshipDef] = Field(default_factory=list)
    technologies: list[TechnologyDef] = Field(default_factory=list)
