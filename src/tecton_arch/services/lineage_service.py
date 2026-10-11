"""Data Lineage & Interface Architecture Service orchestrator."""

from pathlib import Path
from datetime import date
from tecton_arch.dsl.parser import C4EAMParser, CompiledGraph
from tecton_arch.dsl.schema import DataObjectDef, InterfaceDef
from tecton_arch.engines.lineage_engine import DataLineageReport, LineageEngine
from tecton_arch.exporters.mermaid import MermaidExporter


class LineageService:
    """Service orchestrating data object inventory, interface contracts, and lineage tracing."""

    def __init__(self, graph_or_path: CompiledGraph | Path | str, config=None) -> None:
        if isinstance(graph_or_path, CompiledGraph):
            self.graph = graph_or_path
        else:
            from tecton_arch.core.config import TectonConfig
            config = config or TectonConfig.load(workspace_dir=Path(graph_or_path) if Path(graph_or_path).is_dir() else Path(graph_or_path).parent)
            self.graph = C4EAMParser(config=config).parse_directory(graph_or_path)
        self.config = config
        self.engine = LineageEngine()

    def list_data_objects(self) -> list[DataObjectDef]:
        """Return all business data objects in the architecture catalog."""
        return sorted(list(self.graph.data_objects.values()), key=lambda d: d.name)

    def list_interfaces(self) -> list[InterfaceDef]:
        """Return all communication interfaces and API contracts."""
        return sorted(list(self.graph.interfaces.values()), key=lambda i: i.name)

    def trace_lineage(self, data_object_id: str, as_of_date: date | None = None) -> DataLineageReport:
        """Trace end-to-end data trajectory and compliance risks."""
        return self.engine.trace_lineage(data_object_id, self.graph, as_of_date=as_of_date, config=self.config)

    def export_lineage_flowchart(
        self, data_object_id: str, title: str = "Data Lineage Trajectory", as_of_date: date | None = None
    ) -> str:
        """Generate Mermaid flowchart diagram of the data flow."""
        report = self.trace_lineage(data_object_id, as_of_date=as_of_date)
        return MermaidExporter.to_data_lineage_flowchart(report, title=title)
