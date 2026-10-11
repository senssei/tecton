"""C4-Extended Enterprise Architecture DSL Schemas (Pydantic v2).

Defines the declarative Architecture-as-Code schema bridging C4 structural models
with Enterprise Architecture Portfolio Management (capabilities, TIME scores, lifecycles).
"""

from datetime import date
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

from tecton_arch.core.models import (
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
    relation_type: str = Field(default="depends_on", description="Relationship semantics (e.g., depends_on, realizes, integrates_with, uses, data_flow)")
    technology: str | None = Field(default=None, description="Integration protocol or tech")
    data_objects: list[str] = Field(default_factory=list, description="IDs of data objects transferred across this relationship")
    description: str | None = None

    @field_validator("source_id", "target_id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Relationship endpoint ID must not be empty")
        return clean


class DataClassification(str, Enum):
    """Data privacy and security classification tiers."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED_PII = "RESTRICTED_PII"
    PCI_DSS = "PCI_DSS"


class DataObjectDef(BaseModel):
    """Business Data Object / Entity cataloged in Enterprise Architecture."""

    id: str
    name: str
    classification: DataClassification = DataClassification.INTERNAL
    description: str | None = None
    owner: str | None = None

    @field_validator("id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("DataObject id must not be empty")
        return clean


class InterfaceDef(BaseModel):
    """Communication interface or API contract exposed by a provider system."""

    id: str
    name: str
    protocol: str = Field(default="REST", description="Integration protocol (e.g., REST, GraphQL, gRPC, Kafka, AMQP)")
    provider_system_id: str = Field(description="Slug ID of provider system exposing the interface")
    consumer_system_ids: list[str] = Field(default_factory=list, description="Slug IDs of consumer systems")
    data_objects: list[str] = Field(default_factory=list, description="IDs of data objects transferred by this interface")
    description: str | None = None

    @field_validator("id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Interface id must not be empty")
        return clean


class SoftwareSystemDef(BaseModel):
    """C4 Software System extended with EAM portfolio properties."""

    id: str
    name: str
    description: str | None = None
    owner: str | None = Field(default=None, description="Accountable team or person")
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

    def to_application(self, as_of_date: date | None = None) -> Application:
        """Convert SoftwareSystemDef into core Application domain model as of target date."""
        if as_of_date and self.lifecycle:
            phase = self.lifecycle.phase_as_of(as_of_date) or self.current_phase
        elif not self.current_phase and self.lifecycle:
            phase = self.lifecycle.phase_as_of()
        else:
            phase = self.current_phase
        return Application(
            id=self.id,
            name=self.name,
            business_criticality=self.business_criticality,
            functional_suitability=self.functional_suitability,
            technical_suitability=self.technical_suitability,
            time_classification=self.time_classification,
            current_phase=phase,
            lifecycle=self.lifecycle,
            capabilities=self.capabilities,
            user_groups=self.user_groups,
            tags=self.tags,
            metadata={
                **self.metadata,
                "technologies": self.technologies,
                "description": self.description,
                "owner": self.owner,
            },
        )


class WorkPackageStatus(str, Enum):
    """Execution status for architecture transformation work packages."""

    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PlateauDef(BaseModel):
    """Architecture Plateau representing a stable baseline, transition, or target state."""

    id: str
    name: str
    description: str | None = None
    target_date: date | None = Field(default=None, description="Target milestone completion date")
    previous_plateau_id: str | None = Field(default=None, description="Predecessor plateau ID")
    active_system_ids: list[str] = Field(default_factory=list, description="Active software systems in this plateau")
    decommissioned_system_ids: list[str] = Field(default_factory=list, description="Retired software systems in this plateau")
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Plateau id must not be empty")
        return clean

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Plateau name must not be empty")
        return clean


class WorkPackageDef(BaseModel):
    """Transformation initiative, migration project, or work package."""

    id: str
    name: str
    description: str | None = None
    start_date: date | None = Field(default=None, description="Scheduled start date")
    target_date: date | None = Field(default=None, description="Scheduled completion date")
    status: WorkPackageStatus = WorkPackageStatus.PLANNED
    from_plateau_id: str | None = Field(default=None, description="Starting transition plateau")
    to_plateau_id: str | None = Field(default=None, description="Target transition plateau")
    involved_system_ids: list[str] = Field(default_factory=list, description="Systems affected or delivered")
    realized_capability_ids: list[str] = Field(default_factory=list, description="Capabilities delivered or impacted")
    depends_on: list[str] = Field(default_factory=list, description="Prerequisite work package IDs")
    owner: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def id_must_be_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("WorkPackage id must not be empty")
        return clean

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("WorkPackage name must not be empty")
        return clean


class DFDNodeDef(BaseModel):
    """Explicit node in a diagram-local DFD namespace."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: str = Field(pattern="^(process|data_store|external_entity)$")
    description: str | None = None
    system_id: str | None = None

    @field_validator("id", "name")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DFD node ID and name must not be blank")
        return value.strip()


class DFDFlowDef(BaseModel):
    """Named data transfer between DFD nodes; references shared data objects."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    data_objects: list[str] = Field(min_length=1)
    description: str | None = None

    @field_validator("id", "name", "source_id", "target_id")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DFD flow fields must not be blank")
        return value.strip()


class DataFlowDiagramDef(BaseModel):
    """Explicit DFD; nodes and flow IDs are local to this diagram."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    nodes: list[DFDNodeDef] = Field(default_factory=list)
    flows: list[DFDFlowDef] = Field(default_factory=list)

    @field_validator("id", "name")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DFD ID and name must not be blank")
        return value.strip()


class C4EAMManifest(BaseModel):
    """Root or grouped manifest document representing architecture entities."""

    capabilities: list[BusinessCapabilityDef] = Field(default_factory=list)
    systems: list[SoftwareSystemDef] = Field(default_factory=list)
    containers: list[ContainerDef] = Field(default_factory=list)
    relationships: list[RelationshipDef] = Field(default_factory=list)
    technologies: list[TechnologyDef] = Field(default_factory=list)
    data_objects: list[DataObjectDef] = Field(default_factory=list)
    interfaces: list[InterfaceDef] = Field(default_factory=list)
    plateaus: list[PlateauDef] = Field(default_factory=list)
    work_packages: list[WorkPackageDef] = Field(default_factory=list)
    data_flow_diagrams: list[DataFlowDiagramDef] = Field(default_factory=list)

