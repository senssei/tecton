"""Unified exporter interface and registry for Tecton architecture models."""

from abc import ABC, abstractmethod
from typing import Any
from tecton.application.dto import ExportResultDto
from tecton.application.exceptions import ExportError
from tecton.connectors.archimate import ArchiMateConnector
from tecton.connectors.backstage import BackstageConnector
from tecton.dsl.parser import CompiledGraph
from tecton.exporters.markdown import MarkdownExporter
from tecton.exporters.mermaid import MermaidExporter


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
        if dtype in ("time-matrix", "time"):
            content = MermaidExporter.to_time_quadrant_chart(graph.get_applications())
        elif dtype in ("bcm-heatmap", "bcm", "heatmap"):
            from tecton.services.bcm_service import BCMService
            content = BCMService(graph).export_heatmap()
        elif dtype in ("tech-radar", "trm", "radar"):
            from tecton.services.trm_service import TRMService
            content = TRMService(graph).export_radar()
        elif dtype in ("roadmap-gantt", "roadmap", "gantt"):
            from tecton.services.roadmap_service import RoadmapService
            content = RoadmapService(graph).export_gantt()
        else:
            content = MermaidExporter.to_time_quadrant_chart(graph.get_applications())

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
        content = MarkdownExporter.export_executive_summary(graph)
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
