"""Business Capability Management (BCM) Service orchestrator."""

from pathlib import Path
from tecton_arch.dsl.parser import C4EAMParser, CompiledGraph
from tecton_arch.engines.bcm_engine import BCMEngine, BCMReport
from tecton_arch.exporters.mermaid import MermaidExporter


class BCMService:
    """Service orchestrating business capability realization analytics and visualizations."""

    def __init__(self, graph_or_path: CompiledGraph | Path | str) -> None:
        if isinstance(graph_or_path, CompiledGraph):
            self.graph = graph_or_path
        else:
            self.graph = C4EAMParser().parse_directory(graph_or_path)
        self.engine = BCMEngine()

    def analyze(self) -> BCMReport:
        """Run complete capability coverage and health assessment."""
        apps = self.graph.get_applications()
        return self.engine.analyze(self.graph.capabilities, apps)

    def export_heatmap(self, title: str = "Business Capability Realization Heatmap") -> str:
        """Generate Mermaid heatmap diagram representing capability health."""
        report = self.analyze()
        return MermaidExporter.to_capability_heatmap(report, title=title)
