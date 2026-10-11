"""Integration tests for Tecton CLI commands using CliRunner."""

from typer.testing import CliRunner
from tecton_arch.cli.main import app

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Tecton Engine version 0.1.0" in result.stdout


def test_cli_apm_list() -> None:
    result = runner.invoke(app, ["apm", "list", "--source", "tests/fixtures/sample_applications.json"])
    assert result.exit_code == 0
    assert "Global Salesforce CRM" in result.stdout
    assert "Mainframe Core Ledger" in result.stdout


def test_cli_apm_analyze() -> None:
    result = runner.invoke(app, ["apm", "analyze", "--source", "tests/fixtures/sample_applications.json"])
    assert result.exit_code == 0
    assert "Gartner TIME Classification Results" in result.stdout
    assert "INVEST" in result.stdout
    assert "TOLERATE" in result.stdout
    assert "Functional Redundancy Clusters Detected" in result.stdout


def test_cli_apm_export_mermaid() -> None:
    result = runner.invoke(
        app,
        ["apm", "export-matrix", "--source", "tests/fixtures/sample_applications.json", "--format", "mermaid"],
    )
    assert result.exit_code == 0
    assert "quadrantChart" in result.stdout
    assert "Global Salesforce CRM:" in result.stdout


def test_cli_apm_export_markdown() -> None:
    result = runner.invoke(
        app,
        ["apm", "export-matrix", "--source", "tests/fixtures/sample_applications.json", "--format", "markdown"],
    )
    assert result.exit_code == 0
    assert "# Tecton APM Portfolio Analysis Report" in result.stdout
    assert "TIME Quadrant Distribution" in result.stdout


def test_cli_apm_patch_time_dry_run() -> None:
    result = runner.invoke(
        app,
        ["apm", "patch-time", "--source", "tests/fixtures/sample_applications.json"],
    )
    assert result.exit_code == 0
    assert "[DRY-RUN - SIMULATION]" in result.stdout
    assert "Entity ID:" in result.stdout
