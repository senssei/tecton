"""Integration tests for TRM CLI subcommands."""

from pathlib import Path
from typer.testing import CliRunner
from tecton_arch.cli.main import app

runner = CliRunner(env={"COLUMNS": "200"})


def test_cli_trm_list():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["trm", "list", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "Technology Standards Catalog" in result.output
    assert "tech-python-312" in result.output
    assert "tech-legacy-solaris" in result.output


def test_cli_trm_blast_radius():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["trm", "blast-radius", "tech-legacy-solaris", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "Blast Radius Impact Analysis" in result.output
    assert "Oracle Solaris 10" in result.output
    assert "Mainframe Monolith Billing System" in result.output
    assert "Cascading Architecture Blast Radius" in result.output


def test_cli_trm_export_radar():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["trm", "export-radar", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "flowchart LR" in result.output
    assert "classDef approved" in result.output
