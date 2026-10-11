from datetime import date
from pathlib import Path
from tecton_arch.cli.catalog_cli import resolve_date
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.table import Table

from tecton_arch.adapters.base import ArchitectureRepositoryPort
from tecton_arch.adapters.file_adapter import FileRepositoryAdapter
from tecton_arch.adapters.git_adapter import GitRepositoryAdapter
from tecton_arch.adapters.graphql_adapter import GraphQLRepositoryAdapter
from tecton_arch.adapters.in_memory import InMemoryRepositoryAdapter
from tecton_arch.core.config import TectonConfig
from tecton_arch.core.models import RedundancyConfig, TimeConfig, TimeQuadrant
from tecton_arch.exporters.markdown import MarkdownExporter
from tecton_arch.exporters.mermaid import MermaidExporter
from tecton_arch.services.apm_service import APMService

app = typer.Typer(name="apm", help="Application Portfolio Management commands.")
console = Console()


def get_repository(source: str | None, config: TectonConfig) -> ArchitectureRepositoryPort:
    """Resolve repository adapter based on command line source or configuration."""
    if source:
        src_path = Path(source)
        if src_path.is_file():
            return FileRepositoryAdapter(src_path)
        if src_path.is_dir():
            return GitRepositoryAdapter(src_path, config=config)

    if config.repository.url:
        return GraphQLRepositoryAdapter(
            endpoint_url=config.repository.url,
            api_token=config.repository.token,
            timeout_seconds=config.repository.timeout_seconds,
            verify_ssl=config.repository.verify_ssl,
        )

    # Fallback to sample in-memory repository
    return InMemoryRepositoryAdapter()


@app.command("list")
def list_applications(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to input JSON/YAML file")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config", "-c", help="Path to tecton.yaml")] = None,
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for lifecycle phase")] = None,
) -> None:
    """List all applications in the portfolio with fit scores and lifecycle."""
    config = TectonConfig.load(config_path, workspace_dir=Path(source) if source and Path(source).is_dir() else Path(source).parent if source else None)
    repo = get_repository(source, config)
    service = APMService(repo, config.time, config.redundancy)

    eval_date = resolve_date(as_of_date)
    applications = service.get_applications(as_of_date=eval_date)
    if not applications:
        console.print("[yellow]No applications found in repository.[/yellow]")
        return

    title = f"Application Portfolio ({len(applications)} systems)"
    if as_of_date:
        title += f" [As of: {as_of_date}]"
    table = Table(title=title)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold cyan", no_wrap=True)
    table.add_column("Criticality", style="magenta")
    table.add_column("Business Fit", justify="right")
    table.add_column("Technical Fit", justify="right")
    table.add_column("TIME", style="bold")
    table.add_column("Phase", style="green")

    for a in sorted(applications, key=lambda x: x.name):
        b_str = f"{a.functional_suitability:.1f}" if a.functional_suitability else "-"
        t_str = f"{a.technical_suitability:.1f}" if a.technical_suitability else "-"
        phase_str = a.current_phase.value if a.current_phase else "-"

        # Color-coded TIME
        time_style = "white"
        if a.time_classification == TimeQuadrant.INVEST:
            time_style = "bold green"
        elif a.time_classification == TimeQuadrant.TOLERATE:
            time_style = "bold yellow"
        elif a.time_classification == TimeQuadrant.MIGRATE:
            time_style = "bold blue"
        elif a.time_classification == TimeQuadrant.ELIMINATE:
            time_style = "bold red"

        table.add_row(
            a.id[:8],
            a.name,
            a.business_criticality or "-",
            b_str,
            t_str,
            f"[{time_style}]{a.time_classification.value}[/{time_style}]",
            phase_str,
        )

    console.print(table)


