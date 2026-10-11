from datetime import date
from pathlib import Path
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tecton_arch.dsl.schema import WorkPackageStatus
from tecton_arch.services.roadmap_service import RoadmapService

app = typer.Typer(name="roadmap", help="Architecture Transformation Roadmapping, Plateaus, and Work Packages.")
console = Console()


def _resolve_source(source: str | None) -> Path:
    target = Path(source) if source else Path(".")
    if not target.exists():
        console.print(f"[bold red]Error: Path '{target}' does not exist.[/bold red]")
        raise typer.Exit(code=1)
    return target


@app.command("list")
def list_roadmap(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """List architecture plateaus and transformation work packages."""
    target_path = _resolve_source(source)
    service = RoadmapService(target_path)

    plateaus = service.list_plateaus()
    work_packages = service.list_work_packages()

    if not plateaus and not work_packages:
        console.print("[yellow]No architecture plateaus or work packages defined in repository.[/yellow]")
        return

    if plateaus:
        p_table = Table(title=f"Architecture Transformation Plateaus ({len(plateaus)} milestones)")
        p_table.add_column("ID", style="dim", no_wrap=True)
        p_table.add_column("Plateau Name", style="bold cyan")
        p_table.add_column("Target Date", justify="center", style="green")
        p_table.add_column("Predecessor", style="magenta")
        p_table.add_column("Active Systems", justify="right")
        p_table.add_column("Retired Systems", justify="right")

        for p in plateaus:
            active_cnt = str(len(p.active_system_ids)) if p.active_system_ids else "inherited"
            decom_cnt = str(len(p.decommissioned_system_ids))
            p_table.add_row(
                p.id,
                p.name,
                str(p.target_date) if p.target_date else "Milestone",
                p.previous_plateau_id or "-",
                active_cnt,
                f"[red]{decom_cnt}[/red]" if decom_cnt != "0" else "0",
            )
        console.print(p_table)

    if work_packages:
        w_table = Table(title=f"Transformation Work Packages ({len(work_packages)} initiatives)")
        w_table.add_column("ID", style="dim", no_wrap=True)
        w_table.add_column("Work Package Name", style="bold")
        w_table.add_column("Status", justify="center")
        w_table.add_column("Timeline", justify="center")
        w_table.add_column("Depends On", style="magenta")
        w_table.add_column("Involved Systems", justify="right")

        for wp in work_packages:
            color = "cyan"
            if wp.status == WorkPackageStatus.COMPLETED:
                color = "green"
            elif wp.status == WorkPackageStatus.IN_PROGRESS:
                color = "bold yellow"
            elif wp.status == WorkPackageStatus.CANCELLED:
                color = "red"

            timeline = "-"
            if wp.start_date and wp.target_date:
                timeline = f"{wp.start_date} -> {wp.target_date}"
            elif wp.start_date:
                timeline = f"from {wp.start_date}"
            elif wp.target_date:
                timeline = f"due {wp.target_date}"

            w_table.add_row(
                wp.id,
                wp.name,
                f"[{color}]{wp.status.value}[/{color}]",
                timeline,
                ", ".join(wp.depends_on) if wp.depends_on else "-",
                str(len(wp.involved_system_ids)),
            )
        console.print(w_table)


@app.command("analyze")
def analyze_roadmap(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for roadmap analysis")] = None,
) -> None:
    """Audit roadmap consistency, evaluate plateau states, and detect transitional capability gaps."""
    target_path = _resolve_source(source)
    service = RoadmapService(target_path)
    eval_date = date.fromisoformat(as_of_date) if as_of_date else None
    report = service.analyze(as_of_date=eval_date)

    status_str = " | ".join(f"{k}: {v}" for k, v in report.work_packages_by_status.items() if v > 0)
    date_str = f" [As of: {as_of_date}]" if as_of_date else ""
    summary_panel = Panel(
        f"[bold]Total Plateaus:[/bold] {report.total_plateaus}  |  "
        f"[bold]Total Work Packages:[/bold] {report.total_work_packages}\n"
        f"[bold]Work Package Statuses:[/bold] {status_str or 'None'}\n"
        f"[bold]Transitional Capability Gaps:[/bold] {len(report.transitional_gaps)}",
        title=f"🗺️ Architecture Transformation Roadmap Summary{date_str}",
        border_style="cyan",
    )
    console.print(summary_panel)

    if report.plateau_states:
        table = Table(title="Plateau Architectural Footprint & Health")
        table.add_column("Plateau ID", style="dim", no_wrap=True)
        table.add_column("Plateau Name", style="bold cyan")
        table.add_column("Target Date", justify="center")
        table.add_column("Active Systems", justify="right", style="green")
        table.add_column("Covered Capabilities", justify="right", style="bold green")
        table.add_column("Uncovered Capabilities", justify="right", style="yellow")
        table.add_column("Tech Debt Techs", justify="right")

        for ps in report.plateau_states:
            tech_debt_str = (
                f"[bold red]{len(ps.deprecated_or_eol_techs_in_use)}[/bold red]"
                if ps.deprecated_or_eol_techs_in_use
                else "[green]0[/green]"
            )
            table.add_row(
                ps.plateau_id,
                ps.plateau_name,
                str(ps.target_date) if ps.target_date else "-",
                str(len(ps.active_system_ids)),
                str(len(ps.covered_capability_ids)),
                str(len(ps.uncovered_capability_ids)),
                tech_debt_str,
            )
        console.print(table)

    if report.transitional_gaps:
        console.print("\n[bold red]⚠️  Transitional Capability Gaps Detected:[/bold red]")
        for gap in report.transitional_gaps:
            console.print(
                f"  • [bold]{gap.capability_name}[/bold] ({gap.capability_id}): "
                f"Gap created transitioning [cyan]{gap.from_plateau_id}[/cyan] -> [cyan]{gap.to_plateau_id}[/cyan]. "
                f"Decommissioned: [red]{', '.join(gap.decommissioned_system_ids)}[/red]"
            )
    else:
        console.print("\n[bold green]✓ No transitional capability gaps detected across plateaus.[/bold green]")


@app.command("compare")
def compare_plateaus(
    from_plateau: Annotated[str, typer.Argument(help="Baseline or starting plateau ID (e.g. As-Is)")],
    to_plateau: Annotated[str, typer.Argument(help="Target plateau ID (e.g. To-Be)")],
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for tech debt evaluation")] = None,
) -> None:
    """Compare two architecture plateaus and compute scenario delta (As-Is vs To-Be)."""
    target_path = _resolve_source(source)
    service = RoadmapService(target_path)
    eval_date = date.fromisoformat(as_of_date) if as_of_date else None

    try:
        comparison = service.compare_plateaus(from_plateau, to_plateau, as_of_date=eval_date)
    except KeyError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    date_str = f" [As of: {as_of_date}]" if as_of_date else ""
    panel = Panel(
        f"[bold]From Plateau:[/bold] {comparison.from_plateau_name} ({comparison.from_plateau_id})\n"
        f"[bold]To Plateau:[/bold]   {comparison.to_plateau_name} ({comparison.to_plateau_id})\n"
        f"[bold]Net Capability Gain:[/bold] [green]{comparison.net_capability_gain:+d}[/green]\n"
        f"[bold]Tech Debt Reduction:[/bold] [green]{comparison.tech_debt_reduction_count} obsolete technologies eliminated[/green]",
        title=f"🔬 Architecture Scenario Comparison (As-Is vs To-Be){date_str}",
        border_style="magenta",
    )
    console.print(panel)

    # Systems Delta
    sys_table = Table(title="Application Systems Evolution")
    sys_table.add_column("Category", style="bold")
    sys_table.add_column("Count", justify="right")
    sys_table.add_column("System IDs", style="dim")
    sys_table.add_row(
        "[green]+ Added Systems[/green]",
        str(len(comparison.added_system_ids)),
        ", ".join(comparison.added_system_ids) if comparison.added_system_ids else "-",
    )
    sys_table.add_row(
        "[red]- Decommissioned Systems[/red]",
        str(len(comparison.decommissioned_system_ids)),
        ", ".join(comparison.decommissioned_system_ids) if comparison.decommissioned_system_ids else "-",
    )
    sys_table.add_row(
        "[cyan]= Retained Systems[/cyan]",
        str(len(comparison.retained_system_ids)),
        ", ".join(comparison.retained_system_ids) if comparison.retained_system_ids else "-",
    )
    console.print(sys_table)

    # Capabilities Delta
    cap_table = Table(title="Business Capabilities Coverage Evolution")
    cap_table.add_column("Category", style="bold")
    cap_table.add_column("Count", justify="right")
    cap_table.add_column("Capability IDs", style="dim")
    cap_table.add_row(
        "[green]+ Gained Capabilities[/green]",
        str(len(comparison.gained_capability_ids)),
        ", ".join(comparison.gained_capability_ids) if comparison.gained_capability_ids else "-",
    )
    cap_table.add_row(
        "[red]- Lost Capabilities[/red]",
        str(len(comparison.lost_capability_ids)),
        ", ".join(comparison.lost_capability_ids) if comparison.lost_capability_ids else "-",
    )
    cap_table.add_row(
        "[cyan]= Retained Coverage[/cyan]",
        str(len(comparison.retained_capability_ids)),
        ", ".join(comparison.retained_capability_ids) if comparison.retained_capability_ids else "-",
    )
    console.print(cap_table)

    # Technologies Delta
    tech_table = Table(title="Technology Radar & Tech Debt Delta")
    tech_table.add_column("Category", style="bold")
    tech_table.add_column("Count", justify="right")
    tech_table.add_column("Technology IDs", style="dim")
    tech_table.add_row(
        "[green]+ Introduced Technologies[/green]",
        str(len(comparison.introduced_technologies)),
        ", ".join(comparison.introduced_technologies) if comparison.introduced_technologies else "-",
    )
    tech_table.add_row(
        "[cyan]- Eliminated Technologies[/cyan]",
        str(len(comparison.eliminated_technologies)),
        ", ".join(comparison.eliminated_technologies) if comparison.eliminated_technologies else "-",
    )
    tech_table.add_row(
        "[bold green]🌱 Eliminated Obsolete / EOL Tech[/bold green]",
        str(len(comparison.eliminated_obsolete_technologies)),
        ", ".join(comparison.eliminated_obsolete_technologies) if comparison.eliminated_obsolete_technologies else "-",
    )
    console.print(tech_table)


@app.command("export-gantt")
def export_gantt(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path")] = None,
    title: Annotated[str, typer.Option("--title", "-t", help="Chart title")] = "Enterprise Architecture Transformation Roadmap",
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for Gantt chart")] = None,
) -> None:
    """Export Mermaid Gantt chart of architecture transformation roadmap."""
    target_path = _resolve_source(source)
    service = RoadmapService(target_path)
    eval_date = date.fromisoformat(as_of_date) if as_of_date else None
    diagram = service.export_gantt(title=title, as_of_date=eval_date)

    if output:
        out_file = Path(output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(diagram, encoding="utf-8")
        console.print(f"[bold green]✓ Successfully exported Gantt chart to '{output}'[/bold green]")
    else:
        console.print(diagram)
