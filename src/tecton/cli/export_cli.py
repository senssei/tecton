"""CLI subcommands for Open EA Exporters (export)."""

from pathlib import Path
from typing import Annotated, Optional
import typer
from rich.console import Console

from tecton.application.app import TectonApp
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
    app_instance = TectonApp(target_path)
    res = app_instance.export("backstage")
    yaml_content = res.content

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
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path (defaults to stdout)")] = None,
    format: Annotated[str, typer.Option("--format", "-f", help="Format: 'exchange' (Open Group XML) or 'archi' (Archi native .archimate)")] = "exchange",
    model_name: Annotated[str, typer.Option("--name", "-n", help="ArchiMate model name")] = "Tecton Architecture Model",
) -> None:
    """Export architecture graph to ArchiMate (Open Group standard XML or Archi native .archimate)."""
    target_path = _resolve_source(source)
    app_instance = TectonApp(target_path)

    # Auto-detect format if output extension is .archimate
    selected_format = "archi" if (output and output.endswith(".archimate")) or format.lower() == "archi" else "exchange"
    res = app_instance.export(selected_format, options={"model_name": model_name})
    content = res.content
    desc = "Archi Native XML (.archimate)" if selected_format == "archi" else "ArchiMate Open Exchange XML"

    if output:
        out_file = Path(output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(content, encoding="utf-8")
        console.print(f"[bold green]✓ Successfully exported {desc} to '{output}'[/bold green]")
    else:
        console.print(content)


@app.command("archi")
def export_archi(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output .archimate file path (defaults to stdout)")] = None,
    model_name: Annotated[str, typer.Option("--name", "-n", help="Model name")] = "Tecton Architecture Model",
) -> None:
    """Export architecture graph to Archi tool native format (.archimate) for direct 1-click opening via File > Open."""
    target_path = _resolve_source(source)
    app_instance = TectonApp(target_path)
    res = app_instance.export("archi", options={"model_name": model_name})
    content = res.content

    if output:
        out_file = Path(output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(content, encoding="utf-8")
        console.print(f"[bold green]✓ Successfully exported native Archi model to '{output}'[/bold green]")
    else:
        console.print(content)


@app.command("portal")
def export_portal(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output_dir: Annotated[str, typer.Option("--output-dir", "-o", help="Target directory for generated portal (defaults to dist/)")] = "dist",
) -> None:
    """Export self-contained, offline-first Architecture Intelligence Web Portal HTML bundle."""
    target_path = _resolve_source(source)
    app_instance = TectonApp(target_path)
    out_file = PortalBuilder.export_portal(app_instance, output_dir)
    console.print(f"[bold green]✓ Successfully exported living Architecture Portal to '{out_file}'[/bold green]")
