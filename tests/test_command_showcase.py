from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from raveil.command_showcase import list_showcases, mutate_showcase, prepare_showcase, run_showcase
from raveil.workspace import NativeWorkspace


class CommandShowcaseTests(unittest.TestCase):
    def test_list_names_all_non_claim_scenarios(self) -> None:
        listed = list_showcases()
        self.assertIn("conceptual tool/process-level", listed)
        self.assertIn("does not test an ISA or CPU microarchitecture", listed)
        self.assertIn("showcase-parallel", listed)
        self.assertIn("showcase-incremental", listed)
        self.assertIn("control-small", listed)
        self.assertIn("not connected", listed)

    def test_parallel_initial_and_incremental_reuse_are_real(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = NativeWorkspace(Path(directory))
            prepared = prepare_showcase(workspace, "showcase-incremental", 16)
            self.assertIn("synthetic=true", prepared)
            self.assertIn("conceptual-only", prepared)
            first = run_showcase(workspace, "showcase-incremental", 16)
            self.assertIn("OoO replacement", first)
            self.assertIn("semantic_hashes=valid", first)
            self.assertIn("reuse executed=16", first)
            self.assertIn("production_reuse=not-implemented", first)
            changed = mutate_showcase(workspace, "showcase-incremental", 0)
            self.assertIn("deterministic=true", changed)
            second = run_showcase(workspace, "showcase-incremental", 16)
            self.assertIn("reuse executed=1", second)
            self.assertIn("reused=15", second)
            self.assertIn("invalidated=1", second)

    def test_small_control_exposes_overhead_without_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = NativeWorkspace(Path(directory))
            prepare_showcase(workspace, "control-small")
            result = run_showcase(workspace, "control-small")
            self.assertIn("nodes=4", result)
            self.assertIn("development-non-claim", result)
            self.assertIn("baseline-first evaluation_total", result)


if __name__ == "__main__":
    unittest.main()
