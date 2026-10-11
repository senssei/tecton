"""Configuration management for Tecton Engine."""

import os
from pathlib import Path
from typing import Any, Literal
from decimal import Decimal
import yaml
from pydantic import BaseModel, Field, ConfigDict, field_validator

from tecton_arch.core.models import RedundancyConfig, TimeConfig


class RepositoryConfig(BaseModel):
    """Configuration for remote graph repository connections."""

    url: str | None = None
    token: str | None = None
    workspace: str | None = None
    timeout_seconds: int = 30
    verify_ssl: bool = True


class ManifestsConfig(BaseModel):
    """Scoped workspace manifest discovery configuration."""

    include: list[str] = Field(default_factory=lambda: ["**/*.yaml", "**/*.yml", "**/*.json"])
    exclude: list[str] = Field(default_factory=list)


class WorkspaceConfig(BaseModel):
    """Workspace settings and quality gate defaults."""

    name: str | None = None
    strict: bool = False
    require_owner: bool = False


class OwnerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    active: bool = True


class TeamConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capacity_person_days: Decimal = Field(default=0, ge=0, allow_inf_nan=False)
    monthly_capacity: dict[str, Decimal] = Field(default_factory=dict)

    @field_validator("monthly_capacity")
    @classmethod
    def validate_capacity(cls, values):
        import re
        for month, amount in values.items():
            if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month) or not amount.is_finite() or amount < 0:
                raise ValueError("Invalid month or capacity")
        return values


class QualityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review_valid_days: int = Field(default=180, gt=0)
    rules: dict[str, Literal["error", "warning", "off"]] = Field(default_factory=dict)

    @field_validator("rules")
    @classmethod
    def valid_rules(cls, values):
        from tecton_arch.core.quality import RULES, PROTECTED_PREFIXES, PROTECTED_RULES
        for rule, level in values.items():
            if rule not in RULES:
                raise ValueError(f"Unknown quality rule: {rule}")
            if (rule in PROTECTED_RULES or rule.startswith(PROTECTED_PREFIXES)) and level != "error":
                raise ValueError(f"Structural rule {rule} must remain error")
        return values


class TectonConfig(BaseModel):
    """Global configuration for Tecton."""

    quality: QualityConfig = Field(default_factory=QualityConfig)
    owners: dict[str, OwnerConfig] = Field(default_factory=dict)
    teams: dict[str, TeamConfig] = Field(default_factory=dict)
    budgets: dict[str, dict[str, Decimal]] = Field(default_factory=dict)

    @field_validator("budgets")
    @classmethod
    def valid_budgets(cls, values):
        import re
        for month, currencies in values.items():
            if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
                raise ValueError("Invalid budget month")
            for currency, amount in currencies.items():
                if not re.fullmatch(r"[A-Z]{3}", currency) or not amount.is_finite() or amount < 0:
                    raise ValueError("Invalid currency or budget amount")
        return values

    dry_run: bool = True
    strict: bool = False
    manifests: ManifestsConfig = Field(default_factory=ManifestsConfig)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    time: TimeConfig = Field(default_factory=TimeConfig)
    redundancy: RedundancyConfig = Field(default_factory=RedundancyConfig)
    repository: RepositoryConfig = Field(default_factory=RepositoryConfig)

    @classmethod
    def load(
        cls,
        config_path: str | Path | None = None,
        workspace_dir: str | Path | None = None,
    ) -> "TectonConfig":
        """Load configuration from YAML file and environment variables."""
        if config_path and not Path(config_path).is_file():
            raise FileNotFoundError(f"Configuration does not exist: {config_path}")
        data: dict[str, Any] = {}

        ws_path = Path(workspace_dir).resolve() if workspace_dir else None

        candidate_paths: list[Path | None] = [
            Path(config_path) if config_path else None,
            (ws_path / "tecton.yaml") if ws_path and ws_path.is_dir() else None,
            (ws_path / ".tecton.yaml") if ws_path and ws_path.is_dir() else None,
            (ws_path / "tecton.yml") if ws_path and ws_path.is_dir() else None,
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
                        raise ValueError(f"Configuration {p} must be a mapping")
                except (OSError, yaml.YAMLError) as exc:
                    raise ValueError(f"Cannot load configuration {p}: {exc}") from exc

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

        if "TECTON_STRICT" in os.environ:
            data["strict"] = os.environ["TECTON_STRICT"].lower() in ("1", "true", "yes")
        elif "strict" in data.get("workspace", {}):
            data["strict"] = data["workspace"]["strict"]

        time_data = data.setdefault("time", {})
        if "TECTON_TIME_BUSINESS_THRESHOLD" in os.environ:
            time_data["business_threshold"] = float(os.environ["TECTON_TIME_BUSINESS_THRESHOLD"])
        if "TECTON_TIME_TECHNICAL_THRESHOLD" in os.environ:
            time_data["technical_threshold"] = float(os.environ["TECTON_TIME_TECHNICAL_THRESHOLD"])

        return cls.model_validate(data)

