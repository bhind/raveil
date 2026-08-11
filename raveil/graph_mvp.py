from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Literal, Protocol

from .experiment_schema import BenchmarkCandidate, WorkloadSpec
from .native_backend import NativeMeasurement


GRAPH_SCHEMA = "raveil.graph-program/v1"
RESULT_SCHEMA = "raveil.graph-mvp-result/v1"
VARIANT_SCHEMA = "raveil.graph-variant/v1"
MEMORY_PLAN_SCHEMA = "raveil.memory-plan/v1"
PROPOSAL_SCHEMA = "raveil.optimization-proposal/v1"


def _identity(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _require_exact_keys(value: dict[str, object], expected: set[str], kind: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{kind} fields do not match schema")


def _valid_identity(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    op: str
    inputs: tuple[str, ...]
    output: str


@dataclass(frozen=True)
class GraphProgram:
    program_id: str
    family: Literal["gemm", "gemm_bias_relu"]
    m: int
    n: int
    k: int
    nodes: tuple[GraphNode, ...]
    schema: str = GRAPH_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != GRAPH_SCHEMA:
            raise ValueError(f"unsupported graph schema: {self.schema}")
        if self.family not in {"gemm", "gemm_bias_relu"}:
            raise ValueError(f"unsupported MVP graph family: {self.family}")
        if min(self.m, self.n, self.k) <= 0 or max(self.m, self.n, self.k) > 512:
            raise ValueError("graph dimensions must be between 1 and 512")
        expected_ops = (
            ("matmul",)
            if self.family == "gemm"
            else ("matmul", "bias_add", "relu")
        )
        if tuple(node.op for node in self.nodes) != expected_ops:
            raise ValueError(f"{self.family} graph must contain {expected_ops}")
        available = {"a", "b", "bias"}
        for node in self.nodes:
            if not node.node_id or not node.output or not set(node.inputs) <= available:
                raise ValueError(f"graph node {node.node_id or '<unnamed>'} is not topological")
            if node.output in available:
                raise ValueError(f"graph output {node.output} is not unique")
            available.add(node.output)
        expected_wiring = (
            (("matmul", ("a", "b"), "mm"),)
            if self.family == "gemm"
            else (
                ("matmul", ("a", "b"), "mm"),
                ("bias_add", ("mm", "bias"), "biased"),
                ("relu", ("biased",), "output"),
            )
        )
        wiring = tuple((node.op, node.inputs, node.output) for node in self.nodes)
        if wiring != expected_wiring:
            raise ValueError(f"{self.family} graph wiring is outside the admitted MVP shape")

    @classmethod
    def create(
        cls, family: Literal["gemm", "gemm_bias_relu"], m: int, n: int, k: int
    ) -> "GraphProgram":
        nodes = [GraphNode("matmul", "matmul", ("a", "b"), "mm")]
        if family == "gemm_bias_relu":
            nodes.extend(
                (
                    GraphNode("bias", "bias_add", ("mm", "bias"), "biased"),
                    GraphNode("relu", "relu", ("biased",), "output"),
                )
            )
        return cls(f"{family}-{m}x{n}x{k}", family, m, n, k, tuple(nodes))

    @property
    def identity(self) -> str:
        return _identity(asdict(self))

    def workload(self, inner_iterations: int = 1) -> WorkloadSpec:
        return WorkloadSpec(
            self.program_id,
            self.family,
            self.m,
            self.n,
            self.k,
            "graph-mvp",
            "runtime",
            "host-managed",
            "+".join(node.op for node in self.nodes),
            inner_iterations,
        )


@dataclass(frozen=True)
class MemoryPlan:
    plan_id: str
    storage: Literal["host-memory"]
    materialization: Literal["fused", "materialized"]
    maximum_intermediate_bytes: int
    schema: str = MEMORY_PLAN_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != MEMORY_PLAN_SCHEMA or not self.plan_id:
            raise ValueError("invalid memory plan identity or schema")
        if self.storage != "host-memory":
            raise ValueError("unsupported MVP memory-plan storage")
        if self.materialization not in {"fused", "materialized"}:
            raise ValueError("unsupported MVP materialization")
        if type(self.maximum_intermediate_bytes) is not int or not (
            0 <= self.maximum_intermediate_bytes <= 512 * 512 * 8
        ):
            raise ValueError("memory-plan bound is outside the MVP limit")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "MemoryPlan":
        _require_exact_keys(value, set(cls.__dataclass_fields__), "memory plan")
        return cls(**value)  # type: ignore[arg-type]


@dataclass(frozen=True)
class GraphVariant:
    candidate: BenchmarkCandidate
    transforms: tuple[str, ...]
    program_sha256: str
    contract_sha256: str
    memory_plan: MemoryPlan
    schema: str = VARIANT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != VARIANT_SCHEMA:
            raise ValueError("unsupported graph-variant schema")
        if not _valid_identity(self.program_sha256) or not _valid_identity(
            self.contract_sha256
        ):
            raise ValueError("graph variant lineage identities must be SHA-256")
        if not self.transforms or any(
            type(item) is not str or not item for item in self.transforms
        ) or len(set(self.transforms)) != len(self.transforms):
            raise ValueError("graph variant transforms must be unique nonempty strings")
        if self.memory_plan.materialization != self.candidate.materialization:
            raise ValueError("memory plan does not match candidate materialization")

    @property
    def variant_id(self) -> str:
        return self.candidate.candidate_id

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "GraphVariant":
        _require_exact_keys(value, set(cls.__dataclass_fields__), "graph variant")
        copied = dict(value)
        if type(copied["candidate"]) is not dict or type(copied["memory_plan"]) is not dict:
            raise ValueError("graph variant nested records must be objects")
        copied["candidate"] = BenchmarkCandidate.from_dict(copied["candidate"])
        copied["memory_plan"] = MemoryPlan.from_dict(copied["memory_plan"])
        if type(copied["transforms"]) not in {list, tuple}:
            raise ValueError("graph variant transforms must be an array")
        copied["transforms"] = tuple(copied["transforms"])
        return cls(**copied)  # type: ignore[arg-type]


@dataclass(frozen=True)
class ExecutionContract:
    contract_id: str = "posix-cpu-userspace-v1"
    allowed_ops: tuple[str, ...] = ("matmul", "bias_add", "relu")
    maximum_dimension: int = 512
    trusted_baseline: str = "baseline-ijk"

    def validate(self, program: GraphProgram) -> None:
        if max(program.m, program.n, program.k) > self.maximum_dimension:
            raise ValueError(f"program exceeds contract {self.contract_id} dimensions")
        rejected = sorted({node.op for node in program.nodes} - set(self.allowed_ops))
        if rejected:
            raise ValueError(f"program uses operations outside the contract: {rejected}")

    @property
    def identity(self) -> str:
        return _identity(asdict(self))


class GraphCompiler:
    """Lower the owned graph into a small, explicit native candidate slate."""

    def __init__(self, contract: ExecutionContract | None = None) -> None:
        self.contract = contract or ExecutionContract()

    def compile(self, program: GraphProgram) -> tuple[GraphVariant, ...]:
        self.contract.validate(program)
        lineage = (program.identity, self.contract.identity)
        intermediate_bytes = program.m * program.n * 8

        def variant(candidate: BenchmarkCandidate, transforms: tuple[str, ...]) -> GraphVariant:
            plan = MemoryPlan(
                f"host-{candidate.candidate_id}",
                "host-memory",
                candidate.materialization,
                0 if candidate.materialization == "fused" else intermediate_bytes,
            )
            return GraphVariant(candidate, transforms, *lineage, plan)

        variants = [
            variant(
                BenchmarkCandidate("baseline-ijk", "ijk", 0, "materialized", 0, True),
                ("trusted-baseline",),
            ),
            variant(
                BenchmarkCandidate("loop-ikj", "ikj", 0, "materialized", 1),
                ("loop-interchange",),
            ),
            variant(
                BenchmarkCandidate("tile32", "tiled", 32, "materialized", 2),
                ("loop-tiling:32",),
            ),
        ]
        if program.family == "gemm_bias_relu":
            variants.extend(
                (
                    variant(
                        BenchmarkCandidate("loop-ikj-fused", "ikj", 0, "fused", 3),
                        ("loop-interchange", "fuse:bias_add+relu"),
                    ),
                    variant(
                        BenchmarkCandidate("tile32-fused", "tiled", 32, "fused", 4),
                        ("loop-tiling:32", "fuse:bias_add+relu"),
                    ),
                )
            )
        return tuple(variants)


@dataclass(frozen=True)
class RankedVariant:
    variant_id: str
    relative_cost: float


@dataclass(frozen=True)
class OptimizationProposal:
    variant_id: str | None
    predicted_improvement: float
    abstained: bool
    reason: str
    ranking: tuple[RankedVariant, ...]
    program_sha256: str
    contract_sha256: str
    candidate_set_sha256: str
    schema: str = PROPOSAL_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != PROPOSAL_SCHEMA or not all(
            _valid_identity(value)
            for value in (
                self.program_sha256,
                self.contract_sha256,
                self.candidate_set_sha256,
            )
        ):
            raise ValueError("invalid optimization-proposal schema or lineage")
        if type(self.predicted_improvement) not in {int, float} or isinstance(
            self.predicted_improvement, bool
        ) or not math.isfinite(self.predicted_improvement) or not (
            0 <= self.predicted_improvement <= 1
        ):
            raise ValueError("predicted improvement must be finite and in [0, 1]")
        if not self.reason or not self.ranking:
            raise ValueError("proposal reason and ranking are required")
        identifiers = [item.variant_id for item in self.ranking]
        if len(set(identifiers)) != len(identifiers) or any(
            not math.isfinite(item.relative_cost) or item.relative_cost < 0
            for item in self.ranking
        ):
            raise ValueError("proposal ranking is invalid")
        if self.abstained != (self.variant_id is None):
            raise ValueError("proposal abstention and variant must agree")
        if self.variant_id is not None and self.variant_id not in identifiers:
            raise ValueError("proposal variant is outside its ranking")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "OptimizationProposal":
        _require_exact_keys(value, set(cls.__dataclass_fields__), "optimization proposal")
        copied = dict(value)
        if type(copied["ranking"]) not in {list, tuple}:
            raise ValueError("proposal ranking must be an array")
        ranking: list[RankedVariant] = []
        for item in copied["ranking"]:
            if type(item) is not dict:
                raise ValueError("proposal ranking entries must be objects")
            _require_exact_keys(item, {"variant_id", "relative_cost"}, "ranked variant")
            ranking.append(RankedVariant(**item))
        copied["ranking"] = tuple(ranking)
        return cls(**copied)  # type: ignore[arg-type]


def variant_set_identity(variants: tuple[GraphVariant, ...]) -> str:
    return _identity([variant.to_dict() for variant in variants])


class AnalyticalPredictor:
    """Cheap proposal heuristic. It advises; measurements and contracts decide."""

    def __init__(self, minimum_predicted_improvement: float = 0.05) -> None:
        if not 0 <= minimum_predicted_improvement < 1:
            raise ValueError("minimum predicted improvement must be in [0, 1)")
        self.minimum_predicted_improvement = minimum_predicted_improvement

    def _cost(self, program: GraphProgram, variant: GraphVariant) -> float:
        candidate = variant.candidate
        cost = 1.0
        if candidate.loop_order == "ikj":
            cost *= 0.78 if program.n >= 16 else 0.98
        elif candidate.loop_order == "tiled":
            cost *= 0.72 if min(program.m, program.n, program.k) >= candidate.tile else 1.04
        if candidate.materialization == "fused" and program.family == "gemm_bias_relu":
            cost *= 0.86
        return cost

    def propose(
        self, program: GraphProgram, variants: tuple[GraphVariant, ...]
    ) -> OptimizationProposal:
        if not variants or not variants[0].candidate.trusted_baseline:
            raise ValueError("variant slate must start with one trusted baseline")
        ranking = tuple(
            sorted(
                (RankedVariant(item.variant_id, self._cost(program, item)) for item in variants),
                key=lambda item: (item.relative_cost, item.variant_id),
            )
        )
        best = ranking[0]
        improvement = max(0.0, 1.0 - best.relative_cost)
        lineage = (
            program.identity,
            variants[0].contract_sha256,
            variant_set_identity(variants),
        )
        if best.variant_id == variants[0].variant_id or improvement < self.minimum_predicted_improvement:
            return OptimizationProposal(
                None,
                improvement,
                True,
                "predicted improvement is below the abstention threshold",
                ranking,
                *lineage,
            )
        return OptimizationProposal(
            best.variant_id,
            improvement,
            False,
            "candidate cleared the advisory threshold",
            ranking,
            *lineage,
        )


class ExecutionBackend(Protocol):
    def measure(self, context: WorkloadSpec, candidate: BenchmarkCandidate) -> NativeMeasurement:
        ...


@dataclass(frozen=True)
class VariantObservation:
    variant_id: str
    latency_ns: int | None
    checksum: str | None
    reference_checksum: str | None
    semantic_valid: bool
    failure: str

    @classmethod
    def from_measurement(
        cls, variant_id: str, measurement: NativeMeasurement
    ) -> "VariantObservation":
        return cls(
            variant_id,
            measurement.latency_ns,
            measurement.checksum,
            measurement.reference_checksum,
            measurement.semantic_valid,
            measurement.failure,
        )


@dataclass(frozen=True)
class GraphMVPResult:
    program_id: str
    program_sha256: str
    contract_sha256: str
    variants: tuple[dict[str, object], ...]
    proposal: OptimizationProposal
    observations: tuple[VariantObservation, ...]
    selected_variant: str | None
    outcome: str
    rollback_reason: str
    claim_status: str = "development-non-claim"
    evidence_class: str = "host-correctness"
    schema: str = RESULT_SCHEMA

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class GraphExecutor:
    """Run baseline-first, validate proposals, and fail closed to the baseline."""

    def __init__(
        self, backend: ExecutionBackend, contract: ExecutionContract | None = None
    ) -> None:
        self.backend = backend
        self.contract = contract or ExecutionContract()

    @staticmethod
    def _valid(measurement: NativeMeasurement) -> bool:
        return (
            measurement.semantic_valid
            and measurement.latency_ns is not None
            and measurement.checksum is not None
            and measurement.checksum == measurement.reference_checksum
        )

    def execute(
        self,
        program: GraphProgram,
        variants: tuple[GraphVariant, ...],
        proposal: OptimizationProposal,
        *,
        inner_iterations: int = 1,
    ) -> GraphMVPResult:
        self.contract.validate(program)
        if not variants or not variants[0].candidate.trusted_baseline:
            raise ValueError("variant slate must start with the trusted baseline")
        if sum(item.candidate.trusted_baseline for item in variants) != 1:
            raise ValueError("variant slate must contain exactly one trusted baseline")
        if len({item.variant_id for item in variants}) != len(variants):
            raise ValueError("variant identifiers must be unique")
        if any(
            item.program_sha256 != program.identity
            or item.contract_sha256 != self.contract.identity
            for item in variants
        ):
            raise ValueError("variant lineage does not match program and contract")
        if (
            proposal.program_sha256 != program.identity
            or proposal.contract_sha256 != self.contract.identity
            or proposal.candidate_set_sha256 != variant_set_identity(variants)
        ):
            raise ValueError("proposal lineage does not match admitted variants")
        by_id = {variant.variant_id: variant for variant in variants}
        baseline = variants[0]
        workload = program.workload(inner_iterations)
        baseline_measurement = self.backend.measure(workload, baseline.candidate)
        observations = [VariantObservation.from_measurement(baseline.variant_id, baseline_measurement)]
        variant_records = tuple(variant.to_dict() for variant in variants)
        common = {
            "program_id": program.program_id,
            "program_sha256": program.identity,
            "contract_sha256": self.contract.identity,
            "variants": variant_records,
            "proposal": proposal,
        }
        if not self._valid(baseline_measurement):
            return GraphMVPResult(
                **common,
                observations=tuple(observations),
                selected_variant=None,
                outcome="failed-closed",
                rollback_reason="trusted baseline failed semantic or execution validation",
            )
        if proposal.abstained or proposal.variant_id is None:
            return GraphMVPResult(
                **common,
                observations=tuple(observations),
                selected_variant=baseline.variant_id,
                outcome="abstained",
                rollback_reason=proposal.reason,
            )
        proposed = by_id.get(proposal.variant_id)
        if proposed is None or proposed.candidate.trusted_baseline:
            raise ValueError("proposal must name a non-baseline variant in the slate")
        proposed_measurement = self.backend.measure(workload, proposed.candidate)
        observations.append(
            VariantObservation.from_measurement(proposed.variant_id, proposed_measurement)
        )
        if not self._valid(proposed_measurement):
            return GraphMVPResult(
                **common,
                observations=tuple(observations),
                selected_variant=baseline.variant_id,
                outcome="rolled-back",
                rollback_reason="proposal failed semantic or execution validation",
            )
        if (
            proposed_measurement.checksum != baseline_measurement.checksum
            or proposed_measurement.reference_checksum
            != baseline_measurement.reference_checksum
        ):
            return GraphMVPResult(
                **common,
                observations=tuple(observations),
                selected_variant=baseline.variant_id,
                outcome="rolled-back",
                rollback_reason="proposal disagreed with the trusted baseline",
            )
        if int(proposed_measurement.latency_ns) >= int(baseline_measurement.latency_ns):
            return GraphMVPResult(
                **common,
                observations=tuple(observations),
                selected_variant=baseline.variant_id,
                outcome="rolled-back",
                rollback_reason="proposal did not improve the observed development run",
            )
        return GraphMVPResult(
            **common,
            observations=tuple(observations),
            selected_variant=proposed.variant_id,
            outcome="committed-proposal",
            rollback_reason="",
        )


def run_graph_mvp(
    program: GraphProgram,
    backend: ExecutionBackend,
    *,
    minimum_predicted_improvement: float = 0.05,
    inner_iterations: int = 1,
) -> GraphMVPResult:
    contract = ExecutionContract()
    variants = GraphCompiler(contract).compile(program)
    proposal = AnalyticalPredictor(minimum_predicted_improvement).propose(program, variants)
    return GraphExecutor(backend, contract).execute(
        program, variants, proposal, inner_iterations=inner_iterations
    )
