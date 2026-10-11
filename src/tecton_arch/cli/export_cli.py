from datetime import date
from pathlib import Path
from tecton_arch.cli.catalog_cli import resolve_date
from tecton_arch.core.config import TectonConfig
from typing import Annotated, Optional
import typer
from rich.console import Console

from tecton_arch.application.app import TectonApp
from tecton_arch.portal.builder import PortalBuilder

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
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output YAML file path (defaults to stdout)")] = None,
) -> None:
    """Export architecture graph to Spotify Backstage Software Catalog YAML."""
    target_path = _resolve_source(source)
    app_instance = TectonApp(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    res = app_instance.export("backstage")
    for warning in res.warnings:
        Console(stderr=True).print(warning, markup=False)
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
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path (defaults to stdout)")] = None,
    format: Annotated[str, typer.Option("--format", "-f", help="Format: 'exchange' (Open Group XML) or 'archi' (Archi native .archimate)")] = "exchange",
    model_name: Annotated[str, typer.Option("--name", "-n", help="ArchiMate model name")] = "Tecton Architecture Model",
) -> None:
    """Export architecture graph to ArchiMate (Open Group standard XML or Archi native .archimate)."""
    target_path = _resolve_source(source)
    app_instance = TectonApp(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))

    # Auto-detect format if output extension is .archimate
    selected_format = "archi" if (output and output.endswith(".archimate")) or format.lower() == "archi" else "exchange"
    res = app_instance.export(selected_format, options={"model_name": model_name})
    for warning in res.warnings:
        Console(stderr=True).print(warning, markup=False)
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
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output .archimate file path (defaults to stdout)")] = None,
    model_name: Annotated[str, typer.Option("--name", "-n", help="Model name")] = "Tecton Architecture Model",
) -> None:
    """Export architecture graph to Archi tool native format (.archimate) for direct 1-click opening via File > Open."""
    target_path = _resolve_source(source)
    app_instance = TectonApp(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    res = app_instance.export("archi", options={"model_name": model_name})
    for warning in res.warnings:
        Console(stderr=True).print(warning, markup=False)
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
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output_dir: Annotated[str, typer.Option("--output-dir", "-o", help="Target directory for generated portal (defaults to dist/)")] = "dist",
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for snapshot")] = None,
) -> None:
    """Export Architecture Intelligence Web Portal self-contained offline HTML snapshot."""
    target_path = _resolve_source(source)
    eval_date = resolve_date(as_of_date)
    app_instance = TectonApp(target_path, as_of_date=eval_date, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    out_file = PortalBuilder.export_portal(app_instance, output_dir, as_of_date=eval_date)
    console.print(f"[bold green]✓ Successfully exported living Architecture Portal to '{out_file}'[/bold green]")


@app.command("report")
def export_report(
    source: Annotated[str, typer.Option("--source", "-s")] = ".",
    format_name: Annotated[str, typer.Option("--format", "-f", help="mermaid or markdown")] = "markdown",
    diagram_type: Annotated[str, typer.Option("--diagram-type")] = "time-matrix",
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o")] = None,
):
    from tecton_arch.cli.catalog_cli import make_app
    if format_name not in ("mermaid", "markdown"):
        raise typer.BadParameter("Format must be mermaid or markdown")
    model = make_app(source, as_of_date, config_path)
    result = model.export(format_name, {"diagram_type": diagram_type})
    if output:
        Path(output).write_text(result.content, encoding="utf-8")
    else:
        console.print(result.content, markup=False)
