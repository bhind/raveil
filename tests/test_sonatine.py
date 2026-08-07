from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SONATINE = ROOT / "sonatine"


class SonatineSourceTests(unittest.TestCase):
    def test_boot_path_sources_are_present(self) -> None:
        required = {
            "src/start.S",
            "src/trap.S",
            "src/kernel.c",
            "src/console.c",
            "src/memory.c",
            "src/capability.c",
            "src/task.c",
            "src/ipc.c",
            "src/timer.c",
            "src/shell.c",
            "link.ld",
            "Makefile",
            "Dockerfile",
        }
        self.assertEqual([], sorted(str(path) for path in required if not (SONATINE / path).is_file()))

    def test_shell_exposes_each_minimum_subsystem(self) -> None:
        shell = (SONATINE / "src/shell.c").read_text(encoding="utf-8")
        for command in ("help", "info", "mem", "ps", "caps", "ticks", "ipc", "alloc"):
            self.assertIn(f'"{command}"', shell)
        kernel = (SONATINE / "src/kernel.c").read_text(encoding="utf-8")
        for subsystem in ("physical memory", "capability", "task", "IPC", "timer"):
            self.assertIn(subsystem, kernel)

    def test_capability_task_and_ipc_host_model(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("host C compiler is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "sonatine-host-test"
            command = [
                compiler,
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-Werror",
                f"-I{SONATINE / 'include'}",
                str(ROOT / "tests/sonatine_host_test.c"),
                str(SONATINE / "src/util.c"),
                str(SONATINE / "src/capability.c"),
                str(SONATINE / "src/task.c"),
                str(SONATINE / "src/ipc.c"),
                "-o",
                str(executable),
            ]
            subprocess.run(command, check=True)
            subprocess.run([str(executable)], check=True)

    def test_freestanding_c_sources_are_syntax_clean(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("host C compiler is unavailable")
        sources = sorted(str(path) for path in (SONATINE / "src").glob("*.c"))
        subprocess.run(
            [
                compiler,
                "-std=c11",
                "-ffreestanding",
                "-fsyntax-only",
                "-Wall",
                "-Wextra",
                "-Werror",
                f"-I{SONATINE / 'include'}",
                *sources,
            ],
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
