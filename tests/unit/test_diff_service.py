"""Unit tests for DiffService security and git revision comparison."""

from pathlib import Path
import pytest
from tecton.services.diff_service import DiffService


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


def test_diff_service_valid_git_revision_diff():
    service = DiffService()
    repo_root = Path(__file__).parents[2]
    # Compare HEAD with WORKTREE / working directory
    report = service.compare_git_revisions(
        base_ref="HEAD",
        head_ref="WORKTREE",
        repo_root=repo_root,
    )
    assert report is not None
    assert report.base_ref == "HEAD"
    assert report.head_ref == "WORKTREE"
