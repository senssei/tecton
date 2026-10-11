"""CLI acceptance tests for evaluation reports and input protection."""

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from tecton_arch.cli.main import app


runner = CliRunner()
EXAMPLES = Path(__file__).resolve().parents[2] / 'examples/evaluation'


def invoke(*args):
    return runner.invoke(app, ['evaluate', '--source', str(EXAMPLES / 'catalog'),
                               '--suite', str(EXAMPLES / 'suite.yaml'), '--as-of-date', '2026-06-01', *args])


def test_example_passes_with_json_output():
    result = invoke('--format', 'json')
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data['as_of_date'] == '2026-06-01'
    assert data['passed']
    assert data['recommendations']['checked'] == 4
    assert data['recommendations']['agreement_percentage'] == 100


def test_mismatch_example_reports_failure():
    result = invoke('--suite', str(EXAMPLES / 'mismatch.yaml'), '--format', 'json')
    assert result.exit_code == 1, result.output
    data = json.loads(result.output)
    assert not data['passed']
    assert data['recommendations']['checks'][0]['expected'] == 'INVEST'
    assert data['recommendations']['checks'][0]['actual'] == 'TOLERATE'


@pytest.mark.parametrize('format', ['json', 'markdown', 'table'])
def test_formats_written_only_when_requested(tmp_path, format):
    output = tmp_path / 'report.txt'
    result = invoke('--format', format, '--output', str(output))
    assert result.exit_code == 0, result.output
    assert result.output == ''
    text = output.read_text()
    assert 'crm' in text
    if format == 'json':
        assert json.loads(text)['passed']
    if format == 'markdown':
        assert '## TIME checks' in text
        assert '| crm | TOLERATE | TOLERATE | True |' in text


@pytest.mark.parametrize('format', ['table', 'markdown'])
def test_human_formats(format):
    result = invoke('--format', format)
    assert result.exit_code == 0, result.output
    assert 'crm' in result.output
    assert 'TOLERATE' in result.output


@pytest.mark.parametrize('args', [
    ['--as-of-date', 'bad-date'], ['--format', 'csv'], ['--suite', '/nonexistent/suite.yaml'],
    ['--config', '/nonexistent/tecton.yaml'],
])
def test_invalid_inputs_exit_two(args):
    result = invoke(*args)
    assert result.exit_code == 2
    assert 'Evaluation error:' in result.output


@pytest.mark.parametrize('protected', ['model.yaml', 'suite.yaml', 'tecton.yaml', 'hardlink', 'symlink'])
def test_output_cannot_overwrite_input_files(tmp_path, protected):
    source = tmp_path / 'catalog'
    source.mkdir()
    model = source / 'model.yaml'
    model.write_text('systems:\n- {id: crm, name: CRM}\n')
    suite = source / 'suite.yaml'
    suite.write_text((EXAMPLES / 'mismatch.yaml').read_text())
    config = source / 'tecton.yaml'
    config.write_text('quality: {}\n')
    output = source / protected
    if protected == 'hardlink':
        output.hardlink_to(model)
    elif protected == 'symlink':
        output.symlink_to(model)
    before = {path: path.read_bytes() for path in (model, suite, config)}
    result = runner.invoke(app, ['evaluate', '--source', str(source), '--suite', str(suite),
                                '--output', str(output), '--format', 'json'])
    assert result.exit_code == 2, result.output
    assert 'overwrite an input file' in result.output
    assert {path: path.read_bytes() for path in before} == before


def test_strict_config_reports_failure_without_losing_report(tmp_path):
    config = tmp_path / 'config.yaml'
    config.write_text('strict: true\nquality:\n  rules:\n    REVIEW_MISSING: warning\n')
    result = invoke('--config', str(config), '--format', 'json')
    assert result.exit_code == 1, result.output
    data = json.loads(result.output)
    assert data['strict']
    assert data['catalog_quality']['warning_count'] == 4


def test_failed_evaluation_still_writes_report(tmp_path):
    config = tmp_path / 'config.yaml'
    config.write_text('quality:\n  rules:\n    REVIEW_MISSING: warning\n')
    output = tmp_path / 'failed.json'
    result = invoke('--config', str(config), '--strict', '--format', 'json', '--output', str(output))
    assert result.exit_code == 1, result.output
    assert json.loads(output.read_text())['passed'] is False


def test_suite_inside_source_and_incomplete_axis(tmp_path):
    source = tmp_path / 'catalog'
    source.mkdir()
    (source / 'model.yaml').write_text('systems:\n- {id: crm, name: CRM, technical_suitability: 5}\n')
    suite = yaml.safe_load((EXAMPLES / 'suite.yaml').read_text())
    suite['applications']['crm']['technical'] = {}
    suite['expected_time'] = {'crm': 'UNKNOWN'}
    path = source / 'suite.yaml'
    path.write_text(yaml.safe_dump(suite))
    result = runner.invoke(app, ['evaluate', '--source', str(source), '--suite', str(path), '--format', 'json'])
    assert result.exit_code == 1, result.output
    data = json.loads(result.output)
    assert data['catalog_quality']['error_count'] == 0
    assert data['applications'][0]['technical_suitability'] is None
    assert data['recommendations']['passed'] == 1


def test_existing_manifest_filters_are_respected(tmp_path):
    source = tmp_path / 'catalog'
    source.mkdir()
    (source / 'model.yaml').write_text((EXAMPLES / 'catalog/model.yaml').read_text())
    (source / 'ignored.yaml').write_text('systems: invalid\n')
    (source / 'tecton.yaml').write_text('manifests:\n  include: ["model.yaml"]\n')
    result = runner.invoke(app, ['evaluate', '--source', str(source), '--suite', str(EXAMPLES / 'suite.yaml'),
                                '--format', 'json'])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)['catalog_quality']['error_count'] == 0


def test_dogfood_catalog_evaluation_passes():
    from datetime import date
    from pathlib import Path

    from tecton_arch.services.evaluation_service import EvaluationService

    root = Path(__file__).parents[2] / "examples" / "dogfood"
    report = EvaluationService(
        root / "tecton_c4_workspace", root / "evaluation.yaml", as_of_date=date(2026, 10, 11)
    ).evaluate()
    assert report.passed
