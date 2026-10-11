"""Explicit DFD validation and delivery contracts."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from tecton_arch.application import TectonApp, Workspace
from tecton_arch.dsl.parser import C4EAMParser
from tecton_arch.dsl.schema import DataFlowDiagramDef, DFDNodeDef
from tecton_arch.engines.linter import GraphLinter

ROOT = Path(__file__).resolve().parents[2]


def sample():
    return C4EAMParser().parse_directory(ROOT / 'examples/c4_eam_workspace')


def test_explicit_dfd_is_valid_and_exported():
    graph = sample()
    report = GraphLinter().lint(graph)
    assert not any(issue.rule.startswith('DFD_') for issue in report.issues)
    app = TectonApp(Workspace.from_graph(graph))
    diagrams = app.data_flow_diagrams()
    assert diagrams == app.portal_snapshot()['dataFlowDiagrams']
    assert {node['kind'] for node in diagrams[0]['nodes']} == {'process','data_store','external_entity'}
    assert all(flow['name'] and flow['data_objects'] for flow in diagrams[0]['flows'])


@pytest.mark.parametrize('change,rule', [
    ('endpoint','DFD_UNKNOWN_ENDPOINT'),('object','DFD_UNKNOWN_DATA_OBJECT'),
    ('system','DFD_UNKNOWN_SYSTEM'),('duplicate','DFD_DUPLICATE_ID'),
    ('process','DFD_PROCESS_REQUIRED'),('self','DFD_SELF_FLOW'),
])
def test_dfd_invalid_references_block_validation(change, rule):
    graph = sample()
    diagram = next(iter(graph.data_flow_diagrams.values()))
    flow = diagram.flows[0]
    if change == 'endpoint': flow.source_id = 'missing'
    if change == 'object': flow.data_objects = ['missing']
    if change == 'system': diagram.nodes[0].system_id = 'missing'
    if change == 'duplicate': diagram.nodes.append(diagram.nodes[0].model_copy())
    if change == 'process': flow.target_id = 'orders'
    if change == 'self': flow.target_id = flow.source_id
    assert any(issue.rule == rule and issue.severity == 'ERROR' for issue in GraphLinter().lint(graph).issues)


def test_dfd_does_not_infer_nodes_from_systems():
    graph = C4EAMParser().parse_content('systems: [{id: example, name: Example}]')
    assert TectonApp(Workspace.from_graph(graph)).data_flow_diagrams() == []


def test_diagram_local_ids_do_not_collide_across_diagrams():
    graph = sample()
    diagram = next(iter(graph.data_flow_diagrams.values())).model_copy(deep=True)
    diagram.id = 'another-dfd'
    graph.table.register_data_flow_diagram(diagram, '<test>')
    assert not any(i.rule == 'DFD_DUPLICATE_ID' for i in GraphLinter().lint(graph).issues)


def test_dfd_schema_rejects_blank_names_and_unknown_node_kind():
    with pytest.raises(ValidationError):
        DFDNodeDef(id='p', name=' ', kind='process')
    with pytest.raises(ValidationError):
        DFDNodeDef(id='p', name='Process', kind='system')
