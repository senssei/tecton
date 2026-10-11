"""Architecture Diff Service orchestrating semantic graph comparisons across Git & folders."""

import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any
from tecton_arch.core.config import TectonConfig
from tecton_arch.engines.diff_engine import changed_fields

from tecton_arch.dsl.parser import C4EAMParser, CompiledGraph
from tecton_arch.engines.diff_engine import ArchitectureDiffReport, ChangeType, DiffEngine


class DiffService:
    """Service orchestrating semantic architectural comparisons across directories or Git commits."""

    def __init__(self) -> None:
        self.parser = C4EAMParser()
        self.engine = DiffEngine()

    def compare_directories(
        self,
        base_path: Path | str,
        head_path: Path | str,
        base_label: str | None = None,
        head_label: str | None = None,
        as_of_date=None,
        config=None,
    ) -> ArchitectureDiffReport:
        """Compare two filesystem directories or manifest files."""
        b_path = Path(base_path)
        h_path = Path(head_path)

        if not b_path.exists():
            raise FileNotFoundError(f"Base path does not exist: {b_path}")
        if not h_path.exists():
            raise FileNotFoundError(f"Head path does not exist: {h_path}")

        effective_config = config or TectonConfig.load(workspace_dir=h_path if h_path.is_dir() else h_path.parent)
        parser = C4EAMParser(config=effective_config)
        base_graph = parser.parse_directory(b_path)
        head_graph = parser.parse_directory(h_path)

        report = self.engine.compare(
            base_graph=base_graph,
            head_graph=head_graph,
            base_ref=base_label or str(b_path),
            head_ref=head_label or str(h_path),
            as_of_date=as_of_date, config=effective_config,
        )
        report.configuration_changes = changed_fields(
            TectonConfig.load(workspace_dir=b_path if b_path.is_dir() else b_path.parent).model_dump(mode="json", exclude={"repository"}),
            TectonConfig.load(workspace_dir=h_path if h_path.is_dir() else h_path.parent).model_dump(mode="json", exclude={"repository"}),
        )
        return report

    def compare_git_revisions(
        self,
        base_ref: str,
        head_ref: str = "HEAD",
        repo_root: Path | str = ".",
        workspace_path: str = ".",
        as_of_date=None,
        config=None,
    ) -> ArchitectureDiffReport:
        """Extract and compare two Git revisions (commit hashes, branches, or tags)."""
        root = Path(repo_root).resolve()

        subpath = Path(workspace_path)
        if subpath.is_absolute() or ".." in subpath.parts:
            raise ValueError("workspace_path must stay relative to the repository")
        with tempfile.TemporaryDirectory() as tmp_base, tempfile.TemporaryDirectory() as tmp_head:
            self._extract_git_tree(base_ref, Path(tmp_base), root)
            base_path = Path(tmp_base) / subpath
            if head_ref in ("WORKTREE", "WORKING_DIR", "."):
                head_path = root / subpath
                if not head_path.resolve().is_relative_to(root):
                    raise ValueError("Workspace resolves outside repository")
            else:
                self._extract_git_tree(head_ref, Path(tmp_head), root)
                head_path = Path(tmp_head) / subpath
            return self.compare_directories(base_path, head_path, base_ref, head_ref, as_of_date, config)

    def _extract_git_tree(self, ref: str, dest_dir: Path, repo_root: Path) -> None:
        """Extract a Git tree at a given ref into a target directory securely without shell execution."""
        # Validate that ref exists and resolves cleanly to a commit or tree object
        try:
            rev_parse = subprocess.run(
                ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if rev_parse.returncode != 0:
                rev_parse = subprocess.run(
                    ["git", "rev-parse", "--verify", ref],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if rev_parse.returncode != 0:
                    raise ValueError(f"Invalid Git reference '{ref}': {rev_parse.stderr.strip()}")
        except (subprocess.SubprocessError, OSError) as e:
            raise ValueError(f"Failed to verify Git ref '{ref}': {e}") from e

        # Archive ref safely without shell
        try:
            proc = subprocess.run(
                ["git", "archive", "--format=tar", ref],
                cwd=repo_root,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to archive Git ref '{ref}': {e.stderr.decode(errors='replace')}") from e

        # Safely extract in Python, guarding against directory traversal
        try:
            tar_stream = io.BytesIO(proc.stdout)
            with tarfile.open(fileobj=tar_stream, mode="r:") as tar:
                if hasattr(tarfile, "data_filter"):
                    tar.extractall(path=dest_dir, filter="data")
                else:
                    tar.extractall(path=dest_dir)
        except Exception as e:
            raise ValueError(f"Failed to extract tar archive for Git ref '{ref}': {e}") from e

    @staticmethod
    def to_pr_comment_markdown(report: ArchitectureDiffReport) -> str:
        """Format an ArchitectureDiffReport into an executive GitHub/GitLab Pull Request comment."""
        status_badge = "🟢 **PASS: No Breaking Architectural Changes**"
        if report.has_breaking_changes:
            status_badge = "🔴 **BLOCKED: Breaking Architectural Regressions Detected**"

        lines = [
            "## 🏛️ Tecton Architecture Review Gate",
            "",
            status_badge,
            "",
            f"> Comparing `{report.base_ref}` ➔ `{report.head_ref}`",
            "",
            f"Evaluation date: {report.as_of_date}",
            f"Configuration fingerprint: `{report.config_fingerprint}`",
            "",
            "### 📊 Architectural Change Summary",
            "",
            "| Metric | Value |",
            "| :--- | :--- |",
            f"| **Added Entities** | `{report.added_count}` |",
            f"| **Removed Entities** | `{report.removed_count}` |",
            f"| **Modified Entities** | `{report.modified_count}` |",
            f"| **New Risks / Linter Issues** | `{len(report.new_risk_issues)}` |",
            f"| **New Capability Gaps** | `{len(report.new_capability_gaps)}` |",
            "",
        ]

        if report.configuration_changes:
            lines.extend(["### Configuration changes", "", "```json", json.dumps(report.configuration_changes, indent=2, default=str), "```", ""])

        if report.new_risk_issues:
            lines.append("### 🚨 New Risks & Quality Regressions Detected")
            lines.append("")
            lines.append("| Severity | Rule | Impacted Entity | Message |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for risk in report.new_risk_issues:
                icon = "🚨 ERROR" if risk.get("severity") == "ERROR" else "⚠️ WARN"
                lines.append(
                    f"| {icon} | `{risk.get('rule')}` | `{risk.get('entity_id')}` | {risk.get('message')} |"
                )
            lines.append("")

        if report.new_capability_gaps:
            lines.append("### ⚠️ New Business Capability Blind Spots (Gaps)")
            lines.append("")
            lines.append("The following business capabilities lost all supporting IT systems:")
            for gap in report.new_capability_gaps:
                lines.append(f"- 🛑 `{gap}`")
            lines.append("")

        if report.deltas:
            lines.append("<details><summary><b>🔍 Detailed Entity Change Log (Click to expand)</b></summary>")
            lines.append("")
            lines.append("| Entity Type | Entity ID | Change Type | Name / Field Changes |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for d in report.deltas:
                change_badge = (
                    "🟢 ADDED" if d.change_type == ChangeType.ADDED
                    else "🔴 REMOVED" if d.change_type == ChangeType.REMOVED
                    else "🟡 MODIFIED"
                )
                fields_desc = d.name or "-"
                if d.field_changes:
                    fields_desc += " (" + ", ".join(f"`{k}`: {v[0]} ➔ {v[1]}" for k, v in d.field_changes.items()) + ")"
                lines.append(f"| `{d.entity_type}` | `{d.entity_id}` | {change_badge} | {fields_desc} |")
            lines.append("</details>")
            lines.append("")

        return "\n".join(lines)
