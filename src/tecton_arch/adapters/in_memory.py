"""In-memory Repository Adapter for offline execution, testing, and CI/CD."""

from datetime import date
from typing import Any
from tecton_arch.adapters.base import ArchitectureRepositoryPort
from tecton_arch.core.models import Application, TimeQuadrant


class InMemoryRepositoryAdapter(ArchitectureRepositoryPort):
    """Fast, in-memory implementation of the Architecture Repository Port."""

    def __init__(self, applications: list[Application] | None = None) -> None:
        self._storage: dict[str, Application] = {}
        if applications:
            for app in applications:
                self._storage[app.id] = app.model_copy(deep=True)

    def fetch_applications(self, as_of_date: date | None = None) -> list[Application]:
        """Return all applications stored in memory, evaluating active phase as of target date if supplied."""
        apps: list[Application] = []
        for app in self._storage.values():
            copy = app.model_copy(deep=True)
            if as_of_date:
                copy.current_phase = copy.phase_as_of(as_of_date)
            apps.append(copy)
        return apps

    def get_application(self, app_id: str) -> Application | None:
        """Get an application by its ID."""
        app = self._storage.get(app_id)
        return app.model_copy(deep=True) if app else None

    def save_application(self, application: Application) -> Application:
        """Store or update an application in memory."""
        stored = application.model_copy(deep=True)
        self._storage[application.id] = stored
        return stored.model_copy(deep=True)

    def apply_patches(
        self, entity_id: str, patches: list[dict[str, Any]], dry_run: bool = True
    ) -> dict[str, Any]:
        """Simulate or apply JSON Patch mutations to the in-memory entity."""
        app = self._storage.get(entity_id)
        if not app:
            raise KeyError(f"Entity with ID {entity_id} not found in in-memory repository.")

        applied_changes: list[dict[str, Any]] = []

        for p in patches:
            op = p.get("op")
            path = p.get("path", "")
            val = p.get("value")

            applied_changes.append({"op": op, "path": path, "value": val, "status": "simulated" if dry_run else "applied"})

            if not dry_run:
                # Apply simple path modifications
                if path in ("/timeClassification", "/time_classification"):
                    app.time_classification = TimeQuadrant(val)
                elif path in ("/businessCriticality", "/business_criticality"):
                    app.business_criticality = str(val)
                elif path in ("/functionalSuitability", "/functional_suitability"):
                    app.functional_suitability = float(val) if val is not None else None
                elif path in ("/technicalSuitability", "/technical_suitability"):
                    app.technical_suitability = float(val) if val is not None else None

        return {
            "entity_id": entity_id,
            "dry_run": dry_run,
            "applied_count": len(patches),
            "patches": applied_changes,
        }
