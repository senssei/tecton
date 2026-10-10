"""The Open Group ArchiMate Model Exchange File Format (XML) Connector.

Provides bi-directional interoperability between Tecton Architecture-as-Code
and standard Open Group ArchiMate 3.0/3.1 XML models.
"""

from typing import Any
import xml.etree.ElementTree as ET
from xml.dom import minidom

from tecton.dsl.parser import CompiledGraph


class ArchiMateConnector:
    """Connector for The Open Group ArchiMate Model Exchange File Format."""

    ARCHIMATE_NS = "http://www.opengroup.org/xsd/archimate/3.0/"
    ARCHI_NATIVE_NS = "http://www.archimatetool.com/archimate"
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

    @staticmethod
    def _to_xml_id(raw_id: str) -> str:
        """Ensure ID starts with 'id-' for strict XML NCName / ID compliance."""
        if not raw_id:
            return "id-unspecified"
        clean = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in raw_id)
        return clean if clean.startswith("id-") else f"id-{clean}"

    @classmethod
    def export_xml(cls, graph: CompiledGraph, model_name: str = "Tecton Architecture Model") -> str:
        """Export CompiledGraph into standard ArchiMate Open Exchange XML format."""
        ET.register_namespace("", cls.ARCHIMATE_NS)
        ET.register_namespace("xsi", cls.XSI_NS)

        root = ET.Element(
            f"{{{cls.ARCHIMATE_NS}}}model",
            attrib={
                "identifier": "id-tecton-eam-model",
                f"{{{cls.XSI_NS}}}schemaLocation": (
                    "http://www.opengroup.org/xsd/archimate/3.0/ "
                    "http://www.opengroup.org/xsd/archimate/3.0/archimate3_Model.xsd"
                ),
            },
        )

        name_elem = ET.SubElement(root, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
        name_elem.text = model_name

        elements_elem = ET.SubElement(root, f"{{{cls.ARCHIMATE_NS}}}elements")
        relationships_elem = ET.SubElement(root, f"{{{cls.ARCHIMATE_NS}}}relationships")

        # 1. Business Capabilities
        for cap in graph.capabilities.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": cls._to_xml_id(cap.id),
                    f"{{{cls.XSI_NS}}}type": "Capability",
                },
            )
            c_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
            c_name.text = cap.name
            if cap.description:
                c_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                c_doc.text = cap.description

            # Capability hierarchy as Composition relationship
            if cap.parent_id and cap.parent_id in graph.capabilities:
                rel = ET.SubElement(
                    relationships_elem,
                    f"{{{cls.ARCHIMATE_NS}}}relationship",
                    attrib={
                        "identifier": cls._to_xml_id(f"rel-comp-{cap.parent_id}-{cap.id}"),
                        "source": cls._to_xml_id(cap.parent_id),
                        "target": cls._to_xml_id(cap.id),
                        f"{{{cls.XSI_NS}}}type": "Composition",
                    },
                )
                r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                r_name.text = "Composes"

        # 2. Software Systems (Application Components)
        for sys in graph.systems.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": cls._to_xml_id(sys.id),
                    f"{{{cls.XSI_NS}}}type": "ApplicationComponent",
                },
            )
            s_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
            s_name.text = sys.name
            if sys.description:
                s_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                s_doc.text = sys.description

            # Realization of capabilities
            for cap_id in sys.capabilities:
                if cap_id in graph.capabilities:
                    rel = ET.SubElement(
                        relationships_elem,
                        f"{{{cls.ARCHIMATE_NS}}}relationship",
                        attrib={
                            "identifier": cls._to_xml_id(f"rel-realize-{sys.id}-{cap_id}"),
                            "source": cls._to_xml_id(sys.id),
                            "target": cls._to_xml_id(cap_id),
                            f"{{{cls.XSI_NS}}}type": "Realization",
                        },
                    )
                    r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                    r_name.text = "Realizes"

        # 3. Interfaces (Application Interfaces)
        for iface in graph.interfaces.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": cls._to_xml_id(iface.id),
                    f"{{{cls.XSI_NS}}}type": "ApplicationInterface",
                },
            )
            i_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
            i_name.text = iface.name
            if iface.description:
                i_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                i_doc.text = iface.description

            # Assignment: Provider System -> Interface
            if iface.provider_system_id in graph.systems:
                rel = ET.SubElement(
                    relationships_elem,
                    f"{{{cls.ARCHIMATE_NS}}}relationship",
                    attrib={
                        "identifier": cls._to_xml_id(f"rel-assign-{iface.provider_system_id}-{iface.id}"),
                        "source": cls._to_xml_id(iface.provider_system_id),
                        "target": cls._to_xml_id(iface.id),
                        f"{{{cls.XSI_NS}}}type": "Assignment",
                    },
                )
                r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                r_name.text = "Exposes Interface"

        # 4. Data Objects
        for do in graph.data_objects.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": cls._to_xml_id(do.id),
                    f"{{{cls.XSI_NS}}}type": "DataObject",
                },
            )
            d_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
            d_name.text = do.name
            if do.description:
                d_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                d_doc.text = do.description

        # 5. Technologies (Nodes)
        for tech in graph.technologies.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": cls._to_xml_id(tech.id),
                    f"{{{cls.XSI_NS}}}type": "Node",
                },
            )
            t_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
            t_name.text = tech.name
            if tech.description:
                t_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                t_doc.text = tech.description

        # 6. Plateaus
        for plateau in graph.plateaus.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": cls._to_xml_id(plateau.id),
                    f"{{{cls.XSI_NS}}}type": "Plateau",
                },
            )
            p_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
            p_name.text = plateau.name
            if plateau.description:
                p_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                p_doc.text = plateau.description

            if plateau.previous_plateau_id and plateau.previous_plateau_id in graph.plateaus:
                rel = ET.SubElement(
                    relationships_elem,
                    f"{{{cls.ARCHIMATE_NS}}}relationship",
                    attrib={
                        "identifier": cls._to_xml_id(f"rel-trig-{plateau.previous_plateau_id}-{plateau.id}"),
                        "source": cls._to_xml_id(plateau.previous_plateau_id),
                        "target": cls._to_xml_id(plateau.id),
                        f"{{{cls.XSI_NS}}}type": "Triggering",
                    },
                )
                r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                r_name.text = "Precedes"

        # 7. Work Packages
        for wp in graph.work_packages.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": cls._to_xml_id(wp.id),
                    f"{{{cls.XSI_NS}}}type": "WorkPackage",
                },
            )
            w_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
            w_name.text = wp.name
            if wp.description:
                w_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
                w_doc.text = wp.description

        # 8. C4 System Relationships (Flow)
        for idx, rel_def in enumerate(graph.relationships):
            rel = ET.SubElement(
                relationships_elem,
                f"{{{cls.ARCHIMATE_NS}}}relationship",
                attrib={
                    "identifier": cls._to_xml_id(f"rel-flow-{idx}-{rel_def.source_id}-{rel_def.target_id}"),
                    "source": cls._to_xml_id(rel_def.source_id),
                    "target": cls._to_xml_id(rel_def.target_id),
                    f"{{{cls.XSI_NS}}}type": "Flow",
                },
            )
            r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
            r_name.text = rel_def.description or "Interacts with"

        # 9. Default Architecture Views (Diagrams)
        views_specs = cls._generate_default_views(graph)
        views_elem = ET.SubElement(root, f"{{{cls.ARCHIMATE_NS}}}views")
        diagrams_elem = ET.SubElement(views_elem, f"{{{cls.ARCHIMATE_NS}}}diagrams")
        for v in views_specs:
            v_elem = ET.SubElement(
                diagrams_elem,
                f"{{{cls.ARCHIMATE_NS}}}view",
                attrib={"identifier": cls._to_xml_id(v["id"])},
            )
            v_name = ET.SubElement(v_elem, f"{{{cls.ARCHIMATE_NS}}}name", attrib={"{http://www.w3.org/XML/1998/namespace}lang": "en"})
            v_name.text = v["name"]

            for node in v["nodes"]:
                ET.SubElement(
                    v_elem,
                    f"{{{cls.ARCHIMATE_NS}}}node",
                    attrib={
                        "identifier": node["diag_id"],
                        "elementRef": node["elem_id"],
                        "x": str(node["x"]),
                        "y": str(node["y"]),
                        "w": str(node["w"]),
                        "h": str(node["h"]),
                        f"{{{cls.XSI_NS}}}type": "Element",
                    },
                )

            for conn in v["connections"]:
                ET.SubElement(
                    v_elem,
                    f"{{{cls.ARCHIMATE_NS}}}connection",
                    attrib={
                        "identifier": conn["id"],
                        "relationshipRef": conn["rel_id"],
                        "source": conn["source_diag_id"],
                        "target": conn["target_diag_id"],
                        f"{{{cls.XSI_NS}}}type": "Relationship",
                    },
                )

        # Pretty print XML
        raw_xml = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(raw_xml)
        return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    @classmethod
    def export_archi_xml(cls, graph: CompiledGraph, model_name: str = "Tecton Architecture Model") -> str:
        """Export CompiledGraph into Archi's native XML (.archimate) format.

        This format can be directly opened in Archi via 'File > Open...' or double-click,
        without requiring 'File > Import > Model from Open Exchange File...'.
        """
        ET.register_namespace("archimate", cls.ARCHI_NATIVE_NS)
        ET.register_namespace("xsi", cls.XSI_NS)

        root = ET.Element(
            f"{{{cls.ARCHI_NATIVE_NS}}}model",
            attrib={
                "name": model_name,
                "id": cls._to_xml_id("model-tecton-archimate"),
                "version": "5.0.0",
            },
        )

        # 9 Standard Archi Folder Containers
        f_strategy = ET.SubElement(root, "folder", attrib={"name": "Strategy", "id": "id-folder-strategy", "type": "strategy"})
        f_business = ET.SubElement(root, "folder", attrib={"name": "Business", "id": "id-folder-business", "type": "business"})
        f_application = ET.SubElement(root, "folder", attrib={"name": "Application", "id": "id-folder-application", "type": "application"})
        f_technology = ET.SubElement(root, "folder", attrib={"name": "Technology & Physical", "id": "id-folder-technology", "type": "technology"})
        f_motivation = ET.SubElement(root, "folder", attrib={"name": "Motivation", "id": "id-folder-motivation", "type": "motivation"})
        f_implementation = ET.SubElement(root, "folder", attrib={"name": "Implementation & Migration", "id": "id-folder-implementation", "type": "implementation_migration"})
        f_other = ET.SubElement(root, "folder", attrib={"name": "Other", "id": "id-folder-other", "type": "other"})
        f_relations = ET.SubElement(root, "folder", attrib={"name": "Relations", "id": "id-folder-relations", "type": "relations"})
        f_views = ET.SubElement(root, "folder", attrib={"name": "Views", "id": "id-folder-views", "type": "diagrams"})

        # 1. Strategy Folder -> Capabilities
        for cap in graph.capabilities.values():
            elem = ET.SubElement(
                f_strategy,
                "element",
                attrib={
                    f"{{{cls.XSI_NS}}}type": "archimate:Capability",
                    "id": cls._to_xml_id(cap.id),
                    "name": cap.name,
                },
            )
            if cap.description:
                doc = ET.SubElement(elem, "documentation")
                doc.text = cap.description

        # 2. Application Folder -> Systems, Interfaces, Data Objects
        for sys in graph.systems.values():
            elem = ET.SubElement(
                f_application,
                "element",
                attrib={
                    f"{{{cls.XSI_NS}}}type": "archimate:ApplicationComponent",
                    "id": cls._to_xml_id(sys.id),
                    "name": sys.name,
                },
            )
            if sys.description:
                doc = ET.SubElement(elem, "documentation")
                doc.text = sys.description

        for iface in graph.interfaces.values():
            elem = ET.SubElement(
                f_application,
                "element",
                attrib={
                    f"{{{cls.XSI_NS}}}type": "archimate:ApplicationInterface",
                    "id": cls._to_xml_id(iface.id),
                    "name": iface.name,
                },
            )
            if iface.description:
                doc = ET.SubElement(elem, "documentation")
                doc.text = iface.description

        for do in graph.data_objects.values():
            elem = ET.SubElement(
                f_application,
                "element",
                attrib={
                    f"{{{cls.XSI_NS}}}type": "archimate:DataObject",
                    "id": cls._to_xml_id(do.id),
                    "name": do.name,
                },
            )
            if do.description:
                doc = ET.SubElement(elem, "documentation")
                doc.text = do.description

        # 3. Technology Folder -> Nodes
        for tech in graph.technologies.values():
            elem = ET.SubElement(
                f_technology,
                "element",
                attrib={
                    f"{{{cls.XSI_NS}}}type": "archimate:Node",
                    "id": cls._to_xml_id(tech.id),
                    "name": tech.name,
                },
            )
            if tech.description:
                doc = ET.SubElement(elem, "documentation")
                doc.text = tech.description

        # 4. Implementation Folder -> Plateaus & Work Packages
        for plateau in graph.plateaus.values():
            elem = ET.SubElement(
                f_implementation,
                "element",
                attrib={
                    f"{{{cls.XSI_NS}}}type": "archimate:Plateau",
                    "id": cls._to_xml_id(plateau.id),
                    "name": plateau.name,
                },
            )
            if plateau.description:
                doc = ET.SubElement(elem, "documentation")
                doc.text = plateau.description

        for wp in graph.work_packages.values():
            elem = ET.SubElement(
                f_implementation,
                "element",
                attrib={
                    f"{{{cls.XSI_NS}}}type": "archimate:WorkPackage",
                    "id": cls._to_xml_id(wp.id),
                    "name": wp.name,
                },
            )
            if wp.description:
                doc = ET.SubElement(elem, "documentation")
                doc.text = wp.description

        # 5. Relations Folder -> Composition, Realization, Assignment, Flow, Triggering
        for cap in graph.capabilities.values():
            if cap.parent_id and cap.parent_id in graph.capabilities:
                ET.SubElement(
                    f_relations,
                    "element",
                    attrib={
                        f"{{{cls.XSI_NS}}}type": "archimate:CompositionRelationship",
                        "id": cls._to_xml_id(f"rel-comp-{cap.parent_id}-{cap.id}"),
                        "source": cls._to_xml_id(cap.parent_id),
                        "target": cls._to_xml_id(cap.id),
                        "name": "Composes",
                    },
                )

        for sys in graph.systems.values():
            for cap_id in sys.capabilities:
                if cap_id in graph.capabilities:
                    ET.SubElement(
                        f_relations,
                        "element",
                        attrib={
                            f"{{{cls.XSI_NS}}}type": "archimate:RealizationRelationship",
                            "id": cls._to_xml_id(f"rel-realize-{sys.id}-{cap_id}"),
                            "source": cls._to_xml_id(sys.id),
                            "target": cls._to_xml_id(cap_id),
                            "name": "Realizes",
                        },
                    )

        for iface in graph.interfaces.values():
            if iface.provider_system_id in graph.systems:
                ET.SubElement(
                    f_relations,
                    "element",
                    attrib={
                        f"{{{cls.XSI_NS}}}type": "archimate:AssignmentRelationship",
                        "id": cls._to_xml_id(f"rel-assign-{iface.provider_system_id}-{iface.id}"),
                        "source": cls._to_xml_id(iface.provider_system_id),
                        "target": cls._to_xml_id(iface.id),
                        "name": "Exposes Interface",
                    },
                )

        for idx, rel_def in enumerate(graph.relationships):
            ET.SubElement(
                f_relations,
                "element",
                attrib={
                    f"{{{cls.XSI_NS}}}type": "archimate:FlowRelationship",
                    "id": cls._to_xml_id(f"rel-flow-{idx}-{rel_def.source_id}-{rel_def.target_id}"),
                    "source": cls._to_xml_id(rel_def.source_id),
                    "target": cls._to_xml_id(rel_def.target_id),
                    "name": rel_def.description or "Interacts with",
                },
            )

        for plateau in graph.plateaus.values():
            if plateau.previous_plateau_id and plateau.previous_plateau_id in graph.plateaus:
                ET.SubElement(
                    f_relations,
                    "element",
                    attrib={
                        f"{{{cls.XSI_NS}}}type": "archimate:TriggeringRelationship",
                        "id": cls._to_xml_id(f"rel-trig-{plateau.previous_plateau_id}-{plateau.id}"),
                        "source": cls._to_xml_id(plateau.previous_plateau_id),
                        "target": cls._to_xml_id(plateau.id),
                        "name": "Precedes",
                    },
                )

        # 6. Default Architecture Views (Diagrams)
        views_specs = cls._generate_default_views(graph)
        for v in views_specs:
            v_elem = ET.SubElement(
                f_views,
                "element",
                attrib={
                    f"{{{cls.XSI_NS}}}type": "archimate:ArchimateDiagramModel",
                    "id": cls._to_xml_id(v["id"]),
                    "name": v["name"],
                },
            )

            # Map targetConnections per node
            node_target_conns: dict[str, list[str]] = {n["diag_id"]: [] for n in v["nodes"]}
            node_source_conns: dict[str, list[dict[str, Any]]] = {n["diag_id"]: [] for n in v["nodes"]}
            for conn in v["connections"]:
                if conn["target_diag_id"] in node_target_conns:
                    node_target_conns[conn["target_diag_id"]].append(conn["id"])
                if conn["source_diag_id"] in node_source_conns:
                    node_source_conns[conn["source_diag_id"]].append(conn)

            for node in v["nodes"]:
                diag_id = node["diag_id"]
                child_attrib = {
                    f"{{{cls.XSI_NS}}}type": "archimate:DiagramObject",
                    "id": diag_id,
                    "archimateElement": node["elem_id"],
                }
                if node_target_conns[diag_id]:
                    child_attrib["targetConnections"] = " ".join(node_target_conns[diag_id])

                child = ET.SubElement(v_elem, "child", attrib=child_attrib)
                ET.SubElement(
                    child,
                    "bounds",
                    attrib={
                        "x": str(node["x"]),
                        "y": str(node["y"]),
                        "width": str(node["w"]),
                        "height": str(node["h"]),
                    },
                )

                for conn in node_source_conns[diag_id]:
                    ET.SubElement(
                        child,
                        "sourceConnection",
                        attrib={
                            f"{{{cls.XSI_NS}}}type": "archimate:Connection",
                            "id": conn["id"],
                            "source": conn["source_diag_id"],
                            "target": conn["target_diag_id"],
                            "relationship": conn["rel_id"],
                        },
                    )

        raw_xml = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(raw_xml)
        return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    @classmethod
    def _generate_default_views(cls, graph: CompiledGraph) -> list[dict[str, Any]]:
        """Synthesize pre-laid-out enterprise views for visual diagrams."""
        views: list[dict[str, Any]] = []

        # 1. C4 System Landscape View
        c4_nodes: list[dict[str, Any]] = []
        c4_conns: list[dict[str, Any]] = []
        sys_diag_map: dict[str, str] = {}

        for idx, sys in enumerate(graph.systems.values()):
            diag_id = cls._to_xml_id(f"diag-c4-{sys.id}")
            sys_diag_map[sys.id] = diag_id
            col = idx % 3
            row = idx // 3
            x = 60 + col * 280
            y = 60 + row * 220
            c4_nodes.append({
                "diag_id": diag_id,
                "elem_id": cls._to_xml_id(sys.id),
                "x": x,
                "y": y,
                "w": 220,
                "h": 85,
            })

        for iface in graph.interfaces.values():
            if iface.provider_system_id in sys_diag_map:
                prov_idx = list(graph.systems.keys()).index(iface.provider_system_id)
                col = prov_idx % 3
                row = prov_idx // 3
                diag_id = cls._to_xml_id(f"diag-c4-iface-{iface.id}")
                c4_nodes.append({
                    "diag_id": diag_id,
                    "elem_id": cls._to_xml_id(iface.id),
                    "x": 60 + col * 280 + 20,
                    "y": 60 + row * 220 + 110,
                    "w": 180,
                    "h": 50,
                })
                c4_conns.append({
                    "id": cls._to_xml_id(f"dc-assign-{iface.provider_system_id}-{iface.id}"),
                    "rel_id": cls._to_xml_id(f"rel-assign-{iface.provider_system_id}-{iface.id}"),
                    "source_diag_id": sys_diag_map[iface.provider_system_id],
                    "target_diag_id": diag_id,
                })

        for idx, rel_def in enumerate(graph.relationships):
            if rel_def.source_id in sys_diag_map and rel_def.target_id in sys_diag_map:
                c4_conns.append({
                    "id": cls._to_xml_id(f"dc-flow-{idx}"),
                    "rel_id": cls._to_xml_id(f"rel-flow-{idx}-{rel_def.source_id}-{rel_def.target_id}"),
                    "source_diag_id": sys_diag_map[rel_def.source_id],
                    "target_diag_id": sys_diag_map[rel_def.target_id],
                })

        views.append({
            "id": "view-c4-landscape",
            "name": "C4 System Landscape",
            "nodes": c4_nodes,
            "connections": c4_conns,
        })

        # 2. Business Capability Map (BCM) View
        bcm_nodes: list[dict[str, Any]] = []
        bcm_conns: list[dict[str, Any]] = []
        cap_diag_map: dict[str, str] = {}

        roots = [c for c in graph.capabilities.values() if not c.parent_id or c.parent_id not in graph.capabilities]
        children = [c for c in graph.capabilities.values() if c.parent_id and c.parent_id in graph.capabilities]

        col_x = 60
        for root_cap in roots:
            r_diag_id = cls._to_xml_id(f"diag-bcm-{root_cap.id}")
            cap_diag_map[root_cap.id] = r_diag_id
            bcm_nodes.append({
                "diag_id": r_diag_id,
                "elem_id": cls._to_xml_id(root_cap.id),
                "x": col_x,
                "y": 60,
                "w": 260,
                "h": 70,
            })

            subs = [c for c in children if c.parent_id == root_cap.id]
            for s_idx, sub_cap in enumerate(subs):
                s_diag_id = cls._to_xml_id(f"diag-bcm-{sub_cap.id}")
                cap_diag_map[sub_cap.id] = s_diag_id
                bcm_nodes.append({
                    "diag_id": s_diag_id,
                    "elem_id": cls._to_xml_id(sub_cap.id),
                    "x": col_x + 15,
                    "y": 150 + s_idx * 75,
                    "w": 230,
                    "h": 60,
                })
                bcm_conns.append({
                    "id": cls._to_xml_id(f"dc-comp-{root_cap.id}-{sub_cap.id}"),
                    "rel_id": cls._to_xml_id(f"rel-comp-{root_cap.id}-{sub_cap.id}"),
                    "source_diag_id": r_diag_id,
                    "target_diag_id": s_diag_id,
                })
            col_x += 300

        views.append({
            "id": "view-bcm-heatmap",
            "name": "Business Capability Map",
            "nodes": bcm_nodes,
            "connections": bcm_conns,
        })

        # 3. Layered Enterprise Architecture View
        layered_nodes: list[dict[str, Any]] = []
        layered_conns: list[dict[str, Any]] = []
        l_cap_map: dict[str, str] = {}

        # Layer 1: Strategy (Capabilities)
        for idx, cap in enumerate(graph.capabilities.values()):
            diag_id = cls._to_xml_id(f"diag-lay-cap-{cap.id}")
            l_cap_map[cap.id] = diag_id
            layered_nodes.append({
                "diag_id": diag_id,
                "elem_id": cls._to_xml_id(cap.id),
                "x": 60 + idx * 240,
                "y": 60,
                "w": 210,
                "h": 65,
            })

        # Layer 2: Application (Systems)
        for idx, sys in enumerate(graph.systems.values()):
            diag_id = cls._to_xml_id(f"diag-lay-sys-{sys.id}")
            layered_nodes.append({
                "diag_id": diag_id,
                "elem_id": cls._to_xml_id(sys.id),
                "x": 60 + idx * 260,
                "y": 230,
                "w": 230,
                "h": 80,
            })
            for cap_id in sys.capabilities:
                if cap_id in l_cap_map:
                    layered_conns.append({
                        "id": cls._to_xml_id(f"dc-lay-realize-{sys.id}-{cap_id}"),
                        "rel_id": cls._to_xml_id(f"rel-realize-{sys.id}-{cap_id}"),
                        "source_diag_id": diag_id,
                        "target_diag_id": l_cap_map[cap_id],
                    })

        # Layer 3: Technology (Nodes)
        for idx, tech in enumerate(graph.technologies.values()):
            diag_id = cls._to_xml_id(f"diag-lay-tech-{tech.id}")
            layered_nodes.append({
                "diag_id": diag_id,
                "elem_id": cls._to_xml_id(tech.id),
                "x": 60 + idx * 240,
                "y": 420,
                "w": 210,
                "h": 65,
            })

        views.append({
            "id": "view-layered-architecture",
            "name": "Layered Enterprise Architecture",
            "nodes": layered_nodes,
            "connections": layered_conns,
        })

        # 4. Transformation Roadmap View (if plateaus exist)
        if graph.plateaus:
            road_nodes: list[dict[str, Any]] = []
            road_conns: list[dict[str, Any]] = []
            p_diag_map: dict[str, str] = {}

            for idx, plateau in enumerate(graph.plateaus.values()):
                diag_id = cls._to_xml_id(f"diag-road-plat-{plateau.id}")
                p_diag_map[plateau.id] = diag_id
                road_nodes.append({
                    "diag_id": diag_id,
                    "elem_id": cls._to_xml_id(plateau.id),
                    "x": 60 + idx * 280,
                    "y": 80,
                    "w": 240,
                    "h": 80,
                })
                if plateau.previous_plateau_id and plateau.previous_plateau_id in p_diag_map:
                    road_conns.append({
                        "id": cls._to_xml_id(f"dc-trig-{plateau.previous_plateau_id}-{plateau.id}"),
                        "rel_id": cls._to_xml_id(f"rel-trig-{plateau.previous_plateau_id}-{plateau.id}"),
                        "source_diag_id": p_diag_map[plateau.previous_plateau_id],
                        "target_diag_id": diag_id,
                    })

            for idx, wp in enumerate(graph.work_packages.values()):
                road_nodes.append({
                    "diag_id": cls._to_xml_id(f"diag-road-wp-{wp.id}"),
                    "elem_id": cls._to_xml_id(wp.id),
                    "x": 60 + idx * 260,
                    "y": 240,
                    "w": 230,
                    "h": 75,
                })

            views.append({
                "id": "view-transformation-roadmap",
                "name": "Transformation Roadmap",
                "nodes": road_nodes,
                "connections": road_conns,
            })

        return views

    @classmethod
    def import_xml(cls, xml_content: str) -> dict[str, list[dict[str, Any]]]:
        """Parse ArchiMate XML (either Open Group Exchange XML or Archi Native XML)."""
        try:
            root = ET.fromstring(xml_content)
        except Exception as e:
            raise ValueError(f"Invalid ArchiMate XML: {e}") from e

        def strip_ns(val: str) -> str:
            if "}" in val:
                val = val.split("}")[-1]
            if ":" in val:
                val = val.split(":")[-1]
            return val

        manifest: dict[str, list[dict[str, Any]]] = {
            "capabilities": [],
            "systems": [],
            "technologies": [],
            "interfaces": [],
            "data_objects": [],
            "plateaus": [],
            "work_packages": [],
            "relationships": [],
        }

        systems_dict: dict[str, dict[str, Any]] = {}
        capabilities_dict: dict[str, dict[str, Any]] = {}

        # Scan elements
        for elem in root.iter():
            tag_name = strip_ns(elem.tag)
            if tag_name == "element":
                elem_id = elem.attrib.get("identifier") or elem.attrib.get("id") or ""
                xsi_type = ""
                for k, v in elem.attrib.items():
                    if strip_ns(k) == "type":
                        xsi_type = strip_ns(v)

                name_node = None
                doc_node = None
                for child in elem:
                    c_tag = strip_ns(child.tag)
                    if c_tag == "name":
                        name_node = child.text
                    elif c_tag == "documentation":
                        doc_node = child.text

                name = elem.attrib.get("name") or name_node or elem_id
                desc = doc_node or ""

                # Skip if this element is a relationship (Archi native stores relationships as element)
                if xsi_type.endswith("Relationship") or ("source" in elem.attrib and "target" in elem.attrib):
                    continue

                if xsi_type == "ApplicationComponent":
                    sys_obj = {
                        "id": elem_id,
                        "name": name,
                        "description": desc,
                        "capabilities": [],
                    }
                    systems_dict[elem_id] = sys_obj
                elif xsi_type == "Capability":
                    cap_obj = {
                        "id": elem_id,
                        "name": name,
                        "description": desc,
                    }
                    capabilities_dict[elem_id] = cap_obj
                elif xsi_type == "ApplicationInterface":
                    manifest["interfaces"].append({
                        "id": elem_id,
                        "name": name,
                        "provider_system_id": "unknown",
                        "description": desc,
                    })
                elif xsi_type == "DataObject":
                    manifest["data_objects"].append({
                        "id": elem_id,
                        "name": name,
                        "description": desc,
                        "classification": "INTERNAL",
                    })
                elif xsi_type in ("Node", "TechnologyService", "Device"):
                    manifest["technologies"].append({
                        "id": elem_id,
                        "name": name,
                        "description": desc,
                    })
                elif xsi_type == "Plateau":
                    manifest["plateaus"].append({
                        "id": elem_id,
                        "name": name,
                        "description": desc,
                    })
                elif xsi_type == "WorkPackage":
                    manifest["work_packages"].append({
                        "id": elem_id,
                        "name": name,
                        "description": desc,
                    })

        # Scan relationships (can be <relationship> or <element xsi:type="archimate:...Relationship">)
        for rel in root.iter():
            tag_name = strip_ns(rel.tag)
            src = rel.attrib.get("source", "")
            dst = rel.attrib.get("target", "")

            if not (src and dst):
                continue

            xsi_type = ""
            for k, v in rel.attrib.items():
                if strip_ns(k) == "type":
                    xsi_type = strip_ns(v)

            # Normalize Archi relationship type name: RealizationRelationship -> Realization
            if xsi_type.endswith("Relationship"):
                xsi_type = xsi_type[:-12]

            rel_desc = rel.attrib.get("name", "")
            for child in rel:
                if strip_ns(child.tag) == "name" and child.text:
                    rel_desc = child.text

            if xsi_type == "Realization" and src in systems_dict:
                systems_dict[src]["capabilities"].append(dst)
            elif xsi_type == "Composition" and src in capabilities_dict and dst in capabilities_dict:
                capabilities_dict[dst]["parent_id"] = src
            elif xsi_type in ("Flow", "Serving") and src in systems_dict and dst in systems_dict:
                manifest["relationships"].append({
                    "source_id": src,
                    "target_id": dst,
                    "description": rel_desc or "Interacts with",
                })

        manifest["systems"] = list(systems_dict.values())
        manifest["capabilities"] = list(capabilities_dict.values())

        return manifest
