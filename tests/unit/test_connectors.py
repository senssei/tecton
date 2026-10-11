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
    assert "Test Model" in xml_str
    assert 'xsi:type="Capability"' in xml_str
    assert 'xsi:type="ApplicationComponent"' in xml_str
    assert 'xsi:type="Plateau"' in xml_str
    assert 'xsi:type="Realization"' in xml_str
    assert 'xsi:type="Composition"' in xml_str
    assert '<views>' in xml_str
    assert '<diagrams>' in xml_str
    assert "C4 System Landscape" in xml_str


def test_archimate_connector_export_archi_xml():
    yaml_content = """
capabilities:
  - id: cap-payment
    name: Payments
    level: L1
systems:
  - id: sys-billing
    name: Billing Engine
    capabilities: [cap-payment]
interfaces:
  - id: iface-pay
    name: Payment API
    provider_system_id: sys-billing
technologies:
  - id: tech-db
    name: Database Node
plateaus:
  - id: plat-cur
    name: Current Plateau
work_packages:
  - id: wp-mig
    name: Cloud Migration
relationships:
  - source_id: sys-billing
    target_id: sys-billing
    description: Internal Loop
"""
    graph = C4EAMParser().parse_content(yaml_content)
    archi_xml = ArchiMateConnector.export_archi_xml(graph, model_name="Archi Native Test")

    assert 'xmlns:archimate="http://www.archimatetool.com/archimate"' in archi_xml
    assert 'name="Archi Native Test"' in archi_xml
    assert '<folder name="Strategy" id="id-folder-strategy" type="strategy">' in archi_xml
    assert '<folder name="Application" id="id-folder-application" type="application">' in archi_xml
    assert '<folder name="Technology &amp; Physical"' in archi_xml
    assert '<folder name="Relations" id="id-folder-relations" type="relations">' in archi_xml
    assert '<folder name="Views" id="id-folder-views" type="diagrams">' in archi_xml

    # Check typed elements inside folders
    assert 'xsi:type="archimate:Capability"' in archi_xml
    assert 'name="Payments"' in archi_xml
    assert 'xsi:type="archimate:ApplicationComponent"' in archi_xml
    assert 'name="Billing Engine"' in archi_xml
    assert 'xsi:type="archimate:RealizationRelationship"' in archi_xml
    assert 'name="Realizes"' in archi_xml
    assert 'xsi:type="archimate:ArchimateDiagramModel"' in archi_xml
    assert 'name="C4 System Landscape"' in archi_xml
    assert 'name="Business Capability Map"' in archi_xml
    assert 'name="Transformation Roadmap"' in archi_xml


def test_archimate_connector_import_xml():
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       identifier="id-test">
  <name xml:lang="en">Imported Model</name>
  <elements>
    <element identifier="cap-orders" xsi:type="Capability">
      <name xml:lang="en">Orders</name>
      <documentation xml:lang="en">Order processing</documentation>
    </element>
    <element identifier="sys-store" xsi:type="ApplicationComponent">
      <name xml:lang="en">Online Store</name>
    </element>
    <element identifier="node-db" xsi:type="Node">
      <name xml:lang="en">PostgreSQL Server</name>
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


def test_archimate_connector_import_archi_native_xml():
    native_xml = """<?xml version="1.0" encoding="utf-8"?>
<archimate:model xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:archimate="http://www.archimatetool.com/archimate" name="Native Model" id="id-model" version="5.0.0">
  <folder name="Strategy" id="f-strat" type="strategy">
    <element xsi:type="archimate:Capability" id="cap-cust" name="Customer Management">
      <documentation>Handles customer CRM</documentation>
    </element>
  </folder>
  <folder name="Application" id="f-app" type="application">
    <element xsi:type="archimate:ApplicationComponent" id="sys-portal" name="Customer Portal"/>
  </folder>
  <folder name="Relations" id="f-rel" type="relations">
    <element xsi:type="archimate:RealizationRelationship" id="r-real" source="sys-portal" target="cap-cust" name="Realizes"/>
  </folder>
</archimate:model>"""
    manifest = ArchiMateConnector.import_xml(native_xml)
    assert len(manifest["capabilities"]) == 1
    assert manifest["capabilities"][0]["id"] == "cap-cust"
    assert manifest["capabilities"][0]["name"] == "Customer Management"
    assert len(manifest["systems"]) == 1
    assert manifest["systems"][0]["id"] == "sys-portal"
    assert manifest["systems"][0]["capabilities"] == ["cap-cust"]


