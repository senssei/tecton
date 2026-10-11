"""Business Capability Management (BCM) Service orchestrator."""

from datetime import date
from pathlib import Path
from tecton_arch.dsl.parser import C4EAMParser, CompiledGraph
from tecton_arch.engines.bcm_engine import BCMEngine, BCMReport
from tecton_arch.exporters.mermaid import MermaidExporter


class BCMService:
    """Service orchestrating business capability realization analytics and visualizations."""

    def __init__(self, graph_or_path: CompiledGraph | Path | str, config=None) -> None:
        if isinstance(graph_or_path, CompiledGraph):
            self.graph = graph_or_path
        else:
            from tecton_arch.core.config import TectonConfig
            config = config or TectonConfig.load(workspace_dir=Path(graph_or_path) if Path(graph_or_path).is_dir() else Path(graph_or_path).parent)
            self.graph = C4EAMParser(config=config).parse_directory(graph_or_path)
        self.config = config
        self.engine = BCMEngine()

    def analyze(self, as_of_date: date | None = None) -> BCMReport:
        """Run complete capability coverage and health assessment."""
        apps = self.graph.get_applications(as_of_date=as_of_date)
        from tecton_arch.services.assessment import evaluate_applications
        return self.engine.analyze(self.graph.capabilities, evaluate_applications(apps, self.config, as_of_date))

    def export_heatmap(self, title: str = "Business Capability Realization Heatmap", as_of_date: date | None = None) -> str:
        """Generate Mermaid heatmap diagram representing capability health."""
        report = self.analyze(as_of_date=as_of_date)
        return MermaidExporter.to_capability_heatmap(report, title=title)
