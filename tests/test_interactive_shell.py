from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from raveil.interactive_shell import NativeInteractiveSession, dispatch, run_interactive_shell


ROOT = Path(__file__).resolve().parents[1]


class NativeInteractiveShellTests(unittest.TestCase):
    def test_order_errors_and_unknown_commands_are_explained(self) -> None:
        session = NativeInteractiveSession()
        for command, message in (("variants", "no graph"), ("propose", "invalid order"), ("execute", "invalid order"), ("result", "no result")):
            with self.assertRaisesRegex(ValueError, message):
                dispatch(session, command)
        with self.assertRaisesRegex(ValueError, "unknown command"):
            dispatch(session, "not-a-command")

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
            session = NativeInteractiveSession(source=ROOT / "benchmarks/native/benchmark.c")
            dispatch(session, "graph create gemm --m 8 --n 8 --k 8")
            dispatch(session, "variants")
            dispatch(session, "propose")
            self.assertIn("outcome=", dispatch(session, "execute")[1])
            with self.assertRaisesRegex(ValueError, "already executed"):
                dispatch(session, "execute")
            output = Path(directory) / "result.json"
            dispatch(session, f"result {output}")
            value = json.loads(output.read_text())
            self.assertEqual(value["schema"], "raveil.graph-mvp-result/v1")
            with self.assertRaises(FileExistsError):
                dispatch(session, f"result {output}")

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
