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
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

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

        name_elem = ET.SubElement(root, f"{{{cls.ARCHIMATE_NS}}}name")
        name_elem.text = model_name

        elements_elem = ET.SubElement(root, f"{{{cls.ARCHIMATE_NS}}}elements")
        relationships_elem = ET.SubElement(root, f"{{{cls.ARCHIMATE_NS}}}relationships")

        # 1. Business Capabilities
        for cap in graph.capabilities.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": cap.id,
                    f"{{{cls.XSI_NS}}}type": "Capability",
                },
            )
            c_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name")
            c_name.text = cap.name
            if cap.description:
                c_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation")
                c_doc.text = cap.description

            # Capability hierarchy as Composition relationship
            if cap.parent_id and cap.parent_id in graph.capabilities:
                rel = ET.SubElement(
                    relationships_elem,
                    f"{{{cls.ARCHIMATE_NS}}}relationship",
                    attrib={
                        "identifier": f"rel-comp-{cap.parent_id}-{cap.id}",
                        "source": cap.parent_id,
                        "target": cap.id,
                        f"{{{cls.XSI_NS}}}type": "Composition",
                    },
                )
                r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name")
                r_name.text = "Composes"

        # 2. Software Systems (Application Components)
        for sys in graph.systems.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": sys.id,
                    f"{{{cls.XSI_NS}}}type": "ApplicationComponent",
                },
            )
            s_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name")
            s_name.text = sys.name
            if sys.description:
                s_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation")
                s_doc.text = sys.description

            # Realization of capabilities
            for cap_id in sys.capabilities:
                if cap_id in graph.capabilities:
                    rel = ET.SubElement(
                        relationships_elem,
                        f"{{{cls.ARCHIMATE_NS}}}relationship",
                        attrib={
                            "identifier": f"rel-realize-{sys.id}-{cap_id}",
                            "source": sys.id,
                            "target": cap_id,
                            f"{{{cls.XSI_NS}}}type": "Realization",
                        },
                    )
                    r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name")
                    r_name.text = "Realizes"

        # 3. Interfaces (Application Interfaces)
        for iface in graph.interfaces.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": iface.id,
                    f"{{{cls.XSI_NS}}}type": "ApplicationInterface",
                },
            )
            i_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name")
            i_name.text = iface.name
            if iface.description:
                i_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation")
                i_doc.text = iface.description

            # Assignment: Provider System -> Interface
            if iface.provider_system_id in graph.systems:
                rel = ET.SubElement(
                    relationships_elem,
                    f"{{{cls.ARCHIMATE_NS}}}relationship",
                    attrib={
                        "identifier": f"rel-assign-{iface.provider_system_id}-{iface.id}",
                        "source": iface.provider_system_id,
                        "target": iface.id,
                        f"{{{cls.XSI_NS}}}type": "Assignment",
                    },
                )
                r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name")
                r_name.text = "Exposes Interface"

        # 4. Data Objects
        for do in graph.data_objects.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": do.id,
                    f"{{{cls.XSI_NS}}}type": "DataObject",
                },
            )
            d_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name")
            d_name.text = do.name
            if do.description:
                d_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation")
                d_doc.text = do.description

        # 5. Technologies (Nodes)
        for tech in graph.technologies.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": tech.id,
                    f"{{{cls.XSI_NS}}}type": "Node",
                },
            )
            t_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name")
            t_name.text = tech.name
            if tech.description:
                t_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation")
                t_doc.text = tech.description

        # 6. Plateaus
        for plateau in graph.plateaus.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": plateau.id,
                    f"{{{cls.XSI_NS}}}type": "Plateau",
                },
            )
            p_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name")
            p_name.text = plateau.name
            if plateau.description:
                p_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation")
                p_doc.text = plateau.description

            if plateau.previous_plateau_id and plateau.previous_plateau_id in graph.plateaus:
                rel = ET.SubElement(
                    relationships_elem,
                    f"{{{cls.ARCHIMATE_NS}}}relationship",
                    attrib={
                        "identifier": f"rel-trig-{plateau.previous_plateau_id}-{plateau.id}",
                        "source": plateau.previous_plateau_id,
                        "target": plateau.id,
                        f"{{{cls.XSI_NS}}}type": "Triggering",
                    },
                )
                r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name")
                r_name.text = "Precedes"

        # 7. Work Packages
        for wp in graph.work_packages.values():
            elem = ET.SubElement(
                elements_elem,
                f"{{{cls.ARCHIMATE_NS}}}element",
                attrib={
                    "identifier": wp.id,
                    f"{{{cls.XSI_NS}}}type": "WorkPackage",
                },
            )
            w_name = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}name")
            w_name.text = wp.name
            if wp.description:
                w_doc = ET.SubElement(elem, f"{{{cls.ARCHIMATE_NS}}}documentation")
                w_doc.text = wp.description

        # 8. C4 System Relationships (Flow)
        for idx, rel_def in enumerate(graph.relationships):
            rel = ET.SubElement(
                relationships_elem,
                f"{{{cls.ARCHIMATE_NS}}}relationship",
                attrib={
                    "identifier": f"rel-flow-{idx}-{rel_def.source_id}-{rel_def.target_id}",
                    "source": rel_def.source_id,
                    "target": rel_def.target_id,
                    f"{{{cls.XSI_NS}}}type": "Flow",
                },
            )
            r_name = ET.SubElement(rel, f"{{{cls.ARCHIMATE_NS}}}name")
            r_name.text = rel_def.description or "Interacts with"

        # Pretty print XML
        raw_xml = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(raw_xml)
        return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    @classmethod
    def import_xml(cls, xml_content: str) -> dict[str, list[dict[str, Any]]]:
        """Parse ArchiMate Model Exchange XML into Tecton C4 EAM manifest format."""
        try:
            root = ET.fromstring(xml_content)
        except Exception as e:
            raise ValueError(f"Invalid ArchiMate XML: {e}") from e

        def strip_ns(tag: str) -> str:
            return tag.split("}")[-1] if "}" in tag else tag

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
            if strip_ns(elem.tag) == "element":
                elem_id = elem.attrib.get("identifier", "")
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

                name = name_node or elem_id
                desc = doc_node or ""

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

        # Scan relationships
        for rel in root.iter():
            if strip_ns(rel.tag) == "relationship":
                src = rel.attrib.get("source", "")
                dst = rel.attrib.get("target", "")
                xsi_type = ""
                for k, v in rel.attrib.items():
                    if strip_ns(k) == "type":
                        xsi_type = strip_ns(v)

                rel_desc = ""
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
