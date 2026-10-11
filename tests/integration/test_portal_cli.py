"""Integration tests for Portal CLI export command."""

from pathlib import Path
from typer.testing import CliRunner

from tecton_arch.cli.main import app

runner = CliRunner()
WORKSPACE = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"


def test_cli_export_portal(tmp_path: Path):
    out_dir = tmp_path / "site"
    result = runner.invoke(
        app,
        ["export", "portal", "--source", str(WORKSPACE), "-o", str(out_dir)],
    )
    assert result.exit_code == 0
    assert "Successfully exported living Architecture Portal" in result.stdout
    index_html = out_dir / "index.html"
    assert index_html.exists()
    content = index_html.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Global CRM Platform" in content
    assert "Order Management" in content
    assert "quadrantChart" in content
