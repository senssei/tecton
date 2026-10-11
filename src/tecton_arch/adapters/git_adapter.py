"""Git Repository Adapter (loads architecture graph from a Git workspace directory)."""

from datetime import date
from pathlib import Path
from typing import Any
import yaml

from tecton_arch.adapters.in_memory import InMemoryRepositoryAdapter
from tecton_arch.core.models import Application, TimeQuadrant
from tecton_arch.dsl.parser import C4EAMParser, CompiledGraph


class GitRepositoryAdapter(InMemoryRepositoryAdapter):
    """Hexagonal Architecture adapter that ingests an entire Git repository workspace.
    
    Parses all distributed C4-Extended YAML/JSON manifests into a compiled graph
    and serves Application Portfolio Management (APM) requests.
    """

    def __init__(self, workspace_path: str | Path, config: Any = None, strict: bool = False) -> None:
        super().__init__()
        self.workspace_path = Path(workspace_path)
        self.config = config
        self.strict = strict
        self.parser = C4EAMParser(config=self.config, strict=self.strict)
        self.graph: CompiledGraph = self.parser.parse_directory(self.workspace_path)
        self._hydrate()


    def _hydrate(self) -> None:
        """Hydrate internal storage with applications from the compiled graph."""
        self._storage.clear()
        for app in self.graph.get_applications():
            self._storage[app.id] = app

    def reload(self) -> None:
        """Reload and recompile the architecture graph from the Git workspace."""
        self.graph = self.parser.parse_directory(self.workspace_path)
        self._hydrate()

    def fetch_applications(self, as_of_date: date | None = None) -> list[Application]:
        """Fetch applications with active phases evaluated as of target date."""
        if as_of_date:
            return self.graph.get_applications(as_of_date=as_of_date)
        return super().fetch_applications()

    def apply_patches(
        self, entity_id: str, patches: list[dict[str, Any]], dry_run: bool = True
    ) -> dict[str, Any]:
        """Apply patches atomically: write to disk first, then reload graph/storage."""
        if dry_run:
            return super().apply_patches(entity_id, patches, dry_run=True)

        app = self.get_application(entity_id)
        if not app:
            raise KeyError(f"Entity with ID {entity_id} not found in in-memory repository.")

        origin_file = self.graph.symbol_origins.get(entity_id)
        if origin_file and Path(origin_file).is_file():
            self._persist_entity_patch(entity_id, patches, Path(origin_file))

        self.reload()

        applied_changes = [
            {"op": p.get("op"), "path": p.get("path", ""), "value": p.get("value"), "status": "applied"}
            for p in patches
        ]
        return {
            "entity_id": entity_id,
            "dry_run": False,
            "applied_count": len(patches),
            "patches": applied_changes,
        }

    def _persist_entity_patch(self, entity_id: str, patches: list[dict[str, Any]], file_path: Path) -> None:
        """Atomically update entity fields in the origin YAML file."""
        import os
        import tempfile

        try:
            content = file_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)

            updated = False
            # If root dictionary with "systems" list
            if isinstance(data, dict) and "systems" in data:
                for sys in data["systems"]:
                    if str(sys.get("id")) == entity_id:
                        for p in patches:
                            path = p.get("path", "").lstrip("/")
                            # normalize camelCase or snake_case
                            if path in ("timeClassification", "time_classification"):
                                sys["time_classification"] = p.get("value")
                                updated = True
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and str(item.get("id")) == entity_id:
                        for p in patches:
                            path = p.get("path", "").lstrip("/")
                            if path in ("timeClassification", "time_classification"):
                                item["time_classification"] = p.get("value")
                                updated = True

            if not updated:
                raise ValueError(f"Entity '{entity_id}' could not be matched in manifest '{file_path}'")

            temp_file = None
            try:
                with tempfile.NamedTemporaryFile("w", dir=file_path.parent, delete=False, encoding="utf-8") as tf:
                    temp_file = tf.name
                    yaml.dump(data, tf, sort_keys=False)
                os.replace(temp_file, file_path)
            except Exception:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except OSError:
                        pass
                raise
        except Exception as e:
            raise IOError(f"Failed to persist patch for entity '{entity_id}' into '{file_path}': {e}") from e
