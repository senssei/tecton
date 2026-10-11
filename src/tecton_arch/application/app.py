"""TectonApp: Central Application Service Facade.

Coordinates all architecture intelligence use cases, ensuring delivery channels
(CLI, FastAPI server, and Web Portal) remain thin translators.
"""

from datetime import date
from pathlib import Path
from typing import Any, Optional

from tecton_arch import __version__
from tecton_arch.application.dto import (
    ExportResultDto,
    HealthDto,
    OverviewDto,
    ValidationIssueDto,
    ValidationReportDto,
)
from tecton_arch.application.exceptions import (
    EntityNotFoundError,
    ValidationFailedError,
)
from tecton_arch.application.exporters import ExporterRegistry
from tecton_arch.application.workspace import Workspace
from tecton_arch.engines.diff_engine import ArchitectureDiffReport
from tecton_arch.engines.linter import GraphLinter, LintSeverity
from tecton_arch.exporters.mermaid import MermaidExporter
from tecton_arch.services.apm_service import APMService
from tecton_arch.services.bcm_service import BCMService
from tecton_arch.services.diff_service import DiffService
from tecton_arch.services.lineage_service import LineageService
from tecton_arch.services.roadmap_service import RoadmapService
from tecton_arch.services.trm_service import TRMService


class TectonApp:
    """Central facade orchestrating Architecture Intelligence use cases."""

    def __init__(self, workspace: Workspace | Path | str = ".") -> None:
        if isinstance(workspace, Workspace):
            self.workspace = workspace
        else:
            self.workspace = Workspace(workspace)
        self.exporter_registry = ExporterRegistry.default()

    @property
    def graph(self):
        return self.workspace.graph

    def reload(self) -> dict[str, Any]:
        """Reload workspace manifests from disk."""
        graph = self.workspace.reload()
        return {
            "status": "reloaded",
            "files_scanned": len(graph.files_parsed),
            "applications": len(graph.systems),
        }

    def health(self) -> HealthDto:
        """Return system health and loaded entity metrics."""
        graph = self.graph
        return HealthDto(
            status="ok",
            version=__version__,
            workspace_path=str(self.workspace.path),
            files_scanned=len(graph.files_parsed),
            applications=len(graph.systems),
            capabilities=len(graph.capabilities),
            technologies=len(graph.technologies),
            interfaces=len(graph.interfaces),
            data_objects=len(graph.data_objects),
            relationships=len(graph.relationships),
            plateaus=len(graph.plateaus),
            work_packages=len(graph.work_packages),
        )

    def overview(self, as_of_date: date | None = None) -> OverviewDto:
        """Calculate executive summary across APM, BCM, TRM, and Quality Gate."""
        graph = self.graph
        linter_report = GraphLinter().lint(graph, as_of_date=as_of_date)
        bcm_report = BCMService(graph).analyze()
        trm_report = TRMService(graph).evaluate_technologies(as_of_date=as_of_date)

        return OverviewDto(
            version=__version__,
            workspace_path=str(self.workspace.path),
            quality_gate_valid=linter_report.is_valid,
            linter_errors=linter_report.error_count,
            linter_warnings=linter_report.warning_count,
            total_applications=len(graph.systems),
            total_capabilities=bcm_report.total_capabilities,
            capability_coverage_percentage=bcm_report.coverage_percentage,
            capability_blind_spots=len(bcm_report.orphaned_capabilities),
            total_technologies=trm_report.total_technologies,
            technologies_past_eol=trm_report.eol_count,
            total_interfaces=len(graph.interfaces),
            total_data_objects=len(graph.data_objects),
            total_plateaus=len(graph.plateaus),
            total_work_packages=len(graph.work_packages),
        )

    def validate(self, strict: bool = False, as_of_date: date | None = None, *, require_owner: bool = False) -> ValidationReportDto:
        """Run architecture quality gate and graph linter."""
        graph = self.graph
        report = GraphLinter().lint(graph, as_of_date=as_of_date, require_owner=require_owner)

        dto_issues = [
            ValidationIssueDto(
                severity=iss.severity.value,
                rule=iss.rule,
                message=iss.message,
                entity_id=iss.entity_id,
                file_origin=iss.file_origin,
            )
            for iss in report.issues
        ]

        result = ValidationReportDto(
            valid=report.is_valid and (report.warning_count == 0 if strict else True),
            error_count=report.error_count,
            warning_count=report.warning_count,
            issues=dto_issues,
        )

        if strict and not result.valid:
            raise ValidationFailedError(
                f"Architecture Quality Gate failed in strict mode ({report.error_count} errors, {report.warning_count} warnings)"
            )
        return result

    def export(self, format_name: str, options: dict[str, Any] | None = None) -> ExportResultDto:
        """Export architecture graph to the target format via the Exporter Registry."""
        exporter = self.exporter_registry.get(format_name)
        return exporter.export(self.graph, options=options)

    def export_backstage_entities(self) -> list[dict[str, Any]]:
        """Export raw Backstage catalog entity dictionaries."""
        from tecton_arch.connectors.backstage import BackstageConnector
        return BackstageConnector.export_catalog(self.graph)

    def import_model(self, format_name: str, content: str) -> dict[str, Any]:
        """Import external architecture model into Tecton manifest dictionary."""
        fmt = format_name.lower().strip()
        if fmt in ("backstage", "yaml"):
            from tecton_arch.connectors.backstage import BackstageConnector
            return BackstageConnector.import_catalog(content)
        elif fmt in ("archimate", "exchange", "xml", "archi"):
            from tecton_arch.connectors.archimate import ArchiMateConnector
            return ArchiMateConnector.import_xml(content)
        else:
            raise ValueError(f"Unsupported import format: '{format_name}'. Supported: backstage, archimate")

    def apm_applications(self) -> list[dict[str, Any]]:
        """List application portfolio with Gartner TIME classifications and metrics."""
        apps = self.workspace.adapter.fetch_applications()
        service = APMService(self.workspace.adapter)
        time_map = service.time_engine.evaluate_all(apps)
        return [
            {
                "id": app.id,
                "name": app.name,
                "business_criticality": app.business_criticality,
                "functional_suitability": app.functional_suitability,
                "technical_suitability": app.technical_suitability,
                "time_classification": time_map.get(app.id, app.time_classification).value,
                "current_phase": app.current_phase.value if app.current_phase else None,
                "capabilities": app.capabilities,
                "tags": app.tags,
                "technologies": app.metadata.get("technologies", []),
                "description": app.metadata.get("description"),
                "owner": app.metadata.get("owner"),
                "components": [
                    {"id": c.id, "name": c.name, "description": c.description}
                    for c in sorted(self.graph.containers.values(), key=lambda c: c.id)
                    if c.system_id == app.id
                ],
            }
            for app in sorted(apps, key=lambda a: a.name)
        ]

    def apm_analysis(self) -> dict[str, Any]:
        """Execute full deterministic APM evaluation (TIME, Redundancy, Lifecycle)."""
        from collections import Counter
        service = APMService(self.workspace.adapter)
        result = service.analyze()
        counts = Counter(result.time_classifications.values())
        return {
            "total_applications": len(result.applications),
            "time_distribution": {k.value: v for k, v in counts.items()},
            "redundancy_clusters": [
                {
                    "cluster_id": c.cluster_id,
                    "applications": c.application_names,
                    "similarity_score": c.similarity_score,
                    "shared_capabilities": c.shared_capabilities,
                    "recommendation": c.recommendation,
                }
                for c in result.redundancy_clusters
            ],
            "lifecycle_issues": [
                {
                    "application_id": i.application_id,
                    "application_name": i.application_name,
                    "severity": i.severity,
                    "message": i.message,
                }
                for i in result.lifecycle_report.issues
            ],
            "patches_needed": result.patches_needed,
        }

    def bcm_capabilities(self) -> list[dict[str, Any]]:
        """List all business capabilities with realization mapping."""
        graph = self.graph
        return [
            {
                "id": c.id,
                "name": c.name,
                "level": c.level,
                "parent_id": c.parent_id,
                "description": c.description,
            }
            for c in sorted(graph.capabilities.values(), key=lambda c: c.name)
        ]

    def data_objects(self) -> list[dict[str, Any]]:
        """List enterprise business data objects."""
        graph = self.graph
        return [
            {
                "id": d.id,
                "name": d.name,
                "classification": d.classification.value,
                "description": d.description,
            }
            for d in sorted(graph.data_objects.values(), key=lambda d: d.name)
        ]

    def interfaces(self) -> list[dict[str, Any]]:
        """List interface contracts and protocols."""
        graph = self.graph
        return [
            {
                "id": i.id,
                "name": i.name,
                "protocol": i.protocol,
                "provider_system_id": i.provider_system_id,
                "description": i.description,
            }
            for i in sorted(graph.interfaces.values(), key=lambda i: i.name)
        ]

    def data_lineage_flowchart(self, data_id: str) -> str:
        """Export living Mermaid flowchart of data lineage trajectory."""
        service = LineageService(self.graph)
        return service.export_lineage_flowchart(data_id)

    def bcm_analysis(self) -> dict[str, Any]:
        """Run Business Capability Mapping (BCM) analysis."""
        service = BCMService(self.graph)
        report = service.analyze()
        return report.model_dump()

    def trm_evaluation(self, as_of_date: date | None = None) -> dict[str, Any]:
        """Run Technology Radar & Risk Management (TRM) evaluation."""
        service = TRMService(self.graph)
        report = service.evaluate_technologies(as_of_date=as_of_date)
        return report.model_dump()

    def trm_blast_radius(self, tech_id: str, as_of_date: date | None = None) -> dict[str, Any]:
        """Calculate blast radius and cascade failure impact for a technology."""
        service = TRMService(self.graph)
        try:
            report = service.calculate_blast_radius(tech_id, as_of_date=as_of_date)
            return report.model_dump()
        except KeyError as e:
            raise EntityNotFoundError(f"Technology '{tech_id}' not found in architecture catalog") from e

    def data_lineage(self, data_id: str) -> dict[str, Any]:
        """Trace data lineage trajectory and compliance risk for a data object."""
        service = LineageService(self.graph)
        try:
            report = service.trace_lineage(data_id)
            dump = report.model_dump()
            dump["is_compliant"] = report.is_compliant
            dump["risk_count"] = report.risk_count
            return dump
        except KeyError as e:
            raise EntityNotFoundError(f"Data object '{data_id}' not found in architecture catalog") from e

    def list_plateaus(self) -> list[dict[str, Any]]:
        """List transformation plateaus ordered chronologically and by predecessor."""
        service = RoadmapService(self.graph)
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "target_date": str(p.target_date) if p.target_date else None,
                "previous_plateau_id": p.previous_plateau_id,
                "active_system_ids": p.active_system_ids,
                "decommissioned_system_ids": p.decommissioned_system_ids,
            }
            for p in service.list_plateaus()
        ]

    def list_work_packages(self) -> list[dict[str, Any]]:
        """List transformation work packages and migration initiatives."""
        service = RoadmapService(self.graph)
        return [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "status": w.status.value,
                "start_date": str(w.start_date) if w.start_date else None,
                "target_date": str(w.target_date) if w.target_date else None,
                "from_plateau_id": w.from_plateau_id,
                "to_plateau_id": w.to_plateau_id,
                "involved_system_ids": w.involved_system_ids,
                "realized_capability_ids": w.realized_capability_ids,
                "depends_on": w.depends_on,
                "owner": w.owner,
            }
            for w in service.list_work_packages()
        ]

    def roadmap_analysis(self) -> dict[str, Any]:
        """Analyze transition plateaus and work packages."""
        service = RoadmapService(self.graph)
        return service.analyze().model_dump()

    def roadmap_compare(self, from_plateau: str, to_plateau: str) -> dict[str, Any]:
        """Compare architectural delta between two roadmap plateaus."""
        service = RoadmapService(self.graph)
        comp = service.compare_plateaus(from_plateau, to_plateau)
        return comp.model_dump()

    def diff_directories(self, base_path: Path | str, head_path: Path | str) -> ArchitectureDiffReport:
        """Run semantic diff between two directories."""
        return DiffService().compare_directories(base_path, head_path)

    def diff_git(self, base_ref: str, head_ref: str = "HEAD") -> ArchitectureDiffReport:
        """Run semantic diff between two Git revisions."""
        return DiffService().compare_git_revisions(
            base_ref=base_ref,
            head_ref=head_ref,
            repo_root=self.workspace.path,
        )

    def portal_snapshot(self) -> dict[str, Any]:
        """Compute complete, pre-calculated snapshot payload for offline and online portals."""
        graph = self.graph
        apps = self.workspace.adapter.fetch_applications()
        bcm_report = BCMService(graph).analyze()
        trm_report = TRMService(graph).evaluate_technologies()
        roadmap_service = RoadmapService(graph)

        lineage_service = LineageService(graph)
        diagrams = {
            "time-matrix": MermaidExporter.to_time_quadrant_chart(apps),
            "bcm-heatmap": BCMService(graph).export_heatmap(),
            "tech-radar": TRMService(graph).export_radar(),
            "roadmap-gantt": roadmap_service.export_gantt(),
        }
        for do_id in graph.data_objects:
            try:
                diagrams[f"lineage-{do_id}"] = lineage_service.export_lineage_flowchart(do_id)
            except Exception:
                pass

        trm_service = TRMService(graph)
        blast_reports = {
            t_id: trm_service.calculate_blast_radius(t_id).model_dump()
            for t_id in graph.technologies
        }

        plateaus = roadmap_service.list_plateaus()
        comparisons = {}
        for i in range(len(plateaus) - 1):
            p1 = plateaus[i].id
            p2 = plateaus[i + 1].id
            comparisons[f"{p1}_{p2}"] = roadmap_service.compare_plateaus(p1, p2).model_dump()

        return {
            "version": __version__,
            "overview": self.overview().model_dump(),
            "validation": self.validate().model_dump(),
            "applications": self.apm_applications(),
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
            "backstage_yaml": self.export("backstage").content,
            "archimate_xml": self.export("exchange").content,
            "archi_native_xml": self.export("archi").content,
        }
