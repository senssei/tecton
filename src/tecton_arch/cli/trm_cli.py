from datetime import date
from pathlib import Path
from tecton_arch.cli.catalog_cli import resolve_date
from tecton_arch.core.config import TectonConfig
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tecton_arch.dsl.schema import TechnologyStatus
from tecton_arch.services.trm_service import TRMService

app = typer.Typer(name="trm", help="Technology Risk & Obsolescence Management (TRM) commands.")
console = Console()


def _resolve_source(source: str | None) -> Path:
    target = Path(source) if source else Path(".")
    if not target.exists():
        console.print(f"[bold red]Error: Path '{target}' does not exist.[/bold red]")
        raise typer.Exit(code=1)
    return target


@app.command("list")
def list_technologies(
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for EOL obsolescence")] = None,
) -> None:
    """List technology standards, obsolescence milestones, and system adoption count."""
    target_path = _resolve_source(source)
    service = TRMService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    eval_date = resolve_date(as_of_date)
    report = service.evaluate_technologies(as_of_date=eval_date)

    if not report.technologies:
        console.print("[yellow]No technologies registered in architecture catalog.[/yellow]")
        return

    title = f"Technology Standards Catalog ({report.total_technologies} technologies)"
    if as_of_date:
        title += f" [As of: {as_of_date}]"
    table = Table(title=title)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Technology Name", style="bold cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Radar Status", justify="center")
    table.add_column("EOL Date", justify="center")
    table.add_column("Applications", justify="right")

    for t in report.technologies:
        # Color coding status
        status_color = "white"
        if t.status == TechnologyStatus.APPROVED:
            status_color = "bold green"
        elif t.status == TechnologyStatus.UNDER_EVALUATION:
            status_color = "bold cyan"
        elif t.status == TechnologyStatus.DEPRECATED:
            status_color = "bold yellow"
        elif t.status == TechnologyStatus.PROHIBITED:
            status_color = "bold red"

        eol_str = "-"
        if t.eol_date:
            if t.is_eol:
                eol_str = f"[bold red]{t.eol_date} (EXPIRED)[/bold red]"
            else:
                eol_str = f"[green]{t.eol_date}[/green] ({t.days_to_eol} days)"

        table.add_row(
            t.id,
            t.name,
            t.category or "-",
            f"[{status_color}]{t.status.value.upper()}[/{status_color}]",
            eol_str,
            str(t.realizing_systems_count),
        )

    console.print()
    console.print(table)
    console.print(
        f"Summary: [green]{report.approved_count} approved[/green], "
        f"[yellow]{report.deprecated_count} deprecated[/yellow], "
        f"[red]{report.prohibited_count} prohibited[/red], "
        f"[bold red]{report.eol_count} past EOL[/bold red].\n"
    )


@app.command("blast-radius")
def calculate_blast_radius(
    technology_id: Annotated[str, typer.Argument(help="Technology ID to evaluate blast radius")],
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for EOL obsolescence")] = None,
) -> None:
    """Calculate direct and cascading blast radius if a technology fails or reaches EOL."""
    target_path = _resolve_source(source)
    service = TRMService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    eval_date = resolve_date(as_of_date)

    try:
        report = service.calculate_blast_radius(technology_id, as_of_date=eval_date)
    except KeyError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)

    risk_style = "bold red" if report.risk_score >= 60 else "bold yellow" if report.risk_score >= 30 else "green"

    date_str = f" [As of: {as_of_date}]" if as_of_date else ""
    console.print(f"\n[bold]Blast Radius Impact Analysis:[/bold] [cyan]{report.technology_name}[/cyan] ({report.technology_id}){date_str}")
    console.print(Panel(
        f"[bold]Summary:[/bold] {report.summary}\n\n"
        f"• Technology Status: [bold]{report.status.value.upper()}[/bold] "
        f"({'[bold red]⚠️ EXPIRED EOL[/bold red]' if report.is_eol else '[green]Active[/green]'})\n"
        f"• Highest Impacted Criticality: [bold magenta]{report.highest_criticality}[/bold magenta]\n"
        f"• Calculated Risk Score: [{risk_style}]{report.risk_score}/100.0[/{risk_style}]",
        title="Architectural Risk Assessment",
    ))

    table = Table(title="Cascading Architecture Blast Radius Propagation")
    table.add_column("Impact Level", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Impacted Architecture Assets")

    direct_display = ", ".join(report.directly_affected_system_names) if report.directly_affected_system_names else "[dim]None[/dim]"
    cascading_display = ", ".join(report.cascading_system_names) if report.cascading_system_names else "[dim]None[/dim]"
    caps_display = ", ".join(report.compromised_capability_ids) if report.compromised_capability_ids else "[dim]None[/dim]"

    table.add_row("[bold red]Directly Impacted Systems[/bold red]", str(len(report.directly_affected_system_ids)), direct_display)
    table.add_row("[bold yellow]Cascading Dependent Systems[/bold yellow]", str(len(report.cascading_system_ids)), cascading_display)
    table.add_row("[bold cyan]Compromised Business Capabilities[/bold cyan]", str(len(report.compromised_capability_ids)), caps_display)

    console.print(table)
    console.print()


@app.command("export-radar")
def export_radar(
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path (default stdout)")] = None,
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for EOL obsolescence")] = None,
) -> None:
    """Export Mermaid diagram of the Technology Radar."""
    target_path = _resolve_source(source)
    service = TRMService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    eval_date = resolve_date(as_of_date)
    chart = service.export_radar(as_of_date=eval_date)

    if output:
        out_path = Path(output)
        out_path.write_text(chart, encoding="utf-8")
        console.print(f"[green]Mermaid Technology Radar saved to file:[/green] {out_path.resolve()}")
    else:
        console.print(chart)
