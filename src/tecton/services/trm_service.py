"""Technology Risk & Obsolescence Management (TRM) Service orchestrator."""

from pathlib import Path
from tecton.dsl.parser import C4EAMParser, CompiledGraph
from tecton.engines.trm_engine import BlastRadiusReport, TRMEngine, TRMReport
from tecton.exporters.mermaid import MermaidExporter


class TRMService:
    """Service orchestrating tech radar evaluations and blast radius impact assessments."""

    def __init__(self, graph_or_path: CompiledGraph | Path | str) -> None:
        if isinstance(graph_or_path, CompiledGraph):
            self.graph = graph_or_path
        else:
            self.graph = C4EAMParser().parse_directory(graph_or_path)
        self.engine = TRMEngine()

    def evaluate_technologies(self) -> TRMReport:
        """Assess entire technology catalog for EOL and status distribution."""
        return self.engine.evaluate_technologies(self.graph)

    def calculate_blast_radius(self, technology_id: str) -> BlastRadiusReport:
        """Trace direct and cascading blast radius for a given technology asset."""
        return self.engine.calculate_blast_radius(technology_id, self.graph)

    def export_radar(self, title: str = "Technology Standards & Obsolescence Radar") -> str:
        """Generate Mermaid flowchart representing technology standards by category."""
        report = self.evaluate_technologies()
        return MermaidExporter.to_tech_radar_flowchart(report.technologies, title=title)
