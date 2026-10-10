"""CLI subcommands for Architecture Quality Gate and Graph Linter (validate/lint)."""

import json
from pathlib import Path
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.table import Table

from tecton.dsl.linter import GraphLinter, LintSeverity
from tecton.dsl.parser import C4EAMParser

console = Console()


def run_validation(
    path: Path,
    strict: bool = False,
    output_format: str = "table",
) -> None:
    """Validate architecture DSL workspace and enforce CI/CD quality gate."""
    target_path = path.resolve()
    if not target_path.exists():
        console.print(f"[bold red]Błąd: Ścieżka '{target_path}' nie istnieje.[/bold red]")
        raise typer.Exit(code=1)

    parser = C4EAMParser()
    try:
        graph = parser.parse_directory(target_path)
    except Exception as e:
        console.print(f"[bold red]Krytyczny błąd parsowania manifestu: {e}[/bold red]")
        raise typer.Exit(code=1)

    linter = GraphLinter()
    report = linter.lint(graph)

    if output_format.lower() == "json":
        data = {
            "valid": report.is_valid and (report.warning_count == 0 if strict else True),
            "files_scanned": len(graph.files_parsed),
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "rule": issue.rule,
                    "entity_id": issue.entity_id,
                    "message": issue.message,
                    "file_origin": issue.file_origin,
                }
                for issue in report.issues
            ],
        }
        console.print_json(json.dumps(data))
        if report.has_errors or (strict and report.warning_count > 0):
            raise typer.Exit(code=1)
        raise typer.Exit(code=0)

    # Table format
    console.print("\n[bold cyan]Tecton Architecture Quality Gate & Graph Linter[/bold cyan]")
    console.print(
        f"Skanowanie katalogu: [dim]{target_path}[/dim] "
        f"({len(graph.files_parsed)} plików, "
        f"{len(graph.capabilities)} zdolności, "
        f"{len(graph.systems)} systemów, "
        f"{len(graph.containers)} kontenerów, "
        f"{len(graph.relationships)} relacji, "
        f"{len(graph.technologies)} technologii)"
    )

    if not report.issues:
        console.print(
            "\n[bold green]✓ Architektura poprawna.[/bold green] "
            "Brak błędów integralności referencyjnej, cykli ani naruszeń cyklu życia.\n"
        )
        return

    table = Table(title="Wykryte Problemy Architektoniczne")
    table.add_column("Severity", justify="center", no_wrap=True)
    table.add_column("Rule", style="dim", no_wrap=True)
    table.add_column("Entity ID", style="bold cyan")
    table.add_column("Komunikat")
    table.add_column("Plik Źródłowy", style="dim")

    for issue in report.issues:
        sev_style = (
            "[bold red]ERROR[/bold red]"
            if issue.severity == LintSeverity.ERROR
            else "[bold yellow]WARN[/bold yellow]"
        )
        file_display = Path(issue.file_origin).name if issue.file_origin else "-"
        table.add_row(
            sev_style,
            issue.rule,
            issue.entity_id or "-",
            issue.message,
            file_display,
        )

    console.print()
    console.print(table)
    console.print(
        f"\nPodsumowanie: [bold red]{report.error_count} błędów[/bold red], "
        f"[bold yellow]{report.warning_count} ostrzeżeń[/bold yellow]."
    )

    # Determine exit code for CI/CD gates
    if report.has_errors:
        console.print("[bold red]❌ BRAMKA CI/CD ZABLOKOWANA: Wykryto błędy krytyczne w grafie architektury.[/bold red]")
        raise typer.Exit(code=1)

    if strict and report.warning_count > 0:
        console.print("[bold red]❌ BRAMKA CI/CD ZABLOKOWANA: Tryb --strict wykrył ostrzeżenia.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]✓ BRAMKA CI/CD ZATWIERDZONA (Exit code 0).[/bold green]\n")


def validate_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Ścieżka do katalogu architektury lub pliku manifestu",
            exists=True,
            file_okay=True,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
    strict: Annotated[
        bool,
        typer.Option("--strict", "-s", help="Traktuj ostrzeżenia jako błędy krytyczne (exit code 1)"),
    ] = False,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Format wyjścia: table lub json"),
    ] = "table",
) -> None:
    """Validate architecture DSL workspace and enforce referential integrity & DAG invariants."""
    run_validation(path=path, strict=strict, output_format=output_format)
