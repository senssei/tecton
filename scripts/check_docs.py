"""Check local documentation links and executable manifest examples offline."""

import re
import shlex
import sys
from pathlib import Path

import yaml
from typer.main import get_command
from tecton_arch.cli.main import app
from tecton_arch.dsl.parser import C4EAMParser
from tecton_arch.engines.linter import GraphLinter

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = {"systems", "containers", "capabilities", "technologies", "relationships",
               "data_objects", "interfaces", "plateaus", "work_packages", "data_flow_diagrams"}


def main():
    documents = sorted(ROOT.glob("*.md")) + sorted((ROOT / "docs").rglob("*.md"))
    failures = []
    manifests = commands = links = 0
    cli = get_command(app)
    for path in documents:
        content = path.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", content, flags=re.S)
        targets = re.findall(r"\]\(([^\s)]+)\)", text)
        targets += re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', text)
        for target in targets:
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            destination = (path.parent / target.split("#", 1)[0]).resolve()
            links += 1
            if not destination.exists():
                failures.append(f"{path.relative_to(ROOT)}: missing link {target}")
        for language, block in re.findall(r"```([\w-]*)\n(.*?)```", content, re.S):
            if language in ("yaml", "yml", "json"):
                data = yaml.safe_load(block)
                if isinstance(data, dict) and COLLECTIONS.intersection(data):
                    manifests += 1
                    try:
                        graph = C4EAMParser().parse_content(block, str(path))
                        report = GraphLinter().lint(graph)
                        if report.has_errors:
                            raise ValueError("; ".join(issue.message for issue in report.issues if issue.severity == "ERROR"))
                    except Exception as error:
                        failures.append(f"{path.relative_to(ROOT)}: invalid example: {error}")
            if language in ("bash", "sh", "shell"):
                for line in block.splitlines():
                    if not line.startswith("tecton "):
                        continue
                    tokens = shlex.split(line)
                    command = cli
                    for token in tokens[1:]:
                        if not hasattr(command, "commands"):
                            break
                        if token.startswith("-"):
                            break
                        if token not in command.commands:
                            failures.append(f"{path.relative_to(ROOT)}: unknown command in {line}")
                            break
                        command = command.commands[token]
                    commands += 1
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Docs OK: {len(documents)} files, {links} local links, {manifests} manifest examples, {commands} command paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
