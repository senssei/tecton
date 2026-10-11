"""In-Memory Graph Compiler and Directory Manifest Parser for C4-Extended EAM DSL."""

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
import yaml

from tecton_arch.core.models import Application
from tecton_arch.dsl.schema import (
    BusinessCapabilityDef,
    C4EAMManifest,
    ContainerDef,
    DataObjectDef,
    DataFlowDiagramDef,
    InterfaceDef,
    PlateauDef,
    RelationshipDef,
    SoftwareSystemDef,
    TechnologyDef,
    WorkPackageDef,
)


@dataclass
class SymbolTable:
    """Registry of all resolved architectural symbols across workspace files."""

    capabilities: dict[str, BusinessCapabilityDef] = field(default_factory=dict)
    systems: dict[str, SoftwareSystemDef] = field(default_factory=dict)
    containers: dict[str, ContainerDef] = field(default_factory=dict)
    technologies: dict[str, TechnologyDef] = field(default_factory=dict)
    relationships: list[RelationshipDef] = field(default_factory=list)
    data_objects: dict[str, DataObjectDef] = field(default_factory=dict)
    interfaces: dict[str, InterfaceDef] = field(default_factory=dict)
    plateaus: dict[str, PlateauDef] = field(default_factory=dict)
    work_packages: dict[str, WorkPackageDef] = field(default_factory=dict)
    symbol_origins: dict[str, str] = field(default_factory=dict)
    duplicate_ids: list[tuple[str, str, str]] = field(default_factory=list)
    data_flow_diagrams: dict[str, DataFlowDiagramDef] = field(default_factory=dict)

    def register_data_flow_diagram(self, diagram: DataFlowDiagramDef, origin: str) -> None:
        if diagram.id in self.symbol_origins:
            self.duplicate_ids.append((diagram.id, self.symbol_origins[diagram.id], origin))
        else:
            self.symbol_origins[diagram.id] = origin
        self.data_flow_diagrams[diagram.id] = diagram

    def register_capability(self, cap: BusinessCapabilityDef, origin: str) -> None:
        if cap.id in self.symbol_origins:
            self.duplicate_ids.append((cap.id, self.symbol_origins[cap.id], origin))
        else:
            self.symbol_origins[cap.id] = origin
        self.capabilities[cap.id] = cap

    def register_system(self, sys: SoftwareSystemDef, origin: str) -> None:
        if sys.id in self.symbol_origins:
            self.duplicate_ids.append((sys.id, self.symbol_origins[sys.id], origin))
        else:
            self.symbol_origins[sys.id] = origin
        self.systems[sys.id] = sys

    def register_container(self, cnt: ContainerDef, origin: str) -> None:
        if cnt.id in self.symbol_origins:
            self.duplicate_ids.append((cnt.id, self.symbol_origins[cnt.id], origin))
        else:
            self.symbol_origins[cnt.id] = origin
        self.containers[cnt.id] = cnt

    def register_technology(self, tech: TechnologyDef, origin: str) -> None:
        if tech.id in self.symbol_origins:
            self.duplicate_ids.append((tech.id, self.symbol_origins[tech.id], origin))
        else:
            self.symbol_origins[tech.id] = origin
        self.technologies[tech.id] = tech

    def register_data_object(self, obj: DataObjectDef, origin: str) -> None:
        if obj.id in self.symbol_origins:
            self.duplicate_ids.append((obj.id, self.symbol_origins[obj.id], origin))
        else:
            self.symbol_origins[obj.id] = origin
        self.data_objects[obj.id] = obj

    def register_interface(self, iface: InterfaceDef, origin: str) -> None:
        if iface.id in self.symbol_origins:
            self.duplicate_ids.append((iface.id, self.symbol_origins[iface.id], origin))
        else:
            self.symbol_origins[iface.id] = origin
        self.interfaces[iface.id] = iface

    def register_plateau(self, plateau: PlateauDef, origin: str) -> None:
        if plateau.id in self.symbol_origins:
            self.duplicate_ids.append((plateau.id, self.symbol_origins[plateau.id], origin))
        else:
            self.symbol_origins[plateau.id] = origin
        self.plateaus[plateau.id] = plateau

    def register_work_package(self, wp: WorkPackageDef, origin: str) -> None:
        if wp.id in self.symbol_origins:
            self.duplicate_ids.append((wp.id, self.symbol_origins[wp.id], origin))
        else:
            self.symbol_origins[wp.id] = origin
        self.work_packages[wp.id] = wp

    def register_relationship(self, rel: RelationshipDef) -> None:
        self.relationships.append(rel)


