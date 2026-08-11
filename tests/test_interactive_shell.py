from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from raveil.interactive_shell import NativeInteractiveSession, dispatch, run_interactive_shell
from raveil.workspace import MAX_DIRECTORY_ENTRIES, MAX_FILE_BYTES, NativeWorkspace, WorkspaceError


ROOT = Path(__file__).resolve().parents[1]


class NativeInteractiveShellTests(unittest.TestCase):
    @staticmethod
    def session(root: Path) -> NativeInteractiveSession:
        return NativeInteractiveSession(
            source=ROOT / "benchmarks/native/benchmark.c",
            workspace=NativeWorkspace(root),
        )

    def test_order_errors_and_unknown_commands_are_explained(self) -> None:
        session = NativeInteractiveSession()
        for command, message in (("variants", "no graph"), ("propose", "invalid order"), ("execute", "invalid order"), ("result", "no result")):
            with self.assertRaisesRegex(ValueError, message):
                dispatch(session, command)
        with self.assertRaisesRegex(ValueError, "unknown command"):
            dispatch(session, "not-a-command")

    def test_help_is_vertical_and_describes_every_command(self) -> None:
        help_text = dispatch(NativeInteractiveSession(), "help")[1]
        self.assertTrue(help_text.startswith("Available commands:\n"))
        self.assertGreaterEqual(help_text.count("\n"), 20)
        for command in (
            "help", "pwd", "cd [PATH]", "ls [PATH]", "cat PATH", "stat PATH",
            "mkdir PATH", "write PATH TEXT...", "graph create gemm", "graph show", "variants", "propose",
            "execute", "result [PATH]", "history", "reset", "exit",
        ):
            self.assertIn(command, help_text)
        self.assertIn("trusted baseline first", help_text)
        self.assertIn("exclusively save", help_text)

    def test_state_machine_create_show_variants_propose_reset(self) -> None:
        session = NativeInteractiveSession()
        dispatch(session, "graph create gemm --m 8 --n 8 --k 8")
        shown = json.loads(dispatch(session, "graph show")[1])
        self.assertEqual(shown["program_id"], "gemm-8x8x8")
        self.assertTrue(dispatch(session, "variants")[1].startswith("baseline-ijk"))
        proposal = json.loads(dispatch(session, "propose")[1])
        self.assertEqual(proposal["schema"], "raveil.optimization-proposal/v1")
        self.assertIn("graph-created", dispatch(session, "history")[1])
        dispatch(session, "reset")
        self.assertIsNone(session.graph)

    def test_real_native_backend_e2e_and_exclusive_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = self.session(root)
            dispatch(session, "mkdir /output")
            dispatch(session, "graph create gemm --m 8 --n 8 --k 8")
            dispatch(session, "variants")
            dispatch(session, "propose")
            self.assertIn("outcome=", dispatch(session, "execute")[1])
            with self.assertRaisesRegex(ValueError, "already executed"):
                dispatch(session, "execute")
            with self.assertRaisesRegex(WorkspaceError, "parent traversal"):
                dispatch(session, "result ../outside.json")
            output = root / "output/result.json"
            dispatch(session, "result /output/result.json")
            value = json.loads(output.read_text())
            self.assertEqual(value["schema"], "raveil.graph-mvp-result/v1")
            with self.assertRaisesRegex(WorkspaceError, "already exists"):
                dispatch(session, "result /output/result.json")

    def test_workspace_commands_and_virtual_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = self.session(root)
            self.assertEqual(dispatch(session, "pwd")[1], "/")
            dispatch(session, "mkdir docs")
            dispatch(session, "write /docs/note.txt hello world")
            dispatch(session, "write /.hidden visible")
            self.assertEqual(dispatch(session, "ls /")[1].splitlines(), [".hidden", "docs"])
            self.assertEqual(dispatch(session, "cd /docs")[1], "/docs")
            self.assertEqual(dispatch(session, "cat note.txt")[1], "hello world")
            metadata = dispatch(session, "stat /docs/note.txt")[1]
            self.assertIn("path: /docs/note.txt", metadata)
            self.assertIn("type: file", metadata)
            self.assertNotIn(str(root), metadata)
            self.assertEqual(dispatch(session, "cd")[1], "/")
            self.assertEqual((root / "docs/note.txt").read_text(), "hello world")

    def test_workspace_rejects_escape_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            outside_path = Path(outside)
            (outside_path / "secret").write_text("host secret")
            (root / "file-link").symlink_to(outside_path / "secret")
            (root / "dir-link").symlink_to(outside_path, target_is_directory=True)
            (root / "broken").symlink_to(root / "missing")
            session = self.session(root)
            for command in (
                "cat ../secret", "cat /../secret", "cat /file-link",
                "cat /dir-link/secret", "cat /broken", "write /dir-link/new data",
            ):
                with self.assertRaises(WorkspaceError, msg=command):
                    dispatch(session, command)
            # A host absolute path is interpreted below the virtual root.
            with self.assertRaisesRegex(WorkspaceError, "does not exist"):
                dispatch(session, f"cat {outside_path}/secret")

    def test_workspace_rejects_special_and_oversized_objects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = self.session(root)
            (root / "large.txt").write_bytes(b"x" * (MAX_FILE_BYTES + 1))
            (root / "binary").write_bytes(b"\xff")
            with self.assertRaisesRegex(WorkspaceError, "exceeds"):
                dispatch(session, "cat /large.txt")
            with self.assertRaisesRegex(WorkspaceError, "UTF-8"):
                dispatch(session, "cat /binary")
            with self.assertRaisesRegex(WorkspaceError, "exceeds"):
                session.workspace.write_text("/too-large", "x" * (MAX_FILE_BYTES + 1))
            if hasattr(os, "mkfifo"):
                os.mkfifo(root / "pipe")
                with self.assertRaisesRegex(WorkspaceError, "regular files"):
                    dispatch(session, "cat /pipe")

    def test_workspace_rejects_large_listing_and_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            crowded = root / "crowded"
            crowded.mkdir()
            for index in range(MAX_DIRECTORY_ENTRIES + 1):
                (crowded / f"{index:04d}").touch()
            session = self.session(root)
            with self.assertRaisesRegex(WorkspaceError, "exceeds"):
                dispatch(session, "ls /crowded")
            dispatch(session, "write /once data")
            with self.assertRaisesRegex(WorkspaceError, "already exists"):
                dispatch(session, "write /once replacement")

    def test_workspace_requires_real_directory_and_detects_root_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            missing = parent / "missing"
            with self.assertRaisesRegex(WorkspaceError, "unavailable"):
                NativeWorkspace(missing)
            regular = parent / "file"
            regular.write_text("x")
            with self.assertRaisesRegex(WorkspaceError, "directory"):
                NativeWorkspace(regular)
            root = parent / "root"
            root.mkdir()
            workspace = NativeWorkspace(root)
            moved = parent / "moved"
            root.rename(moved)
            root.mkdir()
            with self.assertRaisesRegex(WorkspaceError, "replaced"):
                workspace.pwd()

    def test_workspace_rejects_oversized_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = self.session(Path(directory))
            with self.assertRaisesRegex(WorkspaceError, "path exceeds"):
                dispatch(session, "cat /" + "x" * 4097)

    def test_root_agent_names_is_not_tracked_or_reintroduced(self) -> None:
        self.assertFalse((ROOT / "AgentNames.md").exists())
        self.assertIn("AgentNames.md", (ROOT / ".gitignore").read_text().splitlines())

    def test_loop_handles_errors_without_traceback(self) -> None:
        commands = iter(("execute", "help", "exit"))
        output: list[str] = []
        code = run_interactive_shell(
            NativeInteractiveSession(), input_fn=lambda _: next(commands), output_fn=output.append
        )
        self.assertEqual(code, 0)
        self.assertTrue(any(item.startswith("error: invalid order") for item in output))
        self.assertEqual(output[-1], "bye")


if __name__ == "__main__":
    unittest.main()
