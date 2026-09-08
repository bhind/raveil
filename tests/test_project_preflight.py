from __future__ import annotations

import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from raveil.cli import main
from raveil.native_backend import NativeCBackend
from raveil.project import Project, init_project
from raveil.project_preflight import Probes, check
from raveil.sonatine_backend import SonatineQEMUBackend


def project_snapshot(root: Path) -> dict[str, tuple[int, bytes]]:
    snapshot: dict[str, tuple[int, bytes]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            metadata = path.stat()
            snapshot[path.relative_to(root).as_posix()] = (metadata.st_mtime_ns, path.read_bytes())
    return snapshot


class ProjectPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "work"
        init_project(self.root)
        self.project = Project(self.root)
        self.probes = Probes(lambda name: f"/tools/{name}", lambda path: True,
                             lambda path: True)

    @contextlib.contextmanager
    def no_execution(self):
        with patch.object(NativeCBackend, "compile", side_effect=AssertionError("must not compile")), \
                patch.object(SonatineQEMUBackend, "measure", side_effect=AssertionError("must not measure")), \
                patch("raveil.project_graph.run_snapshot", side_effect=AssertionError("must not simulate")), \
                patch("subprocess.run", side_effect=AssertionError("must not invoke")), \
                patch("subprocess.call", side_effect=AssertionError("must not invoke")):
            yield

    def test_native_command_admits_allowlist_and_never_executes(self) -> None:
        before = project_snapshot(self.root)
        with self.no_execution():
            status, report = check(self.project, "logs", "native", repository=Path("/repo"),
                                   kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=self.probes)
        self.assertEqual(status, 0)
        self.assertTrue(report.startswith(
            "RAVEIL-PROJECT-CHECK-V1 recipe=logs backend=native "
            "known_prerequisites=true execution_readiness=not-checked actions=0 runs_created=0"))
        self.assertIn("recipe: pass", report)
        self.assertIn("input: pass - declared regular inputs admitted: /events.txt; declared outputs absent: /errors.txt", report)
        self.assertIn("admission: pass", report)
        self.assertIn("tools: pass", report)
        self.assertIn("no workload, tool invocation, run, build, network, simulation, device or install action", report)
        self.assertEqual(before, project_snapshot(self.root))
        self.assertEqual(list((self.root / "runs").iterdir()), [])

    def test_default_command_tool_probe_reuses_fixed_registry_search(self) -> None:
        with patch("raveil.project_preflight.ToolRegistry._candidate",
                   side_effect=ValueError("unavailable")), \
                patch("raveil.project_preflight.shutil.which",
                      return_value="/untrusted/path/cat"):
            status, report = check(self.project, "logs", "native",
                                   repository=Path("/repo"), kernel=Path("/kernel"),
                                   compiler="cc", qemu="qemu")
        self.assertEqual(status, 2)
        self.assertIn("tools: fail - missing required command tool(s): cat, grep, wc", report)

    def test_failure_and_backend_mismatch_return_two_with_explicit_categories(self) -> None:
        status, report = check(self.project, "gemm", "rtl-sim", repository=Path("/repo"),
                               kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=self.probes)
        self.assertEqual(status, 2)
        for category in ("recipe:", "input:", "admission:", "tools:"):
            self.assertIn(category, report)
        self.assertIn("admission: fail", report)
        self.assertIn("tools: not-applicable", report)

    def test_graph_rtl_reports_daemon_and_image_not_checked(self) -> None:
        repo = Path(self.temporary.name) / "repo"
        runner = repo / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh"
        runner.parent.mkdir(parents=True)
        runner.write_text("#!/bin/sh\n")
        runner.chmod(0o700)
        (repo / "hardware/chisel/Dockerfile").write_text("FROM scratch\n")
        status, report = check(self.project, "bias-grid", "rtl-sim", repository=repo,
                               kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=self.probes)
        self.assertEqual(status, 0)
        self.assertIn("input: pass", report)
        self.assertIn("admission: pass", report)
        self.assertIn("Docker daemon/image: not-checked", report)

    def test_rtl_runner_must_be_an_executable_regular_file(self) -> None:
        repo = Path(self.temporary.name) / "non-executable-repo"
        runner = repo / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh"
        runner.parent.mkdir(parents=True)
        runner.write_text("#!/bin/sh\n")
        (repo / "hardware/chisel/Dockerfile").write_text("FROM scratch\n")
        probes = Probes(lambda name: f"/tools/{name}", lambda path: True,
                        lambda path: False)
        status, report = check(self.project, "bias-grid", "rtl-sim", repository=repo,
                               kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=probes)
        self.assertEqual(status, 2)
        self.assertIn("not an executable regular file", report)
        self.assertIn("known_prerequisites=false execution_readiness=not-checked", report)

    def test_cli_failure_does_not_create_run_or_call_processes(self) -> None:
        before = sorted((self.root / "runs").iterdir())
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("subprocess.run", side_effect=AssertionError("must not invoke")), \
                patch("subprocess.call", side_effect=AssertionError("must not invoke")), \
                contextlib.redirect_stdout(stdout), patch("sys.stderr", stderr):
            status = main(["project", "check", "gemm", "--backend", "sonatine-qemu", "--project", str(self.root),
                           "--qemu", "definitely-missing-qemu", "--sonatine-kernel", str(self.root / "missing.elf")])
        self.assertEqual(status, 2)
        self.assertIn("tools: fail", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(before, sorted((self.root / "runs").iterdir()))

    def test_command_compile_failure_makes_no_input_success_claim(self) -> None:
        (self.root / "recipes/logs.json").write_text(
            '{"schema":"raveil.project-recipe/v1","kind":"command","source":"bad-tool"}\n'
        )
        status, report = check(self.project, "logs", "native", repository=Path("/repo"),
                               kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=self.probes)
        self.assertEqual(status, 2)
        self.assertIn("input: not-applicable", report)
        self.assertIn("admission: fail", report)
        self.assertNotIn("input: pass", report)

    def test_command_missing_input_fails_without_execution(self) -> None:
        (self.root / "inputs/events.txt").unlink()
        with self.no_execution():
            status, report = check(self.project, "logs", "native", repository=Path("/repo"),
                                   kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=self.probes)
        self.assertEqual(status, 2)
        self.assertIn("input: fail", report)
        self.assertIn("admission: not-applicable", report)
        self.assertNotIn("input: pass", report)

    def test_native_compiler_absence_is_a_required_failure(self) -> None:
        probes = Probes(lambda name: None if name == "cc" else f"/tools/{name}",
                        lambda path: True, lambda path: True)
        status, report = check(self.project, "gemm", "native", repository=Path("/repo"),
                               kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=probes)
        self.assertEqual(status, 2)
        self.assertIn("tools: fail - missing C compiler: cc", report)

    def test_sonatine_qemu_and_kernel_are_independently_required(self) -> None:
        absent_qemu = Probes(lambda name: None if name == "qemu" else f"/tools/{name}",
                             lambda path: True, lambda path: True)
        status, report = check(self.project, "gemm", "sonatine-qemu", repository=Path("/repo"),
                               kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=absent_qemu)
        self.assertEqual(status, 2)
        self.assertIn("QEMU: qemu", report)
        absent_kernel = Probes(lambda name: f"/tools/{name}",
                               lambda path: path != Path("/kernel"), lambda path: True)
        status, report = check(self.project, "gemm", "sonatine-qemu", repository=Path("/repo"),
                               kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=absent_kernel)
        self.assertEqual(status, 2)
        self.assertIn("Sonatine kernel: /kernel", report)

    def test_valid_gemm_sonatine_fixture_is_ready_without_execution(self) -> None:
        with self.no_execution():
            status, report = check(self.project, "gemm", "sonatine-qemu", repository=Path("/repo"),
                                   kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=self.probes)
        self.assertEqual(status, 0)
        self.assertIn("known_prerequisites=true execution_readiness=not-checked", report)
        self.assertIn("tools: pass - QEMU and Sonatine kernel present; neither invoked", report)

    def test_graph_descriptor_and_explicit_input_fail_without_execution(self) -> None:
        (self.root / "inputs/bias-grid.json").write_text("{")
        with self.no_execution():
            status, report = check(self.project, "bias-grid", "rtl-sim", repository=Path("/repo"),
                                   kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=self.probes)
        self.assertEqual(status, 2)
        self.assertIn("input: fail", report)
        self.assertIn("admission: not-applicable", report)
        self.assertIn("tools: pass", report)

        other_root = self.root.parent / "other"
        init_project(other_root)
        other = Project(other_root)
        (other_root / "inputs/bias-grid-data.json").write_text('{"schema":"raveil.graph-input/v1","words":[]}\n')
        with self.no_execution():
            status, report = check(other, "bias-grid", "rtl-sim", repository=Path("/repo"),
                                   kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=self.probes)
        self.assertEqual(status, 2)
        self.assertIn("input: fail", report)
        self.assertIn("admission: pass", report)

    def test_docker_cli_absence_is_required_and_daemon_image_are_not_checked(self) -> None:
        repo = self.root.parent / "repo"
        runner = repo / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh"
        runner.parent.mkdir(parents=True)
        runner.write_text("#!/bin/sh\n")
        runner.chmod(0o700)
        (repo / "hardware/chisel/Dockerfile").write_text("FROM scratch\n")
        probes = Probes(lambda name: None if name == "docker" else f"/tools/{name}",
                        lambda path: True, lambda path: True)
        status, report = check(self.project, "bias-grid", "rtl-sim", repository=repo,
                               kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=probes)
        self.assertEqual(status, 2)
        self.assertIn("tools: fail - missing docker CLI; Docker daemon/image: not-checked", report)

    def test_direct_unsupported_backend_has_all_categories_and_fails(self) -> None:
        status, report = check(self.project, "gemm", "other", repository=Path("/repo"),
                               kernel=Path("/kernel"), compiler="cc", qemu="qemu", probes=self.probes)
        self.assertEqual(status, 2)
        self.assertIn("known_prerequisites=false execution_readiness=not-checked", report)
        for category in ("recipe:", "input:", "admission:", "tools:"):
            self.assertIn(category, report)
        self.assertIn("admission: fail - unsupported backend", report)

    def test_cli_checks_leave_every_project_file_and_run_unchanged(self) -> None:
        before = project_snapshot(self.root)
        stdout, stderr = io.StringIO(), io.StringIO()
        with self.no_execution(), contextlib.redirect_stdout(stdout), patch("sys.stderr", stderr):
            self.assertEqual(main(["project", "check", "logs", "--backend", "native", "--project", str(self.root)]), 0)
            self.assertEqual(main(["project", "check", "bias-grid", "--backend", "rtl-sim", "--project", str(self.root)]), 0)
            self.assertEqual(main(["project", "check", "gemm", "--backend", "sonatine-qemu", "--project", str(self.root),
                                   "--qemu", "definitely-missing-qemu", "--sonatine-kernel", str(self.root / "missing.elf")]), 2)
        self.assertIn("RAVEIL-PROJECT-CHECK-V1", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(before, project_snapshot(self.root))
        self.assertEqual(list((self.root / "runs").iterdir()), [])
