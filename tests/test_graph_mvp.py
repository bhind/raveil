from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from raveil.cli import main
from raveil.graph_mvp import (
    AnalyticalPredictor,
    GraphCompiler,
    GraphExecutor,
    GraphProgram,
    GraphVariant,
    MemoryPlan,
    MiroirsStructuralValidator,
    OptimizationProposal,
    PavaneSemanticOracle,
)
from raveil.native_backend import NativeMeasurement


ROOT = Path(__file__).resolve().parents[1]


def measurement(
    latency: int | None, *, valid: bool = True, checksum: str | None = None
) -> NativeMeasurement:
    checksum = checksum or ("same" if valid else "wrong")
    return NativeMeasurement(
        latency,
        checksum,
        checksum if valid else "same",
        valid,
        "" if valid else "checksum mismatch",
    )


class FakeBackend:
    def __init__(self, results: dict[str, NativeMeasurement]) -> None:
        self.results = results
        self.calls: list[str] = []

    def measure(self, context, candidate):  # type: ignore[no-untyped-def]
        self.calls.append(candidate.candidate_id)
        return self.results[candidate.candidate_id]


class GraphCompilerTests(unittest.TestCase):
    def test_compiler_emits_baseline_and_materially_different_fused_variants(self) -> None:
        variants = GraphCompiler().compile(GraphProgram.create("gemm_bias_relu", 64, 64, 64))
        self.assertTrue(variants[0].candidate.trusted_baseline)
        self.assertEqual(len([item for item in variants if item.candidate.trusted_baseline]), 1)
        self.assertIn("fuse:bias_add+relu", variants[-1].transforms)
        self.assertEqual(len({item.variant_id for item in variants}), len(variants))

    def test_program_validation_rejects_non_topological_graph(self) -> None:
        program = GraphProgram.create("gemm", 8, 8, 8)
        broken = program.nodes[0].__class__("broken", "matmul", ("missing", "b"), "out")
        with self.assertRaisesRegex(ValueError, "not topological"):
            GraphProgram("broken", "gemm", 8, 8, 8, (broken,))

    def test_program_validation_rejects_wiring_backend_does_not_implement(self) -> None:
        program = GraphProgram.create("gemm", 8, 8, 8)
        rewired = program.nodes[0].__class__("matmul", "matmul", ("b", "a"), "mm")
        with self.assertRaisesRegex(ValueError, "outside the admitted MVP shape"):
            GraphProgram("rewired", "gemm", 8, 8, 8, (rewired,))

    def test_program_validation_rejects_ambiguous_identity_and_dimensions(self) -> None:
        program = GraphProgram.create("gemm", 8, 8, 8)
        with self.assertRaisesRegex(ValueError, "identity is required"):
            replace(program, program_id="")
        with self.assertRaisesRegex(ValueError, "dimensions"):
            replace(program, m=True)
        with self.assertRaisesRegex(ValueError, "identifiers must be unique"):
            replace(program, nodes=(program.nodes[0], program.nodes[0]))

    def test_predictor_abstains_when_threshold_exceeds_advisory_gain(self) -> None:
        program = GraphProgram.create("gemm", 64, 64, 64)
        variants = GraphCompiler().compile(program)
        proposal = AnalyticalPredictor(0.99).propose(program, variants)
        self.assertTrue(proposal.abstained)
        self.assertIsNone(proposal.variant_id)

    def test_owned_variant_memory_plan_and_proposal_round_trip_strictly(self) -> None:
        program = GraphProgram.create("gemm_bias_relu", 32, 24, 16)
        variants = GraphCompiler().compile(program)
        proposal = AnalyticalPredictor().propose(program, variants)
        self.assertEqual(GraphVariant.from_dict(variants[-1].to_dict()), variants[-1])
        self.assertEqual(
            MemoryPlan.from_dict(variants[-1].memory_plan.to_dict()),
            variants[-1].memory_plan,
        )
        self.assertEqual(OptimizationProposal.from_dict(proposal.to_dict()), proposal)
        self.assertEqual(variants[-1].program_sha256, program.identity)
        self.assertEqual(variants[-1].memory_plan.maximum_intermediate_bytes, 0)

    def test_owned_schemas_reject_unknown_fields_and_mismatched_memory_plan(self) -> None:
        variant = GraphCompiler().compile(GraphProgram.create("gemm", 8, 8, 8))[0]
        malformed = variant.to_dict()
        malformed["unknown"] = True
        with self.assertRaisesRegex(ValueError, "fields do not match"):
            GraphVariant.from_dict(malformed)
        with self.assertRaisesRegex(ValueError, "does not match"):
            replace(
                variant,
                memory_plan=replace(variant.memory_plan, materialization="fused"),
            )


class GraphExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.program = GraphProgram.create("gemm_bias_relu", 64, 64, 64)
        self.variants = GraphCompiler().compile(self.program)
        self.proposal = AnalyticalPredictor().propose(self.program, self.variants)
        self.checksum = PavaneSemanticOracle().expected_checksum(self.program)
        self.assertIsNotNone(self.proposal.variant_id)

    def measured(
        self, latency: int | None, *, valid: bool = True, checksum: str | None = None
    ) -> NativeMeasurement:
        return measurement(latency, valid=valid, checksum=checksum or self.checksum)

    def test_baseline_runs_first_and_faster_valid_proposal_commits(self) -> None:
        backend = FakeBackend(
            {"baseline-ijk": self.measured(200), self.proposal.variant_id: self.measured(100)}  # type: ignore[dict-item]
        )
        result = GraphExecutor(backend).execute(self.program, self.variants, self.proposal)
        self.assertEqual(backend.calls[0], "baseline-ijk")
        self.assertEqual(result.outcome, "committed-proposal")
        self.assertEqual(result.selected_variant, self.proposal.variant_id)

    def test_invalid_proposal_rolls_back_to_baseline(self) -> None:
        backend = FakeBackend(
            {"baseline-ijk": self.measured(200), self.proposal.variant_id: self.measured(100, valid=False)}  # type: ignore[dict-item]
        )
        result = GraphExecutor(backend).execute(self.program, self.variants, self.proposal)
        self.assertEqual(result.outcome, "rolled-back")
        self.assertEqual(result.selected_variant, "baseline-ijk")

    def test_slower_proposal_rolls_back_to_baseline(self) -> None:
        backend = FakeBackend(
            {"baseline-ijk": self.measured(100), self.proposal.variant_id: self.measured(200)}  # type: ignore[dict-item]
        )
        result = GraphExecutor(backend).execute(self.program, self.variants, self.proposal)
        self.assertEqual(result.outcome, "rolled-back")
        self.assertEqual(result.selected_variant, "baseline-ijk")

    def test_self_valid_candidate_that_disagrees_with_baseline_rolls_back(self) -> None:
        backend = FakeBackend(
            {
                "baseline-ijk": self.measured(200),
                self.proposal.variant_id: self.measured(100, checksum="candidate"),  # type: ignore[dict-item]
            }
        )
        result = GraphExecutor(backend).execute(self.program, self.variants, self.proposal)
        self.assertEqual(result.outcome, "rolled-back")
        self.assertEqual(
            result.rollback_reason,
            "proposal failed semantic or execution validation",
        )
        self.assertEqual(result.selected_variant, "baseline-ijk")

    def test_invalid_baseline_fails_closed_without_running_proposal(self) -> None:
        backend = FakeBackend({"baseline-ijk": self.measured(100, valid=False)})
        result = GraphExecutor(backend).execute(self.program, self.variants, self.proposal)
        self.assertEqual(result.outcome, "failed-closed")
        self.assertIsNone(result.selected_variant)
        self.assertEqual(backend.calls, ["baseline-ijk"])

    def test_abstention_runs_only_the_trusted_baseline(self) -> None:
        proposal = AnalyticalPredictor(0.99).propose(self.program, self.variants)
        backend = FakeBackend({"baseline-ijk": self.measured(100)})
        result = GraphExecutor(backend).execute(self.program, self.variants, proposal)
        self.assertEqual(result.outcome, "abstained")
        self.assertEqual(result.selected_variant, "baseline-ijk")
        self.assertEqual(backend.calls, ["baseline-ijk"])

    def test_unknown_proposal_cannot_bypass_the_admitted_slate(self) -> None:
        backend = FakeBackend({"baseline-ijk": self.measured(100)})
        with self.assertRaisesRegex(ValueError, "outside its ranking"):
            proposal = replace(self.proposal, variant_id="not-admitted")
            GraphExecutor(backend).execute(self.program, self.variants, proposal)
        self.assertEqual(backend.calls, [])

    def test_stale_proposal_lineage_is_rejected_before_execution(self) -> None:
        proposal = replace(self.proposal, candidate_set_sha256="0" * 64)
        backend = FakeBackend({"baseline-ijk": self.measured(100)})
        with self.assertRaisesRegex(ValueError, "lineage does not match"):
            GraphExecutor(backend).execute(self.program, self.variants, proposal)
        self.assertEqual(backend.calls, [])

    def test_miroirs_rejects_incomplete_ranking_before_backend_execution(self) -> None:
        proposal = replace(self.proposal, ranking=self.proposal.ranking[:-1])
        backend = FakeBackend({"baseline-ijk": self.measured(100)})
        with self.assertRaisesRegex(ValueError, "ranking does not match"):
            GraphExecutor(backend).execute(self.program, self.variants, proposal)
        self.assertEqual(backend.calls, [])

    def test_miroirs_accepts_the_compiler_owned_slate(self) -> None:
        MiroirsStructuralValidator().validate(
            self.program,
            GraphCompiler().contract,
            self.variants,
            self.proposal,
        )

    def test_pavane_verdict_is_semantic_and_not_a_timing_decision(self) -> None:
        verdict = PavaneSemanticOracle().compare(
            self.program,
            self.measured(None),
            self.measured(None),
        )
        self.assertTrue(verdict.approved)
        self.assertTrue(verdict.equivalent)
        self.assertTrue(verdict.baseline_valid)
        self.assertTrue(verdict.candidate_valid)

    def test_pavane_rejects_candidate_that_only_self_validates(self) -> None:
        verdict = PavaneSemanticOracle().compare(
            self.program,
            self.measured(200),
            self.measured(100, checksum="candidate"),
        )
        self.assertFalse(verdict.approved)
        self.assertTrue(verdict.baseline_valid)
        self.assertFalse(verdict.candidate_valid)
        self.assertFalse(verdict.equivalent)

    def test_pavane_rejects_a_self_consistent_wrong_backend_reference(self) -> None:
        wrong = NativeMeasurement(100, "deadbeefdeadbeef", "deadbeefdeadbeef", True)
        verdict = PavaneSemanticOracle().baseline(self.program, wrong)
        self.assertFalse(verdict.approved)

    def test_miroirs_rejects_noncanonical_candidate_before_execution(self) -> None:
        forged = replace(
            self.variants[1],
            candidate=replace(self.variants[1].candidate, cold_priority=99),
        )
        variants = (self.variants[0], forged, *self.variants[2:])
        proposal = AnalyticalPredictor().propose(self.program, variants)
        backend = FakeBackend({"baseline-ijk": self.measured(100)})
        with self.assertRaisesRegex(ValueError, "canonical compiler"):
            GraphExecutor(backend).execute(self.program, variants, proposal)
        self.assertEqual(backend.calls, [])

    def test_no_timing_baseline_remains_valid_for_abstention(self) -> None:
        proposal = AnalyticalPredictor(0.99).propose(self.program, self.variants)
        backend = FakeBackend({"baseline-ijk": self.measured(None)})
        result = GraphExecutor(backend).execute(self.program, self.variants, proposal)
        self.assertEqual(result.outcome, "abstained")
        self.assertEqual(result.selected_variant, "baseline-ijk")


