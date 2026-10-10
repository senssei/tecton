"""Static and Dynamic Architecture Portal Generator."""

import json
from pathlib import Path
from typing import Any

from tecton.connectors.archimate import ArchiMateConnector
from tecton.connectors.backstage import BackstageConnector
from tecton.dsl.linter import GraphLinter
from tecton.dsl.parser import CompiledGraph
from tecton.exporters.mermaid import MermaidExporter
from tecton.portal.template import PORTAL_HTML_TEMPLATE
from tecton.services.bcm_service import BCMService
from tecton.services.lineage_service import LineageService
from tecton.services.roadmap_service import RoadmapService
from tecton.services.trm_service import TRMService


class PortalBuilder:
    """Builder for Living Architecture Intelligence Web Portal & Dashboard."""

    @classmethod
    def build_dynamic_portal_html(cls) -> str:
        """Generate dynamic HTML connected to Tecton live REST API endpoints."""
        return PORTAL_HTML_TEMPLATE.replace("__DATA_PAYLOAD__", "null")

    @classmethod
    def build_static_portal_html(cls, graph: CompiledGraph) -> str:
        """Generate 100% offline self-contained HTML bundle with pre-baked JSON graph payload."""
        linter_report = GraphLinter().lint(graph)
        bcm_report = BCMService(graph).analyze()
        trm_report = TRMService(graph).evaluate_technologies()
        roadmap_service = RoadmapService(graph)
        lineage_service = LineageService(graph)

        apps = graph.get_applications()

        # Pre-render Mermaid diagrams
        diagrams: dict[str, str] = {
            "time-matrix": MermaidExporter.to_time_quadrant_chart(apps),
            "bcm-heatmap": BCMService(graph).export_heatmap(),
            "tech-radar": TRMService(graph).export_radar(),
            "roadmap-gantt": roadmap_service.export_gantt(),
        }

        # Pre-render lineage diagrams
        for do in graph.data_objects.values():
            try:
                diagrams[f"lineage-{do.id}"] = lineage_service.export_lineage_flowchart(do.id)
            except Exception:
                pass

        # Pre-calculate blast radius for all technologies
        blast_reports: dict[str, Any] = {}
        trm_svc = TRMService(graph)
        for tech in graph.technologies.values():
            try:
                br = trm_svc.calculate_blast_radius(tech.id)
                blast_reports[tech.id] = {
                    "technology_name": br.technology_name,
                    "risk_score": br.risk_score,
                    "summary": br.summary,
                    "directly_affected_system_names": br.directly_affected_system_names,
                    "cascading_system_names": br.cascading_system_names,
                    "compromised_capability_ids": br.compromised_capability_ids,
                }
            except Exception:
                pass

        # Pre-calculate scenario comparisons
        comparisons: dict[str, Any] = {}
        plateaus_list = list(graph.plateaus.values())
        for i in range(len(plateaus_list)):
            for j in range(i + 1, len(plateaus_list)):
                p1 = plateaus_list[i].id
                p2 = plateaus_list[j].id
                try:
                    comp = roadmap_service.compare_plateaus(p1, p2)
                    comparisons[f"{p1}_{p2}"] = comp.model_dump()
                except Exception:
                    pass

        payload = {
            "overview": {
                "version": "0.1.0",
                "quality_gate_valid": linter_report.is_valid,
                "linter_errors": linter_report.error_count,
                "linter_warnings": linter_report.warning_count,
                "total_applications": len(graph.systems),
                "total_capabilities": bcm_report.total_capabilities,
                "capability_coverage_percentage": bcm_report.coverage_percentage,
                "total_technologies": trm_report.total_technologies,
                "technologies_past_eol": trm_report.eol_count,
                "total_interfaces": len(graph.interfaces),
                "total_data_objects": len(graph.data_objects),
                "total_plateaus": len(graph.plateaus),
                "total_work_packages": len(graph.work_packages),
            },
            "validation": {
                "valid": linter_report.is_valid,
                "error_count": linter_report.error_count,
                "warning_count": linter_report.warning_count,
                "issues": [
                    {
                        "severity": iss.severity.value,
                        "rule": iss.rule,
                        "message": iss.message,
                        "entity_id": iss.entity_id,
                    }
                    for iss in linter_report.issues
                ],
            },
            "applications": [
                {
                    "id": a.id,
                    "name": a.name,
                    "time_classification": a.time_classification.value,
                    "business_criticality": a.business_criticality,
                    "functional_suitability": a.functional_suitability,
                    "technical_suitability": a.technical_suitability,
                    "capabilities": a.capabilities,
                    "tags": a.tags,
                }
                for a in apps
            ],
            "capabilities": [
                {
                    "id": c.id,
                    "name": c.name,
                    "level": c.level,
                    "description": c.description,
                }
                for c in graph.capabilities.values()
            ],
            "coverage": {
                "coverages": {
                    cid: {
                        "realizing_systems_count": len(cov.realizing_system_ids),
                        "realizing_systems": cov.realizing_system_names,
                        "health": cov.health.value,
                    }
                    for cid, cov in bcm_report.coverages.items()
                }
            },
            "technologies": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "category": t.category,
                }
                for t in trm_report.technologies
            ],
            "dataObjects": [
                {
                    "id": d.id,
                    "name": d.name,
                    "classification": d.classification.value,
                }
                for d in graph.data_objects.values()
            ],
            "interfaces": [
                {
                    "id": i.id,
                    "name": i.name,
                    "protocol": i.protocol,
                    "provider_system_id": i.provider_system_id,
                }
                for i in graph.interfaces.values()
            ],
            "plateaus": [
                {
                    "id": p.id,
                    "name": p.name,
                    "target_date": str(p.target_date) if p.target_date else None,
                }
                for p in roadmap_service.list_plateaus()
            ],
            "workPackages": [
                {
                    "id": w.id,
                    "name": w.name,
                    "status": w.status.value,
                }
                for w in roadmap_service.list_work_packages()
            ],
            "diagrams": diagrams,
            "blastRadiusReports": blast_reports,
            "scenarioComparisons": comparisons,
            "backstage_yaml": BackstageConnector.export_yaml(graph),
            "archimate_xml": ArchiMateConnector.export_xml(graph),
            "archi_native_xml": ArchiMateConnector.export_archi_xml(graph),
        }

        # Sanitize serialized JSON against script injection / breakout (e.g., </script>)
        serialized_data = (
            json.dumps(payload, default=str)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
        )
        return PORTAL_HTML_TEMPLATE.replace("__DATA_PAYLOAD__", serialized_data)

    @classmethod
    def export_portal(cls, graph: CompiledGraph, output_dir: Path | str) -> Path:
        """Export static portal bundle to target directory."""
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        html_file = target / "index.html"
        html_content = cls.build_static_portal_html(graph)
        html_file.write_text(html_content, encoding="utf-8")
        return html_file
