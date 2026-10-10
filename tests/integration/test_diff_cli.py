"""Integration tests for CLI diff command."""

import json
from pathlib import Path
from typer.testing import CliRunner
from tecton.cli.main import app

runner = CliRunner()


def test_cli_diff_between_workspaces():
    base_ws = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    head_ws = Path(__file__).parents[2] / "examples" / "dogfood" / "tecton_c4_workspace"

    result = runner.invoke(app, ["diff", str(base_ws), str(head_ws)])
    assert result.exit_code == 0
    assert "Tecton Semantic Architecture Diff" in result.output
    assert "Architectural Change Summary" in result.output
    assert "Added entities" in result.output


def test_cli_diff_format_pr_comment():
    base_ws = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    head_ws = Path(__file__).parents[2] / "examples" / "dogfood" / "tecton_c4_workspace"

    result = runner.invoke(app, ["diff", str(base_ws), str(head_ws), "--format", "pr-comment"])
    assert result.exit_code == 0
    assert "## 🏛️ Tecton Architecture Review Gate" in result.output
    assert "Architectural Change Summary" in result.output


def test_cli_diff_format_json():
    base_ws = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    head_ws = Path(__file__).parents[2] / "examples" / "dogfood" / "tecton_c4_workspace"

    result = runner.invoke(app, ["diff", str(base_ws), str(head_ws), "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "deltas" in data
    assert "new_risk_issues" in data
    assert len(data["deltas"]) > 0


def test_cli_diff_fail_on_risk_flag():
    base_ws = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    head_ws = Path(__file__).parents[2] / "examples" / "dogfood" / "tecton_c4_workspace"

    # Since comparing these two different workspaces creates new gaps, fail_on_risk exits with 1
    result = runner.invoke(app, ["diff", str(base_ws), str(head_ws), "--fail-on-risk"])
    assert result.exit_code == 1
    assert "ARCHITECTURE GATE BLOCKED" in result.output
