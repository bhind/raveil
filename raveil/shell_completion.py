"""Readline adapter for deterministic Native CLI completion."""

from __future__ import annotations

import shlex
from typing import Any

from .command_graph import ALLOWLIST
from .interactive_shell import NativeInteractiveSession


TOP_LEVEL = (
    "help", "pwd", "cd", "ls", "cat", "stat", "mkdir", "write", "run",
    "graph", "variants", "propose", "execute", "result", "history", "reset", "exit",
)
GRAPH = ("compile", "execute", "benchmark", "result", "create", "show")


def _words(text: str) -> list[str]:
    try:
        return shlex.split(text)
    except ValueError:
        return text.strip().split()


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(" ", "\\ ")


def completion_candidates(session: NativeInteractiveSession, line: str, begidx: int, text: str) -> list[str]:
    before = _words(line[:begidx])
    if not before:
        return [item for item in TOP_LEVEL if item.startswith(text)]
    if before == ["graph"]:
        return [item for item in GRAPH if item.startswith(text)]
    if before == ["graph", "create"]:
        return ["gemm"] if "gemm".startswith(text) else []
    if before[:3] == ["graph", "create", "gemm"]:
        used = set(before)
        return [item for item in ("--m", "--n", "--k") if item not in used and item.startswith(text)]
    if before[:2] == ["graph", "benchmark"]:
        used = set(before)
        return [item for item in ("--warmups", "--repetitions") if item not in used and item.startswith(text)]
    if before[:2] in (["graph", "execute"],):
        return ["--compare"] if "--compare".startswith(text) else []
    path_command = before[0] in {"cd", "ls", "cat", "stat", "mkdir", "write", "result"} and len(before) == 1
    graph_result = before[:2] == ["graph", "result"] and len(before) == 2
    if path_command or graph_result:
        directories_only = before[0] == "cd"
        return [_escape(item) for item in session.workspace.complete_paths(text, directories_only=directories_only)]
    command_source = before[0] == "run" or before[:2] == ["graph", "compile"]
    if command_source:
        previous = before[-1] if before else ""
        if not before or previous in {"|", "&&", ";", "|||"} or (before[0] == "run" and len(before) == 1) or (before[:2] == ["graph", "compile"] and len(before) == 2):
            return [item for item in sorted(ALLOWLIST) if item.startswith(text)]
        if text.startswith(("/", ".")):
            return [_escape(item) for item in session.workspace.complete_paths(text)]
    return []


class NativeShellCompleter:
    def __init__(self, session: NativeInteractiveSession, readline_module: Any) -> None:
        self.session = session
        self.readline = readline_module
        self._matches: list[str] = []

    def __call__(self, text: str, state: int) -> str | None:
        if state == 0:
            self._matches = completion_candidates(
                self.session, self.readline.get_line_buffer(), self.readline.get_begidx(), text
            )
        return self._matches[state] if state < len(self._matches) else None


def configure_readline(session: NativeInteractiveSession, readline_module: Any) -> NativeShellCompleter:
    completer = NativeShellCompleter(session, readline_module)
    readline_module.set_completer_delims(" \t\n|<>&;")
    readline_module.set_completer(completer)
    if "libedit" in str(getattr(readline_module, "__doc__", "")).lower():
        readline_module.parse_and_bind("bind ^I rl_complete")
    else:
        readline_module.parse_and_bind("tab: complete")
    return completer
