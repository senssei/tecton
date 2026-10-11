"""In-Memory Graph Compiler and Directory Manifest Parser for C4-Extended EAM DSL."""

import fnmatch
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
import yaml
from pydantic import ValidationError

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

CONFIG_FILENAMES = {"tecton.yaml", "tecton.yml", ".tecton.yaml", ".tecton.yml"}


class SchemaValidationError(ValueError):
    """Raised when manifest content violates strict schema constraints or contains unknown fields."""


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
    schema_issues: list[tuple[str, str, str, str | None, str | None]] = field(default_factory=list)

    def add_schema_issue(
        self,
        severity: str,
        rule: str,
        message: str,
        entity_id: str | None = None,
        file_origin: str | None = None,
    ) -> None:
        self.schema_issues.append((severity, rule, message, entity_id, file_origin))


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

    @property
    def schema_issues(self) -> list[tuple[str, str, str, str | None, str | None]]:
        return self.table.schema_issues


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

    def __init__(self, config: Any = None, strict: bool = False) -> None:
        self.config = config
        self.strict = strict

    def parse_directory(self, dir_path: Path | str) -> CompiledGraph:
        """Recursively scan directory and parse scoped YAML and JSON manifests."""
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Architecture directory not found: {path}")

        table = SymbolTable()
        parsed_files: list[str] = []

        if path.is_file():
            self._parse_file(path, table)
            parsed_files.append(str(path))
            if self.strict and any(sev.upper() == "ERROR" for sev, _, _, _, _ in table.schema_issues):
                err_msgs = [f"[{rule}] {msg}" for sev, rule, msg, _, _ in table.schema_issues if sev.upper() == "ERROR"]
                raise SchemaValidationError(f"Strict manifest parsing failed for {path}: {'; '.join(err_msgs)}")
            return CompiledGraph(table, parsed_files)

        # Determine includes and excludes
        include_patterns = ["**/*.yaml", "**/*.yml", "**/*.json"]
        exclude_patterns: list[str] = []
        if self.config:
            manifests_cfg = getattr(self.config, "manifests", None)
            if manifests_cfg:
                if getattr(manifests_cfg, "include", None):
                    include_patterns = list(manifests_cfg.include)
                if getattr(manifests_cfg, "exclude", None):
                    exclude_patterns = list(manifests_cfg.exclude)

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

        def is_ignored(p: Path) -> bool:
            if p.name in CONFIG_FILENAMES:
                return True
            try:
                rel = p.relative_to(path)
                for part in rel.parts[:-1]:
                    if part.startswith(".") or part in ignored_dir_names:
                        return True
            except ValueError:
                for part in p.parts:
                    if part.startswith(".") or part in ignored_dir_names:
                        return True
            return False

        candidates: set[Path] = set()
        for pat in include_patterns:
            candidates.update(p for p in path.glob(pat) if p.is_file())

        for pat in exclude_patterns:
            candidates.difference_update(path.glob(pat))

        manifest_files = sorted(p for p in candidates if not is_ignored(p))


        for mf in manifest_files:
            self._parse_file(mf, table)
            parsed_files.append(str(mf))

        if self.strict and any(sev.upper() == "ERROR" for sev, _, _, _, _ in table.schema_issues):
            err_msgs = [f"[{rule}] {msg}" for sev, rule, msg, _, _ in table.schema_issues if sev.upper() == "ERROR"]
            raise SchemaValidationError(f"Strict manifest parsing failed in workspace: {'; '.join(err_msgs)}")

        return CompiledGraph(table, parsed_files)

    def parse_content(self, content: str, file_origin: str = "<memory>") -> CompiledGraph:
        """Parse raw YAML or JSON string content."""
        table = SymbolTable()
        self._parse_content_into_table(content, file_origin, table)
        if self.strict and any(sev.upper() == "ERROR" for sev, _, _, _, _ in table.schema_issues):
            err_msgs = [f"[{rule}] {msg}" for sev, rule, msg, _, _ in table.schema_issues if sev.upper() == "ERROR"]
            raise SchemaValidationError(f"Strict manifest parsing failed in {file_origin}: {'; '.join(err_msgs)}")
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
                else:
                    msg = f"Unexpected non-object element in list: {item}"
                    table.add_schema_issue("ERROR", "INVALID_MANIFEST_STRUCTURE", msg, None, origin)
                    if self.strict:
                        raise SchemaValidationError(f"{origin}: {msg}")
        elif isinstance(doc, dict):
            known_collections = {
                "capabilities", "systems", "containers", "relationships",
                "technologies", "data_objects", "interfaces", "plateaus",
                "work_packages", "data_flow_diagrams",
            }
            has_collections = any(k in doc for k in known_collections)
            if has_collections:
                extra_top_keys = set(doc.keys()) - known_collections
                if extra_top_keys:
                    msg = f"Extra top-level keys not permitted in collection manifest: {sorted(extra_top_keys)}"
                    table.add_schema_issue("ERROR", "SCHEMA_EXTRA_FORBIDDEN", msg, None, origin)
                    if self.strict:
                        raise SchemaValidationError(f"{origin}: {msg}")

                self._ingest_collection(doc.get("data_flow_diagrams", []), DataFlowDiagramDef, table.register_data_flow_diagram, "data_flow_diagrams", origin, table)
                self._ingest_collection(doc.get("capabilities", []), BusinessCapabilityDef, table.register_capability, "capabilities", origin, table)
                self._ingest_collection(doc.get("systems", []), SoftwareSystemDef, table.register_system, "systems", origin, table)
                self._ingest_collection(doc.get("containers", []), ContainerDef, table.register_container, "containers", origin, table)
                self._ingest_collection(doc.get("relationships", []), RelationshipDef, lambda rel, orig: table.register_relationship(rel), "relationships", origin, table)
                self._ingest_collection(doc.get("technologies", []), TechnologyDef, table.register_technology, "technologies", origin, table)
                self._ingest_collection(doc.get("data_objects", []), DataObjectDef, table.register_data_object, "data_objects", origin, table)
                self._ingest_collection(doc.get("interfaces", []), InterfaceDef, table.register_interface, "interfaces", origin, table)
                self._ingest_collection(doc.get("plateaus", []), PlateauDef, table.register_plateau, "plateaus", origin, table)
                self._ingest_collection(doc.get("work_packages", []), WorkPackageDef, table.register_work_package, "work_packages", origin, table)
            else:
                self._ingest_single_dict(doc, origin, table)
        elif doc is not None:
            msg = f"Unexpected manifest document type {type(doc).__name__}"
            table.add_schema_issue("ERROR", "INVALID_MANIFEST_STRUCTURE", msg, None, origin)
            if self.strict:
                raise SchemaValidationError(f"{origin}: {msg}")

    def _ingest_collection(
        self,
        items: Any,
        model_cls: type,
        register_fn: Any,
        entity_name: str,
        origin: str,
        table: SymbolTable,
    ) -> None:
        if not items:
            return
        if not isinstance(items, list):
            msg = f"Collection '{entity_name}' must be a list, got {type(items).__name__}"
            table.add_schema_issue("ERROR", "INVALID_COLLECTION_TYPE", msg, None, origin)
            if self.strict:
                raise SchemaValidationError(f"{origin}: {msg}")
            return

        for raw in items:
            if not isinstance(raw, dict):
                msg = f"Item in '{entity_name}' collection must be a mapping, got {type(raw).__name__}"
                table.add_schema_issue("ERROR", "INVALID_ENTITY_STRUCTURE", msg, None, origin)
                if self.strict:
                    raise SchemaValidationError(f"{origin}: {msg}")
                continue
            try:
                entity = model_cls.model_validate(raw)
                register_fn(entity, origin)
            except ValidationError as e:
                ent_id = raw.get("id") or (f"{raw.get('source_id')}->{raw.get('target_id')}" if "source_id" in raw else None)
                clean_errs = "; ".join(f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors())
                msg = f"Validation failed for {entity_name} '{ent_id or 'unknown'}': {clean_errs}"
                table.add_schema_issue("ERROR", "SCHEMA_VALIDATION_ERROR", msg, ent_id, origin)
                if self.strict:
                    raise SchemaValidationError(f"{origin}: {msg}") from e

    def _ingest_single_dict(self, item: dict[str, Any], origin: str, table: SymbolTable) -> None:
        kind = item.get("kind", "").lower() if isinstance(item.get("kind"), str) else ""
        ent_id = item.get("id") or (f"{item.get('source_id')}->{item.get('target_id')}" if "source_id" in item else None)

        def _validate_and_register(model_cls: type, register_fn: Any, name: str) -> bool:
            try:
                entity = model_cls.model_validate(item)
                register_fn(entity, origin)
                return True
            except ValidationError as e:
                clean_errs = "; ".join(f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors())
                msg = f"Validation failed for {name} '{ent_id or 'unknown'}': {clean_errs}"
                table.add_schema_issue("ERROR", "SCHEMA_VALIDATION_ERROR", msg, ent_id, origin)
                if self.strict:
                    raise SchemaValidationError(f"{origin}: {msg}") from e
                return False

        if kind in ("data_flow_diagram", "dfd"):
            _validate_and_register(DataFlowDiagramDef, table.register_data_flow_diagram, "data_flow_diagram")
        elif kind in ("capability", "businesscapability"):
            _validate_and_register(BusinessCapabilityDef, table.register_capability, "capability")
        elif kind in ("system", "softwaresystem", "application"):
            _validate_and_register(SoftwareSystemDef, table.register_system, "system")
        elif kind in ("container",):
            _validate_and_register(ContainerDef, table.register_container, "container")
        elif kind in ("relationship",):
            _validate_and_register(RelationshipDef, lambda rel, orig: table.register_relationship(rel), "relationship")
        elif kind in ("technology",):
            _validate_and_register(TechnologyDef, table.register_technology, "technology")
        elif kind in ("dataobject", "data_object", "data-object"):
            _validate_and_register(DataObjectDef, table.register_data_object, "data_object")
        elif kind in ("interface", "api", "contract"):
            _validate_and_register(InterfaceDef, table.register_interface, "interface")
        elif kind in ("plateau", "architectureplateau", "architecture_plateau"):
            _validate_and_register(PlateauDef, table.register_plateau, "plateau")
        elif kind in ("workpackage", "work_package", "work-package", "project", "initiative"):
            _validate_and_register(WorkPackageDef, table.register_work_package, "work_package")
        elif "kind" in item and item["kind"]:
            msg = f"Unrecognized entity kind '{item['kind']}'"
            table.add_schema_issue("ERROR", "UNRECOGNIZED_ENTITY_KIND", msg, ent_id, origin)
            if self.strict:
                raise SchemaValidationError(f"{origin}: {msg}")
        else:
            # Heuristic detection based on required fields
            inferred = False
            if "provider_system_id" in item and "id" in item and "name" in item:
                inferred = _validate_and_register(InterfaceDef, table.register_interface, "interface")
            elif "classification" in item and "id" in item and "name" in item:
                inferred = _validate_and_register(DataObjectDef, table.register_data_object, "data_object")
            elif "system_id" in item and "id" in item and "name" in item:
                inferred = _validate_and_register(ContainerDef, table.register_container, "container")
            elif "source_id" in item and "target_id" in item:
                inferred = _validate_and_register(RelationshipDef, lambda rel, orig: table.register_relationship(rel), "relationship")
            elif "level" in item and "id" in item and "name" in item:
                inferred = _validate_and_register(BusinessCapabilityDef, table.register_capability, "capability")
            elif ("status" in item or "eol_date" in item or "category" in item) and "id" in item and "name" in item:
                inferred = _validate_and_register(TechnologyDef, table.register_technology, "technology")
            elif ("active_system_ids" in item or "decommissioned_system_ids" in item) and "id" in item and "name" in item:
                inferred = _validate_and_register(PlateauDef, table.register_plateau, "plateau")
            elif ("from_plateau_id" in item or "to_plateau_id" in item or "depends_on" in item) and "id" in item and "name" in item:
                inferred = _validate_and_register(WorkPackageDef, table.register_work_package, "work_package")
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
                    inferred = _validate_and_register(SoftwareSystemDef, table.register_system, "system")

            if inferred:
                if self.strict:
                    table.add_schema_issue(
                        "WARNING",
                        "INFERRED_ENTITY_KIND",
                        f"Entity '{ent_id}' is missing explicit 'kind' field and was inferred heuristically.",
                        ent_id,
                        origin,
                    )
            else:
                msg = f"Unrecognized manifest document structure with keys: {sorted(item.keys())}"
                table.add_schema_issue("ERROR", "UNRECOGNIZED_MANIFEST_DOCUMENT", msg, ent_id, origin)
                if self.strict:
                    raise SchemaValidationError(f"{origin}: {msg}")

