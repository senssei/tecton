"""Workspace representation managing repository I/O and compiled architecture graph."""

from pathlib import Path
from inspect import getattr_static
from typing import Any, Protocol, runtime_checkable

from tecton_arch.adapters.git_adapter import GitRepositoryAdapter
from tecton_arch.adapters.in_memory import InMemoryRepositoryAdapter
from tecton_arch.application.exceptions import WorkspaceNotFoundError
from tecton_arch.dsl.parser import CompiledGraph


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

    def __init__(
        self,
        workspace_source: Any = ".",
        config: Any = None,
        strict: bool = False,
    ) -> None:
        self.config = config
        self.strict = strict
        if isinstance(workspace_source, (str, Path)):
            self.path = Path(workspace_source).resolve()
            if not self.path.exists():
                raise WorkspaceNotFoundError(f"Workspace path does not exist: {self.path}")
            if self.config is None:
                from tecton_arch.core.config import TectonConfig
                self.config = TectonConfig.load(workspace_dir=self.path)
            eff_strict = strict or (self.config.strict if self.config else False)
            self.strict = eff_strict
            self._adapter = GitRepositoryAdapter(self.path, config=self.config, strict=eff_strict)
            self._graph: CompiledGraph | None = None
        elif hasattr(workspace_source, "fetch_applications"):
            self.path = Path(".")
            self._adapter = workspace_source
            self._graph = None
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
    def optional_graph(self) -> CompiledGraph | None:
        """Return a graph when supported, propagating graph-loading failures."""
        if self._graph is not None:
            return self._graph
        if getattr_static(self._adapter, "graph", None) is None:
            return None
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