class CompiledGraph:
    """Compiled In-Memory Architectural Graph providing fast index and adjacency queries."""

    def __init__(self, table: SymbolTable, files_parsed: list[str] | None = None) -> None:
        self.table = table
        self.files_parsed = files_parsed or []
        self._outgoing_index: dict[str, list[RelationshipDef]] = {}
        self._incoming_index: dict[str, list[RelationshipDef]] = {}
        self._build_indices()

    def _build_indices(self) -> None:
        for rel in self.table.relationships:
            self._outgoing_index.setdefault(rel.source_id, []).append(rel)
            self._incoming_index.setdefault(rel.target_id, []).append(rel)

    @property
    def capabilities(self) -> dict[str, BusinessCapabilityDef]:
        return self.table.capabilities

    @property
    def systems(self) -> dict[str, SoftwareSystemDef]:
        return self.table.systems

    @property
    def containers(self) -> dict[str, ContainerDef]:
        return self.table.containers

    @property
    def technologies(self) -> dict[str, TechnologyDef]:
        return self.table.technologies

    @property
    def data_objects(self) -> dict[str, DataObjectDef]:
        return self.table.data_objects

    @property
    def interfaces(self) -> dict[str, InterfaceDef]:
        return self.table.interfaces

    @property
    def plateaus(self) -> dict[str, PlateauDef]:
        return self.table.plateaus

    @property
    def work_packages(self) -> dict[str, WorkPackageDef]:
        return self.table.work_packages

    @property
    def relationships(self) -> list[RelationshipDef]:
        return self.table.relationships

    @property
    def data_flow_diagrams(self) -> dict[str, DataFlowDiagramDef]:
        return self.table.data_flow_diagrams

    @property
    def symbol_origins(self) -> dict[str, str]:
        return self.table.symbol_origins

    @property
    def duplicate_ids(self) -> list[tuple[str, str, str]]:
        return self.table.duplicate_ids

    def all_symbol_ids(self) -> set[str]:
        """Return union of all registered entity IDs."""
        return (
            set(self.table.capabilities.keys())
            | set(self.table.systems.keys())
            | set(self.table.containers.keys())
            | set(self.table.technologies.keys())
            | set(self.table.data_objects.keys())
            | set(self.table.interfaces.keys())
            | set(self.table.plateaus.keys())
            | set(self.table.work_packages.keys())
            | set(self.table.data_flow_diagrams.keys())
        )

    def get_entity(self, entity_id: str) -> Any | None:
        """Fetch entity by ID from any metamodel collection."""
        if entity_id in self.table.data_flow_diagrams:
            return self.table.data_flow_diagrams[entity_id]
        if entity_id in self.table.systems:
            return self.table.systems[entity_id]
        if entity_id in self.table.capabilities:
            return self.table.capabilities[entity_id]
        if entity_id in self.table.containers:
            return self.table.containers[entity_id]
        if entity_id in self.table.technologies:
            return self.table.technologies[entity_id]
        if entity_id in self.table.data_objects:
            return self.table.data_objects[entity_id]
        if entity_id in self.table.interfaces:
            return self.table.interfaces[entity_id]
        if entity_id in self.table.plateaus:
            return self.table.plateaus[entity_id]
        if entity_id in self.table.work_packages:
            return self.table.work_packages[entity_id]
        return None

    def outgoing_relationships(self, source_id: str) -> list[RelationshipDef]:
        return self._outgoing_index.get(source_id, [])

    def incoming_relationships(self, target_id: str) -> list[RelationshipDef]:
        return self._incoming_index.get(target_id, [])

    def get_applications(self, as_of_date: date | None = None) -> list[Application]:
        """Convert all SoftwareSystems into core Application models as of target date."""
        return [sys.to_application(as_of_date=as_of_date) for sys in self.table.systems.values()]


