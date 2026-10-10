"""Main entry point for Tecton CLI."""

import typer
from rich.console import Console
from tecton.cli.apm_cli import app as apm_app
from tecton.cli.validate_cli import validate_command

app = typer.Typer(
    name="tecton",
    help="Tecton: Deterministic Enterprise Architecture Intelligence Engine & Architecture-as-Code Toolkit.",
    no_args_is_help=True,
)

console = Console()

app.add_typer(apm_app, name="apm")
app.command(name="validate", help="Validate architecture DSL manifests and enforce CI/CD quality gate.")(validate_command)
app.command(name="lint", help="Alias for validate: Lint architecture DSL manifests.")(validate_command)


def version_callback(value: bool) -> None:
    if value:
        console.print("[bold cyan]Tecton Engine[/bold cyan] version [bold green]0.1.0[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Pokaż wersję programu i wyjdź.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Tecton CLI callback."""
    pass


if __name__ == "__main__":
    app()
