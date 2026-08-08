#!/usr/bin/env python3
"""Rank Raveil files for a query without emitting whole-file contents."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[4]
ALWAYS = ("AGENTS.md", "docs/README.md", "docs/STATUS.md", "TODO.md")
ALIASES = {
    "gate": {"roadmap", "status", "todo", "experiment"},
    "measurement": {"benchmark", "metrics", "energy", "experience", "experiment"},
    "measure": {"benchmark", "metrics", "energy", "experience", "experiment"},
    "agent": {"workflow", "codex", "role", "skill"},
    "storage": {"bundle", "artifact", "rclone", "drive", "evidence"},
    "release": {"version", "tag", "roadmap", "status"},
    "sonatine": {"kernel", "riscv", "qemu", "rv64"},
}
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{2,}", re.IGNORECASE)


def terms_for(query: str) -> set[str]:
    terms = {token.lower() for token in TOKEN_RE.findall(query)}
    for term in tuple(terms):
        terms.update(ALIASES.get(term, set()))
    return terms


def candidates() -> list[Path]:
    roots = [ROOT / "raveil", ROOT / "tests", ROOT / "docs", ROOT / ".codex", ROOT / ".agents"]
    paths: list[Path] = []
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".md", ".toml", ".yaml", ".c", ".h"}:
                continue
            relative = path.relative_to(ROOT)
            if relative.parts[:2] in {("docs", "history"), ("docs", "archive")}:
                continue
            paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()
    terms = terms_for(args.query)
    ranked: list[tuple[int, str, list[str]]] = []
    for path in candidates():
        relative = path.relative_to(ROOT).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        hits: dict[int, set[str]] = defaultdict(set)
        lower_path = relative.lower()
        score = sum(5 for term in terms if term in lower_path)
        for number, line in enumerate(lines, start=1):
            lowered = line.lower()
            matched = {term for term in terms if term in lowered}
            if matched:
                hits[number].update(matched)
                score += len(matched)
                if line.startswith(("#", "class ", "def ")):
                    score += 2
        if score:
            snippets = []
            for number in sorted(hits, key=lambda item: (-len(hits[item]), item))[:3]:
                excerpt = lines[number - 1].strip()
                snippets.append(f"L{number}: {excerpt[:140]}")
            ranked.append((score, relative, snippets))

    print("required routing records:")
    for relative in ALWAYS:
        print(f"  {relative}")
    print("ranked task context:")
    for score, relative, snippets in sorted(ranked, key=lambda item: (-item[0], item[1]))[: args.limit]:
        print(f"  {score:3} {relative}")
        for snippet in snippets:
            print(f"      {snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
