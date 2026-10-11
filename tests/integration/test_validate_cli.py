"""Integration tests for CLI validate and lint commands."""

import json
from pathlib import Path
from typer.testing import CliRunner
from tecton_arch.cli.main import app

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


def test_cli_validate_as_of_date():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["validate", "--format", "json", "--as-of-date", "2020-01-01", str(workspace)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["as_of_date"] == "2020-01-01"


def test_cli_validate_empty_workspace_behavior(tmp_path: Path):
    # Lenient validation warns but exits 0
    res_lenient = runner.invoke(app, ["validate", str(tmp_path)])
    assert res_lenient.exit_code == 0
    assert "EMPTY_WORKSPACE" in res_lenient.output

    # Strict validation treats empty workspace as error and exits 1
    res_strict = runner.invoke(app, ["validate", "--strict", str(tmp_path)])
    assert res_strict.exit_code == 1
    assert "EMPTY_WORKSPACE" in res_strict.output
    assert "CI/CD QUALITY GATE BLOCKED" in res_strict.output


def test_cli_validate_strict_rejects_typo_fields(tmp_path: Path):
    manifest = tmp_path / "systems.yaml"
    manifest.write_text(
        """
        systems:
          - id: sys-billing
            name: Billing
            ownr: Team Billing   # typo: should be owner
        """,
        encoding="utf-8",
    )
    res = runner.invoke(app, ["validate", str(tmp_path)])
    assert res.exit_code == 1
    assert "ownr" in res.output or "SCHEMA_VALIDATION_ERROR" in res.output
    assert "CI/CD QUALITY GATE BLOCKED" in res.output


def test_cli_validate_with_config_scoping(tmp_path: Path):
    arch_dir = tmp_path / "architecture"
    arch_dir.mkdir()
    (arch_dir / "systems.yaml").write_text(
        "systems:\n  - id: sys-valid\n    name: Valid\n",
        encoding="utf-8",
    )
    ignored_dir = tmp_path / "drafts"
    ignored_dir.mkdir()
    (ignored_dir / "broken.yaml").write_text(
        "systems:\n  - id: sys-draft\n    name: Draft\n    capabilities: [cap-missing]\n",
        encoding="utf-8",
    )
    # Write tecton.yaml that scopes manifests to architecture/
    (tmp_path / "tecton.yaml").write_text(
        "manifests:\n  include:\n    - 'architecture/*.yaml'\n  exclude:\n    - 'drafts/**'\n",
        encoding="utf-8",
    )
    res = runner.invoke(app, ["validate", str(tmp_path)])
    assert res.exit_code == 0
    assert "CI/CD QUALITY GATE PASSED" in res.output or "Architecture valid" in res.output


