"""Unit tests for LifecycleValidator."""

from datetime import date
from tecton.core.models import Application, Lifecycle, LifecyclePhase, LifecyclePhaseDate
from tecton.engines.lifecycle_validator import LifecycleValidator


def test_valid_lifecycle() -> None:
    validator = LifecycleValidator()
    app = Application(
        id="app-1",
        name="Valid App",
        lifecycle=Lifecycle(
            phases=[
                LifecyclePhaseDate(phase=LifecyclePhase.PLAN, start_date=date(2023, 1, 1)),
                LifecyclePhaseDate(phase=LifecyclePhase.ACTIVE, start_date=date(2024, 1, 1)),
                LifecyclePhaseDate(phase=LifecyclePhase.END_OF_LIFE, start_date=date(2030, 1, 1)),
            ]
        ),
    )
    issues = validator.validate_application(app)
    assert len(issues) == 0


def test_chronological_inversion_detected() -> None:
    validator = LifecycleValidator()
    app = Application(
        id="app-2",
        name="Inverted App",
        lifecycle=Lifecycle(
            phases=[
                LifecyclePhaseDate(phase=LifecyclePhase.ACTIVE, start_date=date(2025, 1, 1)),
                LifecyclePhaseDate(phase=LifecyclePhase.PLAN, start_date=date(2024, 1, 1)),
            ]
        ),
    )
    issues = validator.validate_application(app)
    assert len(issues) >= 1
    assert any("order violation" in issue.message.lower() for issue in issues)


def test_past_eol_warning_on_active_app() -> None:
    validator = LifecycleValidator()
    app = Application(
        id="app-3",
        name="Zombie App",
        current_phase=LifecyclePhase.ACTIVE,
        lifecycle=Lifecycle(
            phases=[
                LifecyclePhaseDate(phase=LifecyclePhase.ACTIVE, start_date=date(2015, 1, 1)),
                LifecyclePhaseDate(phase=LifecyclePhase.END_OF_LIFE, start_date=date(2020, 1, 1)),
            ]
        ),
    )
    issues = validator.validate_application(app)
    assert any(i.severity == "WARNING" and "already passed" in i.message for i in issues)
