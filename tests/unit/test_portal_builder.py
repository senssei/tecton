"""Unit tests for PortalBuilder and Living Architecture Web Portal generation."""

from pathlib import Path
from tecton.dsl.parser import C4EAMParser
from tecton.portal.builder import PortalBuilder


def test_portal_builder_dynamic_html():
    html = PortalBuilder.build_dynamic_portal_html()
    assert "<!DOCTYPE html>" in html
    assert "TECTON" in html
    assert "window.__TECTON_DATA__ = null;" in html
    assert "tab-overview" in html
    assert "tab-apm" in html
    assert "tab-bcm" in html
    assert "tab-trm" in html
    assert "tab-data" in html
    assert "tab-roadmap" in html


def test_portal_builder_static_html():
    yaml_content = """
capabilities:
  - id: cap-billing
    name: Billing Operations
    level: L1
systems:
  - id: sys-billing
    name: Cloud Billing
    capabilities: [cap-billing]
    functional_suitability: 4.5
    technical_suitability: 4.2
    time_classification: INVEST
technologies:
  - id: tech-pg
    name: PostgreSQL
    status: approved
"""
    graph = C4EAMParser().parse_content(yaml_content)
    html = PortalBuilder.build_static_portal_html(graph)

    assert "<!DOCTYPE html>" in html
    assert "window.__TECTON_DATA__ = {" in html
    assert '"Cloud Billing"' in html
    assert '"Billing Operations"' in html
    assert '"PostgreSQL"' in html
    assert "time-matrix" in html


def test_portal_builder_export_portal(tmp_path: Path):
    yaml_content = """
systems:
  - id: sys-core
    name: Core System
"""
    graph = C4EAMParser().parse_content(yaml_content)
    out_dir = tmp_path / "portal_site"
    out_file = PortalBuilder.export_portal(graph, out_dir)

    assert out_file.exists()
    assert out_file.name == "index.html"
    content = out_file.read_text(encoding="utf-8")
    assert "Core System" in content
