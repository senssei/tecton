"""Local, read-only suitability assessment and TIME regression evaluation."""

from datetime import date
from decimal import Decimal, localcontext
from glob import escape
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from tecton_arch.application.dto import ValidationReportDto, ValidationIssueDto
from tecton_arch.application.workspace import Workspace
from tecton_arch.core.config import TectonConfig
from tecton_arch.core.models import TimeQuadrant
from tecton_arch.engines.linter import GraphLinter
from tecton_arch.engines.time_scoring import TimeScoringEngine


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


Score = Annotated[float, Field(ge=1, le=5, allow_inf_nan=False)]


def numeric(value: object):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a numeric YAML value")
    return value


class Criterion(StrictModel):
    weight: float = Field(gt=0, allow_inf_nan=False)

    @field_validator("weight", mode="before")
    @classmethod
    def numeric_weight(cls, value):
        return numeric(value)


class Criteria(StrictModel):
    functional: dict[str, Criterion] = Field(min_length=1)
    technical: dict[str, Criterion] = Field(min_length=1)


class Ratings(StrictModel):
    functional: dict[str, Score] = Field(default_factory=dict)
    technical: dict[str, Score] = Field(default_factory=dict)
    rationale: str | None = None

    @field_validator("functional", "technical", mode="before")
    @classmethod
    def numeric_scores(cls, value):
        if isinstance(value, dict):
            for score in value.values():
                numeric(score)
        return value


