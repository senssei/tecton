"""Integration tests for APMService using fixture data."""

from pathlib import Path
from tecton_arch.adapters.file_adapter import FileRepositoryAdapter
from tecton_arch.core.models import RedundancyConfig, TimeConfig, TimeQuadrant
from tecton_arch.services.apm_service import APMService


def test_apm_service_full_analysis() -> None:
    fixture_path = Path("tests/fixtures/sample_applications.json")
    repo = FileRepositoryAdapter(fixture_path)
    service = APMService(
        repository=repo,
        time_config=TimeConfig(business_threshold=3.5, technical_threshold=3.5),
        redundancy_config=RedundancyConfig(similarity_threshold=0.50),
    )

    result = service.analyze()

    assert len(result.applications) == 6

    # Verify Gartner TIME Classifications
    # Global Salesforce CRM: 4.5, 4.2 -> INVEST
    assert result.time_classifications["app-001-crm-global"] == TimeQuadrant.INVEST
    # Mainframe Core Ledger: 4.8, 1.9 -> TOLERATE
    assert result.time_classifications["app-003-core-banking"] == TimeQuadrant.TOLERATE
    # Modern DevTool: 2.2, 4.6 -> MIGRATE
    assert result.time_classifications["app-004-modern-devtool"] == TimeQuadrant.MIGRATE
    # Old Billing: 1.8, 1.5 -> ELIMINATE
    assert result.time_classifications["app-005-legacy-billing"] == TimeQuadrant.ELIMINATE

    # Verify Redundancy detection: Global Salesforce CRM and Regional SalesTracker
    assert len(result.redundancy_clusters) >= 1
    top_cluster = result.redundancy_clusters[0]
    assert "Global Salesforce CRM" in top_cluster.application_names
    assert "Regional SalesTracker" in top_cluster.application_names
    assert top_cluster.similarity_score >= 0.50

    # Verify Lifecycle Validator caught malformed app-006
    assert result.lifecycle_report.is_valid is False
    assert result.lifecycle_report.error_count >= 1
    error_apps = [issue.application_id for issue in result.lifecycle_report.issues if issue.severity == "ERROR"]
    assert "app-006-corrupt-lifecycle" in error_apps

    # Verify Patches generated
    assert result.patches_needed >= 4


def test_apm_service_apply_patches_dry_run() -> None:
    fixture_path = Path("tests/fixtures/sample_applications.json")
    repo = FileRepositoryAdapter(fixture_path)
    service = APMService(repo)

    results = service.apply_time_patches(dry_run=True)
    assert len(results) >= 4
    for r in results:
        assert r["dry_run"] is True
