"""CLI subcommands for Open EA Importers (import)."""

from pathlib import Path
from typing import Annotated, Optional
import typer
import yaml
from rich.console import Console

from tecton.connectors.archimate import ArchiMateConnector
from tecton.connectors.backstage import BackstageConnector

app = typer.Typer(name="import", help="Import external EA models (Backstage, ArchiMate) into Tecton Architecture-as-Code manifests.")
console = Console()


@app.command("backstage")
def import_backstage(
    file_path: Annotated[str, typer.Argument(help="Path to Backstage catalog YAML file")],
    output_dir: Annotated[Optional[str], typer.Option("--output-dir", "-o", help="Target directory for generated manifests")] = None,
) -> None:
    """Import Spotify Backstage Software Catalog into Tecton Architecture manifests."""
    source_file = Path(file_path)
    if not source_file.exists():
        console.print(f"[bold red]Error: File '{source_file}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    content = source_file.read_text(encoding="utf-8")
    manifest = BackstageConnector.import_catalog(content)

    total_entities = sum(len(v) for v in manifest.values())
    console.print(f"[bold green]Parsed {total_entities} entities from Backstage catalog:[/bold green]")
    for kind, items in manifest.items():
        if items:
            console.print(f"  • {kind}: {len(items)}")

    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_manifest = out_dir / "backstage_imported_manifest.yaml"
        # Filter non-empty sections
        clean_manifest = {k: v for k, v in manifest.items() if v}
        out_manifest.write_text(yaml.dump(clean_manifest, sort_keys=False), encoding="utf-8")
        console.print(f"[bold green]✓ Written imported manifest to '{out_manifest}'[/bold green]")
    else:
        clean_manifest = {k: v for k, v in manifest.items() if v}
        console.print(yaml.dump(clean_manifest, sort_keys=False))


@app.command("archimate")
def import_archimate(
    file_path: Annotated[str, typer.Argument(help="Path to ArchiMate Open Exchange XML file")],
    output_dir: Annotated[Optional[str], typer.Option("--output-dir", "-o", help="Target directory for generated manifests")] = None,
) -> None:
    """Import The Open Group ArchiMate Open Exchange XML into Tecton Architecture manifests."""
    source_file = Path(file_path)
    if not source_file.exists():
        console.print(f"[bold red]Error: File '{source_file}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    content = source_file.read_text(encoding="utf-8")
    manifest = ArchiMateConnector.import_xml(content)

    total_entities = sum(len(v) for v in manifest.values())
    console.print(f"[bold green]Parsed {total_entities} entities from ArchiMate XML:[/bold green]")
    for kind, items in manifest.items():
        if items:
            console.print(f"  • {kind}: {len(items)}")

    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_manifest = out_dir / "archimate_imported_manifest.yaml"
        clean_manifest = {k: v for k, v in manifest.items() if v}
        out_manifest.write_text(yaml.dump(clean_manifest, sort_keys=False), encoding="utf-8")
        console.print(f"[bold green]✓ Written imported manifest to '{out_manifest}'[/bold green]")
    else:
        clean_manifest = {k: v for k, v in manifest.items() if v}
        console.print(yaml.dump(clean_manifest, sort_keys=False))
