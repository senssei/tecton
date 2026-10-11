"""Transformation Roadmapping Service orchestrator."""

from datetime import date
from pathlib import Path
from tecton_arch.dsl.parser import C4EAMParser, CompiledGraph
from tecton_arch.dsl.schema import PlateauDef, WorkPackageDef
from tecton_arch.engines.roadmap_engine import (
    PlateauComparison,
    PlateauState,
    RoadmapAnalysisReport,
    RoadmapEngine,
)


class RoadmapService:
    """Service orchestrating plateaus, work packages, roadmap analysis, and Gantt charts."""

    def __init__(self, graph_or_path: CompiledGraph | Path | str) -> None:
        if isinstance(graph_or_path, CompiledGraph):
            self.graph = graph_or_path
        else:
            self.graph = C4EAMParser().parse_directory(graph_or_path)
        self.engine = RoadmapEngine(self.graph)

    def list_plateaus(self) -> list[PlateauDef]:
        """Return all architecture plateaus ordered chronologically and by predecessor."""
        return self.engine.get_ordered_plateaus()

    def list_work_packages(self) -> list[WorkPackageDef]:
        """Return all transformation work packages."""
        return sorted(
            list(self.graph.work_packages.values()),
            key=lambda w: (
                0 if w.start_date else 1,
                str(w.start_date) if w.start_date else "9999-99-99",
                w.name,
            ),
        )

    def evaluate_plateau(self, plateau_id: str, as_of_date: date | None = None) -> PlateauState:
        """Evaluate architectural state, active systems, and capabilities at a given plateau."""
        return self.engine.evaluate_plateau_state(plateau_id, as_of_date=as_of_date)

    def compare_plateaus(self, from_plateau_id: str, to_plateau_id: str, as_of_date: date | None = None) -> PlateauComparison:
        """Calculate As-Is vs To-Be delta, capability gains/losses, and tech debt reduction."""
        return self.engine.compare_plateaus(from_plateau_id, to_plateau_id, as_of_date=as_of_date)

    def analyze(self, as_of_date: date | None = None) -> RoadmapAnalysisReport:
        """Perform comprehensive roadmap health, timeline, and transitional gap audit."""
        return self.engine.analyze_roadmap(as_of_date=as_of_date)

    def export_gantt(self, title: str = "Enterprise Architecture Transformation Roadmap", as_of_date: date | None = None) -> str:
        """Generate Mermaid Gantt chart visualizing plateaus and transformation initiatives."""
        return self.engine.export_gantt_mermaid(title=title, as_of_date=as_of_date)
