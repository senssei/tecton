"""Lifecycle Consistency Validator for architectural timeline governance."""

from datetime import date
from pydantic import BaseModel, Field
from tecton.core.models import Application, LifecyclePhase


class LifecycleIssue(BaseModel):
    """Detected lifecycle anomaly or chronological conflict."""

    application_id: str
    application_name: str
    severity: str = "ERROR"  # ERROR or WARNING
    message: str


class LifecycleValidationReport(BaseModel):
    """Aggregate lifecycle validation report."""

    is_valid: bool
    total_applications: int
    error_count: int
    warning_count: int
    issues: list[LifecycleIssue] = Field(default_factory=list)


class LifecycleValidator:
    """Validates chronological consistency of application lifecycle phases."""

    PHASE_ORDER = {
        LifecyclePhase.PLAN: 1,
        LifecyclePhase.PHASE_IN: 2,
        LifecyclePhase.ACTIVE: 3,
        LifecyclePhase.PHASE_OUT: 4,
        LifecyclePhase.END_OF_LIFE: 5,
    }

    def validate_application(self, application: Application) -> list[LifecycleIssue]:
        """Validate lifecycle phases of a single application."""
        issues: list[LifecycleIssue] = []

        if not application.lifecycle or not application.lifecycle.phases:
            return issues

        phases = application.lifecycle.phases
        # Check chronological order matches canonical lifecycle phase progression
        for i in range(len(phases) - 1):
            curr_p = phases[i]
            next_p = phases[i + 1]

            curr_order = self.PHASE_ORDER.get(curr_p.phase, 0)
            next_order = self.PHASE_ORDER.get(next_p.phase, 0)

            if curr_order > next_order:
                issues.append(
                    LifecycleIssue(
                        application_id=application.id,
                        application_name=application.name,
                        severity="ERROR",
                        message=(
                            f"Phase order violation: {curr_p.phase.value} appears before "
                            f"{next_p.phase.value} in sequence."
                        ),
                    )
                )

            if curr_p.start_date > next_p.start_date:
                issues.append(
                    LifecycleIssue(
                        application_id=application.id,
                        application_name=application.name,
                        severity="ERROR",
                        message=(
                            f"Chronological inverted date: {curr_p.phase.value} ({curr_p.start_date}) "
                            f"is after {next_p.phase.value} ({next_p.start_date})."
                        ),
                    )
                )

        # Check if End-of-Life is in the past while application is marked active
        today = date.today()
        eol_phase = next((p for p in phases if p.phase == LifecyclePhase.END_OF_LIFE), None)
        if eol_phase and eol_phase.start_date < today:
            if application.current_phase == LifecyclePhase.ACTIVE:
                issues.append(
                    LifecycleIssue(
                        application_id=application.id,
                        application_name=application.name,
                        severity="WARNING",
                        message=(
                            f"Application is marked Active, but End-of-Life date ({eol_phase.start_date}) "
                            f"has already passed."
                        ),
                    )
                )

        return issues

    def validate_all(self, applications: list[Application]) -> LifecycleValidationReport:
        """Validate a collection of applications and aggregate issues."""
        all_issues: list[LifecycleIssue] = []
        for app in applications:
            all_issues.extend(self.validate_application(app))

        errors = [i for i in all_issues if i.severity == "ERROR"]
        warnings = [i for i in all_issues if i.severity == "WARNING"]

        return LifecycleValidationReport(
            is_valid=len(errors) == 0,
            total_applications=len(applications),
            error_count=len(errors),
            warning_count=len(warnings),
            issues=all_issues,
        )
