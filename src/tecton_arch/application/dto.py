"""Data Transfer Objects (DTOs) for Tecton application use cases."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class HealthDto(BaseModel):
    status: str = "ok"
    version: str
    workspace_path: str
    files_scanned: int
    applications: int
    capabilities: int
    technologies: int
    interfaces: int
    data_objects: int
    relationships: int
    plateaus: int = 0
    work_packages: int = 0


class OverviewDto(BaseModel):
    version: str
    workspace_path: str
    quality_gate_valid: bool
    linter_errors: int
    linter_warnings: int
    total_applications: int
    total_capabilities: int
    capability_coverage_percentage: float
    capability_blind_spots: int
    total_technologies: int
    technologies_past_eol: int
    total_interfaces: int
    total_data_objects: int
    total_plateaus: int = 0
    total_work_packages: int = 0
    as_of_date: Optional[str] = None


class ValidationIssueDto(BaseModel):
    severity: str
    rule: str
    message: str
    entity_id: Optional[str] = None
    file_origin: Optional[str] = None


class ValidationReportDto(BaseModel):
    valid: bool
    error_count: int
    warning_count: int
    as_of_date: Optional[str] = None
    issues: list[ValidationIssueDto] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0


class ExportResultDto(BaseModel):
    format: str
    content: str
    media_type: str
    file_extension: str
    output_path: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
