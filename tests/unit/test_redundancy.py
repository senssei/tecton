"""Unit tests for RedundancyDetectionEngine."""

from tecton_arch.core.models import Application, RedundancyConfig
from tecton_arch.engines.redundancy import RedundancyDetectionEngine


def test_jaccard_similarity_calculation() -> None:
    engine = RedundancyDetectionEngine(RedundancyConfig(capability_weight=0.5, user_group_weight=0.5))
    app_a = Application(
        id="app-1",
        name="CRM A",
        capabilities=["CRM", "Leads"],
        user_groups=["Sales"],
    )
    app_b = Application(
        id="app-2",
        name="CRM B",
        capabilities=["CRM", "Leads"],
        user_groups=["Sales"],
    )

    sim, shared_caps, shared_users = engine.calculate_similarity(app_a, app_b)
    assert sim == 1.0
    assert shared_caps == ["CRM", "Leads"]
    assert shared_users == ["Sales"]


def test_partial_jaccard_similarity() -> None:
    engine = RedundancyDetectionEngine(RedundancyConfig(capability_weight=0.7, user_group_weight=0.3))
    app_a = Application(
        id="app-1",
        name="CRM A",
        capabilities=["CRM", "Leads"],
        user_groups=["Sales EMEA"],
    )
    app_b = Application(
        id="app-2",
        name="CRM B",
        capabilities=["CRM", "Billing"],
        user_groups=["Sales EMEA", "Finance"],
    )

    # Caps: intersection {"CRM"} (1) / union {"CRM", "Leads", "Billing"} (3) = 1/3
    # Users: intersection {"Sales EMEA"} (1) / union {"Sales EMEA", "Finance"} (2) = 1/2
    # Score: 0.7 * (1/3) + 0.3 * (0.5) = 0.2333 + 0.15 = 0.3833
    sim, shared_caps, shared_users = engine.calculate_similarity(app_a, app_b)
    assert 0.38 <= sim <= 0.39
    assert shared_caps == ["CRM"]
    assert shared_users == ["Sales EMEA"]


def test_find_redundancies_clusters_over_threshold() -> None:
    engine = RedundancyDetectionEngine(RedundancyConfig(similarity_threshold=0.60))
    apps = [
        Application(id="1", name="App 1", capabilities=["A", "B"], user_groups=["U1"]),
        Application(id="2", name="App 2", capabilities=["A", "B"], user_groups=["U1"]),
        Application(id="3", name="App 3", capabilities=["X", "Y"], user_groups=["U2"]),
    ]
    clusters = engine.find_redundancies(apps)
    assert len(clusters) == 1
    assert clusters[0].application_names == ["App 1", "App 2"]
    assert clusters[0].similarity_score == 1.0
