# Local YAML evaluations

`tecton evaluate` combines a weighted application assessment, the existing catalog
quality gate and expected TIME checks. It runs locally with the dependencies already
used by Tecton. It reads the catalog without updating its manifests.

```bash
tecton evaluate --source examples/evaluation/catalog --suite examples/evaluation/suite.yaml --as-of-date 2026-06-01

tecton evaluate --source examples/evaluation/catalog --suite examples/evaluation/suite.yaml --as-of-date 2026-06-01 --format json --output /tmp/tecton-evaluation.json
```

## Define an assessment

```yaml
version: 1
criteria:
  functional:
    business_fit: {weight: 2}
    usability: {weight: 1}
  technical:
    maintainability: {weight: 1}
applications:
  crm:
    functional: {business_fit: 5, usability: 4}
    technical: {maintainability: 2}
    rationale: Strong business fit with expensive maintenance.
expected_time:
  crm: TOLERATE
```

Both criterion axes must be nonempty. Define your own criterion names and weights;
the example is a template, not a prescribed architecture rubric. Scores are numeric
values from 1 to 5, including fractional values. Weights must be positive finite
numbers. Quoted numeric strings, booleans, null scores, nonfinite numbers, unknown
fields and duplicate YAML keys are rejected. Omit an unavailable score instead of
supplying null. Application IDs must exist in the catalog, and rating names must
match the criteria for their axis. Version 1 is the supported document version.

Each axis is calculated as `sum(score × weight) / sum(weight)`, without rounding
before TIME classification. CRM's functional result above is `14 / 3`; its
technical result is `2`. TIME uses the configured Tecton thresholds (default `3.5`
for both axes) and the existing engine's quadrant rules.

For an assessed application, a missing criterion makes that entire axis `null`
and TIME `UNKNOWN`. The report lists the missing criteria and the evaluation fails,
even when `UNKNOWN` is the expected result. Existing catalog scores do not fill
missing ratings. Applications absent from `applications` retain their catalog
scores. `applications` and `expected_time` are optional mappings; omit
`applications` to check existing catalog classifications only.

Catalog quality is evaluated on the original catalog, using its existing
configuration and rule severities. An assessment therefore does not conceal a
missing catalog suitability score. The report includes problems and error/warning
counts rather than an artificial aggregate quality score.

## Interpret results

The report includes the evaluation date, effective strict mode, TIME thresholds,
all applications with their score source and rationale, catalog issues and each
expected/actual TIME comparison. The agreement percentage covers only explicit
`expected_time` entries. With no entries it is `null` and zero checks are reported;
this does not establish recommendation correctness.

Use `--format table` (default), `json` or `markdown`. `--output` writes that format
to a file, including a plain-text table for `table`; otherwise the report goes to
standard output. Failed evaluations also produce reports. Output may not overwrite
the suite, loaded manifests or configuration, including symlink/hardlink aliases.
Keep generated reports outside the catalog so subsequent scans do not treat them
as architecture manifests. A suite inside the source directory is automatically
excluded for this command. Existing manifest include/exclude settings still apply.

| Exit code | Meaning |
| --- | --- |
| `0` | Quality gate passes, supplied assessments are complete and TIME checks agree |
| `1` | Catalog errors, incomplete ratings or TIME mismatches; strict mode also fails on warnings |
| `2` | Invalid input, unsupported options, protected output or execution failure |

`--config` selects a Tecton configuration. `--strict` enables warning failures;
configured strict mode also applies. `--as-of-date YYYY-MM-DD` defaults to today.
Set it explicitly in CI for repeatable lifecycle and review checks. No expected
TIME checks is allowed; use an explicit suite to establish regression coverage.

The mismatch example intentionally exits with code `1`:

```bash
tecton evaluate --source examples/evaluation/catalog --suite examples/evaluation/mismatch.yaml --as-of-date 2026-06-01 --format json
```

## Python interface

```python
from datetime import date
from tecton_arch.services.evaluation_service import EvaluationService

report = EvaluationService(
    "examples/evaluation/catalog", "examples/evaluation/suite.yaml",
    as_of_date=date(2026, 6, 1),
).evaluate()
assert report.passed
payload = report.model_dump(mode="json")
```

The service returns a Pydantic `EvaluationReport`; pytest can assert on it directly
to add regression scenarios. pytest is not needed to run the evaluator. Version 1
does not evaluate redundancy, finance or roadmap recommendations and does not use
an LLM to judge scores or explanations.
