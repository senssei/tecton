"""Unit tests for DiffService security and git revision comparison."""

from pathlib import Path
import pytest
import subprocess
from tecton_arch.services.diff_service import DiffService


def test_diff_service_rejects_malicious_git_ref(tmp_path: Path):
    service = DiffService()
    marker = tmp_path / "injected_file.txt"
    malicious_ref = f"HEAD; touch {marker}"

    with pytest.raises(ValueError, match="Invalid Git reference"):
        service.compare_git_revisions(
            base_ref=malicious_ref,
            head_ref="HEAD",
            repo_root=Path(__file__).parents[2],
        )

    # Verify that the command injection was completely prevented (no shell execution)
    assert not marker.exists(), "Command injection vulnerability detected: injected command was executed!"


def test_diff_service_rejects_invalid_ref():
    service = DiffService()
    with pytest.raises(ValueError, match="Invalid Git reference"):
        service.compare_git_revisions(
            base_ref="non_existent_branch_ref_12345",
            head_ref="HEAD",
            repo_root=Path(__file__).parents[2],
        )


def test_diff_service_valid_git_revision_diff(tmp_path: Path):
    service = DiffService()
    repo_root = tmp_path / "catalog-repo"
    repo_root.mkdir()
    manifest = repo_root / "systems.yaml"
    manifest.write_text("systems:\n  - id: sys-test\n    name: Original\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main", str(repo_root)], check=True, capture_output=True)
    subprocess.run(["git", "add", "systems.yaml"], cwd=repo_root, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false", "commit", "-m", "Baseline"],
        cwd=repo_root, check=True, capture_output=True,
    )
    manifest.write_text("systems:\n  - id: sys-test\n    name: Updated\n", encoding="utf-8")
    # Compare a known committed catalog with its uncommitted update.
    report = service.compare_git_revisions(
        base_ref="HEAD",
        head_ref="WORKTREE",
        repo_root=repo_root,
    )
    assert report is not None
    assert report.base_ref == "HEAD"
    assert report.head_ref == "WORKTREE"

    assert any(delta.entity_id == "sys-test" and "name" in delta.field_changes for delta in report.deltas)
