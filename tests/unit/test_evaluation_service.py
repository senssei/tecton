"""Domain evaluations exercise actual TIME and catalog checks, without persistence."""

from datetime import date
from copy import deepcopy

import pytest
import yaml

from tecton_arch.services.evaluation_service import EvaluationService, load_suite


@pytest.fixture
def evaluation(tmp_path):
    source = tmp_path / "catalog"
    source.mkdir()
    model = {"systems": [{"id": "crm", "name": "CRM", "functional_suitability": 1,
                           "technical_suitability": 5, "time_classification": "INVEST"},
                          {"id": "other", "name": "Other", "functional_suitability": 5,
                           "technical_suitability": 5}]}
    (source / "model.yaml").write_text(yaml.safe_dump(model))
    suite = {"version": 1,
             "criteria": {"functional": {"fit": {"weight": 2}, "usability": {"weight": 1}},
                          "technical": {"maintenance": {"weight": 1}}},
             "applications": {"crm": {"functional": {"fit": 5, "usability": 4},
                                       "technical": {"maintenance": 2}, "rationale": "Legacy CRM"}},
             "expected_time": {"crm": "TOLERATE", "other": "INVEST"}}
    path = tmp_path / "evaluation.yaml"

    def make(data=None, config=None, strict=False):
        path.write_text(yaml.safe_dump(suite if data is None else data))
        if config is not None:
            (source / "tecton.yaml").write_text(yaml.safe_dump(config))
        return EvaluationService(source, path, as_of_date=date(2026, 6, 1), strict=strict)

    return source, path, suite, make


def test_weighted_assessment_and_immutable_catalog(evaluation):
    source, path, suite, make = evaluation
    service = make()
    before = (source / "model.yaml").read_bytes()
    graph_before = service.workspace.graph.systems['crm'].model_dump()
    report = service.evaluate()
    crm, other = report.applications
    assert report.passed
    assert report.as_of_date == date(2026, 6, 1)
    assert crm.functional_suitability == pytest.approx(14 / 3)
    assert crm.technical_suitability == 2
    assert crm.time_classification == "TOLERATE"
    assert crm.rationale == "Legacy CRM"
    assert other.score_source == "catalog"
    assert report.recommendations.agreement_percentage == 100
    assert (source / "model.yaml").read_bytes() == before
    assert service.workspace.graph.systems['crm'].model_dump() == graph_before
    assert service.evaluate() == report


@pytest.mark.parametrize("functional,technical,expected", [
    (5, 5, "INVEST"), (5, 1, "TOLERATE"), (1, 5, "MIGRATE"), (1, 1, "ELIMINATE"),
    (3.5, 3.5, "INVEST"), (3.499999, 3.5, "MIGRATE"),
])
def test_real_time_engine_quadrants_and_boundaries(evaluation, functional, technical, expected):
    _, _, suite, make = evaluation
    suite['applications']['crm']['functional'] = {'fit': functional, 'usability': functional}
    suite['applications']['crm']['technical']['maintenance'] = technical
    suite['expected_time']['crm'] = expected
    report = make().evaluate()
    assert report.passed
    assert report.applications[0].time_classification == expected


def test_missing_rating_never_falls_back_to_catalog(evaluation):
    _, _, suite, make = evaluation
    del suite['applications']['crm']['technical']['maintenance']
    suite['expected_time']['crm'] = 'UNKNOWN'
    report = make().evaluate()
    assert not report.passed
    assert report.applications[0].technical_suitability is None
    assert report.applications[0].time_classification == 'UNKNOWN'
    assert report.applications[0].missing_criteria == ['technical.maintenance']
    assert report.recommendations.passed == 2


def test_quality_checks_original_catalog_even_after_suitability_override(evaluation):
    source, _, _, make = evaluation
    model = yaml.safe_load((source / 'model.yaml').read_text())
    del model['systems'][0]['functional_suitability']
    (source / 'model.yaml').write_text(yaml.safe_dump(model))
    report = make(config={'quality': {'rules': {'SUITABILITY_MISSING': 'error'}}}).evaluate()
    assert report.applications[0].functional_suitability == pytest.approx(14 / 3)
    assert report.catalog_quality.error_count == 1
    assert not report.passed


def test_custom_thresholds_and_mismatch(evaluation):
    _, _, _, make = evaluation
    report = make(config={'time': {'business_threshold': 5, 'technical_threshold': 4}}).evaluate()
    assert report.business_threshold == 5
    assert not report.passed
    check = report.recommendations.checks[0]
    assert (check.expected, check.actual, check.passed) == ('TOLERATE', 'ELIMINATE', False)
    assert report.recommendations.agreement_percentage == 50


def test_no_expectations_is_not_perfect_accuracy(evaluation):
    _, _, suite, make = evaluation
    suite['expected_time'] = {}
    report = make().evaluate()
    assert report.passed
    assert report.recommendations.checked == 0
    assert report.recommendations.agreement_percentage is None


@pytest.mark.parametrize('strict', [False, True])
def test_strict_quality_warnings(evaluation, strict):
    _, _, _, make = evaluation
    report = make(config={'quality': {'rules': {'REVIEW_MISSING': 'warning'}}}, strict=strict).evaluate()
    assert report.catalog_quality.warning_count == 2
    assert report.passed is not strict


