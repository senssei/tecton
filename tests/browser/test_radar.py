"""Run with: python -m pytest tests/browser (requires Playwright + Chromium)."""
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")

from tecton_arch.application import TectonApp
from tecton_arch.portal.builder import PortalBuilder

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def page():
    with playwright.sync_playwright() as driver:
        browser = driver.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.route("http://**/*", lambda route: route.abort())
        page.route("https://**/*", lambda route: route.abort())
        yield page
        browser.close()


@pytest.mark.parametrize("catalog", ["c4_eam_workspace", "dogfood/tecton_c4_workspace"])
def test_radar_offline_filters_selection_and_zoom(page, tmp_path, catalog):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    model = TectonApp(ROOT / "examples" / catalog)
    path = PortalBuilder.export_portal(model, tmp_path)
    page.goto(path.as_uri())
    page.locator('[data-tab="trm"]').click()
    host = page.locator('#technology-radar')
    assert host.locator('.radar-marker').count() == len(model.graph.technologies)
    page.screenshot(path=str(tmp_path / 'radar.png'), full_page=True)
    host.locator('.radar-list button').first.click()
    assert "Impact analysis" in host.locator('.radar-detail').inner_text()
    assert "Static pre-computed report" not in host.locator('.radar-detail').inner_text()
    host.locator('.radar-marker').first.focus()
    page.keyboard.press('Enter')
    assert host.locator('.radar-marker[aria-pressed="true"]').count() == 1
    host.locator('[data-action="in"]').click()
    host.locator('[data-action="reset"]').click()
    host.locator('[data-filter="search"]').fill('no-such-technology')
    assert "No technologies match" in host.inner_text()
    host.locator('[data-action="clear"]').click()
    assert host.locator('.radar-marker').count() == len(model.graph.technologies)
    host.locator('.radar-list button').first.focus()
    page.keyboard.press('Enter')
    assert host.locator('.radar-list button[aria-pressed="true"]').count() == 1
    page.set_viewport_size({"width": 390, "height": 844})
    assert host.locator('.radar-list').is_visible()
    assert not errors


def test_dense_layout_is_repeatable_and_stays_in_bounds(page, tmp_path):
    path = PortalBuilder.export_portal(TectonApp(ROOT / 'examples/c4_eam_workspace'), tmp_path)
    page.goto(path.as_uri())
    result = page.evaluate("""() => {
      const tech = Array.from({length:40}, (_,i)=>({id:`t-${i}`,name:`Technology ${i}`,category:'Runtime',status:'approved',count:1}));
      const first = TectonRadar.layout(tech,['Runtime','Framework','Database','Tools']);
      const second = TectonRadar.layout(tech,['Runtime','Framework','Database','Tools']);
      return {count:first.nodes.length, stable:JSON.stringify(first)===JSON.stringify(second),
        collisions:first.nodes.some((n,i)=>first.nodes.slice(i+1).some(m=>Math.hypot(n.x-m.x,n.y-m.y)<n.r+m.r)),
        bounds:first.nodes.every(n=>Math.hypot(n.x,n.y)>=n.low-.001 && Math.hypot(n.x,n.y)<=n.high+.001)};
    }""")
    assert result == {"count": 40, "stable": True, "collisions": False, "bounds": True}


def test_full_dfd_and_component_panel(page, tmp_path):
    path = PortalBuilder.export_portal(TectonApp(ROOT / 'examples/c4_eam_workspace'), tmp_path)
    page.goto(path.as_uri())
    page.locator('[data-tab="data"]').click()
    diagram = page.locator('#dfd-view')
    assert diagram.locator('.dfd-node').count() == 5
    assert 'Rounded boxes: processes' in diagram.inner_text()
    diagram.locator('summary').click()
    assert 'Submitted sales order' in diagram.inner_text()
    page.screenshot(path=str(tmp_path / 'dfd.png'), full_page=True)
    path = PortalBuilder.export_portal(TectonApp(ROOT / 'examples/dogfood/tecton_c4_workspace'), tmp_path)
    page.goto(path.as_uri())
    page.locator('[data-tab="data"]').click()
    assert 'No data flow diagram defined' in page.locator('#dfd-view').inner_text()
    page.locator('[data-tab="apm"]').click()
    page.locator('[data-components]').click()
    dialog = page.locator('#components-dialog')
    assert dialog.is_visible()
    assert dialog.locator('.component-card').count() == 15
    assert dialog.locator('.component-card').first.bounding_box()['width'] >= 260
    page.screenshot(path=str(tmp_path / 'components.png'), full_page=True)
    page.keyboard.press('Escape')
    assert not dialog.is_visible()


