"""CLI for local YAML evaluations."""

import json
from io import StringIO
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from tecton_arch.cli.catalog_cli import resolve_date
from tecton_arch.services.evaluation_service import EvaluationService


def markdown_report(report):
    def cell(value):
        return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ").replace("\r", " ")

    def table(headers, rows):
        return ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |",
                *["| " + " | ".join(cell(value) for value in row) + " |" for row in rows]]

    lines = ["# Tecton evaluation", "", f"Date: {report['as_of_date']}; passed: {report['passed']}; strict: {report['strict']}",
             f"TIME thresholds: functional {report['business_threshold']}, technical {report['technical_threshold']}",
             "", "## Applications", ""]
    lines += table(["ID", "Source", "Functional", "Technical", "TIME", "Missing criteria", "Rationale"],
                   [[a['id'], a['score_source'], a['functional_suitability'], a['technical_suitability'],
                     a['time_classification'], ', '.join(a['missing_criteria']), a['rationale']] for a in report['applications']])
    quality = report['catalog_quality']
    lines += ["", "## Catalog quality", "", f"Errors: {quality['error_count']}; warnings: {quality['warning_count']}", ""]
    lines += table(["Severity", "Rule", "Entity", "Message", "File"],
                   [[i['severity'], i['rule'], i['entity_id'], i['message'], i['file_origin']] for i in quality['issues']])
    recommendations = report['recommendations']
    lines += ["", "## TIME checks", "", f"Passed: {recommendations['passed']}/{recommendations['checked']}; agreement (%): {cell(recommendations['agreement_percentage'])}", ""]
    lines += table(["ID", "Expected", "Actual", "Passed"],
                   [[c['id'], c['expected'], c['actual'], c['passed']] for c in recommendations['checks']])
    return '\n'.join(lines) + '\n'


def evaluate_command(
    suite: Annotated[Path, typer.Option("--suite", help="Evaluation YAML file")],
    source: Annotated[Path, typer.Option("--source", "-s")] = Path("."),
    config_path: Annotated[Path | None, typer.Option("--config")] = None,
    as_of_date: Annotated[str | None, typer.Option("--as-of-date")] = None,
    output_format: Annotated[str, typer.Option("--format", "-f")] = "table",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    strict: Annotated[bool, typer.Option("--strict")] = False,
):
    """Assess suitability, catalog quality and expected TIME recommendations."""
    console = Console()
    try:
        if output_format not in ("table", "json", "markdown"):
            raise ValueError("Format must be table, json or markdown")
        service = EvaluationService(source, suite, config_path=config_path,
                                    as_of_date=resolve_date(as_of_date), strict=strict)
        if output is not None:
            service.validate_output(output)
        report = service.evaluate()
        data = report.model_dump(mode="json")
        if output_format == "json":
            text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        elif output_format == "markdown":
            text = markdown_report(data)
        else:
            text = None
        if output is not None:
            if text is None:
                # Render plain tables into a recording console for a text artifact.
                file_console = Console(file=StringIO(), record=True, width=120, color_system=None)
                render_tables(file_console, data)
                text = file_console.export_text()
            output.write_text(text, encoding="utf-8")
        elif text is not None:
            console.print(text, markup=False, highlight=False, end="", soft_wrap=True)
        else:
            render_tables(console, data)
    except Exception as exc:
        console.print(f"Evaluation error: {exc}", markup=False, highlight=False)
        raise typer.Exit(2) from exc
    raise typer.Exit(0 if report.passed else 1)


def render_tables(console, report):
    console.print(f"Date: {report['as_of_date']} | Passed: {report['passed']} | Strict: {report['strict']}", markup=False)
    console.print(f"TIME thresholds: functional {report['business_threshold']}, technical {report['technical_threshold']}", markup=False)
    table = Table(title="Applications")
    for column in ("ID", "Source", "Functional", "Technical", "TIME", "Missing criteria", "Rationale"):
        table.add_column(column)
    for item in report['applications']:
        table.add_row(*(Text(str(value if value is not None else "—")) for value in (
            item['id'], item['score_source'], item['functional_suitability'], item['technical_suitability'],
            item['time_classification'], ', '.join(item['missing_criteria']), item['rationale'])))
    console.print(table)
    quality = report['catalog_quality']
    console.print(f"Catalog errors: {quality['error_count']} | warnings: {quality['warning_count']}", markup=False)
    for issue in quality['issues']:
        console.print(f"{issue['severity']} {issue['rule']} ({issue['entity_id']}): {issue['message']} [{issue['file_origin']}]", markup=False, highlight=False)
    checks = report['recommendations']
    console.print(f"TIME checks: {checks['passed']}/{checks['checked']} | Agreement (%): {checks['agreement_percentage'] if checks['checked'] else 'not checked'}", markup=False)
    for check in checks['checks']:
        console.print(f"{check['id']}: expected {check['expected']}, actual {check['actual']}, passed {check['passed']}", markup=False)
