#!/usr/bin/env python3
"""Check deterministic Raveil documentation and record invariants."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[4]
REQUIRED = (
    "AGENTS.md",
    "TODO.md",
    "docs/README.md",
    "docs/STATUS.md",
    "docs/ROADMAP.md",
    "docs/OPEN_QUESTIONS.md",
    "docs/WORKFLOW.md",
)
TASK_RE = re.compile(r"^- \[[ xX]\] \*\*(T-\d{4})\*\*", re.MULTILINE)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
RECORD_RE = re.compile(r"^(ADR|EXP|RFC)-(\d{4})-.*\.md$")
STATUS_RE = re.compile(r"^Status:\s*(.+?)\s*$", re.MULTILINE)
ALLOWED_STATUS = {
    "decisions": {"Proposed", "Accepted", "Rejected", "Superseded"},
    "experiments": {
        "Planned",
        "In progress",
        "Completed",
        "Rejected",
        "Inconclusive",
        "Superseded",
    },
    "rfcs": {"Proposed", "Accepted", "Rejected", "Superseded"},
}


def markdown_files() -> list[Path]:
    ignored = {".git", ".idea", "build", "external", "__pycache__"}
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in ignored for part in path.relative_to(ROOT).parts)
    )


def main() -> int:
    errors: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required record: {relative}")

    handoff_files = list((ROOT / "docs/handoff").glob("**/*")) if (ROOT / "docs/handoff").exists() else []
    if any(path.is_file() for path in handoff_files):
        errors.append("docs/handoff must not contain active records; use canonical docs or archive")

    files = markdown_files()
    for path in files:
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.split("#", 1)[0].strip()
            if not target or re.match(r"^[a-z][a-z0-9+.-]*://", target):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"broken link: {relative}: {raw_target}")

        active = not relative.parts[:2] in {
            ("docs", "archive"),
            ("docs", "history"),
            ("docs", "log"),
        }
        if active and "docs/handoff" in text:
            errors.append(f"stale handoff reference: {relative}")
        if active and "previous/raveil" in text:
            errors.append(f"nonexistent prototype reference in active record: {relative}")
        if "/Users/" in text:
            errors.append(f"machine-local user path: {relative}")

    task_ids = TASK_RE.findall((ROOT / "TODO.md").read_text(encoding="utf-8"))
    for task_id, count in Counter(task_ids).items():
        if count > 1:
            errors.append(f"duplicate task definition: {task_id}")

    record_ids: list[str] = []
    for directory, allowed in ALLOWED_STATUS.items():
        for path in sorted((ROOT / f"docs/{directory}").glob("*.md")):
            match = RECORD_RE.match(path.name)
            if not match:
                continue
            record_ids.append(f"{match.group(1)}-{match.group(2)}")
            status = STATUS_RE.search(path.read_text(encoding="utf-8"))
            if status is None:
                errors.append(f"missing Status field: {path.relative_to(ROOT)}")
            elif status.group(1) not in allowed:
                errors.append(
                    f"invalid Status '{status.group(1)}': {path.relative_to(ROOT)}"
                )
    for record_id, count in Counter(record_ids).items():
        if count > 1:
            errors.append(f"duplicate record identifier: {record_id}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        f"record check passed: {len(files)} Markdown files, "
        f"{len(task_ids)} task definitions, {len(record_ids)} records"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