def test_live_radar_uses_real_api_data(page):
    import json
    model = TectonApp(ROOT / 'examples/c4_eam_workspace')
    snapshot = model.portal_snapshot()
    response_map = {
        '/api/v1/catalog/freshness': model.catalog_freshness(),
        '/api/v1/apm/costs': model.apm_costs(),
        '/api/v1/roadmap/business-case': model.roadmap_business_cases(),
        '/api/v1/roadmap/feasibility': model.roadmap_feasibility(),
        '/api/v1/overview': model.overview().model_dump(mode='json'),
        '/api/v1/validate': model.validate().model_dump(mode='json'),
        '/api/v1/apm/applications': model.apm_applications(),
        '/api/v1/bcm/capabilities': model.bcm_capabilities(),
        '/api/v1/bcm/coverage': model.bcm_analysis(),
        '/api/v1/trm/technologies': model.trm_evaluation(),
        '/api/v1/data/objects': model.data_objects(),
        '/api/v1/data/interfaces': model.interfaces(),
        '/api/v1/data/flow-diagrams': model.data_flow_diagrams(),
        '/api/v1/roadmap/plateaus': model.list_plateaus(),
        '/api/v1/roadmap/work-packages': model.list_work_packages(),
    }
    from urllib.parse import urlparse
    def serve(route):
        path = urlparse(route.request.url).path
        if path == '/':
            route.fulfill(body=PortalBuilder.build_dynamic_portal_html(), content_type='text/html')
        elif path.startswith('/api/v1/trm/blast-radius/'):
            route.fulfill(body=json.dumps(model.trm_blast_radius(path.rsplit('/', 1)[1])), content_type='application/json')
        elif path == '/api/v1/roadmap/compare':
            route.fulfill(body='{}', content_type='application/json')
        elif path in response_map:
            route.fulfill(body=json.dumps(response_map[path], default=str), content_type='application/json')
        elif path.startswith('/api/v1/diagrams/'):
            key = path.rsplit('/', 1)[1]
            route.fulfill(body=json.dumps({'content': snapshot['diagrams'].get(key, '')}), content_type='application/json')
        else:
            route.fulfill(status=404, body='{}', content_type='application/json')
    page.route('http://tecton.test/**', serve)
    page.goto('http://tecton.test/')
    page.locator('[data-tab="trm"]').click()
    page.wait_for_function("document.querySelectorAll('.radar-list button').length === 4")
    page.locator('.radar-list button').first.click()
    page.wait_for_function("document.querySelector('.radar-detail').textContent.includes('Risk score:')")
    assert 'Impact analysis' in page.locator('.radar-detail').inner_text()