def test_archimate_connector_roundtrip_id_stability():
    yaml_content = """
capabilities:
  - id: cap-payment-processing
    name: Payment Processing
    level: L1
systems:
  - id: sys-billing-core
    name: Core Billing Engine
    capabilities: [cap-payment-processing]
  - id: sys-order-processor
    name: Order Processing Service
relationships:
  - source_id: sys-order-processor
    target_id: sys-billing-core
    description: Transmits invoice
"""
    graph = C4EAMParser().parse_content(yaml_content)
    xml_out = ArchiMateConnector.export_xml(graph)

    imported = ArchiMateConnector.import_xml(xml_out)

    sys_ids = {s["id"] for s in imported["systems"]}
    assert "sys-billing-core" in sys_ids
    assert "sys-order-processor" in sys_ids

    cap_ids = {c["id"] for c in imported["capabilities"]}
    assert "cap-payment-processing" in cap_ids

    # Verify flow relationship matches original domain IDs
    assert len(imported["relationships"]) == 1
    rel = imported["relationships"][0]
    assert rel["source_id"] == "sys-order-processor"
    assert rel["target_id"] == "sys-billing-core"


def test_archi_native_roundtrip_id_stability():
    yaml_content = """
capabilities:
  - id: cap-warehouse-ops
    name: Warehouse Operations
systems:
  - id: sys-inventory-mgmt
    name: Inventory Management
    capabilities: [cap-warehouse-ops]
  - id: sys-shipping-router
    name: Shipping Router
relationships:
  - source_id: sys-inventory-mgmt
    target_id: sys-shipping-router
    description: Routes shipment
"""
    graph = C4EAMParser().parse_content(yaml_content)
    archi_out = ArchiMateConnector.export_archi_xml(graph)

    imported = ArchiMateConnector.import_xml(archi_out)

    sys_ids = {s["id"] for s in imported["systems"]}
    assert "sys-inventory-mgmt" in sys_ids
    assert "sys-shipping-router" in sys_ids

    assert len(imported["relationships"]) == 1
    rel = imported["relationships"][0]
    assert rel["source_id"] == "sys-inventory-mgmt"
    assert rel["target_id"] == "sys-shipping-router"


def test_backstage_connector_roundtrip_id_stability():
    yaml_content = """
capabilities:
  - id: cap-customer-support
    name: Customer Support
systems:
  - id: sys-crm-central
    name: Central CRM
    capabilities: [cap-customer-support]
"""
    graph = C4EAMParser().parse_content(yaml_content)
    backstage_out = BackstageConnector.export_yaml(graph)

    imported = BackstageConnector.import_catalog(backstage_out)
    assert any(s["id"] == "sys-crm-central" for s in imported["systems"])
    assert any(c["id"] == "cap-customer-support" for c in imported["capabilities"])


def test_id_mapper_collision_detection():
    from tecton.connectors.id_mapper import IdCollisionError, IdMapper
    import pytest

    mapper = IdMapper()

    # Backstage name collision test
    mapper.register_backstage_name("order_service")
    with pytest.raises(IdCollisionError, match="Backstage name collision"):
        # "order-service" normalizes to the same "order-service" name
        mapper.register_backstage_name("order-service")

    # XML ID collision test
    mapper_xml = IdMapper()
    mapper_xml.register_xml_id("crm:core")
    with pytest.raises(IdCollisionError, match="XML ID collision"):
        # "crm_core" normalizes to the same "id-crm_core"
        mapper_xml.register_xml_id("crm_core")
