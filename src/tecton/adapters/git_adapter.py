"""Git Repository Adapter (loads architecture graph from a Git workspace directory)."""

from pathlib import Path
from typing import Any
import yaml

from tecton.adapters.in_memory import InMemoryRepositoryAdapter
from tecton.core.models import Application, TimeQuadrant
from tecton.dsl.parser import C4EAMParser, CompiledGraph


class GitRepositoryAdapter(InMemoryRepositoryAdapter):
    """Hexagonal Architecture adapter that ingests an entire Git repository workspace.
    
    Parses all distributed C4-Extended YAML/JSON manifests into a compiled graph
    and serves Application Portfolio Management (APM) requests.
    """

    def __init__(self, workspace_path: str | Path) -> None:
        super().__init__()
        self.workspace_path = Path(workspace_path)
        self.parser = C4EAMParser()
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

    def apply_patches(
        self, entity_id: str, patches: list[dict[str, Any]], dry_run: bool = True
    ) -> dict[str, Any]:
        """Apply patches in-memory and optionally sync back to origin YAML file."""
        result = super().apply_patches(entity_id, patches, dry_run=dry_run)

        if not dry_run:
            origin_file = self.graph.symbol_origins.get(entity_id)
            if origin_file and Path(origin_file).is_file():
                self._persist_entity_patch(entity_id, patches, Path(origin_file))

        return result

    def _persist_entity_patch(self, entity_id: str, patches: list[dict[str, Any]], file_path: Path) -> None:
        """Update entity fields in the origin YAML file."""
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

            if updated:
                file_path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")
        except Exception:
            # Fallback gracefully if custom formatting cannot be cleanly overwritten
            pass
