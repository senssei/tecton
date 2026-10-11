from datetime import date
import json
from pathlib import Path
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.table import Table

from tecton_arch.application.app import TectonApp

console = Console()


def run_validation(
    path: Path,
    strict: bool = False,
    output_format: str = "table",
    require_owner: bool = False,
    as_of_date: Optional[date] = None,
) -> None:
    """Validate architecture DSL workspace and enforce CI/CD quality gate."""
    target_path = path.resolve()
    if not target_path.exists():
        console.print(f"[bold red]Error: Path '{target_path}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    try:
        app = TectonApp(target_path, as_of_date=as_of_date)
        graph = app.graph
        report = app.validate(strict=False, as_of_date=as_of_date, require_owner=require_owner)
    except Exception as e:
        console.print(f"[bold red]Critical manifest parsing error: {e}[/bold red]")
        raise typer.Exit(code=1)

    if output_format.lower() == "json":
        data = {
            "valid": report.valid and (report.warning_count == 0 if strict else True),
            "as_of_date": str(as_of_date) if as_of_date else None,
            "files_scanned": len(graph.files_parsed),
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "issues": [
                {
                    "severity": issue.severity,
                    "rule": issue.rule,
                    "entity_id": issue.entity_id,
                    "message": issue.message,
                    "file_origin": issue.file_origin,
                }
                for issue in report.issues
            ],
        }
        console.print_json(json.dumps(data))
        if report.error_count > 0 or (strict and report.warning_count > 0):
            raise typer.Exit(code=1)
        raise typer.Exit(code=0)

    # Table format
    console.print("\n[bold cyan]Tecton Architecture Quality Gate & Graph Linter[/bold cyan]")
    if as_of_date:
        console.print(f"Evaluation Date: [bold magenta]{as_of_date}[/bold magenta]")
    console.print(
        f"Scanning directory: [dim]{target_path}[/dim] "
        f"({len(graph.files_parsed)} files, "
        f"{len(graph.capabilities)} capabilities, "
        f"{len(graph.systems)} systems, "
        f"{len(graph.containers)} containers, "
        f"{len(graph.relationships)} relationships, "
        f"{len(graph.technologies)} technologies)"
    )

    if not report.issues:
        console.print(
            "\n[bold green]✓ Architecture valid.[/bold green] "
            "No referential integrity errors, cycles, or lifecycle violations.\n"
        )
        return

    table = Table(title="Architectural Issues Detected")
    table.add_column("Severity", justify="center", no_wrap=True)
    table.add_column("Rule", style="dim", no_wrap=True)
    table.add_column("Entity ID", style="bold cyan")
    table.add_column("Message")
    table.add_column("Source File", style="dim")

    for issue in report.issues:
        sev_style = (
            "[bold red]ERROR[/bold red]"
            if issue.severity.upper() == "ERROR"
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
        f"\nSummary: [bold red]{report.error_count} errors[/bold red], "
        f"[bold yellow]{report.warning_count} warnings[/bold yellow]."
    )

    # Determine exit code for CI/CD gates
    if report.has_errors:
        console.print("[bold red]❌ CI/CD QUALITY GATE BLOCKED: Critical errors detected in architecture graph.[/bold red]")
        raise typer.Exit(code=1)

    if strict and report.warning_count > 0:
        console.print("[bold red]❌ CI/CD QUALITY GATE BLOCKED: Strict mode detected warnings.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]✓ CI/CD QUALITY GATE PASSED (Exit code 0).[/bold green]\n")


def validate_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to architecture directory or manifest file",
            exists=True,
            file_okay=True,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
    strict: Annotated[
        bool,
        typer.Option("--strict", "-s", help="Treat warnings as critical errors (exit code 1)"),
    ] = False,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: table or json"),
    ] = "table",
    require_owner: Annotated[
        bool, typer.Option("--require-owner", help="Require an accountable owner for every system")
    ] = False,
    as_of_date: Annotated[
        Optional[str],
        typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for lifecycle invariants"),
    ] = None,
) -> None:
    """Validate architecture DSL workspace and enforce referential integrity & DAG invariants."""
    eval_date = date.fromisoformat(as_of_date) if as_of_date else None
    run_validation(
        path=path,
        strict=strict,
        output_format=output_format,
        require_owner=require_owner,
        as_of_date=eval_date,
    )