@app.command("analyze")
def analyze_portfolio(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to input JSON/YAML file")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config", "-c", help="Path to tecton.yaml")] = None,
    business_threshold: Annotated[Optional[float], typer.Option("--b-thresh", help="Business Fit threshold (1.0-5.0)")] = None,
    technical_threshold: Annotated[Optional[float], typer.Option("--t-thresh", help="Technical Fit threshold (1.0-5.0)")] = None,
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for lifecycle phase and APM analytics")] = None,
) -> None:
    """Run full deterministic APM evaluation: TIME classification, Redundancy, and Lifecycle."""
    config = TectonConfig.load(config_path, workspace_dir=Path(source) if source and Path(source).is_dir() else Path(source).parent if source else None)
    if business_threshold is not None:
        config.time.business_threshold = business_threshold
    if technical_threshold is not None:
        config.time.technical_threshold = technical_threshold

    repo = get_repository(source, config)
    service = APMService(repo, config.time, config.redundancy)
    eval_date = resolve_date(as_of_date)

    with console.status("[bold green]Executing Tecton Portfolio Analytics..."):
        result = service.analyze(as_of_date=eval_date)

    date_str = f" [As of: {as_of_date}]" if as_of_date else ""
    console.print(f"\n[bold]1. Gartner TIME Classification Results{date_str}[/bold]")
    summary_table = Table()
    summary_table.add_column("Quadrant", style="bold")
    summary_table.add_column("Application Count", justify="right")
    summary_table.add_column("Architectural Strategy")

    from collections import Counter
    counts = Counter(result.time_classifications.values())
    total = len(result.applications)

    summary_table.add_row("[green]INVEST[/green]", str(counts.get(TimeQuadrant.INVEST, 0)), "Scale and invest in growth")
    summary_table.add_row("[yellow]TOLERATE[/yellow]", str(counts.get(TimeQuadrant.TOLERATE, 0)), "Tolerate, modernize architecture")
    summary_table.add_row("[blue]MIGRATE[/blue]", str(counts.get(TimeQuadrant.MIGRATE, 0)), "Consolidate, re-platform/migrate")
    summary_table.add_row("[red]ELIMINATE[/red]", str(counts.get(TimeQuadrant.ELIMINATE, 0)), "Plan decommissioning and elimination")
    summary_table.add_row("[dim]UNKNOWN[/dim]", str(counts.get(TimeQuadrant.UNKNOWN, 0)), "Missing complete fit scores")
    console.print(summary_table)

    if result.redundancy_clusters:
        console.print("\n[bold]2. Functional Redundancy Clusters Detected[/bold]")
        red_table = Table()
        red_table.add_column("Cluster ID", style="dim")
        red_table.add_column("Applications", style="cyan")
        red_table.add_column("Similarity", justify="right", style="bold")
        red_table.add_column("Recommendation")

        for c in result.redundancy_clusters:
            red_table.add_row(
                c.cluster_id,
                " <-> ".join(c.application_names),
                f"{c.similarity_score*100:.1f}%",
                c.recommendation,
            )
        console.print(red_table)
    else:
        console.print("\n[green]2. No functional redundancies detected above threshold.[/green]")

    if result.lifecycle_report.issues:
        console.print("\n[bold red]3. Chronological Lifecycle Inconsistencies[/bold red]")
        for issue in result.lifecycle_report.issues:
            icon = "[red]🚨 ERROR[/red]" if issue.severity == "ERROR" else "[yellow]⚠️ WARNING[/yellow]"
            console.print(f"  {icon} [bold]{issue.application_name}[/bold]: {issue.message}")
    else:
        console.print("\n[green]3. Lifecycle: All phases maintain valid chronological sequence.[/green]")

    if result.patches_needed > 0:
        console.print(f"\n[cyan]💡 Pending Updates:[/cyan] {result.patches_needed} applications require TIME quadrant updates. Run [bold]`tecton apm patch-time`[/bold].")


@app.command("export-matrix")
def export_matrix(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to input JSON/YAML file")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config", "-c", help="Path to tecton.yaml")] = None,
    fmt: Annotated[str, typer.Option("--format", "-f", help="Export format: mermaid or markdown")] = "mermaid",
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path (default stdout)")] = None,
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date", help="Target evaluation date (YYYY-MM-DD) for portfolio evaluation")] = None,
) -> None:
    """Export TIME model visual diagram (Mermaid quadrantChart) or full Markdown report."""
    config = TectonConfig.load(config_path, workspace_dir=Path(source) if source and Path(source).is_dir() else Path(source).parent if source else None)
    repo = get_repository(source, config)
    service = APMService(repo, config.time, config.redundancy)
    eval_date = resolve_date(as_of_date)

    apps = service.get_applications(as_of_date=eval_date)
    if not apps:
        console.print("[red]No applications found to generate report.[/red]")
        return

    if fmt.lower() == "mermaid":
        content = MermaidExporter.to_time_quadrant_chart(apps, time_config=config.time)
    else:
        result = service.analyze(as_of_date=eval_date)
        content = MarkdownExporter.generate_apm_report(
            applications=result.applications,
            time_classifications=result.time_classifications,
            redundancy_clusters=result.redundancy_clusters,
            lifecycle_report=result.lifecycle_report,
        )

    if output:
        out_path = Path(output)
        out_path.write_text(content, encoding="utf-8")
        console.print(f"[green]Report successfully exported to file:[/green] {out_path.resolve()}")
    else:
        console.print(content)


@app.command("patch-time")
def patch_time_classifications(
    source: Annotated[Optional[str], typer.Option("--source", "-s", help="Path to input JSON/YAML file")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config", "-c", help="Path to tecton.yaml")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Persist changes to repository (default dry-run)")] = False,
) -> None:
    """Apply evaluated TIME classification quadrants to repository entities."""
    config = TectonConfig.load(config_path, workspace_dir=Path(source) if source and Path(source).is_dir() else Path(source).parent if source else None)
    repo = get_repository(source, config)
    service = APMService(repo, config.time, config.redundancy)

    is_dry_run = not apply
    results = service.apply_time_patches(dry_run=is_dry_run)

    mode_label = "[yellow][DRY-RUN - SIMULATION][/yellow]" if is_dry_run else "[green][APPLIED - PERSISTED][/green]"
    console.print(f"{mode_label} Processed {len(results)} TIME quadrant update patches.")

    for res in results:
        status_color = "yellow" if is_dry_run else "green"
        console.print(f"  • Entity ID: {res['entity_id'][:8]} -> [{status_color}]{res.get('status', 'ok')}[/{status_color}] ({res.get('applied_count', 0)} changes)")

    if is_dry_run and results:
        console.print("\n[dim]To persist changes to the repository, provide the `--apply` flag.[/dim]")

from tecton_arch.cli.catalog_cli import make_app, render_report

@app.command("costs")
def apm_costs_command(
    source: Annotated[str, typer.Option("--source", "-s")] = ".",
    as_of_date: Annotated[Optional[str], typer.Option("--as-of-date")] = None,
    output_format: Annotated[str, typer.Option("--format", "-f")] = "table",
    output: Annotated[Optional[str], typer.Option("--output", "-o")] = None,
    config_path: Annotated[Optional[str], typer.Option("--config")] = None,
):
    render_report(make_app(source, as_of_date, config_path).apm_costs(), output_format, output)
