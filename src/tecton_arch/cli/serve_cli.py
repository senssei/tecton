"""CLI command to launch the Tecton Architecture Intelligence REST API server (tecton serve)."""

from pathlib import Path
from typing import Annotated, Optional
import typer
from rich.console import Console
from rich.panel import Panel
import uvicorn

from tecton_arch.server.app import create_app

console = Console()


def serve_command(
    source: Annotated[
        Optional[str],
        typer.Option("--source", "-s", help="Path to architecture directory or manifest (default '.')"),
    ] = None,
    host: Annotated[
        str,
        typer.Option("--host", "-h", help="Bind host address"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Bind port number"),
    ] = 8000,
    reload: Annotated[
        bool,
        typer.Option("--reload", help="Enable auto-reload on workspace file changes"),
    ] = False,
) -> None:
    """Launch headless Architecture Intelligence REST API server."""
    target_path = Path(source) if source else Path(".")
    if not target_path.exists():
        console.print(f"[bold red]Error: Path '{target_path}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    resolved_path = target_path.resolve()
    app = create_app(resolved_path)

    console.print(Panel(
        f"[bold cyan]Tecton Architecture Intelligence Server & Web Portal[/bold cyan]\n\n"
        f"• Workspace: [bold green]{resolved_path}[/bold green]\n"
        f"• Web Portal: [bold yellow]http://{host}:{port}/[/bold yellow]\n"
        f"• OpenAPI Docs: [bold blue]http://{host}:{port}/docs[/bold blue]\n"
        f"• ReDoc Portal: [bold magenta]http://{host}:{port}/redoc[/bold magenta]\n"
        f"• Features: APM, BCM, TRM, Data Lineage, Roadmap Gantt, Backstage/ArchiMate Exports",
        title="🏛️ Tecton Living Architecture Portal",
        border_style="blue",
    ))

    uvicorn.run(app, host=host, port=port)
