"""Cross-module acceptance checks for review, governance and transformation planning."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import json
import yaml
import pytest
from pydantic import ValidationError
from tecton_arch.application import TectonApp, Workspace
from tecton_arch.core.config import TectonConfig
from tecton_arch.dsl.parser import C4EAMParser
from tecton_arch.dsl.schema import MoneyDef, ReviewDef, WorkPackageDef
from tecton_arch.engines.diff_engine import DiffEngine
from tecton_arch.engines.linter import GraphLinter
from tecton_arch.services.bcm_service import BCMService
from tecton_arch.services.catalog_service import CatalogService
from tecton_arch.services.finance_service import business_cases
from tecton_arch.services.feasibility_service import FeasibilityService
from tecton_arch.services.lineage_service import LineageService

MODEL = {
    'capabilities': [
        {'id': 'root', 'name': 'Root'},
        {'id': 'cap', 'name': 'Capability', 'parent_id': 'root', 'importance': 5},
        {'id': 'gap', 'name': 'Gap', 'parent_id': 'root', 'importance': 1},
    ],
    'systems': [
        {'id': 'old', 'name': 'Old', 'owner': 'team', 'functional_suitability': 1, 'technical_suitability': 1, 'time_classification': 'INVEST', 'capabilities': ['cap'], 'technologies': ['tech'], 'annual_cost': {'amount': '100.10', 'currency': 'PLN'}, 'review': {'reviewed_on': '2026-01-01', 'reviewed_by': 'team'}},
        {'id': 'new', 'name': 'New', 'functional_suitability': 5, 'technical_suitability': 5, 'capabilities': ['cap'], 'annual_cost': {'amount': '200.20', 'currency': 'PLN'}},
    ],
    'containers': [{'id': 'component', 'name': 'Component', 'system_id': 'old', 'technology': 'tech'}],
    'technologies': [{'id': 'tech', 'name': 'Runtime', 'eol_date': '2030-01-01'}],
    'data_objects': [{'id': 'data', 'name': 'Data', 'classification': 'RESTRICTED_PII'}],
    'interfaces': [{'id': 'api', 'name': 'API', 'provider_system_id': 'old', 'consumer_system_ids': ['new'], 'data_objects': ['data']}],
    'relationships': [{'source_id': 'old', 'target_id': 'new', 'data_objects': ['data']}],
    'plateaus': [
        {'id': 'baseline', 'name': 'Baseline', 'target_date': '2026-01-01', 'active_system_ids': ['old']},
        {'id': 'target', 'name': 'Target', 'previous_plateau_id': 'baseline', 'target_date': '2026-12-31', 'active_system_ids': ['new'], 'decommissioned_system_ids': ['old']},
    ],
    'work_packages': [{'id': 'migration', 'name': 'Migration', 'start_date': '2026-01-01', 'target_date': '2026-10-01', 'from_plateau_id': 'baseline', 'to_plateau_id': 'target', 'introduced_system_ids': ['new'], 'decommissioned_system_ids': ['old'], 'involved_system_ids': ['old', 'new'], 'realized_capability_ids': ['cap'], 'planned_cost': {'amount': '1000', 'currency': 'PLN'}, 'business_case': {'annual_net_savings': '500', 'horizon_years': 3, 'assumptions': ['Annual savings after migration']}, 'resource_allocations': [{'team_id': 'team', 'month': '2026-06', 'person_days': '30'}], 'spend_plan': [{'month': '2026-06', 'amount': '1000'}]}],
    'data_flow_diagrams': [{'id': 'dfd', 'name': 'DFD', 'nodes': [{'id': 'old', 'name': 'Process', 'kind': 'process', 'system_id': 'old'}, {'id': 'store', 'name': 'Store', 'kind': 'data_store'}], 'flows': [{'id': 'flow', 'name': 'Flow', 'source_id': 'old', 'target_id': 'store', 'data_objects': ['data']}]}],
}


def model():
    return json.loads(json.dumps(MODEL))


def graph(document=None):
    return C4EAMParser(strict=True).parse_content(yaml.safe_dump(document or MODEL))


def test_complete_diff_review_and_nested_paths():
    head = model()
    head['systems'][0]['owner'] = 'other'
    head['systems'][0]['technical_suitability'] = 5
    head['containers'] = []
    head['interfaces'][0]['description'] = 'Changed contract'
    head['data_flow_diagrams'][0]['nodes'][0]['name'] = 'Changed process'
    report = DiffEngine().compare(graph(), graph(head), as_of_date=date(2026, 6, 1))
    assert {'system', 'container', 'interface', 'data_flow_diagram'} <= {d.entity_type for d in report.deltas}
    changed = next(d for d in report.deltas if d.entity_id == 'old')
    assert changed.field_changes['owner'] == ('team', 'other')
    assert 'nodes.old.name' in next(d for d in report.deltas if d.entity_id == 'dfd').field_changes
    assert report.as_of_date == date(2026, 6, 1)
    assert report.config_fingerprint


@pytest.mark.parametrize('collection', ['capabilities','systems','containers','technologies','interfaces','data_objects','plateaus','work_packages','data_flow_diagrams'])
def test_diff_each_collection_add_remove(collection):
    head = model()
    head[collection] = []
    report = DiffEngine().compare(graph(), graph(head))
    assert any(d.change_type.value == 'REMOVED' for d in report.deltas)
    assert all(d.snapshot for d in report.deltas if d.change_type.value == 'REMOVED')


def test_relationship_multiset_and_metadata_order():
    head = model()
    head['relationships'].append(head['relationships'][0].copy())
    report = DiffEngine().compare(graph(), graph(head))
    assert len([d for d in report.deltas if d.entity_type == 'relationship']) == 1
    a, b = model(), model()
    a['systems'][0]['metadata'] = {'tags': ['a', 'b']}
    b['systems'][0]['metadata'] = {'tags': ['b', 'a']}
    assert DiffEngine().compare(graph(a), graph(b)).has_changes
    b = model(); b['systems'][0]['capabilities'] = ['cap']; b['systems'][0]['tags'] = ['b','a']
    a = model(); a['systems'][0]['tags'] = ['a','b']
    assert not DiffEngine().compare(graph(a), graph(b)).has_changes


def test_review_deadline_and_policy_levels():
    service = CatalogService(graph())
    assert next(i for i in service.freshness(date(2026, 6, 30))['items'] if i['entity_id'] == 'old')['status'] == 'current'
    assert next(i for i in service.freshness(date(2026, 7, 1))['items'] if i['entity_id'] == 'old')['status'] == 'overdue'
    assert next(i for i in service.freshness(date(2025, 1, 1))['items'] if i['entity_id'] == 'old')['status'] == 'future_dated'
    config = TectonConfig.model_validate({'quality': {'rules': {'REVIEW_OVERDUE': 'error', 'REVIEW_MISSING': 'warning'}}})
    report = GraphLinter().lint(graph(), as_of_date=date(2026,7,1), config=config)
    assert any(i.rule == 'REVIEW_OVERDUE' and i.severity.value == 'ERROR' for i in report.issues)
    with pytest.raises(ValidationError):
        TectonConfig.model_validate({'quality': {'rules': {'invented': 'off'}}})
    with pytest.raises(ValidationError):
        TectonConfig.model_validate({'quality': {'rules': {'DUPLICATE_ID': 'off'}}})


def test_owner_policies_and_review_validation():
    config = TectonConfig.model_validate({'owners': {'team': {'name': 'Team','active': False}}, 'quality': {'rules': {'OWNER_INACTIVE': 'error'}}})
    assert any(i.rule == 'OWNER_INACTIVE' for i in GraphLinter().lint(graph(), config=config).issues)
    with pytest.raises(ValidationError):
        ReviewDef(reviewed_on=date(2026,1,1))
    with pytest.raises(ValidationError):
        ReviewDef(reviewed_on=date(2026,1,1), reviewed_by='team', next_review_on=date(2025,1,1))


def test_rename_keeps_local_dfd_ids_and_sources(tmp_path):
    source = tmp_path/'source'; source.mkdir()
    original = yaml.safe_dump(MODEL)
    (source/'catalog.yaml').write_text(original)
    output = tmp_path/'result'
    result = CatalogService(graph()).rename('old', 'renamed', source, output)
    assert result['references_changed'] >= 5
    assert (source/'catalog.yaml').read_text() == original
    renamed = C4EAMParser(strict=True).parse_directory(output)
    assert 'renamed' in renamed.systems and 'old' not in renamed.systems
    assert renamed.data_flow_diagrams['dfd'].nodes[0].id == 'old'
    assert renamed.data_flow_diagrams['dfd'].nodes[0].system_id == 'renamed'
    assert renamed.data_flow_diagrams['dfd'].flows[0].source_id == 'old'
    assert renamed.relationships[0].source_id == 'renamed'
    assert GraphLinter().lint(renamed).is_valid
    with pytest.raises(ValueError):
        CatalogService(graph()).rename('old','new',source)
    with pytest.raises(ValueError):
        CatalogService(graph()).rename('old','renamed',source,source/'nested')


@pytest.mark.parametrize('entity_id,new_id', [('cap','cap2'),('tech','tech2'),('data','data2'),('baseline','base2'),('migration','migration2'),('component','comp2'),('api','api2'),('dfd','dfd2')])
def test_rename_all_global_types(tmp_path, entity_id, new_id):
    source=tmp_path/'source';source.mkdir()
    output=tmp_path/'out'
    result=CatalogService(graph()).rename(entity_id,new_id,source,output)
    assert result['valid']
    assert new_id in C4EAMParser(strict=True).parse_directory(output).all_symbol_ids()


def test_shared_classification_coverage_and_costs():
    app = TectonApp(Workspace.from_graph(graph()), as_of_date=date(2026,6,1))
    listing = {a['id']:a for a in app.apm_applications()}
    assert listing['old']['evaluated_time_classification'] == 'ELIMINATE'
    assert listing['old']['declared_time_classification'] == 'INVEST'
    assert listing['old']['classification_mismatch']
    bcm = BCMService(graph()).analyze()
    assert bcm.coverages['cap'].time_distribution == {'ELIMINATE':1, 'INVEST':1}
    assert bcm.coverages['root'].leaf_coverage_percentage == 50
    assert bcm.coverages['root'].weighted_leaf_coverage_percentage == pytest.approx(100*5/6)
    assert bcm.coverages['root'].annual_costs['totals_by_currency']['PLN'] == '300.30'
    assert app.apm_costs()['totals_by_currency']['PLN'] == '300.30'
    assert LineageService(graph()).trace_lineage('data').assessment_status == 'risks_detected'
    empty=model();empty['interfaces']=[];empty['relationships']=[]
    assert LineageService(graph(empty)).trace_lineage('data').assessment_status == 'no_modeled_flows'


def test_finances_exact_math_and_boundaries():
    case=business_cases(graph())['items'][0]
    assert Decimal(case['roi_percent']) == 50
    assert Decimal(case['payback_years']) == 2
    assert Decimal(case['net_benefit']) == 500
    data=model();data['work_packages'][0]['planned_cost']['amount']='0';data['work_packages'][0]['spend_plan']=[]
    assert business_cases(graph(data))['items'][0]['roi_percent'] is None
    data['work_packages'][0]['business_case']['annual_net_savings']='-1'
    assert business_cases(graph(data))['items'][0]['payback_years'] is None
    with pytest.raises(ValidationError):
        MoneyDef(amount='NaN',currency='PLN')
    with pytest.raises(ValidationError):
        MoneyDef(amount=1,currency='pln')
    with pytest.raises(ValidationError):
        WorkPackageDef.model_validate({**MODEL['work_packages'][0], 'spend_plan':[{'month':'2026-06','amount':'999'}]})


def test_feasibility_conflicts_and_completeness():
    config=TectonConfig.model_validate({'teams':{'team':{'capacity_person_days':'20'}}, 'budgets':{'2026-06':{'PLN':'900'}}})
    report=FeasibilityService(graph(),config).analyze(date(2026,6,1))
    assert report['assessment_status']=='violations_detected'
    assert {'TEAM_CAPACITY_EXCEEDED','BUDGET_EXCEEDED'} <= {i['rule'] for i in report['issues']}
    assert report['resource_usage'][0]['work_package_ids']==['migration']
    config=TectonConfig.model_validate({'teams':{'team':{'capacity_person_days':'30'}}, 'budgets':{'2026-06':{'PLN':'1000'}}})
    assert FeasibilityService(graph(),config).analyze()['assessment_status']=='no_detected_violations'
    assert FeasibilityService(graph()).analyze()['assessment_status']=='insufficient_data'


def test_cycles_return_structural_report():
    data=model();data['plateaus'][0]['previous_plateau_id']='target'
    report=FeasibilityService(graph(data)).analyze()
    assert not report['is_valid_dag']
    assert report['assessment_status']=='violations_detected'
    data=model();data['capabilities'][0]['parent_id']='cap'
    report=BCMService(graph(data)).analyze()
    assert report.aggregation_status == "unavailable"
    assert "cycle" in report.issues[0]


def test_rename_failure_never_changes_sources(tmp_path, monkeypatch):
    import tecton_arch.services.catalog_service as service
    source=tmp_path/'source';source.mkdir()
    before=yaml.safe_dump(MODEL)
    (source/'catalog.yaml').write_text(before)
    def fail(*args):
        raise OSError('Simulated publication failure')
    monkeypatch.setattr(service.os, 'rename', fail)
    with pytest.raises(OSError):
        CatalogService(graph()).rename('old','renamed',source,tmp_path/'out')
    assert (source/'catalog.yaml').read_text()==before
    assert not (tmp_path/'out').exists()
    assert not list(tmp_path.glob('.tecton-rename-*'))


def test_costs_never_mix_currencies_or_assume_missing_is_zero():
    data=model();data['systems'][1]['annual_cost']['currency']='EUR'
    app=TectonApp(Workspace.from_graph(graph(data)))
    assert app.apm_costs()['totals_by_currency']=={'EUR':'200.20','PLN':'100.10'}
    del data['systems'][1]['annual_cost']
    app=TectonApp(Workspace.from_graph(graph(data)))
    assert not app.apm_costs()['complete']
    assert app.apm_costs()['missing_system_ids']==['new']


def test_branched_plateaus_compare_actual_predecessor():
    data=model()
    data['plateaus'].append({'id':'branch','name':'Branch','previous_plateau_id':'baseline','active_system_ids':['old']})
    from tecton_arch.engines.roadmap_engine import RoadmapEngine
    report=RoadmapEngine(graph(data)).analyze_roadmap()
    assert report.is_valid_dag
    assert not report.transitional_gaps
    data['plateaus'][1]['active_system_ids']=['old']
    data['plateaus'][1]['decommissioned_system_ids']=[]
    data['plateaus'][2]['active_system_ids']=['new']
    assert not RoadmapEngine(graph(data)).analyze_roadmap().transitional_gaps


def test_missing_replacement_dependency_and_cancelled_capacity():
    data=model()
    data['work_packages'][0]['depends_on']=['missing']
    data['work_packages'][0]['introduced_system_ids']=[]
    report=FeasibilityService(graph(data)).analyze()
    assert any(i['rule']=='PREREQUISITE_UNAVAILABLE' for i in report['issues'])
    assert any(i['control']=='replacement' for i in report['missing_data'])
    data['work_packages'][0]['status']='CANCELLED'
    report=FeasibilityService(graph(data)).analyze()
    assert not report['resource_usage'] and not report['budget_usage']
