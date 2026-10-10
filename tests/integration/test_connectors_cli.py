"""Integration tests for Open EA Connectors CLI subcommands (export and import)."""

from pathlib import Path
from typer.testing import CliRunner

from tecton.cli.main import app

runner = CliRunner()
WORKSPACE = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"


def test_cli_export_and_import_backstage(tmp_path: Path):
    export_file = tmp_path / "catalog-info.yaml"
    res_export = runner.invoke(
        app,
        ["export", "backstage", "--source", str(WORKSPACE), "-o", str(export_file)],
    )
    assert res_export.exit_code == 0
    assert "Successfully exported Backstage catalog" in res_export.stdout
    assert export_file.exists()

    # Import test
    res_import = runner.invoke(
        app,
        ["import", "backstage", str(export_file), "-o", str(tmp_path)],
    )
    assert res_import.exit_code == 0
    assert "Parsed" in res_import.stdout
    assert (tmp_path / "backstage_imported_manifest.yaml").exists()


def test_cli_export_and_import_archimate(tmp_path: Path):
    export_file = tmp_path / "model.xml"
    res_export = runner.invoke(
        app,
        ["export", "archimate", "--source", str(WORKSPACE), "-o", str(export_file)],
    )
    assert res_export.exit_code == 0
    assert "Successfully exported ArchiMate Open Exchange XML" in res_export.stdout
    assert export_file.exists()

    # Import test
    res_import = runner.invoke(
        app,
        ["import", "archimate", str(export_file), "-o", str(tmp_path)],
    )
    assert res_import.exit_code == 0
    assert "Parsed" in res_import.stdout
    assert (tmp_path / "archimate_imported_manifest.yaml").exists()
