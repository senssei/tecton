"""CLI subcommands for Data Architecture, Interface Contracts, and Lineage (data)."""

from pathlib import Path
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tecton.dsl.schema import DataClassification
from tecton.services.lineage_service import LineageService

app = typer.Typer(name="data", help="Data Architecture, Interface Contracts, and Lineage commands.")
console = Console()


def _resolve_source(source: str | None) -> Path:
    target = Path(source) if source else Path(".")
    if not target.exists():
        console.print(f"[bold red]Błąd: Ścieżka '{target}' nie istnieje.[/bold red]")
        raise typer.Exit(code=1)
    return target


@app.command("list")
def list_data_objects(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """List business data objects with privacy and compliance classifications."""
    target_path = _resolve_source(source)
    service = LineageService(target_path)
    data_objects = service.list_data_objects()

    if not data_objects:
        console.print("[yellow]Brak zarejestrowanych obiektów danych (Data Objects) w katalogu.[/yellow]")
        return

    table = Table(title=f"Katalog Obiektów Danych Biznesowych ({len(data_objects)} encji)")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Nazwa Encji Danych", style="bold cyan")
    table.add_column("Klasyfikacja Poufności", justify="center")
    table.add_column("Właściciel Biznesowy (Owner)", style="magenta")
    table.add_column("Opis", style="dim")

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
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """List communication interfaces, protocols, and carried data contracts."""
    target_path = _resolve_source(source)
    service = LineageService(target_path)
    interfaces = service.list_interfaces()

    if not interfaces:
        console.print("[yellow]Brak zarejestrowanych interfejsów (Interfaces) w katalogu.[/yellow]")
        return

    table = Table(title=f"Katalog Interfejsów & Kontraktów API ({len(interfaces)} interfejsów)")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Nazwa Interfejsu", style="bold cyan")
    table.add_column("Protokół", justify="center", style="magenta")
    table.add_column("System Dostawca (Provider)", style="bold green")
    table.add_column("Systemy Konsumenci (Consumers)")
    table.add_column("Przesyłane Obiekty Danych")

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
    data_object_id: Annotated[str, typer.Argument(help="ID obiektu danych do analizy ścieżki przepływu")],
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """Trace end-to-end data lineage trajectory and compliance risks across systems."""
    target_path = _resolve_source(source)
    service = LineageService(target_path)

    try:
        report = service.trace_lineage(data_object_id)
    except KeyError as e:
        console.print(f"[bold red]Błąd: {e}[/bold red]")
        raise typer.Exit(code=1)

    status_color = "bold green" if report.is_compliant else "bold red"
    status_label = "✅ ZGODNY (Brak Ryzyk Zgodności)" if report.is_compliant else f"🚨 WYKRYTO {report.risk_count} ZAGROŻEŃ ZGODNOŚCI"

    console.print(f"\n[bold]Ścieżka Pochodzenia Danych (Data Lineage):[/bold] [cyan]{report.data_object_name}[/cyan] ({report.data_object_id})")
    console.print(Panel(
        f"• Klasyfikacja: [bold]{report.classification.value}[/bold]\n"
        f"• Właściciel: {report.owner or '[dim]Brak[/dim]'}\n"
        f"• Systemy Źródłowe (Producers): [bold green]{', '.join(report.producers) or '-'}[/bold green]\n"
        f"• Systemy Odbiorcze (Consumers): [bold cyan]{', '.join(report.consumers) or '-'}[/bold cyan]\n"
        f"• Status Zgodności / Audytu: [{status_color}]{status_label}[/{status_color}]",
        title="Podsumowanie Encji Danych",
    ))

    if report.compliance_risks:
        console.print("\n[bold red]🚨 Wykryte Zagrożenia Zgodności & Prywatności Danych:[/bold red]")
        risk_table = Table()
        risk_table.add_column("Poziom", justify="center")
        risk_table.add_column("Reguła", style="dim")
        risk_table.add_column("System", style="bold")
        risk_table.add_column("Opis Naruszenia")

        for r in report.compliance_risks:
            sev_color = "[bold red]CRITICAL[/bold red]" if r["severity"] == "CRITICAL" else "[bold yellow]HIGH[/bold yellow]" if r["severity"] == "HIGH" else "[yellow]MED[/yellow]"
            risk_table.add_row(sev_color, r["rule"], r["system_name"], r["message"])
        console.print(risk_table)

    if report.flow_edges:
        console.print("\n[bold]Kaskadowe Krawędzie Przepływu Danych w Architekturze:[/bold]")
        flow_table = Table()
        flow_table.add_column("Nadawca (Source)", style="green")
        flow_table.add_column("Kanał / Interfejs", style="bold magenta", justify="center")
        flow_table.add_column("Odbiorca (Target)", style="cyan")

        for edge in report.flow_edges:
            flow_table.add_row(
                edge.source_system_name,
                f"{edge.channel_name} [{edge.protocol}]",
                edge.target_system_name,
            )
        console.print(flow_table)
    else:
        console.print("\n[dim]Brak wykrytych krawędzi przesyłania tego obiektu danych.[/dim]")

    console.print()


@app.command("export-lineage")
def export_lineage(
    data_object_id: Annotated[str, typer.Argument(help="ID obiektu danych do wygenerowania diagramu")],
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Ścieżka do pliku wyjściowego")] = None,
) -> None:
    """Export Mermaid flowchart diagram of the end-to-end data lineage trajectory."""
    target_path = _resolve_source(source)
    service = LineageService(target_path)

    try:
        chart = service.export_lineage_flowchart(data_object_id)
    except KeyError as e:
        console.print(f"[bold red]Błąd: {e}[/bold red]")
        raise typer.Exit(code=1)

    if output:
        out_path = Path(output)
        out_path.write_text(chart, encoding="utf-8")
        console.print(f"[green]Diagram Mermaid zapisany w pliku:[/green] {out_path.resolve()}")
    else:
        console.print(chart)
