"""Workspace representation managing repository I/O and compiled architecture graph."""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from tecton.adapters.git_adapter import GitRepositoryAdapter
from tecton.adapters.in_memory import InMemoryRepositoryAdapter
from tecton.application.exceptions import WorkspaceNotFoundError
from tecton.dsl.parser import CompiledGraph


@runtime_checkable
class WorkspacePort(Protocol):
    """Abstract port representing an architectural workspace."""

    @property
    def graph(self) -> CompiledGraph:
        """Return compiled architectural graph."""
        ...

    def reload(self) -> CompiledGraph:
        """Reload architecture manifests from disk/storage and update in-memory graph."""
        ...


class Workspace:
    """Encapsulates file I/O, manifest parsing, and graph state for an architecture repository."""

    def __init__(self, workspace_source: Any = ".") -> None:
        if isinstance(workspace_source, (str, Path)):
            self.path = Path(workspace_source).resolve()
            if not self.path.exists():
                raise WorkspaceNotFoundError(f"Workspace path does not exist: {self.path}")
            self._adapter = GitRepositoryAdapter(self.path)
            self._graph: CompiledGraph | None = None
        elif hasattr(workspace_source, "fetch_applications"):
            self.path = Path(".")
            self._adapter = workspace_source
            self._graph = getattr(workspace_source, "graph", None)
        elif hasattr(workspace_source, "systems") and hasattr(workspace_source, "capabilities"):
            self.path = Path(".")
            self._graph = workspace_source
            apps = workspace_source.get_applications() if hasattr(workspace_source, "get_applications") else []
            self._adapter = InMemoryRepositoryAdapter(apps)
        else:
            raise TypeError(f"Unsupported workspace source: {type(workspace_source)}")

    @property
    def graph(self) -> CompiledGraph:
        """Return the current compiled architecture graph."""
        if self._graph is not None:
            return self._graph
        return self._adapter.graph

    @property
    def adapter(self) -> Any:
        """Return the underlying repository adapter."""
        return self._adapter

    def reload(self) -> CompiledGraph:
        """Reload architecture manifests from disk and update in-memory graph."""
        if hasattr(self._adapter, "reload"):
            self._adapter.reload()
            return self._adapter.graph
        return self.graph

    @classmethod
    def from_graph(cls, graph: CompiledGraph) -> "Workspace":
        return cls(graph)

