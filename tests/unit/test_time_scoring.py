"""Unit tests for TimeScoringEngine."""

import pytest
from tecton_arch.core.models import Application, TimeConfig, TimeQuadrant
from tecton_arch.engines.time_scoring import TimeScoringEngine


def test_time_scoring_invest() -> None:
    engine = TimeScoringEngine(TimeConfig(business_threshold=3.5, technical_threshold=3.5))
    app = Application(
        id="app-1",
        name="CRM",
        functional_suitability=4.5,
        technical_suitability=4.0,
    )
    assert engine.evaluate(app) == TimeQuadrant.INVEST


def test_time_scoring_tolerate() -> None:
    engine = TimeScoringEngine(TimeConfig(business_threshold=3.5, technical_threshold=3.5))
    app = Application(
        id="app-2",
        name="Mainframe Ledger",
        functional_suitability=4.8,
        technical_suitability=2.0,
    )
    assert engine.evaluate(app) == TimeQuadrant.TOLERATE


def test_time_scoring_migrate() -> None:
    engine = TimeScoringEngine(TimeConfig(business_threshold=3.5, technical_threshold=3.5))
    app = Application(
        id="app-3",
        name="Modern Internal Tool",
        functional_suitability=2.0,
        technical_suitability=4.2,
    )
    assert engine.evaluate(app) == TimeQuadrant.MIGRATE


def test_time_scoring_eliminate() -> None:
    engine = TimeScoringEngine(TimeConfig(business_threshold=3.5, technical_threshold=3.5))
    app = Application(
        id="app-4",
        name="Old Billing",
        functional_suitability=1.5,
        technical_suitability=1.8,
    )
    assert engine.evaluate(app) == TimeQuadrant.ELIMINATE


def test_time_scoring_unknown_when_missing_scores() -> None:
    engine = TimeScoringEngine()
    app = Application(id="app-5", name="Incomplete App", functional_suitability=None, technical_suitability=3.0)
    assert engine.evaluate(app) == TimeQuadrant.UNKNOWN


def test_time_scoring_custom_thresholds() -> None:
    engine = TimeScoringEngine(TimeConfig(business_threshold=4.0, technical_threshold=4.0))
    app = Application(id="app-6", name="Borderline", functional_suitability=3.8, technical_suitability=4.2)
    # Business fit is below 4.0, technical is >= 4.0 -> MIGRATE
    assert engine.evaluate(app) == TimeQuadrant.MIGRATE


def test_patch_generation() -> None:
    engine = TimeScoringEngine()
    app = Application(id="app-7", name="App", functional_suitability=4.5, technical_suitability=4.5, time_classification=TimeQuadrant.UNKNOWN)
    patch = engine.generate_patch(app, TimeQuadrant.INVEST)
    assert patch == {"op": "add", "path": "/timeClassification", "value": "INVEST"}

    # No patch if already matches
    app_updated = Application(id="app-8", name="App", functional_suitability=4.5, technical_suitability=4.5, time_classification=TimeQuadrant.INVEST)
    assert engine.generate_patch(app_updated, TimeQuadrant.INVEST) is None
