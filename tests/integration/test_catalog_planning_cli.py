"""Acceptance exercises across CLI, configuration, Git diff and native persistence."""
from pathlib import Path
from datetime import date
import json
import subprocess
import yaml
from typer.testing import CliRunner
from tecton_arch.cli.main import app
from tecton_arch.services.diff_service import DiffService
from tecton_arch.core.config import TectonConfig
from tecton_arch.application import TectonApp

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'examples/planning'
runner = CliRunner()


def test_new_reports_are_machine_readable():
    for command in (['catalog','freshness'], ['apm','costs'], ['roadmap','business-case'], ['roadmap','feasibility']):
        result=runner.invoke(app, [*command,'--source',str(SOURCE),'--as-of-date','2026-06-01','--format','json'])
        assert result.exit_code == 0, result.output
        report=json.loads(result.output)
        assert report
    feasibility=json.loads(runner.invoke(app,['roadmap','feasibility','--source',str(SOURCE),'--format','json']).output)
    assert feasibility['assessment_status']=='violations_detected'


def test_rename_preview_and_output(tmp_path):
    preview=runner.invoke(app,['catalog','rename','old','old-renamed','--source',str(SOURCE),'--format','json'])
    assert preview.exit_code==0,preview.output
    assert json.loads(preview.output)['output_path'] is None
    target=tmp_path/'renamed'
    written=runner.invoke(app,['catalog','rename','old','old-renamed','--source',str(SOURCE),'--output',str(target),'--format','json'])
    assert written.exit_code==0,written.output
    assert TectonApp(target).validate().valid
    assert target.joinpath('catalog.yaml').is_file()
    failure=runner.invoke(app,['catalog','rename','old','old-renamed','--source',str(SOURCE),'--output',str(target)])
    assert failure.exit_code==1


def test_git_subpath_head_configuration_and_worktree(tmp_path):
    root=tmp_path/'repo';root.mkdir()
    catalog=root/'catalog';catalog.mkdir()
    (catalog/'model.yaml').write_text('systems:\n  - {id: s, name: S, owner: A}\n')
    unrelated=root/'other';unrelated.mkdir()
    (unrelated/'invalid.yaml').write_text('systems:\n  - {id: s, name: Duplicate}\n')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
    git('init');git('config','commit.gpgsign','false');git('config','user.name','Test');git('config','user.email','test@example.invalid')
    git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD')
    (catalog/'model.yaml').write_text('systems:\n  - {id: s, name: S, owner: B}\n')
    (catalog/'tecton.yaml').write_text('quality:\n  review_valid_days: 365\n')
    git('add','.');git('commit','-m','head')
    report=DiffService().compare_git_revisions(base,'HEAD',root,workspace_path='catalog',as_of_date=date(2026,6,1))
    assert len(report.deltas)==1
    assert report.deltas[0].field_changes['owner']==('A','B')
    assert report.configuration_changes['quality.review_valid_days']==(180,365)
    assert not report.has_breaking_changes
    (catalog/'model.yaml').write_text('systems:\n  - {id: s, name: S, owner: C}\n')
    report=DiffService().compare_git_revisions('HEAD','WORKTREE',root,workspace_path='catalog')
    assert report.deltas[0].field_changes['owner']==('B','C')


def test_export_warning_and_fixed_date_snapshot():
    model=TectonApp(SOURCE,as_of_date=date(2026,6,1))
    assert any('annual_cost' in warning for warning in model.export('backstage').warnings)
    payload=model.portal_snapshot()
    assert payload['as_of_date']=='2026-06-01'
    assert payload['overview']['as_of_date']=='2026-06-01'
    assert payload['catalogFreshness']['as_of_date']=='2026-06-01'
    assert payload['feasibility']['assessment_status']=='violations_detected'
    assert payload['coverage']['coverages']['root']['leaf_coverage_percentage']==50
