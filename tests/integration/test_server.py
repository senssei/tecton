"""Integration tests for Tecton Headless Architecture Intelligence REST API server."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from tecton_arch.server.app import create_app


@pytest.fixture
def client() -> TestClient:
    workspace = Path(__file__).parents[2] / "examples" / "c4_eam_workspace"
    app = create_app(workspace)
    return TestClient(app)


def test_server_health(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["applications"] == 3
    assert data["capabilities"] == 6
    assert data["technologies"] == 4
    assert data["data_objects"] == 3
    assert data["interfaces"] == 2
    assert data["plateaus"] == 2
    assert data["work_packages"] == 2


def test_server_overview(client: TestClient):
    response = client.get("/api/v1/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.1.0"
    assert data["total_applications"] == 3
    assert data["total_capabilities"] == 6
    assert data["total_technologies"] == 4
    assert data["technologies_past_eol"] == 1
    assert data["total_plateaus"] == 2
    assert data["total_work_packages"] == 2
    assert data["quality_gate_valid"] is True


def test_server_reload(client: TestClient):
    response = client.post("/api/v1/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reloaded"
    assert data["applications"] == 3


def test_server_validate(client: TestClient):
    response = client.get("/api/v1/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["error_count"] == 0
    assert data["warning_count"] >= 1


def test_server_apm_endpoints(client: TestClient):
    # 1. Applications
    response = client.get("/api/v1/apm/applications")
    assert response.status_code == 200
    apps = response.json()
    assert len(apps) == 3
    app_ids = {a["id"] for a in apps}
    assert "sys-crm-core" in app_ids
    assert "sys-legacy-billing" in app_ids

    # 2. Analysis
    res_analysis = client.get("/api/v1/apm/analysis")
    assert res_analysis.status_code == 200
    analysis = res_analysis.json()
    assert analysis["total_applications"] == 3
    assert "INVEST" in analysis["time_distribution"]
    assert "ELIMINATE" in analysis["time_distribution"]


def test_server_bcm_endpoints(client: TestClient):
    # 1. Capabilities
    res_caps = client.get("/api/v1/bcm/capabilities")
    assert res_caps.status_code == 200
    caps = res_caps.json()
    assert len(caps) == 6

    # 2. Coverage
    res_cov = client.get("/api/v1/bcm/coverage")
    assert res_cov.status_code == 200
    cov = res_cov.json()
    assert cov["total_capabilities"] == 6
    assert "cap-order-capture" in cov["coverages"]


def test_server_trm_endpoints(client: TestClient):
    # 1. Technologies
    res_techs = client.get("/api/v1/trm/technologies")
    assert res_techs.status_code == 200
    techs = res_techs.json()
    assert techs["total_technologies"] == 4
    assert techs["approved_count"] == 3
    assert techs["deprecated_count"] == 1

    # 2. Blast radius valid
    res_br = client.get("/api/v1/trm/blast-radius/tech-legacy-solaris")
    assert res_br.status_code == 200
    br = res_br.json()
    assert br["technology_id"] == "tech-legacy-solaris"
    assert br["status"] == "deprecated"
    assert len(br["directly_affected_system_ids"]) == 1

    # 3. Blast radius 404
    res_br_404 = client.get("/api/v1/trm/blast-radius/unknown-tech")
    assert res_br_404.status_code == 404


def test_server_data_lineage_endpoints(client: TestClient):
    # 1. Data objects
    res_do = client.get("/api/v1/data/objects")
    assert res_do.status_code == 200
    objects = res_do.json()
    assert len(objects) == 3

    # 2. Interfaces
    res_if = client.get("/api/v1/data/interfaces")
    assert res_if.status_code == 200
    interfaces = res_if.json()
    assert len(interfaces) == 2

    # 3. Lineage valid
    res_lin = client.get("/api/v1/data/lineage/do-customer-profile")
    assert res_lin.status_code == 200
    lineage = res_lin.json()
    assert lineage["data_object_id"] == "do-customer-profile"
    assert lineage["classification"] == "RESTRICTED_PII"
    assert lineage["risk_count"] == 3

    # 4. Lineage 404
    res_lin_404 = client.get("/api/v1/data/lineage/non-existent-do")
    assert res_lin_404.status_code == 404


def test_server_roadmap_endpoints(client: TestClient):
    # 1. Plateaus
    res_plat = client.get("/api/v1/roadmap/plateaus")
    assert res_plat.status_code == 200
    plateaus = res_plat.json()
    assert len(plateaus) == 2
    assert plateaus[0]["id"] == "plateau-2026-as-is"

    # 2. Work packages
    res_wp = client.get("/api/v1/roadmap/work-packages")
    assert res_wp.status_code == 200
    wps = res_wp.json()
    assert len(wps) == 2

    # 3. Analyze
    res_an = client.get("/api/v1/roadmap/analyze")
    assert res_an.status_code == 200
    report = res_an.json()
    assert report["total_plateaus"] == 2
    assert report["total_work_packages"] == 2
    assert len(report["transitional_gaps"]) == 1

    # 4. Compare
    res_comp = client.get("/api/v1/roadmap/compare?from_plateau=plateau-2026-as-is&to_plateau=plateau-2027-target")
    assert res_comp.status_code == 200
    comp = res_comp.json()
    assert comp["from_plateau_id"] == "plateau-2026-as-is"
    assert comp["to_plateau_id"] == "plateau-2027-target"
    assert comp["decommissioned_system_ids"] == ["sys-legacy-billing"]
    assert comp["tech_debt_reduction_count"] == 1


def test_server_diagram_endpoints(client: TestClient):
    # 1. TIME matrix
    res_time = client.get("/api/v1/diagrams/time-matrix")
    assert res_time.status_code == 200
    assert "quadrantChart" in res_time.json()["content"]

    # 2. Capability heatmap
    res_bcm = client.get("/api/v1/diagrams/capability-heatmap")
    assert res_bcm.status_code == 200
    assert "flowchart TD" in res_bcm.json()["content"]

    # 3. Tech radar
    res_trm = client.get("/api/v1/diagrams/tech-radar")
    assert res_trm.status_code == 200
    assert "flowchart LR" in res_trm.json()["content"]

    # 4. Data lineage with data_id
    res_lin = client.get("/api/v1/diagrams/data-lineage?data_id=do-customer-profile")
    assert res_lin.status_code == 200
    assert "flowchart LR" in res_lin.json()["content"]

    # 5. Roadmap Gantt
    res_gantt = client.get("/api/v1/diagrams/roadmap-gantt")
    assert res_gantt.status_code == 200
    assert "gantt" in res_gantt.json()["content"]

    # 6. Data lineage missing data_id -> 400
    res_bad = client.get("/api/v1/diagrams/data-lineage")
    assert res_bad.status_code == 400

    # 7. Unknown chart type -> 400
    res_unknown = client.get("/api/v1/diagrams/non-existent-chart")
    assert res_unknown.status_code == 400


def test_server_connector_export_endpoints(client: TestClient):
    # 1. Backstage
    res_bs = client.get("/api/v1/export/backstage")
    assert res_bs.status_code == 200
    data_bs = res_bs.json()
    assert data_bs["format"] == "yaml"
    assert data_bs["entities_count"] >= 10
    assert "backstage.io/v1alpha1" in data_bs["content"]

    # 2. ArchiMate XML raw
    res_arch = client.get("/api/v1/export/archimate")
    assert res_arch.status_code == 200
    assert "application/xml" in res_arch.headers["content-type"]
    assert "http://www.opengroup.org/xsd/archimate/3.0/" in res_arch.text

    # 3. ArchiMate JSON envelope
    res_arch_json = client.get("/api/v1/export/archimate?format=json")
    assert res_arch_json.status_code == 200
    data_arch = res_arch_json.json()
    assert data_arch["format"] == "xml"
    assert "Tecton Architecture Model" in data_arch["content"]

    # 4. Archi Native format via dialect query
    res_archi_dialect = client.get("/api/v1/export/archimate?dialect=archi")
    assert res_archi_dialect.status_code == 200
    assert "xmlns:archimate=\"http://www.archimatetool.com/archimate\"" in res_archi_dialect.text
    assert "<folder name=\"Strategy\"" in res_archi_dialect.text

    # 5. Dedicated /api/v1/export/archi endpoint
    res_archi_dedicated = client.get("/api/v1/export/archi")
    assert res_archi_dedicated.status_code == 200
    assert "xmlns:archimate=\"http://www.archimatetool.com/archimate\"" in res_archi_dedicated.text
    assert "<folder name=\"Application\"" in res_archi_dedicated.text


def test_server_portal_endpoints(client: TestClient):
    # Root portal
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "text/html" in res_root.headers["content-type"]
    assert "TECTON" in res_root.text
    assert "Architecture Intelligence" in res_root.text

    # /portal alias
    res_portal = client.get("/portal")
    assert res_portal.status_code == 200
    assert "text/html" in res_portal.headers["content-type"]
    assert "Executive Overview" in res_portal.text


def test_server_cors_headers(client: TestClient):
    response = client.get("/api/v1/health", headers={"Origin": "https://example.com"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"
    # Starlette forbids credentials with wildcard origin:
    assert response.headers.get("access-control-allow-credentials") is None


def test_server_reload_with_token(client: TestClient, monkeypatch):
    monkeypatch.setenv("TECTON_API_TOKEN", "secure-token-xyz")

    # Unauthorized request without token
    res_unauth = client.post("/api/v1/reload")
    assert res_unauth.status_code == 401

    # Unauthorized request with wrong token
    res_bad = client.post("/api/v1/reload", headers={"Authorization": "Bearer wrong-token"})
    assert res_bad.status_code == 401

    # Authorized request with valid token
    res_auth = client.post("/api/v1/reload", headers={"Authorization": "Bearer secure-token-xyz"})
    assert res_auth.status_code == 200
    assert res_auth.json()["status"] == "reloaded"



