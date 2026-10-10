"""Unit tests for Open EA Connectors (Backstage and ArchiMate)."""

from tecton.connectors.archimate import ArchiMateConnector
from tecton.connectors.backstage import BackstageConnector
from tecton.dsl.parser import C4EAMParser


def test_backstage_connector_export_catalog():
    yaml_content = """
capabilities:
  - id: cap-payment
    name: Payment Processing
    level: L1
systems:
  - id: sys-billing
    name: Cloud Billing
    capabilities: [cap-payment]
    tags: [fintech]
interfaces:
  - id: iface-payments-api
    name: Payments API
    protocol: REST
    provider_system_id: sys-billing
technologies:
  - id: tech-postgres
    name: PostgreSQL
    category: database
"""
    graph = C4EAMParser().parse_content(yaml_content)
    entities = BackstageConnector.export_catalog(graph)
    assert len(entities) >= 4

    kinds = {e["kind"] for e in entities}
    assert "Domain" in kinds
    assert "System" in kinds
    assert "Component" in kinds
    assert "API" in kinds
    assert "Resource" in kinds

    exported_yaml = BackstageConnector.export_yaml(graph)
    assert "apiVersion: backstage.io/v1alpha1" in exported_yaml
    assert "kind: Domain" in exported_yaml
    assert "kind: System" in exported_yaml


def test_backstage_connector_import_catalog():
    backstage_yaml = """
apiVersion: backstage.io/v1alpha1
kind: Domain
metadata:
  name: domain-logistics
  title: Logistics Domain
spec:
  owner: team-logistics
---
apiVersion: backstage.io/v1alpha1
kind: System
metadata:
  name: system-tracking
  title: Tracking System
spec:
  owner: team-logistics
  domain: domain-logistics
---
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: api-tracking-rest
  title: Tracking REST API
spec:
  type: openapi
  system: system-tracking
"""
    manifest = BackstageConnector.import_catalog(backstage_yaml)
    assert len(manifest["capabilities"]) == 1
    assert manifest["capabilities"][0]["id"] == "domain-logistics"
    assert len(manifest["systems"]) == 1
    assert manifest["systems"][0]["id"] == "system-tracking"
    assert len(manifest["interfaces"]) == 1
    assert manifest["interfaces"][0]["id"] == "api-tracking-rest"


def test_archimate_connector_export_xml():
    yaml_content = """
capabilities:
  - id: cap-l1
    name: Sales Capability
    level: L1
  - id: cap-l2
    name: Lead Management
    level: L2
    parent_id: cap-l1
systems:
  - id: sys-crm
    name: CRM Application
    capabilities: [cap-l2]
relationships:
  - source_id: sys-crm
    target_id: sys-crm
    description: Self loop
plateaus:
  - id: plat-1
    name: Baseline
"""
    graph = C4EAMParser().parse_content(yaml_content)
    xml_str = ArchiMateConnector.export_xml(graph, model_name="Test Model")

    assert 'xmlns="http://www.opengroup.org/xsd/archimate/3.0/"' in xml_str
    assert '<name>Test Model</name>' in xml_str
    assert 'xsi:type="Capability"' in xml_str
    assert 'xsi:type="ApplicationComponent"' in xml_str
    assert 'xsi:type="Plateau"' in xml_str
    assert 'xsi:type="Realization"' in xml_str
    assert 'xsi:type="Composition"' in xml_str


def test_archimate_connector_import_xml():
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       identifier="id-test">
  <name>Imported Model</name>
  <elements>
    <element identifier="cap-orders" xsi:type="Capability">
      <name>Orders</name>
      <documentation>Order processing</documentation>
    </element>
    <element identifier="sys-store" xsi:type="ApplicationComponent">
      <name>Online Store</name>
    </element>
    <element identifier="node-db" xsi:type="Node">
      <name>PostgreSQL Server</name>
    </element>
  </elements>
  <relationships>
    <relationship identifier="r1" source="sys-store" target="cap-orders" xsi:type="Realization"/>
  </relationships>
</model>"""
    manifest = ArchiMateConnector.import_xml(xml_content)
    assert len(manifest["capabilities"]) == 1
    assert manifest["capabilities"][0]["id"] == "cap-orders"
    assert len(manifest["systems"]) == 1
    assert manifest["systems"][0]["id"] == "sys-store"
    assert manifest["systems"][0]["capabilities"] == ["cap-orders"]
    assert len(manifest["technologies"]) == 1
    assert manifest["technologies"][0]["id"] == "node-db"
