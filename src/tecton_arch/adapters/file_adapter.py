"""File-based Repository Adapter (loads applications from local JSON or YAML)."""

import json
from pathlib import Path
from typing import Any
import yaml
from tecton_arch.adapters.in_memory import InMemoryRepositoryAdapter
from tecton_arch.core.models import Application, Lifecycle, LifecyclePhaseDate


class FileRepositoryAdapter(InMemoryRepositoryAdapter):
    """Repository adapter that hydrates from a local JSON or YAML file."""

    def __init__(self, file_path: str | Path) -> None:
        super().__init__()
        self.file_path = Path(file_path)
        self.load()

    def load(self) -> None:
        """Load and parse applications from the file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Repository file not found: {self.file_path}")

        content = self.file_path.read_text(encoding="utf-8")
        if self.file_path.suffix.lower() in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)

        raw_apps: list[dict[str, Any]] = []
        if isinstance(data, list):
            raw_apps = data
        elif isinstance(data, dict):
            # Support {"applications": [...]} or {"data": [...]}
            raw_apps = data.get("applications", data.get("data", []))

        for raw in raw_apps:
            # Map alternative naming conventions if present
            app_id = str(raw.get("id") or raw.get("app_id") or raw.get("name"))
            name = str(raw.get("name") or app_id)

            lifecycle = None
            raw_lc = raw.get("lifecycle")
            if raw_lc and isinstance(raw_lc, dict):
                phases_list = []
                for p in raw_lc.get("phases", []):
                    try:
                        phases_list.append(LifecyclePhaseDate(phase=p["phase"], start_date=p["start_date"]))
                    except Exception:
                        pass
                lifecycle = Lifecycle(as_string=raw_lc.get("as_string") or raw_lc.get("asString"), phases=phases_list)

            raw_phase = (
                raw.get("current_phase")
                or raw.get("currentPhase")
                or (raw_lc.get("as_string") if isinstance(raw_lc, dict) else None)
                or (raw_lc.get("asString") if isinstance(raw_lc, dict) else None)
            )

            app = Application(
                id=app_id,
                name=name,
                business_criticality=raw.get("business_criticality") or raw.get("businessCriticality"),
                functional_suitability=raw.get("functional_suitability") or raw.get("functionalSuitability"),
                technical_suitability=raw.get("technical_suitability") or raw.get("technicalSuitability"),
                time_classification=raw.get("time_classification") or raw.get("timeClassification") or "UNKNOWN",
                current_phase=raw_phase,
                lifecycle=lifecycle,
                capabilities=raw.get("capabilities", []),
                user_groups=raw.get("user_groups") or raw.get("userGroups", []),
                tags=raw.get("tags", []),
                metadata=raw.get("metadata", {}),
            )
            self._storage[app.id] = app

    def save_to_disk(self) -> None:
        """Serialize current state back to disk."""
        data = [app.model_dump(mode="json") for app in self._storage.values()]
        if self.file_path.suffix.lower() in (".yaml", ".yml"):
            self.file_path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")
        else:
            self.file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
