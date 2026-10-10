"""Configuration management for Tecton Engine."""

import os
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field

from tecton.core.models import RedundancyConfig, TimeConfig


class RepositoryConfig(BaseModel):
    """Configuration for remote graph repository connections."""

    url: str | None = None
    token: str | None = None
    workspace: str | None = None
    timeout_seconds: int = 30
    verify_ssl: bool = True


class TectonConfig(BaseModel):
    """Global configuration for Tecton."""

    dry_run: bool = True
    time: TimeConfig = Field(default_factory=TimeConfig)
    redundancy: RedundancyConfig = Field(default_factory=RedundancyConfig)
    repository: RepositoryConfig = Field(default_factory=RepositoryConfig)

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "TectonConfig":
        """Load configuration from YAML file and environment variables."""
        data: dict[str, Any] = {}

        candidate_paths = [
            Path(config_path) if config_path else None,
            Path("tecton.yaml"),
            Path(".tecton.yaml"),
            Path("tecton.yml"),
        ]

        for p in candidate_paths:
            if p and p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        loaded = yaml.safe_load(f)
                        if isinstance(loaded, dict):
                            data = loaded
                            break
                except Exception:
                    pass

        # Environment variable overrides
        repo_data = data.setdefault("repository", {})
        if "TECTON_API_URL" in os.environ:
            repo_data["url"] = os.environ["TECTON_API_URL"]
        if "TECTON_API_TOKEN" in os.environ:
            repo_data["token"] = os.environ["TECTON_API_TOKEN"]
        if "TECTON_WORKSPACE" in os.environ:
            repo_data["workspace"] = os.environ["TECTON_WORKSPACE"]

        if "TECTON_DRY_RUN" in os.environ:
            data["dry_run"] = os.environ["TECTON_DRY_RUN"].lower() in ("1", "true", "yes")

        time_data = data.setdefault("time", {})
        if "TECTON_TIME_BUSINESS_THRESHOLD" in os.environ:
            time_data["business_threshold"] = float(os.environ["TECTON_TIME_BUSINESS_THRESHOLD"])
        if "TECTON_TIME_TECHNICAL_THRESHOLD" in os.environ:
            time_data["technical_threshold"] = float(os.environ["TECTON_TIME_TECHNICAL_THRESHOLD"])

        return cls.model_validate(data)
