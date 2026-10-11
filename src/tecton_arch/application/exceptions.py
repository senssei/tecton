"""Domain and application exceptions for Tecton."""


class TectonApplicationError(Exception):
    """Base class for application and use-case errors."""


class WorkspaceNotFoundError(TectonApplicationError):
    """Raised when the specified architecture workspace path does not exist."""


class InvalidRefError(TectonApplicationError):
    """Raised when an invalid Git revision or reference is supplied."""


class ValidationFailedError(TectonApplicationError):
    """Raised when the architectural quality gate fails in strict mode."""


class ExportError(TectonApplicationError):
    """Raised when an architecture model export fails or format is unrecognized."""


class EntityNotFoundError(TectonApplicationError):
    """Raised when a requested architectural entity is not found in the graph."""