class GraphMVPCLITests(unittest.TestCase):
    def test_cli_runs_owned_graph_through_native_backend(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            with mock.patch("sys.stdout") as stdout:
                exit_code = main(
                    [
                        "graph-mvp",
                        "--family", "gemm_bias_relu",
                        "--m", "17",
                        "--n", "19",
                        "--k", "13",
                        "--output", str(output),
                    ]
                )
            self.assertEqual(exit_code, 0, stdout)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["schema"], "raveil.graph-mvp-result/v1")
            self.assertEqual(result["claim_status"], "development-non-claim")
            self.assertEqual(result["evidence_class"], "host-correctness")
            self.assertNotIn("context", result)
            self.assertNotIn("measurement_valid", result)
            self.assertTrue(result["observations"][0]["semantic_valid"])
            self.assertEqual(result["observations"][0]["variant_id"], "baseline-ijk")
            self.assertIn(result["outcome"], {"committed-proposal", "rolled-back", "abstained"})

    def test_cli_refuses_to_overwrite_segregated_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            output.write_text("preserve-me", encoding="utf-8")
            with mock.patch("sys.stderr"):
                exit_code = main(
                    ["graph-mvp", "--m", "8", "--n", "8", "--k", "8", "--output", str(output)]
                )
            self.assertEqual(exit_code, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "preserve-me")


if __name__ == "__main__":
    unittest.main()
