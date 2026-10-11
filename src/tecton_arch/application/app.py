"""TectonApp: Central Application Service Facade.

Coordinates all architecture intelligence use cases, ensuring delivery channels
(CLI, FastAPI server, and Web Portal) remain thin translators.
"""

from datetime import date
from pathlib import Path
from typing import Any, Optional

from tecton_arch import __version__
from tecton_arch.core.config import TectonConfig
from tecton_arch.services.catalog_service import CatalogService
from tecton_arch.services.finance_service import cost_summary, business_cases
from tecton_arch.services.feasibility_service import FeasibilityService
from tecton_arch.services.assessment import evaluate_applications
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

    def __init__(
        self,
        workspace: Workspace | Path | str = ".",
        as_of_date: date | None = None,
        config: Any = None,
        strict: bool = False,
    ) -> None:
        if isinstance(workspace, Workspace):
            self.workspace = workspace
        else:
            self.workspace = Workspace(workspace, config=config, strict=strict)
        self.config = config or self.workspace.config or TectonConfig()
        self.as_of_date = as_of_date
        self.strict = strict or getattr(self.workspace, "strict", False)
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
        eval_date = as_of_date or self.as_of_date or date.today()
        graph = self.graph
        linter_report = GraphLinter().lint(graph, as_of_date=eval_date, config=self.config)
        bcm_report = BCMService(graph, config=self.config).analyze(as_of_date=eval_date)
        trm_report = TRMService(graph).evaluate_technologies(as_of_date=eval_date)

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
            as_of_date=str(eval_date) if eval_date else None,
        )

    def validate(self, strict: bool | None = None, as_of_date: date | None = None, *, require_owner: bool = False) -> ValidationReportDto:
        """Run architecture quality gate and graph linter."""
        strict = self.config.strict if strict is None else strict
        eval_date = as_of_date or self.as_of_date or date.today()
        graph = self.graph
        report = GraphLinter().lint(
            graph,
            as_of_date=eval_date,
            require_owner=require_owner,
            strict=strict,
            config=self.config,
        )

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
            as_of_date=str(eval_date) if eval_date else None,
            issues=dto_issues,
        )

        if strict and not result.valid:
            raise ValidationFailedError(
                f"Architecture Quality Gate failed in strict mode ({report.error_count} errors, {report.warning_count} warnings)"
            )
        return result



    def export(self, format_name: str, options: dict[str, Any] | None = None) -> ExportResultDto:
        """Export architecture graph to the target format via the Exporter Registry."""
        opts = dict(options or {})
        opts.setdefault("as_of_date", self.as_of_date or date.today())
        opts.setdefault("config", self.config)
        exporter = self.exporter_registry.get(format_name)
        result = exporter.export(self.graph, options=opts)
        if exporter.name in ("backstage", "exchange", "archi"):
            from tecton_arch.dsl.references import COLLECTIONS
            extended = ("review", "annual_cost", "suitability_rationale", "importance", "planned_cost", "business_case", "resource_allocations", "spend_plan", "introduced_system_ids", "decommissioned_system_ids")
            for collection in [*COLLECTIONS, "relationships"]:
                entries = getattr(self.graph, collection)
                entries = entries if isinstance(entries, list) else entries.values()
                for index, entity in enumerate(entries):
                    for field in extended:
                        value = getattr(entity, field, None)
                        if value and not (field == "importance" and value == 1):
                            result.warnings.append(f"{collection}.{getattr(entity, 'id', index)}.{field}: extended field is not guaranteed to survive interchange")
        return result

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

    def apm_applications(self, as_of_date: date | None = None) -> list[dict[str, Any]]:
        """List application portfolio with Gartner TIME classifications and metrics."""
        eval_date = as_of_date or self.as_of_date or date.today()
        apps = self.workspace.adapter.fetch_applications(as_of_date=eval_date)
        service = APMService(self.workspace.adapter, self.config.time, self.config.redundancy)
        apps = evaluate_applications(apps, self.config, eval_date)
        time_map = service.time_engine.evaluate_all(apps)
        graph = self.workspace.optional_graph
        components_by_system: dict[str, list[dict[str, Any]]] = {}
        if graph is not None:
            for component in sorted(graph.containers.values(), key=lambda c: c.id):
                components_by_system.setdefault(component.system_id, []).append({
                    "id": component.id,
                    "name": component.name,
                    "description": component.description,
                })
        return [
            {
                "id": app.id,
                "name": app.name,
                "business_criticality": app.business_criticality,
                "functional_suitability": app.functional_suitability,
                "technical_suitability": app.technical_suitability,
                "time_classification": time_map.get(app.id, app.time_classification).value,
                **app.metadata.get("assessment", {}),
                "current_phase": app.current_phase.value if app.current_phase else None,
                "capabilities": app.capabilities,
                "tags": app.tags,
                "technologies": app.metadata.get("technologies", []),
                "description": app.metadata.get("description"),
                "annual_cost": app.metadata.get("annual_cost"),
                "suitability_rationale": app.metadata.get("suitability_rationale"),
                "owner": app.metadata.get("owner"),
                "components": components_by_system.get(app.id, []),
            }
            for app in sorted(apps, key=lambda a: a.name)
        ]

    def apm_analysis(self, as_of_date: date | None = None) -> dict[str, Any]:
        """Execute full deterministic APM evaluation (TIME, Redundancy, Lifecycle)."""
        from collections import Counter
        eval_date = as_of_date or self.as_of_date or date.today()
        service = APMService(self.workspace.adapter, self.config.time, self.config.redundancy)
        result = service.analyze(as_of_date=eval_date)
        counts = Counter(result.time_classifications.values())
        return {
            "total_applications": len(result.applications),
            "as_of_date": str(eval_date) if eval_date else None,
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
            "application_assessments": {a.id: a.metadata["assessment"] for a in result.applications},
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

    def data_lineage_flowchart(self, data_id: str, as_of_date: date | None = None) -> str:
        """Export living Mermaid flowchart of data lineage trajectory."""
        service = LineageService(self.graph, config=self.config)
        return service.export_lineage_flowchart(data_id, as_of_date=as_of_date or self.as_of_date or date.today())

    def data_flow_diagrams(self) -> list[dict[str, Any]]:
        """Return explicit DFD models without inferring processes or stores."""
        return [diagram.model_dump(mode="json") for diagram in sorted(self.graph.data_flow_diagrams.values(), key=lambda d: d.id)]

    def bcm_analysis(self, as_of_date: date | None = None) -> dict[str, Any]:
        """Run Business Capability Mapping (BCM) analysis."""
        service = BCMService(self.graph, config=self.config)
        report = service.analyze(as_of_date=as_of_date or self.as_of_date or date.today())
        return report.model_dump()

    def trm_evaluation(self, as_of_date: date | None = None) -> dict[str, Any]:
        """Run Technology Radar & Risk Management (TRM) evaluation."""
        eval_date = as_of_date or self.as_of_date or date.today()
        service = TRMService(self.graph)
        report = service.evaluate_technologies(as_of_date=eval_date)
        result = report.model_dump(mode="json")
        result["as_of_date"] = str(eval_date)
        result["technologies"] = self._radar_technologies(report)
        return result

    def _radar_technologies(self, report) -> list[dict[str, Any]]:
        """Use the same technology details for REST and static radar exports."""
        graph = self.graph
        technologies = []
        for technology in sorted(report.technologies, key=lambda t: t.id):
            item = technology.model_dump(mode="json")
            item["description"] = graph.technologies[technology.id].description
            item["realizing_system_details"] = [
                {"id": system.id, "name": system.name, "owner": system.owner}
                for system in sorted(graph.systems.values(), key=lambda s: s.id)
                if technology.id in system.technologies
            ]
            technologies.append(item)
        return technologies

    def trm_blast_radius(self, tech_id: str, as_of_date: date | None = None) -> dict[str, Any]:
        """Calculate blast radius and cascade failure impact for a technology."""
        eval_date = as_of_date or self.as_of_date or date.today()
        service = TRMService(self.graph)
        try:
            report = service.calculate_blast_radius(tech_id, as_of_date=eval_date)
            return report.model_dump()
        except KeyError as e:
            raise EntityNotFoundError(f"Technology '{tech_id}' not found in architecture catalog") from e

    def data_lineage(self, data_id: str, as_of_date: date | None = None) -> dict[str, Any]:
        """Trace data lineage trajectory and compliance risk for a data object."""
        service = LineageService(self.graph, config=self.config)
        try:
            report = service.trace_lineage(data_id, as_of_date=as_of_date or self.as_of_date or date.today())
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

    def roadmap_analysis(self, as_of_date: date | None = None) -> dict[str, Any]:
        """Analyze transition plateaus and work packages."""
        eval_date = as_of_date or self.as_of_date or date.today()
        service = RoadmapService(self.graph)
        result = service.analyze(as_of_date=eval_date).model_dump(mode="json")
        result["as_of_date"] = str(eval_date)
        return result

    def roadmap_compare(self, from_plateau: str, to_plateau: str, as_of_date: date | None = None) -> dict[str, Any]:
        """Compare architectural delta between two roadmap plateaus."""
        eval_date = as_of_date or self.as_of_date or date.today()
        service = RoadmapService(self.graph)
        comp = service.compare_plateaus(from_plateau, to_plateau, as_of_date=eval_date)
        return comp.model_dump()

    def roadmap_gantt(self, title: str = "Enterprise Architecture Transformation Roadmap", as_of_date: date | None = None) -> str:
        """Export Mermaid Gantt chart visualizing plateaus and transformation initiatives."""
        eval_date = as_of_date or self.as_of_date or date.today()
        service = RoadmapService(self.graph)
        return service.export_gantt(title=title, as_of_date=eval_date)

    def diff_directories(self, base_path: Path | str, head_path: Path | str) -> ArchitectureDiffReport:
        """Run semantic diff between two directories."""
        return DiffService().compare_directories(base_path, head_path, as_of_date=self.as_of_date, config=self.config)

    def diff_git(self, base_ref: str, head_ref: str = "HEAD") -> ArchitectureDiffReport:
        """Run semantic diff between two Git revisions."""
        return DiffService().compare_git_revisions(
            base_ref=base_ref,
            head_ref=head_ref,
            repo_root=self.workspace.path,
            as_of_date=self.as_of_date, config=self.config,
        )

    def portal_snapshot(self, as_of_date: date | None = None) -> dict[str, Any]:
        """Compute complete, pre-calculated snapshot payload for offline and online portals."""
        eval_date = as_of_date or self.as_of_date or date.today()
        graph = self.graph
        apps = self.workspace.adapter.fetch_applications(as_of_date=eval_date)
        bcm_report = BCMService(graph, config=self.config).analyze(as_of_date=eval_date)
        trm_report = TRMService(graph).evaluate_technologies(as_of_date=eval_date)
        roadmap_service = RoadmapService(graph)

        lineage_service = LineageService(graph, config=self.config)
        diagrams = {
            "time-matrix": MermaidExporter.to_time_quadrant_chart(apps, time_config=self.config.time),
            "bcm-heatmap": BCMService(graph, config=self.config).export_heatmap(as_of_date=eval_date),
            "tech-radar": TRMService(graph).export_radar(as_of_date=eval_date),
            "roadmap-gantt": roadmap_service.export_gantt(as_of_date=eval_date),
        }
        for do_id in graph.data_objects:
            try:
                diagrams[f"lineage-{do_id}"] = lineage_service.export_lineage_flowchart(do_id, as_of_date=eval_date)
            except Exception:
                pass

        trm_service = TRMService(graph)
        blast_reports = {
            t_id: trm_service.calculate_blast_radius(t_id, as_of_date=eval_date).model_dump()
            for t_id in graph.technologies
        }

        plateaus = roadmap_service.list_plateaus() if roadmap_service.analyze(as_of_date=eval_date).is_valid_dag else []
        comparisons = {}
        for source in plateaus:
            for target in plateaus:
                if source.id != target.id:
                    comparisons[f"{source.id}_{target.id}"] = roadmap_service.compare_plateaus(source.id, target.id, as_of_date=eval_date).model_dump()

        return {
            "catalogFreshness": self.catalog_freshness(eval_date),
            "portfolioCosts": self.apm_costs(),
            "businessCases": self.roadmap_business_cases(),
            "feasibility": self.roadmap_feasibility(eval_date),
            "version": __version__,
            "as_of_date": str(eval_date) if eval_date else None,
            "overview": self.overview(as_of_date=eval_date).model_dump(),
            "validation": self.validate(as_of_date=eval_date).model_dump(),
            "applications": self.apm_applications(as_of_date=eval_date),
            "capabilities": self.bcm_capabilities(),
            "coverage": {
                "coverages": {
                    cid: {
                        **cov.model_dump(mode="json"),
                        "realizing_systems_count": len(cov.realizing_system_ids),
                        "realizing_systems": cov.realizing_system_names,
                        "health": cov.health.value,
                    }
                    for cid, cov in bcm_report.coverages.items()
                }
            },
            "technologies": self._radar_technologies(trm_report),
            "dataObjects": [
                {
                    "id": d.id,
                    "name": d.name,
                    "classification": d.classification.value,
                }
                for d in graph.data_objects.values()
            ],
            "dataFlowDiagrams": self.data_flow_diagrams(),
            "interfaces": [
                {
                    "id": i.id,
                    "name": i.name,
                    "protocol": i.protocol,
                    "provider_system_id": i.provider_system_id,
                }
                for i in graph.interfaces.values()
            ],
            "plateaus": self.list_plateaus(),
            "workPackages": self.list_work_packages(),
            "lineageReports": {data_id: self.data_lineage(data_id, as_of_date=eval_date) for data_id in graph.data_objects},
            "diagrams": diagrams,
            "blastRadiusReports": blast_reports,
            "scenarioComparisons": comparisons,
            "backstage_yaml": self.export("backstage").content,
            "archimate_xml": self.export("exchange").content,
            "archi_native_xml": self.export("archi").content,
            "interchangeWarnings": self.export("backstage").warnings,
        }

    def catalog_freshness(self, as_of_date=None):
        return CatalogService(self.graph, self.config).freshness(as_of_date or self.as_of_date or date.today())

    def catalog_rename(self, old_id, new_id, output=None):
        return CatalogService(self.graph, self.config).rename(old_id, new_id, self.workspace.path, output)

    def apm_costs(self):
        return cost_summary(list(self.graph.systems.values()))

    def roadmap_business_cases(self):
        return business_cases(self.graph)

    def roadmap_feasibility(self, as_of_date=None):
        return FeasibilityService(self.graph, self.config).analyze(as_of_date or self.as_of_date or date.today())
