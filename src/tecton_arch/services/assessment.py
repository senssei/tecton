"""Shared, non-mutating portfolio evaluation with explicit input provenance."""
from datetime import date
from tecton_arch.core.config import TectonConfig
from tecton_arch.engines.time_scoring import TimeScoringEngine


def evaluate_applications(applications, config=None, as_of_date=None):
    config = config or TectonConfig()
    engine = TimeScoringEngine(config.time)
    apps = [app.model_copy(deep=True) for app in applications]
    classifications = engine.evaluate_all(apps)
    for app in apps:
        declared = app.time_classification
        app.current_phase = app.phase_as_of(as_of_date or date.today()) or app.current_phase
        app.time_classification = classifications[app.id]
        app.metadata["assessment"] = {
            "declared_time_classification": declared.value,
            "evaluated_time_classification": app.time_classification.value,
            "functional_suitability": app.functional_suitability,
            "technical_suitability": app.technical_suitability,
            "business_threshold": config.time.business_threshold,
            "technical_threshold": config.time.technical_threshold,
            "missing_data": [key for key in ("functional_suitability", "technical_suitability") if getattr(app, key) is None],
            "classification_mismatch": declared != app.time_classification,
        }
    return apps
