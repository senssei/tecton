"""Spotify Backstage Software Catalog Connector.

Provides bi-directional interoperability between Tecton Architecture-as-Code
and Spotify Backstage entity definitions (Component, System, Domain, API, Resource).
"""

from typing import Any
import yaml

from tecton_arch.dsl.parser import CompiledGraph
from tecton_arch.dsl.schema import (
    BusinessCapabilityDef,
    ContainerDef,
    InterfaceDef,
    SoftwareSystemDef,
    TechnologyDef,
)


class BackstageConnector:
    """Bi-directional adapter for Spotify Backstage Software Catalog manifests."""

    @classmethod
    def export_catalog(cls, graph: CompiledGraph) -> list[dict[str, Any]]:
        """Convert CompiledGraph into a list of Backstage entity definitions."""
        entities: list[dict[str, Any]] = []

        # 1. Domains (from Business Capabilities)
        for cap in graph.capabilities.values():
            if cap.level == "L1" or cap.parent_id is None:
                domain_entity = {
                    "apiVersion": "backstage.io/v1alpha1",
                    "kind": "Domain",
                    "metadata": {
                        "name": cls._sanitize_name(cap.id),
                        "title": cap.name,
                        "description": cap.description or f"Enterprise capability: {cap.name}",
                        "tags": ["capability", f"level-{cap.level or 'L1'}"],
                        "annotations": {
                            "tecton.io/domain-id": cap.id,
                        },
                    },
                    "spec": {
                        "owner": "enterprise-architecture",
                    },
                }
                entities.append(domain_entity)

        # 2. Systems and Components (from Software Systems and Containers)
        for sys in graph.systems.values():
            safe_sys_name = cls._sanitize_name(sys.id)
            domain_ref = cls._sanitize_name(sys.capabilities[0]) if sys.capabilities else None

            # Backstage System grouping
            system_entity = {
                "apiVersion": "backstage.io/v1alpha1",
                "kind": "System",
                "metadata": {
                    "name": safe_sys_name,
                    "title": sys.name,
                    "description": sys.description or f"System: {sys.name}",
                    "tags": [t.lower() for t in sys.tags] + [sys.time_classification.value.lower()],
                    "annotations": {
                        "tecton.io/domain-id": sys.id,
                    },
                },
                "spec": {
                    "owner": sys.metadata.get("owner", "architecture-team"),
                    **({"domain": domain_ref} if domain_ref else {}),
                },
            }
            entities.append(system_entity)

            # Check if containers exist for this system
            sys_containers = [
                c for c in graph.containers.values() if c.system_id == sys.id
            ]

            if sys_containers:
                for cnt in sys_containers:
                    cnt_entity = {
                        "apiVersion": "backstage.io/v1alpha1",
                        "kind": "Component",
                        "metadata": {
                            "name": cls._sanitize_name(cnt.id),
                            "title": cnt.name,
                            "description": cnt.description or f"Container component {cnt.name}",
                            "tags": ["container", cnt.technology.lower()] if cnt.technology else ["container"],
                            "annotations": {
                                "tecton.io/domain-id": cnt.id,
                            },
                        },
                        "spec": {
                            "type": "service",
                            "lifecycle": "production",
                            "owner": sys.metadata.get("owner", "architecture-team"),
                            "system": safe_sys_name,
                        },
                    }
                    entities.append(cnt_entity)
            else:
                # Direct component representation of the system
                comp_entity = {
                    "apiVersion": "backstage.io/v1alpha1",
                    "kind": "Component",
                    "metadata": {
                        "name": f"{safe_sys_name}-service",
                        "title": f"{sys.name} Service",
                        "description": sys.description or f"Core service for {sys.name}",
                        "tags": ["service", sys.time_classification.value.lower()],
                        "annotations": {
                            "tecton.io/domain-id": sys.id,
                        },
                    },
                    "spec": {
                        "type": "service",
                        "lifecycle": "production" if sys.current_phase != "phaseOut" else "deprecated",
                        "owner": sys.metadata.get("owner", "architecture-team"),
                        "system": safe_sys_name,
                        "providesApis": [
                            cls._sanitize_name(iface.id)
                            for iface in graph.interfaces.values()
                            if iface.provider_system_id == sys.id
                        ],
                        "consumesApis": [
                            cls._sanitize_name(iface.id)
                            for iface in graph.interfaces.values()
                            if sys.id in iface.consumer_system_ids
                        ],
                    },
                }
                entities.append(comp_entity)

        # 3. APIs (from Interface contracts)
        for iface in graph.interfaces.values():
            proto_type = "openapi"
            proto_upper = iface.protocol.upper()
            if "GRAPHQL" in proto_upper:
                proto_type = "graphql"
            elif "GRPC" in proto_upper:
                proto_type = "grpc"
            elif any(k in proto_upper for k in ("KAFKA", "AMQP", "EVENT", "MQ")):
                proto_type = "asyncapi"

            api_entity = {
                "apiVersion": "backstage.io/v1alpha1",
                "kind": "API",
                "metadata": {
                    "name": cls._sanitize_name(iface.id),
                    "title": iface.name,
                    "description": iface.description or f"Interface contract: {iface.name}",
                    "tags": ["interface", iface.protocol.lower()],
                    "annotations": {
                        "tecton.io/domain-id": iface.id,
                    },
                },
                "spec": {
                    "type": proto_type,
                    "lifecycle": "production",
                    "owner": cls._sanitize_name(iface.provider_system_id),
                    "system": cls._sanitize_name(iface.provider_system_id),
                    "definition": f"info:\n  title: {iface.name}\n  version: '1.0.0'\npaths: {{}}\n",
                },
            }
            entities.append(api_entity)

        # 4. Resources (from Technologies)
        for tech in graph.technologies.values():
            res_entity = {
                "apiVersion": "backstage.io/v1alpha1",
                "kind": "Resource",
                "metadata": {
                    "name": cls._sanitize_name(tech.id),
                    "title": tech.name,
                    "description": tech.description or f"Technology radar asset: {tech.name}",
                    "tags": ["technology", tech.status.value],
                    "annotations": {
                        "tecton.io/domain-id": tech.id,
                    },
                },
                "spec": {
                    "type": tech.category or "infrastructure",
                    "owner": "platform-engineering",
                },
            }
            entities.append(res_entity)

        return entities

    @classmethod
    def export_yaml(cls, graph: CompiledGraph) -> str:
        """Export all Backstage entities as a multi-document YAML string."""
        entities = cls.export_catalog(graph)
        return yaml.dump_all(entities, sort_keys=False, default_flow_style=False)

    @classmethod
    def import_catalog(cls, yaml_content: str) -> dict[str, list[dict[str, Any]]]:
        """Parse Backstage YAML catalog documents into Tecton C4 EAM manifest format."""
        try:
            docs = list(yaml.safe_load_all(yaml_content))
        except Exception as e:
            raise ValueError(f"Invalid Backstage catalog YAML: {e}") from e

        manifest: dict[str, list[dict[str, Any]]] = {
            "capabilities": [],
            "systems": [],
            "containers": [],
            "technologies": [],
            "interfaces": [],
            "relationships": [],
        }

        name_to_domain: dict[str, str] = {}
        for doc in docs:
            if isinstance(doc, dict):
                meta = doc.get("metadata", {})
                n = meta.get("name", "")
                raw = meta.get("annotations", {}).get("tecton.io/domain-id") or n
                if n:
                    name_to_domain[n] = raw

        for doc in docs:
            if not isinstance(doc, dict):
                continue
            kind = doc.get("kind", "").lower()
            metadata = doc.get("metadata", {})
            spec = doc.get("spec", {})
            name = metadata.get("name", "")
            domain_id = metadata.get("annotations", {}).get("tecton.io/domain-id") or name
            title = metadata.get("title", name)
            description = metadata.get("description", "")

            if not name:
                continue

            if kind == "domain":
                manifest["capabilities"].append({
                    "id": domain_id,
                    "name": title,
                    "level": "L1",
                    "description": description,
                })
            elif kind == "system":
                domain_ref = spec.get("domain")
                mapped_domain = name_to_domain.get(domain_ref, domain_ref) if domain_ref else None
                manifest["systems"].append({
                    "id": domain_id,
                    "name": title,
                    "description": description,
                    "tags": metadata.get("tags", []),
                    "capabilities": [mapped_domain] if mapped_domain else [],
                })
            elif kind == "component":
                comp_type = spec.get("type", "service")
                system_ref = spec.get("system")
                mapped_sys = name_to_domain.get(system_ref, system_ref) if system_ref else None
                if mapped_sys:
                    manifest["containers"].append({
                        "id": domain_id,
                        "name": title,
                        "system_id": mapped_sys,
                        "technology": comp_type,
                        "description": description,
                    })
                else:
                    manifest["systems"].append({
                        "id": domain_id,
                        "name": title,
                        "description": description,
                        "tags": metadata.get("tags", []),
                    })
            elif kind == "api":
                provider_ref = spec.get("system") or spec.get("owner") or "unknown"
                mapped_provider = name_to_domain.get(provider_ref, provider_ref)
                manifest["interfaces"].append({
                    "id": domain_id,
                    "name": title,
                    "protocol": spec.get("type", "REST").upper(),
                    "provider_system_id": mapped_provider,
                    "description": description,
                })
            elif kind == "resource":
                manifest["technologies"].append({
                    "id": domain_id,
                    "name": title,
                    "category": spec.get("type", "infrastructure"),
                    "description": description,
                })

        return manifest

    @staticmethod
    def _sanitize_name(raw_name: str) -> str:
        """Sanitize name to comply with Backstage Kubernetes-compliant entity name rules."""
        sanitized = raw_name.lower().replace("_", "-").replace(" ", "-")
        # Ensure only alphanumeric and hyphen
        cleaned = "".join(c for c in sanitized if c.isalnum() or c == "-")
        return cleaned.strip("-") or "entity"
