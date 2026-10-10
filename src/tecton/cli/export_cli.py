"""CLI subcommands for Open EA Exporters (export)."""

from pathlib import Path
from typing import Annotated, Optional
import typer
from rich.console import Console

from tecton.connectors.archimate import ArchiMateConnector
from tecton.connectors.backstage import BackstageConnector
from tecton.dsl.parser import C4EAMParser
from tecton.portal.builder import PortalBuilder

app = typer.Typer(name="export", help="Export architecture models to external EA ecosystems (Backstage, ArchiMate).")
console = Console()


def _resolve_source(source: str | None) -> Path:
    target = Path(source) if source else Path(".")
    if not target.exists():
        console.print(f"[bold red]Error: Path '{target}' does not exist.[/bold red]")
        raise typer.Exit(code=1)
    return target


@app.command("backstage")
def export_backstage(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output YAML file path (defaults to stdout)")] = None,
) -> None:
    """Export architecture graph to Spotify Backstage Software Catalog YAML."""
    target_path = _resolve_source(source)
    graph = C4EAMParser().parse_directory(target_path)
    yaml_content = BackstageConnector.export_yaml(graph)

    if output:
        out_file = Path(output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(yaml_content, encoding="utf-8")
        console.print(f"[bold green]✓ Successfully exported Backstage catalog to '{output}'[/bold green]")
    else:
        console.print(yaml_content)


@app.command("archimate")
def export_archimate(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output XML file path (defaults to stdout)")] = None,
    model_name: Annotated[str, typer.Option("--name", "-n", help="ArchiMate model name")] = "Tecton Architecture Model",
) -> None:
    """Export architecture graph to The Open Group ArchiMate Model Exchange XML."""
    target_path = _resolve_source(source)
    graph = C4EAMParser().parse_directory(target_path)
    xml_content = ArchiMateConnector.export_xml(graph, model_name=model_name)

    if output:
        out_file = Path(output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(xml_content, encoding="utf-8")
        console.print(f"[bold green]✓ Successfully exported ArchiMate Open Exchange XML to '{output}'[/bold green]")
    else:
        console.print(xml_content)


@app.command("portal")
def export_portal(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output_dir: Annotated[str, typer.Option("--output-dir", "-o", help="Target directory for generated portal (defaults to dist/)")] = "dist",
) -> None:
    """Export self-contained, offline-first Architecture Intelligence Web Portal HTML bundle."""
    target_path = _resolve_source(source)
    graph = C4EAMParser().parse_directory(target_path)
    out_file = PortalBuilder.export_portal(graph, output_dir)
    console.print(f"[bold green]✓ Successfully exported living Architecture Portal to '{out_file}'[/bold green]")

