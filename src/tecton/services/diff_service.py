"""Architecture Diff Service orchestrating semantic graph comparisons across Git & folders."""

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from tecton.dsl.parser import C4EAMParser, CompiledGraph
from tecton.engines.diff_engine import ArchitectureDiffReport, ChangeType, DiffEngine


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
    ) -> ArchitectureDiffReport:
        """Compare two filesystem directories or manifest files."""
        b_path = Path(base_path)
        h_path = Path(head_path)

        if not b_path.exists():
            raise FileNotFoundError(f"Base path does not exist: {b_path}")
        if not h_path.exists():
            raise FileNotFoundError(f"Head path does not exist: {h_path}")

        base_graph = self.parser.parse_directory(b_path)
        head_graph = self.parser.parse_directory(h_path)

        return self.engine.compare(
            base_graph=base_graph,
            head_graph=head_graph,
            base_ref=base_label or str(b_path),
            head_ref=head_label or str(h_path),
        )

    def compare_git_revisions(
        self,
        base_ref: str,
        head_ref: str = "HEAD",
        repo_root: Path | str = ".",
    ) -> ArchitectureDiffReport:
        """Extract and compare two Git revisions (commit hashes, branches, or tags)."""
        root = Path(repo_root).resolve()

        with tempfile.TemporaryDirectory() as tmp_base, tempfile.TemporaryDirectory() as tmp_head:
            # Extract base_ref files
            self._extract_git_tree(base_ref, Path(tmp_base), root)
            base_graph = self.parser.parse_directory(Path(tmp_base))

            if head_ref in ("WORKTREE", "WORKING_DIR", "."):
                # Use current working directory directly
                head_graph = self.parser.parse_directory(root)
            else:
                self._extract_git_tree(head_ref, Path(tmp_head), root)
                head_graph = self.parser.parse_directory(Path(tmp_head))

            return self.engine.compare(
                base_graph=base_graph,
                head_graph=head_graph,
                base_ref=base_ref,
                head_ref=head_ref,
            )

    def _extract_git_tree(self, ref: str, dest_dir: Path, repo_root: Path) -> None:
        """Extract a Git tree at a given ref into a target directory."""
        try:
            # git archive <ref> | tar -x -C <dest_dir>
            cmd = f"git archive {ref} | tar -x -C {dest_dir}"
            subprocess.run(
                cmd,
                shell=True,
                check=True,
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to extract Git ref '{ref}': {e.stderr.decode()}") from e

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
            "### 📊 Podsumowanie Zmian Architektonicznych",
            "",
            "| Metryka | Wartość |",
            "| :--- | :--- |",
            f"| **Dodane Elementy** | `{report.added_count}` |",
            f"| **Usunięte Elementy** | `{report.removed_count}` |",
            f"| **Zmodyfikowane Elementy** | `{report.modified_count}` |",
            f"| **Nowe Ryzyka / Błędy Lintera** | `{len(report.new_risk_issues)}` |",
            f"| **Nowe Luki w Zdolnościach (Gaps)** | `{len(report.new_capability_gaps)}` |",
            "",
        ]

        if report.new_risk_issues:
            lines.append("### 🚨 Nowo Wykryte Zagrożenia & Regresje Jakości")
            lines.append("")
            lines.append("| Poziom | Reguła | Dotknięty Element | Komunikat |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for risk in report.new_risk_issues:
                icon = "🚨 BŁĄD" if risk.get("severity") == "ERROR" else "⚠️ OSTRZEŻENIE"
                lines.append(
                    f"| {icon} | `{risk.get('rule')}` | `{risk.get('entity_id')}` | {risk.get('message')} |"
                )
            lines.append("")

        if report.new_capability_gaps:
            lines.append("### ⚠️ Powstałe Luki w Zdolnościach Biznesowych (Blind Spots)")
            lines.append("")
            lines.append("Poniższe zdolności biznesowe utraciły wszystkie realizujące je systemy informatyczne:")
            for gap in report.new_capability_gaps:
                lines.append(f"- 🛑 `{gap}`")
            lines.append("")

        if report.deltas:
            lines.append("<details><summary><b>🔍 Szczegółowa Lista Zmian Elementów (Kliknij, aby rozwinąć)</b></summary>")
            lines.append("")
            lines.append("| Typ Encji | ID Elementu | Typ Zmiany | Nazwa / Modyfikowane Pola |")
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
