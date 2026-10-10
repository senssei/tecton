"""CLI subcommands for Technology Risk & Obsolescence Management (TRM)."""

from pathlib import Path
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tecton.dsl.schema import TechnologyStatus
from tecton.services.trm_service import TRMService

app = typer.Typer(name="trm", help="Technology Risk & Obsolescence Management (TRM) commands.")
console = Console()


def _resolve_source(source: str | None) -> Path:
    target = Path(source) if source else Path(".")
    if not target.exists():
        console.print(f"[bold red]Błąd: Ścieżka '{target}' nie istnieje.[/bold red]")
        raise typer.Exit(code=1)
    return target


@app.command("list")
def list_technologies(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """List technology standards, obsolescence milestones, and system adoption count."""
    target_path = _resolve_source(source)
    service = TRMService(target_path)
    report = service.evaluate_technologies()

    if not report.technologies:
        console.print("[yellow]Brak technologii zarejestrowanych w katalogu architektury.[/yellow]")
        return

    table = Table(title=f"Katalog Standardów Technologicznych ({report.total_technologies} technologii)")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Nazwa Technologii", style="bold cyan")
    table.add_column("Kategoria", style="magenta")
    table.add_column("Status Radaru", justify="center")
    table.add_column("Data EOL", justify="center")
    table.add_column("Aplikacje", justify="right")

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
                eol_str = f"[bold red]{t.eol_date} (PRZETERMINOWANE)[/bold red]"
            else:
                eol_str = f"[green]{t.eol_date}[/green] ({t.days_to_eol} dni)"

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
        f"Podsumowanie: [green]{report.approved_count} zatwierdzonych[/green], "
        f"[yellow]{report.deprecated_count} wycofywanych[/yellow], "
        f"[red]{report.prohibited_count} zakazanych[/red], "
        f"[bold red]{report.eol_count} przeterminowanych EOL[/bold red].\n"
    )


@app.command("blast-radius")
def calculate_blast_radius(
    technology_id: Annotated[str, typer.Argument(help="ID technologii do analizy promienia rażenia")],
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """Calculate direct and cascading blast radius if a technology fails or reaches EOL."""
    target_path = _resolve_source(source)
    service = TRMService(target_path)

    try:
        report = service.calculate_blast_radius(technology_id)
    except KeyError as e:
        console.print(f"[bold red]Błąd: {e}[/bold red]")
        raise typer.Exit(code=1)

    risk_style = "bold red" if report.risk_score >= 60 else "bold yellow" if report.risk_score >= 30 else "green"

    console.print(f"\n[bold]Analiza Promienia Rażenia (Blast Radius):[/bold] [cyan]{report.technology_name}[/cyan] ({report.technology_id})")
    console.print(Panel(
        f"[bold]Podsumowanie:[/bold] {report.summary}\n\n"
        f"• Status Technologii: [bold]{report.status.value.upper()}[/bold] "
        f"({'[bold red]⚠️ WYGASŁY EOL[/bold red]' if report.is_eol else '[green]Aktywny[/green]'})\n"
        f"• Najwyższa Naruszona Krytyczność: [bold magenta]{report.highest_criticality}[/bold magenta]\n"
        f"• Wyliczony Wskaźnik Ryzyka: [{risk_style}]{report.risk_score}/100.0[/{risk_style}]",
        title="Ocena Ryzyka Architektonicznego",
    ))

    table = Table(title="Kaskadowa Propagacja Zagrożenia w Architekturze")
    table.add_column("Poziom Wpływu", style="bold")
    table.add_column("Liczba", justify="right")
    table.add_column("Dotknięte Zasoby Architektury")

    direct_display = ", ".join(report.directly_affected_system_names) if report.directly_affected_system_names else "[dim]Brak[/dim]"
    cascading_display = ", ".join(report.cascading_system_names) if report.cascading_system_names else "[dim]Brak[/dim]"
    caps_display = ", ".join(report.compromised_capability_ids) if report.compromised_capability_ids else "[dim]Brak[/dim]"

    table.add_row("[bold red]Bezpośrednio Dotknięte Systemy[/bold red]", str(len(report.directly_affected_system_ids)), direct_display)
    table.add_row("[bold yellow]Kaskadowo Zależne Systemy[/bold yellow]", str(len(report.cascading_system_ids)), cascading_display)
    table.add_row("[bold cyan]Zagrożone Zdolności Biznesowe[/bold cyan]", str(len(report.compromised_capability_ids)), caps_display)

    console.print(table)
    console.print()


@app.command("export-radar")
def export_radar(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path (default stdout)")] = None,
) -> None:
    """Export Mermaid diagram of the Technology Radar."""
    target_path = _resolve_source(source)
    service = TRMService(target_path)
    chart = service.export_radar()

    if output:
        out_path = Path(output)
        out_path.write_text(chart, encoding="utf-8")
        console.print(f"[green]Radar technologii Mermaid zapisany w pliku:[/green] {out_path.resolve()}")
    else:
        console.print(chart)
