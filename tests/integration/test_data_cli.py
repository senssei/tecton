"""Integration tests for Data Architecture and Lineage CLI subcommands (tecton data)."""

from pathlib import Path
from typer.testing import CliRunner
from tecton_arch.cli.main import app

runner = CliRunner(env={"COLUMNS": "200"})


def test_cli_data_list():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["data", "list", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "Business Data Objects Catalog" in result.output
    assert "do-customer-profile" in result.output
    assert "RESTRICTED_PII" in result.output
    assert "do-order-record" in result.output


def test_cli_data_interfaces():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["data", "interfaces", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "Interfaces & API Contracts Catalog" in result.output
    assert "iface-crm-order-submission" in result.output
    assert "iface-order-fulfillment-stream" in result.output
    assert "sys-crm-core" in result.output


def test_cli_data_lineage_trace():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["data", "lineage", "do-customer-profile", "--source", str(workspace)])

    assert result.exit_code == 0
    assert "Data Lineage Trajectory" in result.output
    assert "Customer PII Profile" in result.output
    assert "DETECTED" in result.output
    assert "COMPLIANCE RISKS" in result.output
    assert "COMPLIANCE_SENSITIVE_DATA_ON_ELIMINATE_SYSTEM" in result.output


def test_cli_data_lineage_missing_raises_exit_1():
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    result = runner.invoke(app, ["data", "lineage", "unknown-data-id", "--source", str(workspace)])

    assert result.exit_code == 1
    assert "Error:" in result.output


def test_cli_data_export_lineage(tmp_path: Path):
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    out_file = tmp_path / "lineage.mmd"

    result = runner.invoke(
        app,
        ["data", "export-lineage", "do-customer-profile", "--source", str(workspace), "--output", str(out_file)],
    )

    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "flowchart LR" in content
    assert "Customer PII Profile" in content
    assert "sys_sys_crm_core" in content
