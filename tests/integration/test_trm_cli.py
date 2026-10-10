"""Integration tests for TRM CLI subcommands."""

from pathlib import Path
from typer.testing import CliRunner
from tecton.cli.main import app

runner = CliRunner()


def test_cli_trm_list():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["trm", "list", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "Katalog Standardów Technologicznych" in result.output
    assert "tech-python-312" in result.output
    assert "tech-legacy-solaris" in result.output


def test_cli_trm_blast_radius():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["trm", "blast-radius", "tech-legacy-solaris", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "Analiza Promienia Rażenia" in result.output
    assert "Oracle Solaris 10" in result.output
    assert "Mainframe Monolith Billing System" in result.output
    assert "Kaskadowa Propagacja Zagrożenia" in result.output


def test_cli_trm_export_radar():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["trm", "export-radar", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "flowchart LR" in result.output
    assert "classDef approved" in result.output
