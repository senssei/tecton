"""APM Service orchestrating portfolio analytics, engines, and repository mutations."""

from datetime import date
from typing import Any
from pydantic import BaseModel, Field
from tecton_arch.adapters.base import ArchitectureRepositoryPort
from tecton_arch.core.models import Application, RedundancyCluster, RedundancyConfig, TimeConfig, TimeQuadrant
from tecton_arch.engines.lifecycle_validator import LifecycleValidationReport, LifecycleValidator
from tecton_arch.engines.redundancy import RedundancyDetectionEngine
from tecton_arch.engines.time_scoring import TimeScoringEngine


class APMAnalysisResult(BaseModel):
    """Aggregate result of comprehensive APM evaluation."""

    as_of_date: date | None = None
    applications: list[Application]
    time_classifications: dict[str, TimeQuadrant]
    redundancy_clusters: list[RedundancyCluster]
    lifecycle_report: LifecycleValidationReport
    patches_needed: int = 0
    proposed_patches: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class APMService:
    """Orchestration service for Application Portfolio Management."""

    def __init__(
        self,
        repository: ArchitectureRepositoryPort,
        time_config: TimeConfig | None = None,
        redundancy_config: RedundancyConfig | None = None,
    ) -> None:
        self.repository = repository
        self.time_engine = TimeScoringEngine(time_config)
        self.redundancy_engine = RedundancyDetectionEngine(redundancy_config)
        self.lifecycle_validator = LifecycleValidator()

    def get_applications(self, as_of_date: date | None = None) -> list[Application]:
        """Fetch all applications from underlying repository."""
        return self.repository.fetch_applications(as_of_date=as_of_date)

    def analyze(self, as_of_date: date | None = None) -> APMAnalysisResult:
        """Execute full portfolio analysis (TIME, Redundancy, Lifecycle)."""
        as_of_date = as_of_date or date.today()
        apps = self.repository.fetch_applications(as_of_date=as_of_date)
        time_map = self.time_engine.evaluate_all(apps)
        redundancies = self.redundancy_engine.find_redundancies(apps)
        lifecycle_rep = self.lifecycle_validator.validate_all(apps, as_of_date=as_of_date)

        # Calculate patches needed to align repository with evaluated TIME model
        proposed_patches: dict[str, list[dict[str, Any]]] = {}
        total_patch_count = 0

        for app in apps:
            target_time = time_map.get(app.id, TimeQuadrant.UNKNOWN)
            patch = self.time_engine.generate_patch(app, target_time)
            if patch:
                proposed_patches[app.id] = [patch]
                total_patch_count += 1

        from tecton_arch.core.config import TectonConfig
        from tecton_arch.services.assessment import evaluate_applications
        apps = evaluate_applications(apps, TectonConfig(time=self.time_engine.config), as_of_date)
        return APMAnalysisResult(
            as_of_date=as_of_date,
            applications=apps,
            time_classifications=time_map,
            redundancy_clusters=redundancies,
            lifecycle_report=lifecycle_rep,
            patches_needed=total_patch_count,
            proposed_patches=proposed_patches,
        )

    def apply_time_patches(self, dry_run: bool = True) -> list[dict[str, Any]]:
        """Apply generated TIME classification patches to the repository."""
        analysis = self.analyze()
        results: list[dict[str, Any]] = []

        for app_id, patches in analysis.proposed_patches.items():
            res = self.repository.apply_patches(app_id, patches, dry_run=dry_run)
            results.append(res)

        return results
