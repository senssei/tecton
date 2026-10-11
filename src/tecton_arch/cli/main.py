"""Main entry point for Tecton CLI."""

import typer
from tecton_arch import __version__
from rich.console import Console
from tecton_arch.cli.catalog_cli import app as catalog_app
from tecton_arch.cli.apm_cli import app as apm_app
from tecton_arch.cli.bcm_cli import app as bcm_app
from tecton_arch.cli.data_cli import app as data_app
from tecton_arch.cli.diff_cli import diff_command
from tecton_arch.cli.export_cli import app as export_app
from tecton_arch.cli.import_cli import app as import_app
from tecton_arch.cli.roadmap_cli import app as roadmap_app
from tecton_arch.cli.serve_cli import serve_command
from tecton_arch.cli.trm_cli import app as trm_app
from tecton_arch.cli.validate_cli import validate_command

app = typer.Typer(
    name="tecton",
    help="Tecton: Deterministic Enterprise Architecture Intelligence Engine & Architecture-as-Code Toolkit.",
    no_args_is_help=True,
)

console = Console()

app.add_typer(catalog_app, name="catalog")
app.add_typer(apm_app, name="apm")
app.add_typer(bcm_app, name="bcm")
app.add_typer(trm_app, name="trm")
app.add_typer(data_app, name="data")
app.add_typer(roadmap_app, name="roadmap")
app.add_typer(export_app, name="export")
app.add_typer(import_app, name="import")
app.command(name="validate", help="Validate architecture DSL manifests and enforce CI/CD quality gate.")(validate_command)
app.command(name="lint", help="Alias for validate: Lint architecture DSL manifests.")(validate_command)
app.command(name="diff", help="Semantic architectural diff between Git revisions or architecture directories.")(diff_command)
app.command(name="serve", help="Launch headless Architecture Intelligence REST API server.")(serve_command)
app.command(name="portal", help="Launch interactive Architecture Intelligence Web Portal & Dashboard.")(serve_command)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]Tecton Engine[/bold cyan] version [bold green]{__version__}[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show program version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Tecton CLI callback."""
    pass


if __name__ == "__main__":
    app()
