"""Architecture Repository Port (Hexagonal Architecture Interface)."""

from typing import Any, Protocol, runtime_checkable
from tecton_arch.core.models import Application


@runtime_checkable
class ArchitectureRepositoryPort(Protocol):
    """Port for interacting with Enterprise Architecture repositories."""

    def fetch_applications(self) -> list[Application]:
        """Fetch all applications from the architecture repository."""
        ...

    def save_application(self, application: Application) -> Application:
        """Create or update a single application."""
        ...

    def apply_patches(
        self, entity_id: str, patches: list[dict[str, Any]], dry_run: bool = True
    ) -> dict[str, Any]:
        """Apply a list of JSON Patches (add, replace, remove) to an entity."""
        ...
