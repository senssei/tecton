"""Tecton: Deterministic Enterprise Architecture Intelligence Engine & Architecture-as-Code Toolkit."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("tecton")
except PackageNotFoundError:
    __version__ = "0.1.0"
