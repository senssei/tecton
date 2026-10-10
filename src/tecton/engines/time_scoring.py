"""Deterministic TIME Evaluation Engine (Gartner TIME Framework)."""

from typing import Any
from tecton.core.models import Application, TimeConfig, TimeQuadrant


class TimeScoringEngine:
    """Calculates deterministic TIME classification quadrants for applications."""

    def __init__(self, config: TimeConfig | None = None) -> None:
        self.config = config or TimeConfig()

    def evaluate(self, application: Application) -> TimeQuadrant:
        """Classify a single application into a TIME quadrant.

        Quadrant Rules:
        - INVEST: High Business Fit (>= b_thresh) AND High Technical Fit (>= t_thresh)
        - TOLERATE: High Business Fit (>= b_thresh) AND Low Technical Fit (< t_thresh)
        - MIGRATE: Low Business Fit (< b_thresh) AND High Technical Fit (>= t_thresh)
        - ELIMINATE: Low Business Fit (< b_thresh) AND Low Technical Fit (< t_thresh)
        - UNKNOWN: When either suitability score is missing (None)
        """
        b_fit = application.functional_suitability
        t_fit = application.technical_suitability

        if b_fit is None or t_fit is None:
            return TimeQuadrant.UNKNOWN

        b_high = b_fit >= self.config.business_threshold
        t_high = t_fit >= self.config.technical_threshold

        if b_high and t_high:
            return TimeQuadrant.INVEST
        elif b_high and not t_high:
            return TimeQuadrant.TOLERATE
        elif not b_high and t_high:
            return TimeQuadrant.MIGRATE
        else:
            return TimeQuadrant.ELIMINATE

    def evaluate_all(self, applications: list[Application]) -> dict[str, TimeQuadrant]:
        """Classify a collection of applications, returning a mapping {app_id: TimeQuadrant}."""
        return {app.id: self.evaluate(app) for app in applications}

    def generate_patch(
        self, application: Application, target_quadrant: TimeQuadrant
    ) -> dict[str, Any] | None:
        """Generate a JSON Patch mutation if the classified quadrant differs from existing."""
        if target_quadrant == TimeQuadrant.UNKNOWN or application.time_classification == target_quadrant:
            return None

        return {
            "op": "replace" if application.time_classification != TimeQuadrant.UNKNOWN else "add",
            "path": "/timeClassification",
            "value": target_quadrant.value,
        }
