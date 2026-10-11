"""Integration tests for Open EA Connectors CLI subcommands (export and import)."""

from pathlib import Path
from typer.testing import CliRunner

from tecton_arch.cli.main import app

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


def test_cli_export_and_import_archi_native(tmp_path: Path):
    archi_file = tmp_path / "model.archimate"
    res_export = runner.invoke(
        app,
        ["export", "archi", "--source", str(WORKSPACE), "-o", str(archi_file)],
    )
    assert res_export.exit_code == 0
    assert "Successfully exported native Archi model" in res_export.stdout
    assert archi_file.exists()

    content = archi_file.read_text(encoding="utf-8")
    assert 'xmlns:archimate="http://www.archimatetool.com/archimate"' in content
    assert '<folder name="Strategy"' in content
    assert '<folder name="Application"' in content

    # Test auto-detection via `export archimate -o file.archimate`
    auto_file = tmp_path / "auto.archimate"
    res_auto = runner.invoke(
        app,
        ["export", "archimate", "--source", str(WORKSPACE), "-o", str(auto_file)],
    )
    assert res_auto.exit_code == 0
    assert "Successfully exported Archi Native XML (.archimate)" in res_auto.stdout
    assert auto_file.exists()

    # Import test with native .archimate file
    res_import = runner.invoke(
        app,
        ["import", "archimate", str(archi_file), "-o", str(tmp_path)],
    )
    assert res_import.exit_code == 0
    assert "Parsed" in res_import.stdout
