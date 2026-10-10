"""FastAPI application factory for Tecton Headless Architecture Intelligence Server.

Exposes REST API endpoints for APM, BCM, TRM, Data Lineage, Graph Linting,
and living Mermaid diagram export.
"""

from pathlib import Path
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from tecton.adapters.git_adapter import GitRepositoryAdapter
from tecton.dsl.linter import GraphLinter
from tecton.exporters.mermaid import MermaidExporter
from tecton.services.apm_service import APMService
from tecton.services.bcm_service import BCMService
from tecton.services.lineage_service import LineageService
from tecton.services.roadmap_service import RoadmapService
from tecton.services.trm_service import TRMService


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    workspace_path: str
    files_scanned: int
    applications: int
    capabilities: int
    technologies: int
    interfaces: int
    data_objects: int
    relationships: int
    plateaus: int = 0
    work_packages: int = 0


class OverviewResponse(BaseModel):
    version: str = "0.1.0"
    workspace_path: str
    quality_gate_valid: bool
    linter_errors: int
    linter_warnings: int
    total_applications: int
    total_capabilities: int
    capability_coverage_percentage: float
    capability_blind_spots: int
    total_technologies: int
    technologies_past_eol: int
    total_interfaces: int
    total_data_objects: int
    total_plateaus: int = 0
    total_work_packages: int = 0


