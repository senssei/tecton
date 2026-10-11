"""Unified exporter interface and registry for Tecton architecture models."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any
from tecton_arch.application.dto import ExportResultDto
from tecton_arch.application.exceptions import ExportError
from tecton_arch.connectors.archimate import ArchiMateConnector
from tecton_arch.connectors.backstage import BackstageConnector
from tecton_arch.dsl.parser import CompiledGraph
from tecton_arch.exporters.markdown import MarkdownExporter
from tecton_arch.exporters.mermaid import MermaidExporter


class Exporter(ABC):
    """Abstract base class for all architectural artifact exporters."""

    name: str
    media_type: str
    file_extension: str
    description: str

    @abstractmethod
    def export(self, graph: CompiledGraph, options: dict[str, Any] | None = None) -> ExportResultDto:
        """Serialize compiled architecture graph into the target artifact representation."""


class ArchiMateExchangeExporter(Exporter):
    name = "exchange"
    media_type = "application/xml"
    file_extension = ".xml"
    description = "ArchiMate 3.0/3.1 Open Exchange Standard XML format"

    def export(self, graph: CompiledGraph, options: dict[str, Any] | None = None) -> ExportResultDto:
        opts = options or {}
        model_name = opts.get("model_name", "Tecton Architecture Model")
        content = ArchiMateConnector.export_xml(graph, model_name=model_name)
        return ExportResultDto(
            format=self.name,
            content=content,
            media_type=self.media_type,
            file_extension=self.file_extension,
        )


class ArchiNativeExporter(Exporter):
    name = "archi"
    media_type = "application/xml"
    file_extension = ".archimate"
    description = "Archi tool native XML format (.archimate) for direct 1-click opening"

    def export(self, graph: CompiledGraph, options: dict[str, Any] | None = None) -> ExportResultDto:
        opts = options or {}
        model_name = opts.get("model_name", "Tecton Architecture Model")
        content = ArchiMateConnector.export_archi_xml(graph, model_name=model_name)
        return ExportResultDto(
            format=self.name,
            content=content,
            media_type=self.media_type,
            file_extension=self.file_extension,
        )


class BackstageExporter(Exporter):
    name = "backstage"
    media_type = "application/yaml"
    file_extension = ".yaml"
    description = "Spotify Backstage Software Catalog multi-document YAML"

    def export(self, graph: CompiledGraph, options: dict[str, Any] | None = None) -> ExportResultDto:
        content = BackstageConnector.export_yaml(graph)
        return ExportResultDto(
            format=self.name,
            content=content,
            media_type=self.media_type,
            file_extension=self.file_extension,
        )


class MermaidExporterAdapter(Exporter):
    name = "mermaid"
    media_type = "text/vnd.mermaid"
    file_extension = ".mmd"
    description = "Mermaid living architecture diagram syntax"

    def export(self, graph: CompiledGraph, options: dict[str, Any] | None = None) -> ExportResultDto:
        opts = options or {}
        dtype = str(opts.get("diagram_type", "time-matrix")).lower()
        as_of = opts.get("as_of_date")
        if isinstance(as_of, str):
            try:
                as_of = date.fromisoformat(as_of)
            except Exception:
                as_of = None

        if dtype in ("time-matrix", "time"):
            content = MermaidExporter.to_time_quadrant_chart(graph.get_applications(as_of_date=as_of))
        elif dtype in ("bcm-heatmap", "bcm", "heatmap", "capability-heatmap"):
            from tecton_arch.services.bcm_service import BCMService
            title = opts.get("title", "Business Capability Realization Heatmap")
            content = BCMService(graph).export_heatmap(title=title, as_of_date=as_of)
        elif dtype in ("tech-radar", "trm", "radar"):
            from tecton_arch.services.trm_service import TRMService
            title = opts.get("title", "Technology Standards & Obsolescence Radar")
            content = TRMService(graph).export_radar(title=title, as_of_date=as_of)
        elif dtype in ("roadmap-gantt", "roadmap", "gantt"):
            from tecton_arch.services.roadmap_service import RoadmapService
            title = opts.get("title", "Enterprise Architecture Transformation Roadmap")
            content = RoadmapService(graph).export_gantt(title=title, as_of_date=as_of)
        else:
            content = MermaidExporter.to_time_quadrant_chart(graph.get_applications(as_of_date=as_of))

        return ExportResultDto(
            format=self.name,
            content=content,
            media_type=self.media_type,
            file_extension=self.file_extension,
        )


class MarkdownExporterAdapter(Exporter):
    name = "markdown"
    media_type = "text/markdown"
    file_extension = ".md"
    description = "Human-readable architecture executive report in Markdown"

    def export(self, graph: CompiledGraph, options: dict[str, Any] | None = None) -> ExportResultDto:
        opts = options or {}
        as_of = opts.get("as_of_date")
        if isinstance(as_of, str):
            try:
                as_of = date.fromisoformat(as_of)
            except Exception:
                as_of = None

        from tecton_arch.services.apm_service import APMService
        from tecton_arch.adapters.in_memory import InMemoryRepositoryAdapter
        apps = graph.get_applications(as_of_date=as_of)
        repo = InMemoryRepositoryAdapter(apps)
        service = APMService(repo)
        result = service.analyze(as_of_date=as_of)
        content = MarkdownExporter.generate_apm_report(
            applications=result.applications,
            time_classifications=result.time_classifications,
            redundancy_clusters=result.redundancy_clusters,
            lifecycle_report=result.lifecycle_report,
        )
        return ExportResultDto(
            format=self.name,
            content=content,
            media_type=self.media_type,
            file_extension=self.file_extension,
        )


class ExporterRegistry:
    """Registry managing available architecture exporters and format resolution."""

    def __init__(self) -> None:
        self._exporters: dict[str, Exporter] = {}

    def register(self, exporter: Exporter) -> None:
        self._exporters[exporter.name.lower()] = exporter

    def get(self, name: str) -> Exporter:
        key = name.lower()
        # Aliases for backward compatibility
        if key in ("archimate", "xml"):
            key = "exchange"
        if key in ("yaml", "backstage-yaml"):
            key = "backstage"

        if key not in self._exporters:
            available = ", ".join(sorted(self._exporters.keys()))
            raise ExportError(f"Unsupported export format '{name}'. Available formats: {available}")
        return self._exporters[key]

    def list_formats(self) -> list[str]:
        return sorted(self._exporters.keys())

    @classmethod
    def default(cls) -> "ExporterRegistry":
        reg = cls()
        reg.register(ArchiMateExchangeExporter())
        reg.register(ArchiNativeExporter())
        reg.register(BackstageExporter())
        reg.register(MermaidExporterAdapter())
        reg.register(MarkdownExporterAdapter())
        return reg