def test_readable_roadmap(page, tmp_path):
    model = TectonApp(ROOT / 'examples/c4_eam_workspace')
    snapshot = model.portal_snapshot()
    assert snapshot['workPackages'] == model.list_work_packages()
    assert snapshot['plateaus'] == model.list_plateaus()
    path = PortalBuilder.export_portal(model, tmp_path)
    page.goto(path.as_uri())
    page.locator('[data-tab="roadmap"]').click()
    host = page.locator('#roadmap-schedule')
    assert host.locator('.schedule-label').count() == 4
    assert host.locator('.schedule-bar').count() == 2
    assert host.locator('path.schedule-milestone').count() == 2
    assert '01 Jul 2026 – 30 Jun 2027' in host.inner_text()
    assert host.locator('.schedule-bar text').count() == 0
    page.screenshot(path=str(tmp_path / 'roadmap.png'), full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert host.locator('.schedule-scroll').evaluate('(el) => el.scrollWidth > el.clientWidth')
    page.evaluate("TectonRoadmap.render(document.querySelector('#roadmap-schedule'), {plateaus:[],workPackages:[{id:'unknown',name:'Unscheduled initiative'}]})")
    assert host.locator('.schedule-bar').count() == 0
    assert 'Dates not specified' in host.inner_text()


def test_capability_heatmap_preserves_hierarchy(page, tmp_path):
    model = TectonApp(ROOT / 'examples/c4_eam_workspace')
    assert model.portal_snapshot()['capabilities'] == model.bcm_capabilities()
    page.goto(PortalBuilder.export_portal(model, tmp_path).as_uri())
    page.locator('[data-tab="bcm"]').click()
    host = page.locator('#capability-heatmap')
    assert host.locator('.capability-area').count() == 3
    assert host.locator('.capability-cell').count() == 6
    orders = host.locator('.capability-area[aria-label="Order Management"]')
    assert orders.locator('.capability-children .heat-healthy').count() == 2
    assert orders.locator('.capability-cell').first.locator('summary').inner_text().lower().find('no direct systems') >= 0
    risk = host.locator('.heat-at-risk')
    risk.locator('summary').click()
    assert 'Mainframe Monolith Billing System' in risk.inner_text()
    page.screenshot(path=str(tmp_path / 'heatmap.png'), full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert host.evaluate('(el) => el.scrollWidth <= el.clientWidth')


def test_lineage_transfer_channels(page, tmp_path):
    model = TectonApp(ROOT / 'examples/c4_eam_workspace')
    snapshot = model.portal_snapshot()
    assert snapshot['lineageReports']['do-order-record'] == model.data_lineage('do-order-record')
    page.goto(PortalBuilder.export_portal(model, tmp_path).as_uri())
    page.locator('[data-tab="data"]').click()
    page.locator('#lineage-data-select').select_option('do-order-record')
    host = page.locator('#mermaid-data-lineage')
    assert host.locator('.lineage-edge').count() == 2
    assert host.locator('.lineage-node').count() == 3
    assert host.locator('[data-system-id="sys-order-router"]').count() == 1
    assert 'depends_on (' not in host.inner_text()
    assert 'CRM Order Submission API' in host.inner_text()
    page.screenshot(path=str(tmp_path / 'lineage.png'), full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert host.evaluate('(el) => el.scrollWidth <= el.clientWidth')


def test_lineage_branch_and_cycle_keep_unique_nodes(page, tmp_path):
    page.goto(PortalBuilder.export_portal(TectonApp(ROOT / 'examples/c4_eam_workspace'), tmp_path).as_uri())
    result = page.evaluate("""() => {
      const host=document.createElement('div');host.style.width='1000px';document.body.append(host);
      const edges=[['a','b'],['a','c'],['b','d'],['c','d'],['d','a']].map(([s,t])=>({source_system_id:s,source_system_name:s,target_system_id:t,target_system_name:t,channels:new Map([['one',{name:'Channel',protocol:'REST'}]])}));
      TectonLineage.render(host,edges);
      return {nodes:host.querySelectorAll('.lineage-node').length,edges:host.querySelectorAll('.lineage-edge').length};
    }""")
    assert result == {'nodes':4,'edges':5}


def test_scenario_comparison_explains_losses_and_reverse(page, tmp_path):
    model = TectonApp(ROOT / 'examples/c4_eam_workspace')
    page.goto(PortalBuilder.export_portal(model, tmp_path).as_uri())
    page.locator('[data-tab="roadmap"]').click()
    host = page.locator('#scenario-compare-result')
    assert 'Mainframe Monolith Billing System' in host.inner_text()
    assert 'Invoicing & Accounts Receivable' in host.locator('.scenario-warning').inner_text()
    assert host.locator('.scenario-loss > strong').inner_text() == '-1'
    assert 'sys-legacy-billing' not in host.inner_text()
    page.screenshot(path=str(tmp_path / 'comparison.png'), full_page=True)
    page.locator('#compare-from-select').select_option('plateau-2027-target')
    page.locator('#compare-to-select').select_option('plateau-2026-as-is')
    page.locator('#compare-button').click()
    assert '+1' in host.inner_text()
    assert host.locator('.scenario-warning').count() == 0
    page.locator('#compare-to-select').select_option('plateau-2027-target')
    page.locator('#compare-button').click()
    assert 'two different' in host.inner_text()


def test_portal_fully_offline_bundled_mermaid_and_tailwind(page, tmp_path):
    path = PortalBuilder.export_portal(TectonApp(ROOT / 'examples/c4_eam_workspace'), tmp_path)
    page.goto(path.as_uri())
    # Verify no CDN assets were required and runtime objects exist offline
    assert page.evaluate("typeof tailwind !== 'undefined'")
    assert page.evaluate("typeof mermaid !== 'undefined'")
    assert page.evaluate("typeof d3 !== 'undefined'")
    # Switch to APM tab and verify Mermaid renders the quadrant chart SVG offline
    page.locator('[data-tab="apm"]').click()
    page.wait_for_selector("#mermaid-time-matrix svg")
    assert page.locator("#mermaid-time-matrix svg").count() >= 1



def test_planning_reports_offline_and_immutable_date(page, tmp_path):
    from datetime import date
    model=TectonApp(ROOT/'examples/planning',as_of_date=date(2026,6,1))
    path=PortalBuilder.export_portal(model,tmp_path)
    errors=[]
    page.on('pageerror',lambda error: errors.append(str(error)))
    page.goto(path.as_uri())
    page.locator('[data-tab="planning"]').click()
    assert page.locator('#evaluation-date').input_value()=='2026-06-01'
    assert page.locator('#evaluation-date').is_disabled()
    assert '300.30' in page.locator('#portfolio-costs').inner_text()
    assert 'violations detected' in page.locator('#plan-feasibility').inner_text()
    assert 'TEAM_CAPACITY_EXCEEDED' in page.locator('#plan-feasibility').inner_text()
    assert 'Annual savings after migration' in page.locator('#business-cases').inner_text()
    page.set_viewport_size({'width':390,'height':844})
    assert page.locator('#plan-feasibility').is_visible()
    assert not errors


def test_live_portal_uses_one_date_for_all_reports(page):
    import json
    from datetime import date
    from urllib.parse import urlparse, parse_qs
    requests=[]
    def serve(route):
        url=urlparse(route.request.url)
        if url.path=='/':
            route.fulfill(body=PortalBuilder.build_dynamic_portal_html(),content_type='text/html')
            return
        target=parse_qs(url.query).get('as_of_date',['2026-06-01'])[0]
        requests.append((url.path,target))
        model=TectonApp(ROOT/'examples/planning',as_of_date=date.fromisoformat(target))
        payloads={
            '/api/v1/overview':model.overview().model_dump(mode='json'),
            '/api/v1/validate':model.validate().model_dump(mode='json'),
            '/api/v1/apm/applications':model.apm_applications(),
            '/api/v1/bcm/capabilities':model.bcm_capabilities(),
            '/api/v1/bcm/coverage':model.bcm_analysis(),
            '/api/v1/trm/technologies':model.trm_evaluation(),
            '/api/v1/data/objects':model.data_objects(),
            '/api/v1/data/interfaces':model.interfaces(),
            '/api/v1/data/flow-diagrams':model.data_flow_diagrams(),
            '/api/v1/roadmap/plateaus':model.list_plateaus(),
            '/api/v1/roadmap/work-packages':model.list_work_packages(),
            '/api/v1/catalog/freshness':model.catalog_freshness(),
            '/api/v1/apm/costs':model.apm_costs(),
            '/api/v1/roadmap/business-case':model.roadmap_business_cases(),
            '/api/v1/roadmap/feasibility':model.roadmap_feasibility(),
        }
        if url.path.startswith('/api/v1/diagrams/'):
            payload={'content':model.export('mermaid',{'diagram_type':url.path.rsplit('/',1)[1]}).content}
        elif url.path.startswith('/api/v1/data/lineage/'):
            payload=model.data_lineage(url.path.rsplit('/',1)[1])
        else:
            payload=payloads.get(url.path,{})
        route.fulfill(body=json.dumps(payload,default=str),content_type='application/json')
    page.route('http://planning.test/**',serve)
    page.goto('http://planning.test/')
    page.wait_for_function("state.applications.length === 2")
    page.wait_for_function("!document.querySelector('#mermaid-data-lineage').textContent.includes('Loading')")
    requests.clear()
    page.locator('#evaluation-date').fill('2026-06-01')
    page.locator('#evaluation-date').dispatch_event('change')
    page.wait_for_function("state.asOfDate === '2026-06-01' && !document.querySelector('#evaluation-date').disabled")
    assert requests and all(target=='2026-06-01' for _,target in requests)
    page.locator('[data-tab="planning"]').click()
    assert '300.30' in page.locator('#portfolio-costs').inner_text()
