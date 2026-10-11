"""FastAPI application factory for Tecton Headless Architecture Intelligence Server.

Exposes REST API endpoints for APM, BCM, TRM, Data Lineage, Graph Linting,
and living Mermaid diagram export.
"""

from datetime import date
import os
from pathlib import Path
from typing import Any, Optional
from fastapi import FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from tecton_arch import __version__
from tecton_arch.application.app import TectonApp
from tecton_arch.application.exceptions import EntityNotFoundError
from tecton_arch.portal.builder import PortalBuilder


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = __version__
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
    version: str = __version__
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
    as_of_date: Optional[str] = None


def create_app(workspace_path: Path | str = ".") -> FastAPI:
    """Create and configure a FastAPI application serving architecture intelligence."""
    resolved_path = Path(workspace_path).resolve()

    app = FastAPI(
        title="Tecton Architecture Intelligence API",
        description="Deterministic, offline-first Enterprise Architecture Intelligence Engine & Architecture-as-Code REST API.",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS safely: allow_credentials must be False with wildcard origin
    cors_origins = [o.strip() for o in os.environ.get("TECTON_CORS_ORIGINS", "*").split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    tecton_app = TectonApp(resolved_path)

    # --- Architecture Intelligence Web Portal & Dashboard ---
    @app.get("/", response_class=HTMLResponse, tags=["Portal"], include_in_schema=False)
    @app.get("/portal", response_class=HTMLResponse, tags=["Portal"], include_in_schema=False)
    def get_portal() -> HTMLResponse:
        """Serve the living interactive Architecture Intelligence Web Portal & Dashboard."""
        html = PortalBuilder.build_dynamic_portal_html()
        return HTMLResponse(content=html, status_code=200)

    @app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
    def get_health() -> HealthResponse:
        """Return server health and loaded architecture entity counts."""
        dto = tecton_app.health()
        return HealthResponse(**dto.model_dump())

    @app.get("/api/v1/overview", response_model=OverviewResponse, tags=["System"])
    def get_overview(
        as_of_date: Optional[date] = Query(None, description="Target evaluation date (YYYY-MM-DD)"),
    ) -> OverviewResponse:
        """Return executive summary across all architectural dimensions."""
        dto = tecton_app.overview(as_of_date=as_of_date)
        return OverviewResponse(**dto.model_dump())

    @app.post("/api/v1/reload", tags=["System"])
    def reload_workspace(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
        """Reload architecture DSL manifests from disk."""
        expected_token = os.environ.get("TECTON_API_TOKEN")
        if expected_token:
            token = authorization.replace("Bearer ", "").strip() if authorization else ""
            if token != expected_token:
                raise HTTPException(status_code=401, detail="Unauthorized: invalid or missing Tecton API token")
        return tecton_app.reload()

    @app.get("/api/v1/validate", tags=["Quality Gate"])
    def validate_architecture(
        as_of_date: Optional[date] = Query(None, description="Target evaluation date (YYYY-MM-DD)"),
    ) -> dict[str, Any]:
        """Run architecture quality gate and graph linter."""
        report = tecton_app.validate(strict=False, as_of_date=as_of_date)
        return {
            "valid": report.valid,
            "as_of_date": str(as_of_date) if as_of_date else None,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "issues": [
                {
                    "severity": issue.severity,
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
    def list_apm_applications(
        as_of_date: Optional[date] = Query(None, description="Target evaluation date (YYYY-MM-DD)"),
    ) -> list[dict[str, Any]]:
        """List application portfolio with Gartner TIME classifications and metrics."""
        return tecton_app.apm_applications(as_of_date=as_of_date)

    @app.get("/api/v1/apm/analysis", tags=["APM"])
    def analyze_apm_portfolio(
        as_of_date: Optional[date] = Query(None, description="Target evaluation date (YYYY-MM-DD)"),
    ) -> dict[str, Any]:
        """Execute full deterministic APM evaluation (TIME, Redundancy, Lifecycle)."""
        return tecton_app.apm_analysis(as_of_date=as_of_date)

    # --- BCM Endpoints ---
    @app.get("/api/v1/bcm/capabilities", tags=["BCM"])
    def list_capabilities() -> list[dict[str, Any]]:
        """List all business capabilities with realization mapping."""
        return tecton_app.bcm_capabilities()

    @app.get("/api/v1/bcm/coverage", tags=["BCM"])
    def analyze_bcm_coverage() -> dict[str, Any]:
        """Analyze capability coverage, detect unmapped blind spots, and assess health."""
        return tecton_app.bcm_analysis()

    # --- TRM Endpoints ---
    @app.get("/api/v1/trm/technologies", tags=["TRM"])
    def list_technologies(
        as_of_date: Optional[date] = Query(None, description="Target evaluation date (YYYY-MM-DD)"),
    ) -> dict[str, Any]:
        """List technology standards, obsolescence status, and adoption counts."""
        return tecton_app.trm_evaluation(as_of_date=as_of_date)

    @app.get("/api/v1/trm/blast-radius/{technology_id}", tags=["TRM"])
    def get_technology_blast_radius(
        technology_id: str,
        as_of_date: Optional[date] = Query(None, description="Target evaluation date (YYYY-MM-DD)"),
    ) -> dict[str, Any]:
        """Calculate direct and cascading blast radius for a given technology asset."""
        try:
            return tecton_app.trm_blast_radius(technology_id, as_of_date=as_of_date)
        except EntityNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))

    # --- Data Architecture & Lineage Endpoints ---
    @app.get("/api/v1/data/objects", tags=["Data Architecture"])
    def list_data_objects() -> list[dict[str, Any]]:
        """List enterprise business data objects with privacy classifications."""
        return tecton_app.data_objects()

    @app.get("/api/v1/data/interfaces", tags=["Data Architecture"])
    def list_interfaces() -> list[dict[str, Any]]:
        """List registered communication interfaces and API contracts."""
        return tecton_app.interfaces()

    @app.get("/api/v1/data/flow-diagrams", tags=["Data Architecture"])
    def list_data_flow_diagrams() -> list[dict[str, Any]]:
        return tecton_app.data_flow_diagrams()

    @app.get("/api/v1/data/lineage/{data_object_id}", tags=["Data Architecture"])
    def trace_data_lineage(data_object_id: str) -> dict[str, Any]:
        """Trace end-to-end data lineage trajectory and compliance audit report."""
        try:
            return tecton_app.data_lineage(data_object_id)
        except EntityNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))

    # --- Architecture Transformation Roadmap Endpoints ---
    @app.get("/api/v1/roadmap/plateaus", tags=["Roadmap"])
    def list_plateaus() -> list[dict[str, Any]]:
        """List transformation plateaus ordered chronologically and by predecessor."""
        return tecton_app.list_plateaus()

    @app.get("/api/v1/roadmap/work-packages", tags=["Roadmap"])
    def list_work_packages() -> list[dict[str, Any]]:
        """List transformation work packages and migration initiatives."""
        return tecton_app.list_work_packages()

    @app.get("/api/v1/roadmap/analyze", tags=["Roadmap"])
    def analyze_roadmap(
        as_of_date: Optional[date] = Query(None, description="Target evaluation date (YYYY-MM-DD)"),
    ) -> dict[str, Any]:
        """Audit roadmap consistency, plateau states, and transitional capability gaps."""
        return tecton_app.roadmap_analysis(as_of_date=as_of_date)

    @app.get("/api/v1/roadmap/compare", tags=["Roadmap"])
    def compare_plateaus(
        from_plateau: str = Query(..., description="Baseline or predecessor plateau ID"),
        to_plateau: str = Query(..., description="Target plateau ID"),
        as_of_date: Optional[date] = Query(None, description="Target evaluation date (YYYY-MM-DD)"),
    ) -> dict[str, Any]:
        """Compare two architecture plateaus and compute scenario delta (As-Is vs To-Be)."""
        try:
            return tecton_app.roadmap_compare(from_plateau, to_plateau, as_of_date=as_of_date)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

    # --- Living Visualizations Endpoints ---
    @app.get("/api/v1/diagrams/{chart_type}", tags=["Visualizations"])
    def get_diagram(
        chart_type: str,
        data_id: Optional[str] = Query(None, description="Data Object ID for data-lineage chart"),
    ) -> dict[str, Any]:
        """Generate living Mermaid diagram content for external dashboards."""
        if chart_type in ("time-matrix", "time"):
            res = tecton_app.export("mermaid", options={"diagram_type": "time-matrix"})
        elif chart_type in ("capability-heatmap", "bcm-heatmap"):
            res = tecton_app.export("mermaid", options={"diagram_type": "bcm-heatmap"})
        elif chart_type in ("tech-radar", "radar"):
            res = tecton_app.export("mermaid", options={"diagram_type": "tech-radar"})
        elif chart_type == "data-lineage":
            if not data_id:
                raise HTTPException(status_code=400, detail="Query parameter 'data_id' is required for chart_type 'data-lineage'")
            try:
                content = tecton_app.data_lineage_flowchart(data_id)
                return {"chart_type": chart_type, "format": "mermaid", "content": content}
            except EntityNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
        elif chart_type in ("roadmap-gantt", "gantt"):
            res = tecton_app.export("mermaid", options={"diagram_type": "roadmap-gantt"})
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown chart_type '{chart_type}'. Supported types: time-matrix, capability-heatmap, tech-radar, data-lineage, roadmap-gantt",
            )

        return {
            "chart_type": chart_type,
            "format": "mermaid",
            "content": res.content,
        }

    # --- Open EA Ecosystem Connectors Endpoints ---
    @app.get("/api/v1/export/backstage", tags=["Connectors"])
    def export_backstage_catalog() -> dict[str, Any]:
        """Export architecture graph to Spotify Backstage Software Catalog entities."""
        res = tecton_app.export("backstage")
        entities = tecton_app.export_backstage_entities()
        return {
            "format": "yaml",
            "entities_count": len(entities),
            "content": res.content,
        }

    @app.get("/api/v1/export/archimate", tags=["Connectors"])
    def export_archimate_model(
        format: str = Query("xml", description="Response format: xml (raw) or json (envelope)"),
        dialect: str = Query("exchange", description="ArchiMate dialect: 'exchange' (Open Group standard) or 'archi' (Archi native)"),
    ) -> Any:
        """Export architecture graph to ArchiMate XML (Open Group standard or Archi native)."""
        res = tecton_app.export(dialect)
        if format == "json":
            return {
                "format": "xml",
                "dialect": dialect,
                "content": res.content,
            }
        return Response(content=res.content, media_type="application/xml")

    @app.get("/api/v1/export/archi", tags=["Connectors"])
    def export_archi_model() -> Any:
        """Export architecture graph to Archi native format (.archimate) for direct 1-click opening via File > Open."""
        res = tecton_app.export("archi")
        return Response(content=res.content, media_type="application/xml")

    return app