def test_configured_strict_reports_schema_errors_instead_of_raising(evaluation):
    source, _, _, make = evaluation
    (source / 'invalid.yaml').write_text('systems: wrong-type\n')
    report = make(config={'strict': True}).evaluate()
    assert report.strict
    assert not report.passed
    assert report.catalog_quality.error_count >= 1


@pytest.mark.parametrize('kind', ['application', 'expected_application', 'criterion'])
def test_unknown_identifiers(evaluation, kind):
    _, _, suite, make = evaluation
    if kind == 'application':
        suite['applications']['missing'] = deepcopy(suite['applications']['crm'])
    elif kind == 'expected_application':
        suite['expected_time']['missing'] = 'INVEST'
    else:
        suite['applications']['crm']['functional']['typo'] = 3
    with pytest.raises(ValueError, match='Unknown'):
        make().evaluate()


@pytest.mark.parametrize('value', [0, 6, float('nan'), float('inf'), True, '4', None])
def test_invalid_scores(evaluation, value):
    _, _, suite, make = evaluation
    suite['applications']['crm']['functional']['fit'] = value
    with pytest.raises(ValueError):
        make()


@pytest.mark.parametrize('value', [0, -1, float('nan'), float('inf'), True, '2'])
def test_invalid_weights(evaluation, value):
    _, _, suite, make = evaluation
    suite['criteria']['functional']['fit']['weight'] = value
    with pytest.raises(ValueError):
        make()


@pytest.mark.parametrize('text', [
    'version: 1\nversion: 1\n',
    'version: [\n',
    '!!python/object:os.system {}',
    'version: true\ncriteria: {}\n',
    'version: 1\ncriteria: {}\nunknown: 1\n',
    'version: 2\ncriteria: {}\n',
    'version: 1\ncriteria:\n  functional:\n    x: {weight: 1, weight: 2}\n',
    '1: value\n',
    '',
])
def test_invalid_suite_documents(tmp_path, text):
    path = tmp_path / 'suite.yaml'
    path.write_text(text)
    with pytest.raises(ValueError):
        load_suite(path)


def test_suite_inside_catalog_excluded_and_large_weights_are_finite(evaluation):
    source, _, suite, _ = evaluation
    for axis in suite['criteria'].values():
        for criterion in axis.values():
            criterion['weight'] = 1e308
    path = source / 'suite.yaml'
    path.write_text(yaml.safe_dump(suite))
    service = EvaluationService(source, path)
    report = service.evaluate()
    assert report.passed
    assert report.applications[0].functional_suitability == 4.5
    assert str(path) not in service.workspace.graph.files_parsed


def test_decimal_weights_do_not_flip_exact_time_threshold(evaluation):
    _, _, suite, make = evaluation
    weights = [0.5449414806032167, 0.2204406220406967, 0.5892656838759087]
    suite['criteria']['functional'] = {str(i): {'weight': weight} for i, weight in enumerate(weights)}
    suite['applications']['crm']['functional'] = {str(i): 3.5 for i in range(3)}
    suite['applications']['crm']['technical'] = {'maintenance': 3.5}
    suite['expected_time']['crm'] = 'INVEST'
    report = make().evaluate()
    assert report.passed
    assert report.applications[0].functional_suitability == 3.5


@pytest.mark.parametrize('filename', ['suite[1].yaml', 'suite?.yaml'])
def test_suite_names_are_literal_paths_not_glob_patterns(evaluation, filename):
    source, _, suite, _ = evaluation
    path = source / filename
    path.write_text(yaml.safe_dump(suite))
    report = EvaluationService(source, path).evaluate()
    assert report.catalog_quality.error_count == 0
    assert report.passed


def test_symlink_to_external_suite_is_excluded(evaluation):
    source, path, _, make = evaluation
    make()
    alias = source / 'linked-suite.yaml'
    alias.symlink_to(path)
    service = EvaluationService(source, alias)
    assert service.evaluate().passed
    assert str(alias) not in service.workspace.graph.files_parsed


def test_shared_application_instances_are_not_mutated(evaluation, monkeypatch):
    _, _, _, make = evaluation
    service = make()
    graph = service.workspace.graph
    applications = graph.get_applications()
    before = [app.model_dump() for app in applications]
    monkeypatch.setattr(graph, 'get_applications', lambda **kwargs: applications)
    assert service.evaluate().passed
    assert [app.model_dump() for app in applications] == before


def test_quality_review_uses_selected_date(evaluation):
    source, path, _, make = evaluation
    service = make(config={'quality': {'rules': {'REVIEW_OVERDUE': 'error'}}})
    model = yaml.safe_load((source / 'model.yaml').read_text())
    model['systems'][0]['review'] = {'reviewed_on': '2026-01-01', 'reviewed_by': 'architect'}
    (source / 'model.yaml').write_text(yaml.safe_dump(model))
    assert service.evaluate().passed
    later = EvaluationService(source, path, as_of_date=date(2026, 12, 1)).evaluate()
    assert not later.passed
    assert any(issue.rule == 'REVIEW_OVERDUE' for issue in later.catalog_quality.issues)