class C4EAMParser:
    """Parser and Compiler for C4-Extended EAM DSL workspace directories and manifests."""

    def __init__(self) -> None:
        pass

    def parse_directory(self, dir_path: Path | str) -> CompiledGraph:
        """Recursively scan directory and parse all YAML and JSON manifests."""
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Architecture directory not found: {path}")

        table = SymbolTable()
        parsed_files: list[str] = []

        if path.is_file():
            self._parse_file(path, table)
            parsed_files.append(str(path))
            return CompiledGraph(table, parsed_files)

        # Sort for deterministic processing
        ignored_dir_names = {
            "node_modules",
            "dist",
            "build",
            "venv",
            ".venv",
            "__pycache__",
            ".git",
            ".github",
            ".pytest_cache",
            ".ruff_cache",
        }
        manifest_files = sorted(
            [
                p
                for p in path.rglob("*")
                if p.is_file()
                and p.suffix.lower() in (".yaml", ".yml", ".json")
                and not any(part.startswith(".") or part in ignored_dir_names for part in p.parts)
            ]
        )

        for mf in manifest_files:
            self._parse_file(mf, table)
            parsed_files.append(str(mf))

        return CompiledGraph(table, parsed_files)

    def parse_content(self, content: str, file_origin: str = "<memory>") -> CompiledGraph:
        """Parse raw YAML or JSON string content."""
        table = SymbolTable()
        self._parse_content_into_table(content, file_origin, table)
        return CompiledGraph(table, [file_origin])

    def _parse_file(self, file_path: Path, table: SymbolTable) -> None:
        content = file_path.read_text(encoding="utf-8")
        self._parse_content_into_table(content, str(file_path), table)

    def _parse_content_into_table(self, content: str, origin: str, table: SymbolTable) -> None:
        try:
            documents = list(yaml.safe_load_all(content))
        except Exception as e:
            raise ValueError(f"YAML/JSON syntax error in {origin}: {e}") from e

        for doc in documents:
            if doc is None:
                continue
            self._ingest_document(doc, origin, table)

    def _ingest_document(self, doc: Any, origin: str, table: SymbolTable) -> None:
        if isinstance(doc, list):
            for item in doc:
                if isinstance(item, dict):
                    self._ingest_single_dict(item, origin, table)
        elif isinstance(doc, dict):
            # Check if it has collection keys: capabilities, systems, etc.
            has_collections = any(
                k in doc for k in (
                    "capabilities", "systems", "containers", "relationships",
                    "technologies", "data_objects", "interfaces", "plateaus", "work_packages", "data_flow_diagrams"
                )
            )
            if has_collections:
                for raw in doc.get("data_flow_diagrams", []):
                    table.register_data_flow_diagram(DataFlowDiagramDef.model_validate(raw), origin)
                for cap_raw in doc.get("capabilities", []):
                    table.register_capability(BusinessCapabilityDef.model_validate(cap_raw), origin)
                for sys_raw in doc.get("systems", []):
                    table.register_system(SoftwareSystemDef.model_validate(sys_raw), origin)
                for cnt_raw in doc.get("containers", []):
                    table.register_container(ContainerDef.model_validate(cnt_raw), origin)
                for rel_raw in doc.get("relationships", []):
                    table.register_relationship(RelationshipDef.model_validate(rel_raw))
                for tech_raw in doc.get("technologies", []):
                    table.register_technology(TechnologyDef.model_validate(tech_raw), origin)
                for data_raw in doc.get("data_objects", []):
                    table.register_data_object(DataObjectDef.model_validate(data_raw), origin)
                for iface_raw in doc.get("interfaces", []):
                    table.register_interface(InterfaceDef.model_validate(iface_raw), origin)
                for p_raw in doc.get("plateaus", []):
                    table.register_plateau(PlateauDef.model_validate(p_raw), origin)
                for wp_raw in doc.get("work_packages", []):
                    table.register_work_package(WorkPackageDef.model_validate(wp_raw), origin)
            else:
                self._ingest_single_dict(doc, origin, table)

    def _ingest_single_dict(self, item: dict[str, Any], origin: str, table: SymbolTable) -> None:
        kind = item.get("kind", "").lower()
        if kind in ("data_flow_diagram", "dfd"):
            table.register_data_flow_diagram(DataFlowDiagramDef.model_validate(item), origin)
        elif kind in ("capability", "businesscapability"):
            table.register_capability(BusinessCapabilityDef.model_validate(item), origin)
        elif kind in ("system", "softwaresystem", "application"):
            table.register_system(SoftwareSystemDef.model_validate(item), origin)
        elif kind in ("container",):
            table.register_container(ContainerDef.model_validate(item), origin)
        elif kind in ("relationship",):
            table.register_relationship(RelationshipDef.model_validate(item))
        elif kind in ("technology",):
            table.register_technology(TechnologyDef.model_validate(item), origin)
        elif kind in ("dataobject", "data_object", "data-object"):
            table.register_data_object(DataObjectDef.model_validate(item), origin)
        elif kind in ("interface", "api", "contract"):
            table.register_interface(InterfaceDef.model_validate(item), origin)
        elif kind in ("plateau", "architectureplateau", "architecture_plateau"):
            table.register_plateau(PlateauDef.model_validate(item), origin)
        elif kind in ("workpackage", "work_package", "work-package", "project", "initiative"):
            table.register_work_package(WorkPackageDef.model_validate(item), origin)
        else:
            # Heuristic detection based on required fields
            if "provider_system_id" in item and "id" in item and "name" in item:
                table.register_interface(InterfaceDef.model_validate(item), origin)
            elif "classification" in item and "id" in item and "name" in item:
                table.register_data_object(DataObjectDef.model_validate(item), origin)
            elif "system_id" in item and "id" in item and "name" in item:
                table.register_container(ContainerDef.model_validate(item), origin)
            elif "source_id" in item and "target_id" in item:
                table.register_relationship(RelationshipDef.model_validate(item))
            elif "level" in item and "id" in item and "name" in item:
                table.register_capability(BusinessCapabilityDef.model_validate(item), origin)
            elif ("status" in item or "eol_date" in item or "category" in item) and "id" in item and "name" in item:
                table.register_technology(TechnologyDef.model_validate(item), origin)
            elif ("active_system_ids" in item or "decommissioned_system_ids" in item) and "id" in item and "name" in item:
                table.register_plateau(PlateauDef.model_validate(item), origin)
            elif ("from_plateau_id" in item or "to_plateau_id" in item or "depends_on" in item) and "id" in item and "name" in item:
                table.register_work_package(WorkPackageDef.model_validate(item), origin)
            elif "id" in item and "name" in item:
                is_system_like = (
                    "functional_suitability" in item
                    or "technical_suitability" in item
                    or "business_criticality" in item
                    or "time_classification" in item
                    or "capabilities" in item
                    or "user_groups" in item
                    or "current_phase" in item
                    or str(item.get("id", "")).startswith(("sys-", "system-", "app-"))
                )
                if is_system_like:
                    table.register_system(SoftwareSystemDef.model_validate(item), origin)
