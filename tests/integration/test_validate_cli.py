"""Integration tests for CLI validate and lint commands."""

import json
from pathlib import Path
from typer.testing import CliRunner
from tecton.cli.main import app

runner = CliRunner()


def test_cli_validate_success_on_example_workspace():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["validate", str(workspace)])

    assert result.exit_code == 0
    assert "Architecture valid" in result.output or "CI/CD QUALITY GATE PASSED" in result.output


def test_cli_lint_alias_works():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["lint", str(workspace)])

    assert result.exit_code == 0


def test_cli_validate_strict_mode_fails_on_warnings():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["validate", "--strict", str(workspace)])

    assert result.exit_code == 1
    assert "CI/CD QUALITY GATE BLOCKED" in result.output


def test_cli_validate_json_format():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["validate", "--format", "json", str(workspace)])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["valid"] is True
    assert data["files_scanned"] == 7
    assert data["error_count"] == 0
    assert data["warning_count"] >= 1


def test_cli_validate_fails_on_dangling_references(tmp_path: Path):
    corrupted_yaml = tmp_path / "broken.yaml"
    corrupted_yaml.write_text(
        """
        systems:
          - id: sys-broken
            name: Broken System
            capabilities: [cap-non-existent]
        """,
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(tmp_path)])
    assert result.exit_code == 1
    assert "REF_INTEGRITY_DANGLING_SYSTEM_CAPABILITY" in result.output
    assert "CI/CD QUALITY GATE BLOCKED" in result.output
