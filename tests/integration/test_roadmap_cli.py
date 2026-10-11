"""Integration tests for Tecton Roadmap CLI subcommands."""

from pathlib import Path
from typer.testing import CliRunner

from tecton_arch.cli.main import app

runner = CliRunner()
WORKSPACE = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"


def test_cli_roadmap_list():
    result = runner.invoke(app, ["roadmap", "list", "--source", str(WORKSPACE)])
    assert result.exit_code == 0
    assert "Architecture Transformation Plateaus" in result.stdout
    assert "plateau-2026-as-is" in result.stdout
    assert "plateau-2027-target" in result.stdout
    assert "Transformation Work Packages" in result.stdout
    assert "wp-billing-modernization" in result.stdout


def test_cli_roadmap_analyze():
    result = runner.invoke(app, ["roadmap", "analyze", "--source", str(WORKSPACE)])
    assert result.exit_code == 0
    assert "Architecture Transformation Roadmap Summary" in result.stdout
    assert "Plateau Architectural Footprint & Health" in result.stdout
    assert "Transitional Capability Gaps Detected" in result.stdout
    assert "Invoicing & Accounts Receivable" in result.stdout


def test_cli_roadmap_compare():
    result = runner.invoke(
        app,
        ["roadmap", "compare", "plateau-2026-as-is", "plateau-2027-target", "--source", str(WORKSPACE)],
    )
    assert result.exit_code == 0
    assert "Architecture Scenario Comparison" in result.stdout
    assert "sys-legacy-billing" in result.stdout
    assert "cap-invoicing" in result.stdout
    assert "tech-legacy-solaris" in result.stdout


def test_cli_roadmap_export_gantt(tmp_path: Path):
    out_file = tmp_path / "roadmap_gantt.mmd"
    result = runner.invoke(
        app,
        ["roadmap", "export-gantt", "--source", str(WORKSPACE), "-o", str(out_file)],
    )
    assert result.exit_code == 0
    assert "Successfully exported Gantt chart" in result.stdout
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "gantt" in content
    assert "section Plateaus" in content
    assert "section Work Packages" in content
