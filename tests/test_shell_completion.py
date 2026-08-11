from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from raveil.interactive_shell import NativeInteractiveSession
from raveil.shell_completion import configure_readline, completion_candidates
from raveil.workspace import NativeWorkspace


class FakeReadline:
    def __init__(self, line: str, begidx: int) -> None:
        self.line = line; self.begidx = begidx
        self.completer = None; self.delimiters = None; self.binding = None
        self.__doc__ = "GNU readline"

    def get_line_buffer(self) -> str: return self.line
    def get_begidx(self) -> int: return self.begidx
    def set_completer(self, value): self.completer = value
    def set_completer_delims(self, value: str) -> None: self.delimiters = value
    def parse_and_bind(self, value: str) -> None: self.binding = value


class NativeShellCompletionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "docs").mkdir()
        (self.root / "docs/note one.txt").write_text("hello")
        (self.root / ".hidden").write_text("visible")
        (self.root / "plain.txt").write_text("plain")
        (self.root / "link").symlink_to(self.root / "plain.txt")
        self.session = NativeInteractiveSession(workspace=NativeWorkspace(self.root))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_top_level_graph_options_and_allowlisted_tools(self) -> None:
        self.assertEqual(completion_candidates(self.session, "he", 0, "he"), ["help"])
        self.assertIn("compile", completion_candidates(self.session, "graph c", 6, "c"))
        self.assertEqual(completion_candidates(self.session, "graph create g", 13, "g"), ["gemm"])
        self.assertIn("--repetitions", completion_candidates(self.session, "graph benchmark --r", 16, "--r"))
        self.assertIn("cat", completion_candidates(self.session, "run c", 4, "c"))

    def test_virtual_path_completion_is_bounded_and_hides_symlinks(self) -> None:
        root = completion_candidates(self.session, "cat /", 4, "/")
        self.assertIn("/docs/", root)
        self.assertIn("/.hidden", root)
        self.assertNotIn("/link", root)
        self.assertNotIn(str(self.root), " ".join(root))
        self.assertEqual(completion_candidates(self.session, "cd /p", 3, "/p"), [])
        self.assertEqual(completion_candidates(self.session, "cat /p", 4, "/p"), ["/plain.txt"])
        self.assertEqual(completion_candidates(self.session, "cat /docs/n", 4, "/docs/n"), ["/docs/note\\ one.txt"])

    def test_readline_adapter_installs_and_iterates_candidates(self) -> None:
        fake = FakeReadline("gr", 0)
        completer = configure_readline(self.session, fake)
        self.assertIs(fake.completer, completer)
        self.assertEqual(fake.binding, "tab: complete")
        values = []
        state = 0
        while True:
            value = completer("gr", state)
            if value is None: break
            values.append(value); state += 1
        self.assertEqual(values, ["graph"])
        libedit = FakeReadline("gr", 0); libedit.__doc__ = "libedit readline wrapper"
        configure_readline(self.session, libedit)
        self.assertEqual(libedit.binding, "bind ^I rl_complete")

    def test_completion_never_changes_workspace(self) -> None:
        before = sorted(path.relative_to(self.root) for path in self.root.rglob("*") if not path.is_symlink())
        completion_candidates(self.session, "write /docs/", 6, "/docs/")
        completion_candidates(self.session, "run cat /docs/", 8, "/docs/")
        after = sorted(path.relative_to(self.root) for path in self.root.rglob("*") if not path.is_symlink())
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