def create_app(workspace_path: Path | str = ".") -> FastAPI:
    """Create and configure a FastAPI application serving architecture intelligence."""
    resolved_path = Path(workspace_path).resolve()

    app = FastAPI(
        title="Tecton Architecture Intelligence API",
        description="Deterministic, offline-first Enterprise Architecture Intelligence Engine & Architecture-as-Code REST API.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS for developer portal and dashboard integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # State holding the workspace adapter and services
    adapter = GitRepositoryAdapter(resolved_path)

    @app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
    def get_health() -> HealthResponse:
        """Return server health and loaded architecture entity counts."""
        graph = adapter.graph
        return HealthResponse(
            status="ok",
            version="0.1.0",
            workspace_path=str(resolved_path),
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

    @app.get("/api/v1/overview", response_model=OverviewResponse, tags=["System"])
    def get_overview() -> OverviewResponse:
        """Return executive summary across all architectural dimensions."""
        graph = adapter.graph
        linter_report = GraphLinter().lint(graph)
        bcm_report = BCMService(graph).analyze()
        trm_report = TRMService(graph).evaluate_technologies()

        return OverviewResponse(
            version="0.1.0",
            workspace_path=str(resolved_path),
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

    @app.post("/api/v1/reload", tags=["System"])
    def reload_workspace() -> dict[str, Any]:
        """Reload architecture DSL manifests from disk."""
        adapter.reload()
        return {
            "status": "reloaded",
            "files_scanned": len(adapter.graph.files_parsed),
            "applications": len(adapter.graph.systems),
        }

    @app.get("/api/v1/validate", tags=["Quality Gate"])
    def validate_architecture() -> dict[str, Any]:
        """Run architecture quality gate and graph linter."""
        graph = adapter.graph
        report = GraphLinter().lint(graph)
        return {
            "valid": report.is_valid,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "rule": issue.rule,
                    "entity_id": issue.entity_id,
                    "message": issue.message,
                    "file_origin": issue.file_origin,
                }
                for issue in report.issues
            ],
        }

    # --- APM Endpoints ---
    @app.get("/api/v1/apm/applications", tags=["APM"])
    def list_apm_applications() -> list[dict[str, Any]]:
        """List application portfolio with Gartner TIME classifications and metrics."""
        apps = adapter.fetch_applications()
        time_service = APMService(adapter)
        time_map = time_service.time_engine.evaluate_all(apps)

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
                "technologies": app.metadata.get("technologies", []),
                "description": app.metadata.get("description"),
            }
            for app in sorted(apps, key=lambda a: a.name)
        ]

    @app.get("/api/v1/apm/analysis", tags=["APM"])
    def analyze_apm_portfolio() -> dict[str, Any]:
        """Execute full deterministic APM evaluation (TIME, Redundancy, Lifecycle)."""
        service = APMService(adapter)
        result = service.analyze()

        from collections import Counter
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

    # --- BCM Endpoints ---
    @app.get("/api/v1/bcm/capabilities", tags=["BCM"])
    def list_capabilities() -> list[dict[str, Any]]:
        """List all business capabilities with realization mapping."""
        graph = adapter.graph
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

    @app.get("/api/v1/bcm/coverage", tags=["BCM"])
    def analyze_bcm_coverage() -> dict[str, Any]:
        """Analyze capability coverage, detect unmapped blind spots, and assess health."""
        service = BCMService(adapter.graph)
        report = service.analyze()

        return {
            "total_capabilities": report.total_capabilities,
            "mapped_capabilities": report.mapped_capabilities,
            "coverage_percentage": report.coverage_percentage,
            "orphaned_capabilities": report.orphaned_capabilities,
            "overprovisioned_capabilities": report.overprovisioned_capabilities,
            "coverages": {
                c_id: {
                    "capability_id": cov.capability_id,
                    "name": cov.name,
                    "level": cov.level,
                    "parent_id": cov.parent_id,
                    "health": cov.health.value,
                    "realizing_system_ids": cov.realizing_system_ids,
                    "realizing_system_names": cov.realizing_system_names,
                }
                for c_id, cov in report.coverages.items()
            },
        }

    # --- TRM Endpoints ---
    @app.get("/api/v1/trm/technologies", tags=["TRM"])
    def list_technologies() -> dict[str, Any]:
        """List technology standards, obsolescence status, and adoption counts."""
        service = TRMService(adapter.graph)
        report = service.evaluate_technologies()

        return {
            "total_technologies": report.total_technologies,
            "approved_count": report.approved_count,
            "deprecated_count": report.deprecated_count,
            "prohibited_count": report.prohibited_count,
            "eol_count": report.eol_count,
            "technologies": [
                {
                    "id": t.id,
                    "name": t.name,
                    "category": t.category,
                    "status": t.status.value,
                    "eol_date": t.eol_date,
                    "is_eol": t.is_eol,
                    "days_to_eol": t.days_to_eol,
                    "realizing_systems_count": t.realizing_systems_count,
                    "realizing_systems": t.realizing_systems,
                }
                for t in report.technologies
            ],
        }

    @app.get("/api/v1/trm/blast-radius/{technology_id}", tags=["TRM"])
    def get_technology_blast_radius(technology_id: str) -> dict[str, Any]:
        """Calculate direct and cascading blast radius for a given technology asset."""
        service = TRMService(adapter.graph)
        try:
            report = service.calculate_blast_radius(technology_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

        return {
            "technology_id": report.technology_id,
            "technology_name": report.technology_name,
            "status": report.status.value,
            "is_eol": report.is_eol,
            "risk_score": report.risk_score,
            "highest_criticality": report.highest_criticality,
            "directly_affected_system_ids": report.directly_affected_system_ids,
            "directly_affected_system_names": report.directly_affected_system_names,
            "cascading_system_ids": report.cascading_system_ids,
            "cascading_system_names": report.cascading_system_names,
            "compromised_capability_ids": report.compromised_capability_ids,
            "summary": report.summary,
        }

    # --- Data Architecture & Lineage Endpoints ---
    @app.get("/api/v1/data/objects", tags=["Data Architecture"])
    def list_data_objects() -> list[dict[str, Any]]:
        """List enterprise business data objects with privacy classifications."""
        service = LineageService(adapter.graph)
        return [
            {
                "id": d.id,
                "name": d.name,
                "classification": d.classification.value,
                "owner": d.owner,
                "description": d.description,
            }
            for d in service.list_data_objects()
        ]

    @app.get("/api/v1/data/interfaces", tags=["Data Architecture"])
    def list_interfaces() -> list[dict[str, Any]]:
        """List registered communication interfaces and API contracts."""
        service = LineageService(adapter.graph)
        return [
            {
                "id": i.id,
                "name": i.name,
                "protocol": i.protocol,
                "provider_system_id": i.provider_system_id,
                "consumer_system_ids": i.consumer_system_ids,
                "data_objects": i.data_objects,
                "description": i.description,
            }
            for i in service.list_interfaces()
        ]

    @app.get("/api/v1/data/lineage/{data_object_id}", tags=["Data Architecture"])
    def trace_data_lineage(data_object_id: str) -> dict[str, Any]:
        """Trace end-to-end data lineage trajectory and compliance audit report."""
        service = LineageService(adapter.graph)
        try:
            report = service.trace_lineage(data_object_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

        return {
            "data_object_id": report.data_object_id,
            "data_object_name": report.data_object_name,
            "classification": report.classification.value,
            "owner": report.owner,
            "producers": report.producers,
            "consumers": report.consumers,
            "participating_systems": report.participating_systems,
            "flow_edges": [
                {
                    "source_system_id": e.source_system_id,
                    "source_system_name": e.source_system_name,
                    "target_system_id": e.target_system_id,
                    "target_system_name": e.target_system_name,
                    "protocol": e.protocol,
                    "channel_name": e.channel_name,
                }
                for e in report.flow_edges
            ],
            "compliance_risks": report.compliance_risks,
            "is_compliant": report.is_compliant,
            "risk_count": report.risk_count,
        }

    # --- Architecture Transformation Roadmap Endpoints ---
    @app.get("/api/v1/roadmap/plateaus", tags=["Roadmap"])
    def list_plateaus() -> list[dict[str, Any]]:
        """List transformation plateaus ordered chronologically and by predecessor."""
        service = RoadmapService(adapter.graph)
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "target_date": p.target_date,
                "previous_plateau_id": p.previous_plateau_id,
                "active_system_ids": p.active_system_ids,
                "decommissioned_system_ids": p.decommissioned_system_ids,
            }
            for p in service.list_plateaus()
        ]

    @app.get("/api/v1/roadmap/work-packages", tags=["Roadmap"])
    def list_work_packages() -> list[dict[str, Any]]:
        """List transformation work packages and migration initiatives."""
        service = RoadmapService(adapter.graph)
        return [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "status": w.status.value,
                "start_date": w.start_date,
                "target_date": w.target_date,
                "from_plateau_id": w.from_plateau_id,
                "to_plateau_id": w.to_plateau_id,
                "involved_system_ids": w.involved_system_ids,
                "realized_capability_ids": w.realized_capability_ids,
                "depends_on": w.depends_on,
                "owner": w.owner,
            }
            for w in service.list_work_packages()
        ]

    @app.get("/api/v1/roadmap/analyze", tags=["Roadmap"])
    def analyze_roadmap() -> dict[str, Any]:
        """Audit roadmap consistency, plateau states, and transitional capability gaps."""
        service = RoadmapService(adapter.graph)
        report = service.analyze()
        return report.model_dump()

    @app.get("/api/v1/roadmap/compare", tags=["Roadmap"])
    def compare_plateaus(
        from_plateau: str = Query(..., description="Baseline or predecessor plateau ID"),
        to_plateau: str = Query(..., description="Target plateau ID"),
    ) -> dict[str, Any]:
        """Compare two architecture plateaus and compute scenario delta (As-Is vs To-Be)."""
        service = RoadmapService(adapter.graph)
        try:
            comparison = service.compare_plateaus(from_plateau, to_plateau)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return comparison.model_dump()

    # --- Living Visualizations Endpoints ---
    @app.get("/api/v1/diagrams/{chart_type}", tags=["Visualizations"])
    def get_diagram(
        chart_type: str,
        data_id: Optional[str] = Query(None, description="Data Object ID for data-lineage chart"),
    ) -> dict[str, Any]:
        """Generate living Mermaid diagram content for external dashboards."""
        graph = adapter.graph
        if chart_type == "time-matrix":
            apps = adapter.fetch_applications()
            chart = MermaidExporter.to_time_quadrant_chart(apps)
        elif chart_type == "capability-heatmap":
            service_bcm = BCMService(graph)
            chart = service_bcm.export_heatmap()
        elif chart_type == "tech-radar":
            service_trm = TRMService(graph)
            chart = service_trm.export_radar()
        elif chart_type == "data-lineage":
            if not data_id:
                raise HTTPException(status_code=400, detail="Query parameter 'data_id' is required for chart_type 'data-lineage'")
            service_lineage = LineageService(graph)
            try:
                chart = service_lineage.export_lineage_flowchart(data_id)
            except KeyError as e:
                raise HTTPException(status_code=404, detail=str(e))
        elif chart_type == "roadmap-gantt":
            service_roadmap = RoadmapService(graph)
            chart = service_roadmap.export_gantt()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown chart_type '{chart_type}'. Supported types: time-matrix, capability-heatmap, tech-radar, data-lineage, roadmap-gantt",
            )

        return {
            "chart_type": chart_type,
            "format": "mermaid",
            "content": chart,
        }

    return app
