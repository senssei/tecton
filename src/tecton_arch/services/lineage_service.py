"""Data Lineage & Interface Architecture Service orchestrator."""

from pathlib import Path
from tecton_arch.dsl.parser import C4EAMParser, CompiledGraph
from tecton_arch.dsl.schema import DataObjectDef, InterfaceDef
from tecton_arch.engines.lineage_engine import DataLineageReport, LineageEngine
from tecton_arch.exporters.mermaid import MermaidExporter


class LineageService:
    """Service orchestrating data object inventory, interface contracts, and lineage tracing."""

    def __init__(self, graph_or_path: CompiledGraph | Path | str) -> None:
        if isinstance(graph_or_path, CompiledGraph):
            self.graph = graph_or_path
        else:
            self.graph = C4EAMParser().parse_directory(graph_or_path)
        self.engine = LineageEngine()

    def list_data_objects(self) -> list[DataObjectDef]:
        """Return all business data objects in the architecture catalog."""
        return sorted(list(self.graph.data_objects.values()), key=lambda d: d.name)

    def list_interfaces(self) -> list[InterfaceDef]:
        """Return all communication interfaces and API contracts."""
        return sorted(list(self.graph.interfaces.values()), key=lambda i: i.name)

    def trace_lineage(self, data_object_id: str) -> DataLineageReport:
        """Trace end-to-end data trajectory and compliance risks."""
        return self.engine.trace_lineage(data_object_id, self.graph)

    def export_lineage_flowchart(
        self, data_object_id: str, title: str = "Data Lineage Trajectory"
    ) -> str:
        """Generate Mermaid flowchart diagram of the data flow."""
        report = self.trace_lineage(data_object_id)
        return MermaidExporter.to_data_lineage_flowchart(report, title=title)
