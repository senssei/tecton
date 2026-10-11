"""CLI subcommands for Data Architecture, Interface Contracts, and Lineage (data)."""

from pathlib import Path
from tecton_arch.cli.catalog_cli import resolve_date
from tecton_arch.core.config import TectonConfig
from datetime import date
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tecton_arch.dsl.schema import DataClassification
from tecton_arch.services.lineage_service import LineageService

app = typer.Typer(name="data", help="Data Architecture, Interface Contracts, and Lineage commands.")
console = Console()


def _resolve_source(source: str | None) -> Path:
    target = Path(source) if source else Path(".")
    if not target.exists():
        console.print(f"[bold red]Error: Path '{target}' does not exist.[/bold red]")
        raise typer.Exit(code=1)
    return target


@app.command("list")
def list_data_objects(
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """List business data objects with privacy and compliance classifications."""
    target_path = _resolve_source(source)
    service = LineageService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    data_objects = service.list_data_objects()

    if not data_objects:
        console.print("[yellow]No business data objects registered in catalog.[/yellow]")
        return

    table = Table(title=f"Business Data Objects Catalog ({len(data_objects)} entities)")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Data Entity Name", style="bold cyan")
    table.add_column("Classification", justify="center")
    table.add_column("Business Owner", style="magenta")
    table.add_column("Description", style="dim")

    for obj in data_objects:
        color = "green"
        if obj.classification in (DataClassification.RESTRICTED_PII, DataClassification.PCI_DSS):
            color = "bold red"
        elif obj.classification == DataClassification.CONFIDENTIAL:
            color = "bold yellow"
        elif obj.classification == DataClassification.INTERNAL:
            color = "bold cyan"

        table.add_row(
            obj.id,
            obj.name,
            f"[{color}]{obj.classification.value}[/{color}]",
            obj.owner or "-",
            obj.description or "-",
        )

    console.print()
    console.print(table)
    console.print()


@app.command("interfaces")
def list_interfaces(
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """List communication interfaces, protocols, and carried data contracts."""
    target_path = _resolve_source(source)
    service = LineageService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    interfaces = service.list_interfaces()

    if not interfaces:
        console.print("[yellow]No interfaces registered in catalog.[/yellow]")
        return

    table = Table(title=f"Interfaces & API Contracts Catalog ({len(interfaces)} interfaces)")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Interface Name", style="bold cyan")
    table.add_column("Protocol", justify="center", style="magenta")
    table.add_column("Provider System", style="bold green")
    table.add_column("Consumer Systems")
    table.add_column("Carried Data Objects")

    for iface in interfaces:
        consumers_str = ", ".join(iface.consumer_system_ids) or "[dim]-[/dim]"
        data_str = ", ".join(iface.data_objects) or "[dim]-[/dim]"
        table.add_row(
            iface.id,
            iface.name,
            iface.protocol,
            iface.provider_system_id,
            consumers_str,
            data_str,
        )

    console.print()
    console.print(table)
    console.print()


@app.command("lineage")
def trace_lineage(
    data_object_id: Annotated[str, typer.Argument(help="ID of data object to trace flow trajectory")],
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Evaluation date YYYY-MM-DD")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """Trace end-to-end data lineage trajectory and compliance risks across systems."""
    target_path = _resolve_source(source)
    service = LineageService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))

    try:
        report = service.trace_lineage(data_object_id, as_of_date=resolve_date(as_of_date))
    except KeyError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)

    status_color = "bold red" if report.compliance_risks else "yellow"
    status_label = (f"DETECTED {report.risk_count} modeled risks" if report.compliance_risks else report.assessment_status.replace("_", " ")) + " (declared flows only)"

    console.print(f"\n[bold]Data Lineage Trajectory:[/bold] [cyan]{report.data_object_name}[/cyan] ({report.data_object_id})")
    console.print(Panel(
        f"• Classification: [bold]{report.classification.value}[/bold]\n"
        f"• Owner: {report.owner or '[dim]None[/dim]'}\n"
        f"• Source Systems (Producers): [bold green]{', '.join(report.producers) or '-'}[/bold green]\n"
        f"• Receiving Systems (Consumers): [bold cyan]{', '.join(report.consumers) or '-'}[/bold cyan]\n"
        f"• Compliance Audit Status: [{status_color}]{status_label}[/{status_color}]",
        title="Data Entity Summary",
    ))

    if report.compliance_risks:
        console.print("\n[bold red]🚨 Detected Compliance & Privacy Risks:[/bold red]")
        risk_table = Table()
        risk_table.add_column("Severity", justify="center")
        risk_table.add_column("Rule", style="dim")
        risk_table.add_column("System", style="bold")
        risk_table.add_column("Message")

        for r in report.compliance_risks:
            sev_color = "[bold red]CRITICAL[/bold red]" if r["severity"] == "CRITICAL" else "[bold yellow]HIGH[/bold yellow]" if r["severity"] == "HIGH" else "[yellow]MED[/yellow]"
            risk_table.add_row(sev_color, r["rule"], r["system_name"], r["message"])
        console.print(risk_table)

    if report.flow_edges:
        console.print("\n[bold]Cascading Data Flow Edges in Architecture:[/bold]")
        flow_table = Table()
        flow_table.add_column("Source", style="green")
        flow_table.add_column("Channel / Interface", style="bold magenta", justify="center")
        flow_table.add_column("Target", style="cyan")

        for edge in report.flow_edges:
            flow_table.add_row(
                edge.source_system_name,
                f"{edge.channel_name} [{edge.protocol}]",
                edge.target_system_name,
            )
        console.print(flow_table)
    else:
        console.print("\n[dim]No transmission flow edges detected for this data object.[/dim]")

    console.print()


@app.command("export-lineage")
def export_lineage(
    data_object_id: Annotated[str, typer.Argument(help="ID of data object to generate diagram for")],
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Evaluation date YYYY-MM-DD")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path")] = None,
) -> None:
    """Export Mermaid flowchart diagram of the end-to-end data lineage trajectory."""
    target_path = _resolve_source(source)
    service = LineageService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))

    try:
        chart = service.export_lineage_flowchart(data_object_id, as_of_date=resolve_date(as_of_date))
    except KeyError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)

    if output:
        out_path = Path(output)
        out_path.write_text(chart, encoding="utf-8")
        console.print(f"[green]Mermaid diagram saved to file:[/green] {out_path.resolve()}")
    else:
        console.print(chart)