class EvaluationSuite(StrictModel):
    version: Literal[1]
    criteria: Criteria
    applications: dict[str, Ratings] = Field(default_factory=dict)
    expected_time: dict[str, TimeQuadrant] = Field(default_factory=dict)

    @field_validator("version", mode="before")
    @classmethod
    def integer_version(cls, value):
        if type(value) is not int:
            raise ValueError("Suite version must be integer 1")
        return value


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys rather than silently discarding ratings."""


def unique_mapping(loader: UniqueKeyLoader, node):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise ValueError("YAML mapping keys must be strings")
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_suite(path: str | Path) -> EvaluationSuite:
    try:
        data = yaml.load(Path(path).read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid evaluation YAML: {exc}") from exc
    return EvaluationSuite.model_validate(data)


class ApplicationEvaluation(StrictModel):
    id: str
    name: str
    score_source: Literal["suite", "catalog"]
    functional_suitability: float | None
    technical_suitability: float | None
    time_classification: TimeQuadrant
    missing_criteria: list[str] = Field(default_factory=list)
    rationale: str | None = None


class TimeCheck(StrictModel):
    id: str
    expected: TimeQuadrant
    actual: TimeQuadrant
    passed: bool


class RecommendationEvaluation(StrictModel):
    checked: int
    passed: int
    agreement_percentage: float | None
    checks: list[TimeCheck]


class EvaluationReport(StrictModel):
    version: Literal[1] = 1
    as_of_date: date
    passed: bool
    strict: bool
    business_threshold: float
    technical_threshold: float
    applications: list[ApplicationEvaluation]
    catalog_quality: ValidationReportDto
    recommendations: RecommendationEvaluation


def weighted_score(criteria: dict[str, Criterion], scores: dict[str, float]) -> tuple[float | None, list[str]]:
    missing = sorted(set(criteria) - set(scores))
    if missing:
        return None, missing
    # Decimal arithmetic preserves exact threshold results (e.g. all ratings 3.5)
    # and avoids overflowing sums of large finite weights.
    with localcontext() as context:
        context.prec = 50
        weights = {key: Decimal(str(item.weight)) for key, item in criteria.items()}
        numerator = sum(Decimal(str(scores[key])) * weights[key] for key in sorted(criteria))
        return float(numerator / sum(weights.values())), []


class EvaluationService:
    def __init__(self, source: str | Path, suite_path: str | Path, *, config_path=None,
                 as_of_date: date | None = None, strict: bool = False):
        self.source = Path(source).resolve()
        self.suite_path = Path(suite_path).resolve()
        if self.source == self.suite_path:
            raise ValueError("Source and suite must be different files")
        self.suite = load_suite(self.suite_path)
        self.config = TectonConfig.load(config_path, workspace_dir=self.source)
        self.strict = strict or self.config.strict or self.config.workspace.strict
        self.as_of_date = as_of_date or date.today()
        # Collect catalog errors into the report even when the quality gate is strict.
        parse_config = self.config.model_copy(deep=True)
        parse_config.strict = False
        parse_config.workspace.strict = False
        if self.source.is_dir():
            # Match the actual file, including symlink aliases and literal glob characters.
            for pattern in parse_config.manifests.include:
                for candidate in self.source.glob(pattern):
                    if candidate.is_file() and candidate.resolve() == self.suite_path:
                        parse_config.manifests.exclude.append(escape(candidate.relative_to(self.source).as_posix()))
        self.workspace = Workspace(self.source, config=parse_config)
        self.config_path = Path(config_path).resolve() if config_path else None

    def validate_output(self, output: str | Path):
        """Protect manifests, suite and configuration, including filesystem aliases."""
        target = Path(output).resolve()
        protected = [self.suite_path, *map(Path, self.workspace.graph.files_parsed)]
        if self.config_path:
            protected.append(self.config_path)
        root = self.source if self.source.is_dir() else self.source.parent
        protected.extend(root / name for name in ("tecton.yaml", ".tecton.yaml", "tecton.yml"))
        protected.extend(Path.cwd() / name for name in ("tecton.yaml", ".tecton.yaml", "tecton.yml"))
        for path in protected:
            if target == path.resolve() or (target.exists() and path.exists() and target.samefile(path)):
                raise ValueError(f"Output would overwrite an input file: {output}")

    def evaluate(self) -> EvaluationReport:
        graph = self.workspace.graph
        apps = graph.get_applications(as_of_date=self.as_of_date)
        identifiers = {app.id for app in apps}
        unknown = (set(self.suite.applications) | set(self.suite.expected_time)) - identifiers
        if unknown:
            raise ValueError(f"Unknown applications: {', '.join(sorted(unknown))}")
        for app_id, ratings in self.suite.applications.items():
            for axis in ("functional", "technical"):
                unknown = set(getattr(ratings, axis)) - set(getattr(self.suite.criteria, axis))
                if unknown:
                    raise ValueError(f"Unknown {axis} criteria for {app_id}: {', '.join(sorted(unknown))}")

        lint = GraphLinter().lint(graph, as_of_date=self.as_of_date,
                                  strict=self.strict, config=self.config)
        quality = ValidationReportDto(
            valid=not lint.has_errors and (not self.strict or lint.warning_count == 0),
            error_count=lint.error_count, warning_count=lint.warning_count,
            as_of_date=self.as_of_date.isoformat(),
            issues=[ValidationIssueDto(severity=i.severity.value, rule=i.rule, message=i.message,
                                       entity_id=i.entity_id, file_origin=i.file_origin) for i in lint.issues],
        )
        engine = TimeScoringEngine(self.config.time)
        results = []
        for original in sorted(apps, key=lambda app: app.id):
            application = original.model_copy(deep=True)
            ratings = self.suite.applications.get(application.id)
            missing = []
            if ratings is not None:
                for axis in ("functional", "technical"):
                    score, absent = weighted_score(getattr(self.suite.criteria, axis), getattr(ratings, axis))
                    setattr(application, f"{axis}_suitability", score)
                    missing.extend(f"{axis}.{key}" for key in absent)
            results.append(ApplicationEvaluation(
                id=application.id, name=application.name, score_source="suite" if ratings is not None else "catalog",
                functional_suitability=application.functional_suitability,
                technical_suitability=application.technical_suitability,
                time_classification=engine.evaluate(application), missing_criteria=missing,
                rationale=ratings.rationale if ratings is not None else application.metadata.get("suitability_rationale"),
            ))
        actual = {item.id: item.time_classification for item in results}
        checks = [TimeCheck(id=key, expected=expected, actual=actual[key], passed=actual[key] == expected)
                  for key, expected in sorted(self.suite.expected_time.items())]
        passed = sum(check.passed for check in checks)
        return EvaluationReport(
            as_of_date=self.as_of_date, strict=self.strict,
            passed=quality.valid and not any(item.missing_criteria for item in results) and passed == len(checks),
            business_threshold=self.config.time.business_threshold,
            technical_threshold=self.config.time.technical_threshold,
            applications=results, catalog_quality=quality,
            recommendations=RecommendationEvaluation(checked=len(checks), passed=passed,
                agreement_percentage=100 * passed / len(checks) if checks else None, checks=checks),
        )
