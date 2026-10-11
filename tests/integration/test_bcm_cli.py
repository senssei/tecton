"""Integration tests for BCM CLI subcommands."""

from pathlib import Path
from typer.testing import CliRunner
from tecton_arch.cli.main import app

runner = CliRunner()


def test_cli_bcm_tree():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["bcm", "tree", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "Business Capability Map" in result.output
    assert "Order Management" in result.output
    assert "Global CRM Platform" in result.output


def test_cli_bcm_analyze():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["bcm", "analyze", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "Business Capability Coverage Summary" in result.output
    assert "Total Business Capabilities" in result.output
    assert "Business Capability Health Matrix" in result.output


def test_cli_bcm_heatmap():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["bcm", "heatmap", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "flowchart TD" in result.output
    assert "classDef healthy" in result.output
