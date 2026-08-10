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
            ".dockerignore",
        }
        self.assertEqual([], sorted(str(path) for path in required if not (SONATINE / path).is_file()))

        dockerignore = (SONATINE / ".dockerignore").read_text(encoding="utf-8")
        self.assertIn("build/", dockerignore.splitlines())
        dockerfile = (SONATINE / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("RUN make clean && make", dockerfile)

        local_ci = (ROOT / "scripts/ci-local.sh").read_text(encoding="utf-8")
        self.assertIn("python3 -m unittest discover -s tests -v", local_ci)
        self.assertIn("make -C sonatine smoke", local_ci)
        self.assertFalse((ROOT / ".github/workflows/ci.yml").exists())

    def test_shell_exposes_each_minimum_subsystem(self) -> None:
        shell = (SONATINE / "src/shell.c").read_text(encoding="utf-8")
        for command in ("help", "info", "mem", "ps", "caps", "ticks", "ipc", "alloc"):
            self.assertIn(f'"{command}"', shell)
        kernel = (SONATINE / "src/kernel.c").read_text(encoding="utf-8")
        for subsystem in ("physical memory", "capability", "task", "IPC", "timer"):
            self.assertIn(subsystem, kernel)

    def test_makefile_has_isolated_debug_build(self) -> None:
        makefile = (SONATINE / "Makefile").read_text(encoding="utf-8")
        for expected in (
            "DEBUG ?= 0",
            "BUILD := $(BUILD_ROOT)/debug",
            "COPT := -Og -g3",
            "ASDEBUG := -g3",
            "$(MAKE) DEBUG=1 debug-server",
            "$(MAKE) DEBUG=1 gdb-client",
            "-ex 'break kmain'",
            "$(READELF) -S $(BUILD_ROOT)/debug/sonatine.elf",
            "command -v $(GDB)",
        ):
            self.assertIn(expected, makefile)

    def test_qemu_platform_contract_is_explicit_and_shared(self) -> None:
        makefile = (SONATINE / "Makefile").read_text(encoding="utf-8")
        platform = (SONATINE / "include/platform.h").read_text(encoding="utf-8")
        linker = (SONATINE / "link.ld").read_text(encoding="utf-8")
        for expected in (
            "QEMU_MACHINE := virt",
            "QEMU_CPU := rv64",
            "QEMU_MEMORY := 128M",
            "QEMU_HARTS := 1",
            "QEMU_PLATFORM_ARGS :=",
        ):
            self.assertIn(expected, makefile)
        self.assertEqual(3, makefile.count("$(QEMU) $(QEMU_PLATFORM_ARGS)"))
        self.assertIn('SONATINE_PLATFORM_NAME "qemu-virt-rv64-v1"', platform)
        self.assertIn("SONATINE_HART_COUNT 1u", platform)
        self.assertIn("QEMU_RAM_BASE 0x80000000UL", platform)
        self.assertIn("QEMU_RAM_SIZE (128UL * 1024UL * 1024UL)", platform)
        self.assertIn("ORIGIN = 0x80000000, LENGTH = 128M", linker)

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

    def test_sv39_mapping_host_model(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("host C compiler is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "sonatine-vm-host-test"
            subprocess.run([
                compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                f"-I{SONATINE / 'include'}",
                str(ROOT / "tests/sonatine_vm_host_test.c"),
                str(SONATINE / "src/vm.c"), "-o", str(executable),
            ], check=True)
            subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    unittest.main()
