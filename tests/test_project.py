from __future__ import annotations

import json
import contextlib
import io
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from raveil.cli import main
from raveil.workspace import NativeWorkspace, WorkspaceError, MAX_FILE_BYTES, MAX_TEXT_READ_BYTES
from raveil.project import (
    CONFIG,
    Project,
    RECIPE_SCHEMA,
    digest,
    encoded,
    init_project,
)

ROOT = Path(__file__).resolve().parents[1]


class ProjectWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "work"
        init_project(self.root)

    def test_init_creates_editable_samples_and_empty_history(self) -> None:
        self.assertEqual(json.loads((self.root / "project.json").read_text()), CONFIG)
        self.assertEqual(
            sorted(path.name for path in (self.root / "recipes").iterdir()),
            ["files.json", "gemm.json", "logs.json", "neighborhood-data.json", "neighborhood.json"],
        )
        self.assertEqual(Project(self.root).runs(), "No runs yet. Try: project run logs")
        self.assertIn("Try adding an ERROR line", (self.root / "README.md").read_text())

    def test_successful_large_metadata_remains_readable_and_diffable(self) -> None:
        for index in range(230):
            (self.root / "inputs" / f"extra-{index:03d}.txt").write_text("small\n")
        project = Project(self.root)
        first = project.run("logs", "native", kernel=Path("missing"), qemu="missing", compiler="cc")
        self.assertEqual(first["status"], "succeeded")
        path = self.root / "runs" / first["run_id"] / "record.json"
        self.assertGreater(path.stat().st_size, MAX_FILE_BYTES)
        self.assertEqual(project.load_run(first["run_id"]), first)
        (self.root / "inputs" / "extra-000.txt").write_text("changed\n")
        second = project.run("logs", "native", kernel=Path("missing"), qemu="missing", compiler="cc")
        self.assertEqual(second["status"], "succeeded")
        self.assertNotIn("incomplete-or-invalid", project.runs())
        self.assertIn("/extra-000.txt", project.diff(first["run_id"], second["run_id"]))
        with self.assertRaisesRegex(WorkspaceError, "exceeds 65536"):
            NativeWorkspace(path.parent).read_text("record.json")
        path.write_text(path.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            project.load_run(first["run_id"])

    def test_duplicate_input_budget_rejected_before_execution_or_history(self) -> None:
        from raveil.project import tree
        manifest = tree(self.root / "inputs")
        size = sum((self.root / "inputs" / path.lstrip("/")).stat().st_size
                   for path, value in manifest.items() if value != "directory")
        for field, limit in (("MAX_BYTES", 2 * size - 1),
                             ("MAX_ENTRIES", 2 * len(manifest) - 1)):
            with self.subTest(field=field), patch("raveil.project." + field, limit), \
                    patch("raveil.project.CommandComparison.execute",
                          side_effect=AssertionError("execution started before budget rejection")) as execute:
                error = io.StringIO()
                with contextlib.redirect_stderr(error):
                    result = main(["project", "run", "logs", "--project", str(self.root)])
                self.assertEqual(result, 2)
                self.assertIn("duplicated inputs exceed run", error.getvalue())
                self.assertNotIn("Traceback", error.getvalue())
                execute.assert_not_called()
                self.assertEqual(list((self.root / "runs").iterdir()), [])

    def test_explicit_text_read_bound_preserves_validation(self) -> None:
        workspace = NativeWorkspace(self.root)
        target = self.root / "bounded.txt"
        target.write_text("abcd")
        self.assertEqual(workspace.read_text("bounded.txt", maximum=4), "abcd")
        with self.assertRaisesRegex(WorkspaceError, "exceeds 3"):
            workspace.read_text("bounded.txt", maximum=3)
        for maximum in (0, -1, True, "4", MAX_TEXT_READ_BYTES + 1):
            with self.subTest(maximum=maximum), self.assertRaises(WorkspaceError):
                workspace.read_text("bounded.txt", maximum=maximum)
        (self.root / "link.txt").symlink_to(target)
        with self.assertRaisesRegex(WorkspaceError, "symlinks"):
            workspace.read_text("link.txt", maximum=4)

    def test_run_metadata_above_project_bound_is_rejected_before_read(self) -> None:
        from raveil.project import MAX_BYTES
        self.assertEqual(MAX_BYTES, MAX_TEXT_READ_BYTES)
        directory = self.root / "runs" / "oversized"
        directory.mkdir()
        with (directory / "record.json").open("wb") as stream:
            stream.truncate(MAX_BYTES + 1)
        project = Project(self.root)
        with patch("raveil.workspace.os.read", side_effect=AssertionError("oversized read")):
            with self.assertRaisesRegex(WorkspaceError, f"exceeds {MAX_BYTES}"):
                project.load_run("oversized")

    def test_malformed_saved_metadata_fails_cleanly_even_with_matching_checksum(self) -> None:
        project = Project(self.root)
        valid = project.run("logs", "native", kernel=Path("missing"), qemu="missing", compiler="cc")
        run_id = valid["run_id"]
        directory = self.root / "runs" / run_id
        cases = [("backend", None), ("status", []), ("recipe_name", None),
                 ("evidence_class", {}), ("recipe", []), ("inputs", []),
                 ("outputs", []), ("artifacts", []), ("implementation", []),
                 ("inputs", {"/file": 3}), ("outputs", {"/file": []}),
                 ("backend", "unknown"), ("status", "unknown"), ("backend", "rtl-sim")]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                record = dict(valid)
                if value is None:
                    del record[key]
                else:
                    record[key] = value
                payload = encoded(record)
                (directory / "record.json").write_bytes(payload)
                (directory / "record.sha256").write_text(digest(payload) + "\n")
                with self.assertRaisesRegex(ValueError, "invalid run record"):
                    project.load_run(run_id)
                self.assertIn("incomplete-or-invalid", project.runs())
                errors = io.StringIO()
                with contextlib.redirect_stderr(errors), contextlib.redirect_stdout(io.StringIO()):
                    status = main(["project", "diff", run_id, run_id, "--project", str(self.root)])
                self.assertEqual(status, 2)
                self.assertNotIn("Traceback", errors.getvalue())
        (directory / "record.json").write_bytes(encoded(valid))
        (directory / "record.sha256").write_text(digest(encoded(valid)) + "\n")
        self.assertEqual(project.load_run(run_id), valid)
        for missing in ("simulator_sha256", "rtl_manifest_sha256", "program_sha256"):
            record = dict(valid, backend="rtl-sim", recipe={"descriptor": "x.json"},
                          implementation={key: "a" * 64 for key in
                              ("simulator_sha256", "rtl_manifest_sha256", "program_sha256")})
            del record["implementation"][missing]
            payload = encoded(record)
            (directory / "record.json").write_bytes(payload)
            (directory / "record.sha256").write_text(digest(payload) + "\n")
            with self.assertRaisesRegex(ValueError, missing):
                project.load_run(run_id)

    def test_project_and_run_artifacts_are_private_even_with_umask_022(self) -> None:
        private_root = Path(self.temporary.name) / "private"
        previous = os.umask(0o022)
        try:
            init_project(private_root)
            result = Project(private_root).run(
                "logs", "native", kernel=Path("missing"), qemu="missing", compiler="cc"
            )
        finally:
            os.umask(previous)
        run = private_root / "runs" / result["run_id"]
        for directory in (private_root, private_root / "recipes", private_root / "inputs", private_root / "runs", run):
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        for file in (run / "recipe.json", run / "graph.json", run / "stdout.txt", run / "record.json", run / "record.sha256"):
            self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)

    def test_init_never_uses_path_following_chmod(self) -> None:
        target = Path(self.temporary.name) / "nofollow"
        with patch.object(Path, "chmod", side_effect=AssertionError("path chmod followed")):
            init_project(target)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o700)

    def test_rejected_nonempty_init_preserves_mode_and_content(self) -> None:
        target = Path(self.temporary.name) / "existing"
        target.mkdir(mode=0o755)
        marker = target / "keep.txt"
        marker.write_text("keep\n", encoding="utf-8")
        before_mode = stat.S_IMODE(target.stat().st_mode)

        with self.assertRaisesRegex(ValueError, "new or empty directory"):
            init_project(target)

        self.assertEqual(stat.S_IMODE(target.stat().st_mode), before_mode)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")
        self.assertEqual([path.name for path in target.iterdir()], ["keep.txt"])

    def test_show_exposes_command_nodes_dependencies_inputs_and_outputs(self) -> None:
        rendered = Project(self.root).show("logs")
        self.assertIn("nodes=3 edges=2", rendered)
        self.assertIn("node-001-cat: cat /events.txt <- (input)", rendered)
        self.assertIn("node-002-grep: grep ERROR <- node-001-cat", rendered)
        self.assertIn("inputs: /events.txt", rendered)
        self.assertIn("outputs: /errors.txt", rendered)

    def test_show_exposes_gemm_identity_and_backend_boundary(self) -> None:
        rendered = Project(self.root).show("gemm")
        self.assertIn("GEMM 8x8x8", rendered)
        self.assertIn("nodes=1 edges=2", rendered)
        self.assertIn("node-001-gemm: GEMM A[8x8] B[8x8] -> C[8x8]", rendered)
        self.assertIn("program_sha256=", rendered)
        self.assertIn("backends: native; sonatine-qemu", rendered)

    def test_edit_run_edit_rerun_and_diff_preserve_each_input_and_output(self) -> None:
        project = Project(self.root)
        first = project.run("logs", "native", kernel=Path("missing"), qemu="missing", compiler="cc")
        self.assertEqual(first["status"], "succeeded")
        first_path = self.root / "runs" / first["run_id"]
        self.assertEqual((first_path / "inputs/events.txt").read_text(), "INFO start\nERROR failed\nERROR retry\n")
        self.assertEqual((first_path / "workspace/errors.txt").read_text().strip(), "2")

        with (self.root / "inputs/events.txt").open("a", encoding="utf-8") as stream:
            stream.write("ERROR changed\n")
        second = project.run("logs", "native", kernel=Path("missing"), qemu="missing", compiler="cc")
        second_path = self.root / "runs" / second["run_id"]
        self.assertEqual(second["status"], "succeeded")
        self.assertEqual((second_path / "workspace/errors.txt").read_text().strip(), "3")
        self.assertEqual((first_path / "workspace/errors.txt").read_text().strip(), "2")

        rendered = project.diff(first["run_id"], second["run_id"])
        self.assertIn("inputs changed:", rendered)
        self.assertIn("/events.txt", rendered)
        self.assertIn("outputs changed:", rendered)
        self.assertIn("/errors.txt", rendered)
        self.assertIn('text: "2\\n" -> "3\\n"', rendered)
        self.assertIn("Timing is not compared across backends.", rendered)

    def test_run_copies_the_exact_recipe_version(self) -> None:
        recipe_path = self.root / "recipes/logs.json"
        first = Project(self.root).run("logs", "native", kernel=Path("missing"), qemu="missing", compiler="cc")
        recipe = json.loads(recipe_path.read_text())
        recipe["source"] = "cat /events.txt | wc -l > /errors.txt"
        recipe_path.write_text(json.dumps(recipe), encoding="utf-8")
        second = Project(self.root).run("logs", "native", kernel=Path("missing"), qemu="missing", compiler="cc")
        self.assertNotEqual(first["recipe_sha256"], second["recipe_sha256"])
        self.assertEqual(
            json.loads((self.root / "runs" / first["run_id"] / "recipe.json").read_text())["source"],
            "cat /events.txt | grep ERROR | wc -l > /errors.txt",
        )

    def test_changed_history_fails_integrity_check(self) -> None:
        project = Project(self.root)
        result = project.run("logs", "native", kernel=Path("missing"), qemu="missing", compiler="cc")
        saved = self.root / "runs" / result["run_id"] / "workspace/errors.txt"
        saved.write_text("forged\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "saved artifacts changed"):
            project.load_run(result["run_id"])
        self.assertIn("incomplete-or-invalid", project.runs())

    def test_command_recipe_rejects_arbitrary_shell_syntax(self) -> None:
        path = self.root / "recipes/unsafe.json"
        path.write_text(json.dumps({
            "schema": RECIPE_SCHEMA,
            "kind": "command",
            "source": "python3 -c 'print(1)'",
        }), encoding="utf-8")
        with self.assertRaises(ValueError):
            Project(self.root).show("unsafe")

    def test_sonatine_backend_rejects_command_recipe_before_qemu(self) -> None:
        with self.assertRaisesRegex(ValueError, "only GEMM"):
            Project(self.root).run(
                "logs", "sonatine-qemu", kernel=Path("missing"), qemu="missing", compiler="missing"
            )

    def test_cli_connects_project_commands(self) -> None:
        with patch("builtins.print") as output:
            self.assertEqual(main(["project", "show", "logs", "--project", str(self.root)]), 0)
        self.assertIn("nodes=3 edges=2", output.call_args.args[0])

        with patch("builtins.print") as output:
            self.assertEqual(main(["project", "run", "logs", "--project", str(self.root)]), 0)
        rendered = "\n".join(str(call.args[0]) for call in output.call_args_list)
        self.assertIn("Graph output matched direct reference; outputs committed", rendered)
        self.assertIn('text: "2\\n"', rendered)

    def test_raveil_launcher_works_from_inside_the_project(self) -> None:
        environment = dict(os.environ)
        environment["PATH"] = f"{ROOT / 'scripts'}:{environment['PATH']}"
        completed = subprocess.run(
            ["raveil", "project", "show", "logs"],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("nodes=3 edges=2", completed.stdout)

    def test_init_next_hint_executes_for_shell_metacharacters_in_path(self) -> None:
        target = Path(self.temporary.name) / "work space; false"
        with patch("builtins.print") as output:
            self.assertEqual(main(["project", "init", str(target)]), 0)
        hint = next(
            call.args[0].removeprefix("Next: ")
            for call in output.call_args_list
            if call.args[0].startswith("Next: ")
        )
        environment = dict(os.environ)
        environment["PATH"] = f"{ROOT / 'scripts'}:{environment['PATH']}"
        completed = subprocess.run(
            ["/bin/sh", "-c", hint],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("nodes=3 edges=2", completed.stdout)

    def test_init_setup_hint_preserves_literal_checkout_and_existing_path(self) -> None:
        for index, name in enumerate(("plain", "work space", "$RAVEIL_HINT_TEST", "quote'and\"double", "`printf expanded`", "$(printf expanded)")):
            with self.subTest(name=name):
                checkout = Path(self.temporary.name) / name
                target = Path(self.temporary.name) / f"setup-{index}"
                with patch("raveil.project.REPOSITORY", checkout), patch("builtins.print") as output:
                    self.assertEqual(main(["project", "init", str(target)]), 0)
                hint = next(
                    call.args[0].removeprefix("One-time shell setup: ")
                    for call in output.call_args_list
                    if call.args[0].startswith("One-time shell setup: ")
                )
                suffix = "/usr/bin:/bin:/literal path/$unexpanded"
                completed = subprocess.run(
                    ["/bin/sh", "-c", hint + '\nprintf "%s" "$PATH"'],
                    env={"PATH": suffix, "RAVEIL_HINT_TEST": "expanded"},
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(completed.stdout, f"{checkout / 'scripts'}:{suffix}")

    def test_console_uses_the_existing_sonatine_kernel_without_shell(self) -> None:
        kernel = Path(self.temporary.name) / "sonatine.elf"
        kernel.write_bytes(b"elf")
        with patch("raveil.project._executable", return_value="/usr/bin/qemu-system-riscv64"), patch(
            "raveil.project.subprocess.call", return_value=0
        ) as call:
            self.assertEqual(main([
                "project", "console", "sonatine", "--sonatine-kernel", str(kernel)
            ]), 0)
        command = call.call_args.args[0]
        self.assertEqual(command[0], "/usr/bin/qemu-system-riscv64")
        self.assertIn("-nographic", command)
        self.assertEqual(command[-1], str(kernel.resolve()))


if __name__ == "__main__":
    unittest.main()
