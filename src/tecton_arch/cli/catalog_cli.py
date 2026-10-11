"""Read reports and prepare isolated catalog refactorings."""
from datetime import date
from typing import Annotated
import json
import typer
from rich.console import Console
from rich.table import Table
from tecton_arch.application import TectonApp
from tecton_arch.core.config import TectonConfig

app = typer.Typer(help="Catalog maintenance and review")
console = Console()


def resolve_date(value):
    try:
        return date.fromisoformat(value) if value else date.today()
    except ValueError as exc:
        raise typer.BadParameter("Evaluation date must use YYYY-MM-DD") from exc


def make_app(source, as_of_date=None, config_path=None):
    try:
        evaluation_date = resolve_date(as_of_date)
        config = TectonConfig.load(config_path, workspace_dir=source)
        return TectonApp(source, as_of_date=evaluation_date, config=config)
    except (ValueError, OSError) as exc:
        raise typer.BadParameter(str(exc)) from exc


def render_report(report, output_format="table", output=None):
    if output_format not in ("table", "json", "markdown"):
        raise typer.BadParameter("Format must be table, json or markdown")
    text = json.dumps(report, indent=2, ensure_ascii=False, default=str)
    if output_format == "markdown":
        def cell(value):
            return str(value if value is not None else "Not supplied").replace("|", "\\|").replace("\n", " ")
        sections = []
        for key, value in report.items():
            sections.append("## " + key.replace("_", " ").capitalize() + "\n")
            if isinstance(value, list) and value and isinstance(value[0], dict):
                columns = list(dict.fromkeys(k for row in value for k in row))
                sections.append("| " + " | ".join(columns) + " |")
                sections.append("| " + " | ".join("---" for _ in columns) + " |")
                sections.extend("| " + " | ".join(cell(row.get(c)) for c in columns) + " |" for row in value)
            else:
                sections.append(cell(value))
            sections.append("")
        text = "\n".join(sections)
    if output:
        from pathlib import Path
        Path(output).write_text(text, encoding="utf-8")
    elif output_format == "json":
        console.print_json(text)
    elif output_format == "markdown":
        console.print(text, markup=False)
    else:
        for key, value in report.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                columns = list(dict.fromkeys(k for row in value for k in row))
                table = Table(title=key)
                for column in columns:
                    table.add_column(column)
                for row in value:
                    table.add_row(*(str(row.get(c, "")) for c in columns))
                console.print(table)
            else:
                console.print(f"{key}: {value}", markup=False)


@app.command("freshness")
def freshness(
    source: Annotated[str, typer.Option("--source", "-s")] = ".",
    as_of_date: Annotated[str | None, typer.Option("--as-of-date")] = None,
    output_format: Annotated[str, typer.Option("--format", "-f")] = "table",
    output: Annotated[str | None, typer.Option("--output", "-o")] = None,
    config_path: Annotated[str | None, typer.Option("--config")] = None,
):
    render_report(make_app(source, as_of_date, config_path).catalog_freshness(), output_format, output)


@app.command("rename")
def rename(
    old_id: str, new_id: str,
    source: Annotated[str, typer.Option("--source", "-s")] = ".",
    output: Annotated[str | None, typer.Option("--output", "-o")] = None,
    output_format: Annotated[str, typer.Option("--format", "-f")] = "table",
    config_path: Annotated[str | None, typer.Option("--config")] = None,
):
    try:
        render_report(make_app(source, config_path=config_path).catalog_rename(old_id, new_id, output), output_format)
    except (ValueError, OSError) as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(1) from exc
