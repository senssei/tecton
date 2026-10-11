"""CLI subcommands for Business Capability Management (BCM)."""

from pathlib import Path
from tecton_arch.cli.catalog_cli import resolve_date
from tecton_arch.core.config import TectonConfig
from datetime import date
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from tecton_arch.core.models import CapabilityHealth
from tecton_arch.services.bcm_service import BCMService

app = typer.Typer(name="bcm", help="Business Capability Management (BCM) commands.")
console = Console()


def _resolve_source(source: str | None) -> Path:
    target = Path(source) if source else Path(".")
    if not target.exists():
        console.print(f"[bold red]Error: Path '{target}' does not exist.[/bold red]")
        raise typer.Exit(code=1)
    return target


@app.command("tree")
def show_capability_tree(
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Evaluation date YYYY-MM-DD")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """Display the hierarchical Business Capability tree and realizing systems."""
    target_path = _resolve_source(source)
    service = BCMService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    report = service.analyze(as_of_date=resolve_date(as_of_date))

    root_tree = Tree(f"[bold cyan]Business Capability Map[/bold cyan] ({report.total_capabilities} capabilities)")

    # Group by parent
    children_map: dict[str | None, list[str]] = {}
    for c_id, cov in report.coverages.items():
        children_map.setdefault(cov.parent_id, []).append(c_id)

    # Health color map
    color_map = {
        CapabilityHealth.HEALTHY: "green",
        CapabilityHealth.TOLERABLE: "yellow",
        CapabilityHealth.AT_RISK: "red",
        CapabilityHealth.UNMAPPED: "dim",
        CapabilityHealth.UNKNOWN: "cyan",
    }

    def add_nodes(parent_id: str | None, current_tree: Tree) -> None:
        for c_id in sorted(children_map.get(parent_id, [])):
            cov = report.coverages[c_id]
            color = color_map.get(cov.health, "white")
            sys_str = f" [cyan]({len(cov.realizing_system_ids)} apps)[/cyan]" if cov.realizing_system_ids else " [dim](0 apps - GAP)[/dim]"
            node_label = f"[{color}]{cov.name}[/{color}] [dim]({c_id})[/dim]{sys_str} [{color}][{cov.health.value}][/{color}]"
            sub_tree = current_tree.add(node_label)

            # If it realizes systems, add them as leaves
            for s_name in cov.realizing_system_names:
                sub_tree.add(f"[italic dim]⚙ {s_name}[/italic dim]")

            add_nodes(c_id, sub_tree)

    add_nodes(None, root_tree)
    console.print()
    console.print(root_tree)
    console.print()


@app.command("analyze")
def analyze_capabilities(
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Evaluation date YYYY-MM-DD")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
) -> None:
    """Analyze capability coverage, detect unmapped blind spots, and assess health."""
    target_path = _resolve_source(source)
    service = BCMService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    report = service.analyze(as_of_date=resolve_date(as_of_date))

    console.print("\n[bold]1. Business Capability Coverage Summary[/bold]")
    summary_table = Table()
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value", justify="right")

    summary_table.add_row("Total Business Capabilities", str(report.total_capabilities))
    summary_table.add_row("Capabilities Mapped to Systems", f"[green]{report.mapped_capabilities}[/green]")
    summary_table.add_row("Coverage Blind Spots (Gaps / 0 systems)", f"[red]{len(report.orphaned_capabilities)}[/red]")
    summary_table.add_row("Redundancy Hotspots (Over-provisioned)", f"[yellow]{len(report.overprovisioned_capabilities)}[/yellow]")
    summary_table.add_row("Portfolio Coverage Ratio", f"[bold cyan]{report.coverage_percentage:.1f}%[/bold cyan]")
    console.print(summary_table)

    if report.orphaned_capabilities:
        console.print("\n[bold red]⚠️ Coverage Blind Spots Detected (No supporting systems):[/bold red]")
        for c_id in report.orphaned_capabilities:
            cov = report.coverages[c_id]
            console.print(f"  • [red]{cov.name}[/red] [dim]({c_id})[/dim]")

    if report.overprovisioned_capabilities:
        console.print("\n[bold yellow]💡 Redundancy Hotspots Detected (Consolidation candidates):[/bold yellow]")
        for c_id in report.overprovisioned_capabilities:
            cov = report.coverages[c_id]
            console.print(f"  • [yellow]{cov.name}[/yellow] ({len(cov.realizing_system_ids)} systems): {', '.join(cov.realizing_system_names)}")

    console.print("\n[bold]2. Business Capability Health Matrix[/bold]")
    table = Table()
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Capability Name", style="bold")
    table.add_column("Level", justify="center")
    table.add_column("Health Status", justify="center")
    table.add_column("Application Count", justify="right")
    table.add_column("Realizing Systems")

    for c_id, cov in sorted(report.coverages.items(), key=lambda x: x[1].name):
        color = "green" if cov.health == CapabilityHealth.HEALTHY else "yellow" if cov.health == CapabilityHealth.TOLERABLE else "red" if cov.health == CapabilityHealth.AT_RISK else "dim"
        table.add_row(
            c_id,
            cov.name,
            cov.level or "-",
            f"[{color}]{cov.health.value}[/{color}]",
            str(len(cov.realizing_system_ids)),
            ", ".join(cov.realizing_system_names) or "[dim]-[/dim]",
        )

    console.print(table)
    console.print()


@app.command("heatmap")
def export_heatmap(
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Evaluation date YYYY-MM-DD")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config", help="Workspace configuration")] = None,
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to architecture directory or manifest")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path (default stdout)")] = None,
) -> None:
    """Generate color-coded Mermaid flowchart heatmap of the capability architecture."""
    target_path = _resolve_source(source)
    service = BCMService(target_path, config=TectonConfig.load(config_path, workspace_dir=target_path if target_path.is_dir() else target_path.parent))
    chart = service.export_heatmap(as_of_date=resolve_date(as_of_date))

    if output:
        out_path = Path(output)
        out_path.write_text(chart, encoding="utf-8")
        console.print(f"[green]Mermaid heatmap saved to file:[/green] {out_path.resolve()}")
    else:
        console.print(chart)
