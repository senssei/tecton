"""CLI command for semantic architectural diffing between Git revisions or directories."""

import json
from pathlib import Path
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tecton.engines.diff_engine import ChangeType
from tecton.services.diff_service import DiffService

console = Console()


def diff_command(
    base: Annotated[str, typer.Argument(help="Bazowa rewizja Git (np. 'main', 'HEAD~1') lub ścieżka do katalogu bazowego")],
    head: Annotated[Optional[str], typer.Argument(help="Docelowa rewizja Git lub ścieżka (domyślnie HEAD lub bieżący katalog)")] = None,
    output_format: Annotated[str, typer.Option("--format", "-f", help="Format wyjścia: table, markdown, pr-comment, json")] = "table",
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Ścieżka do pliku wyjściowego")] = None,
    fail_on_risk: Annotated[bool, typer.Option("--fail-on-risk", help="Zwróć exit code 1 przy wykryciu regresji architektonicznej lub luki")] = False,
) -> None:
    """Compute semantic architectural diff between two Git revisions or architecture directories."""
    service = DiffService()

    # Determine whether we are comparing directories or Git revisions
    base_path = Path(base)
    head_path = Path(head) if head else None

    if base_path.exists():
        # Directory comparison mode
        actual_head = head_path if head_path and head_path.exists() else Path(".")
        try:
            report = service.compare_directories(base_path, actual_head, base_label=str(base_path), head_label=str(actual_head))
        except Exception as e:
            console.print(f"[bold red]Błąd porównania katalogów: {e}[/bold red]")
            raise typer.Exit(code=1)
    else:
        # Git revision comparison mode
        actual_head_ref = head if head else "HEAD"
        try:
            report = service.compare_git_revisions(base_ref=base, head_ref=actual_head_ref)
        except Exception as e:
            console.print(f"[bold red]Błąd porównania rewizji Git: {e}[/bold red]")
            raise typer.Exit(code=1)

    # Format output
    if output_format.lower() == "json":
        json_output = report.model_dump_json(indent=2)
        if output:
            Path(output).write_text(json_output, encoding="utf-8")
        else:
            console.print_json(json_output)
    elif output_format.lower() in ("markdown", "pr-comment", "github-pr"):
        md_output = service.to_pr_comment_markdown(report)
        if output:
            Path(output).write_text(md_output, encoding="utf-8")
            console.print(f"[green]Raport Markdown zapisany w pliku:[/green] {output}")
        else:
            console.print(md_output)
    else:
        # Rich Terminal Table format
        console.print(f"\n[bold cyan]Tecton Semantic Architecture Diff[/bold cyan] ({report.base_ref} ➔ {report.head_ref})")

        status_text = (
            "[bold red]BLOCKED: Breaking Architectural Changes[/bold red]"
            if report.has_breaking_changes
            else "[bold green]PASS: Clean Architectural Evolution[/bold green]"
        )
        console.print(Panel(
            f"Status: {status_text}\n"
            f"• Dodane elementy: [bold green]+{report.added_count}[/bold green]\n"
            f"• Usunięte elementy: [bold red]-{report.removed_count}[/bold red]\n"
            f"• Zmodyfikowane elementy: [bold yellow]~{report.modified_count}[/bold yellow]\n"
            f"• Nowe błędy lintera / ryzyka: [bold red]{len(report.new_risk_issues)}[/bold red]\n"
            f"• Nowo powstałe luki w zdolnościach: [bold red]{len(report.new_capability_gaps)}[/bold red]",
            title="Podsumowanie Zmian Architektonicznych",
        ))

        if report.new_risk_issues:
            console.print("\n[bold red]🚨 Wykryte Nowe Zagrożenia & Błędy Architektoniczne:[/bold red]")
            risk_table = Table()
            risk_table.add_column("Poziom", justify="center")
            risk_table.add_column("Reguła", style="dim")
            risk_table.add_column("Element ID", style="bold cyan")
            risk_table.add_column("Komunikat")

            for r in report.new_risk_issues:
                sev_style = "[bold red]ERROR[/bold red]" if r.get("severity") == "ERROR" else "[bold yellow]WARN[/bold yellow]"
                risk_table.add_row(sev_style, r.get("rule"), r.get("entity_id") or "-", r.get("message"))
            console.print(risk_table)

        if report.new_capability_gaps:
            console.print("\n[bold red]⚠️ Nowo Powstałe Białe Plamy (Utrata wsparcia zdolności biznesowych):[/bold red]")
            for gap in report.new_capability_gaps:
                console.print(f"  • [red]{gap}[/red]")

        if report.deltas:
            console.print("\n[bold]Szczegóły Modyfikacji w Modelu Architektury:[/bold]")
            delta_table = Table()
            delta_table.add_column("Typ", justify="center")
            delta_table.add_column("Typ Encji", style="dim")
            delta_table.add_column("ID Elementu", style="bold")
            delta_table.add_column("Nazwa / Zmiany Pól")

            for d in report.deltas:
                change_style = (
                    "[bold green]+ ADD[/bold green]"
                    if d.change_type == ChangeType.ADDED
                    else "[bold red]- DEL[/bold red]"
                    if d.change_type == ChangeType.REMOVED
                    else "[bold yellow]~ MOD[/bold yellow]"
                )
                desc = d.name or "-"
                if d.field_changes:
                    desc += " (" + ", ".join(f"{k}: {v[0]} ➔ {v[1]}" for k, v in d.field_changes.items()) + ")"
                delta_table.add_row(change_style, d.entity_type, d.entity_id, desc)
            console.print(delta_table)

        console.print()

    if fail_on_risk and report.has_breaking_changes:
        console.print("[bold red]❌ BRAMKA ARCHITEKTURY ZABLOKOWANA: Wykryto regresje architektoniczne (--fail-on-risk).[/bold red]")
        raise typer.Exit(code=1)
