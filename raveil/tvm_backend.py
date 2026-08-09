from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

from .experiment_schema import BenchmarkCandidate, BenchmarkManifest, WorkloadSpec
from .native_backend import NativeMeasurement


@dataclass
class _PreparedKernel:
    module: Any
    arguments: tuple[Any, ...]
    output: Any
    reference_checksum: str


class TVMMetaScheduleBackend:
    """Pinned official TVM adapter with candidate-scoped database reuse."""

    def __init__(self, pinned_version: str, work_dir: Path, warmups: int = 1) -> None:
        self.pinned_version = pinned_version
        self.work_dir = work_dir
        self.warmups = warmups
        try:
            import numpy as np
            import tvm
            from tvm.s_tir import meta_schedule
        except ImportError as error:
            raise RuntimeError(
                "apache-tvm is not installed; create the isolated Gate 1 TVM environment"
            ) from error
        installed = getattr(tvm, "__version__", "unknown")
        if installed != pinned_version:
            raise RuntimeError(
                f"apache-tvm version mismatch: expected {pinned_version}, found {installed}"
            )
        self.np = np
        self.tvm = tvm
        self.meta_schedule = meta_schedule
        self.target = tvm.target.Target({"kind": "llvm", "num-cores": 1})
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.database = meta_schedule.database.JSONDatabase(work_dir=str(work_dir))
        self._prepared: dict[tuple[str, str], _PreparedKernel] = {}

    @staticmethod
    def _filled_i32(count: int, salt: int) -> list[int]:
        state = 0x9E3779B9 ^ salt
        values = []
        for _ in range(count):
            state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
            values.append(((state >> 16) % 7) - 3)
        return values

    @staticmethod
    def _checksum(values: Any) -> str:
        result = 1469598103934665603
        for raw in values.reshape(-1):
            word = int(raw) & 0xFFFFFFFFFFFFFFFF
            for shift in range(0, 64, 8):
                result ^= (word >> shift) & 0xFF
                result = (result * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return f"{result:016x}"

    def _prim_func(self, workload: WorkloadSpec, candidate: BenchmarkCandidate) -> Any:
        te = self.tvm.te
        a = te.placeholder((workload.m, workload.k), "int32", name="a")
        b = te.placeholder((workload.k, workload.n), "int32", name="b")
        reduce_k = te.reduce_axis((0, workload.k), name="reduce_k")
        hidden = te.compute(
            (workload.m, workload.n),
            lambda i, j: te.sum(
                a[i, reduce_k].astype("int64") * b[reduce_k, j].astype("int64"),
                axis=reduce_k,
            ),
            name="hidden_gemm",
        )
        inputs: list[Any] = [a, b]
        output = hidden
        if workload.family != "gemm":
            bias = te.placeholder((workload.n,), "int64", name="bias")
            activated = te.compute(
                (workload.m, workload.n),
                lambda i, j: te.max(hidden[i, j] + bias[j], self.tvm.tirx.const(0, "int64")),
                name="bias_relu",
            )
            inputs.append(bias)
            output = activated
            if workload.family == "mlp2":
                b2 = te.placeholder((workload.n, workload.k), "int32", name="b2")
                reduce_n = te.reduce_axis((0, workload.n), name="reduce_n")
                output = te.compute(
                    (workload.m, workload.k),
                    lambda i, j: te.sum(
                        activated[i, reduce_n]
                        * b2[reduce_n, j].astype("int64"),
                        axis=reduce_n,
                    ),
                    name="output_gemm",
                )
                inputs.append(b2)
        function = te.create_prim_func([*inputs, output]).with_attr("global_symbol", "main")
        return function.with_attr("raveil.candidate_id", candidate.candidate_id)

    def _schedule(self, function: Any, workload: WorkloadSpec, candidate: BenchmarkCandidate) -> Any:
        schedule = self.tvm.s_tir.Schedule(function)
        block_name = "output_gemm" if workload.family == "mlp2" else "hidden_gemm"
        block = schedule.get_sblock(block_name)
        i_loop, j_loop, reduction_loop = schedule.get_loops(block)[-3:]
        if candidate.loop_order == "ikj":
            schedule.reorder(i_loop, reduction_loop, j_loop)
        elif candidate.loop_order == "tiled":
            i_outer, i_inner = schedule.split(i_loop, factors=[None, candidate.tile])
            j_outer, j_inner = schedule.split(j_loop, factors=[None, candidate.tile])
            r_outer, r_inner = schedule.split(
                reduction_loop, factors=[None, candidate.tile]
            )
            schedule.reorder(
                i_outer, r_outer, j_outer, i_inner, r_inner, j_inner
            )
        if candidate.materialization == "fused" and workload.family != "gemm":
            producer = schedule.get_sblock("hidden_gemm")
            consumer = schedule.get_sblock("bias_relu")
            consumer_loops = schedule.get_loops(consumer)
            schedule.compute_at(producer, consumer_loops[0])
        return schedule

    def _arrays(self, workload: WorkloadSpec) -> tuple[tuple[Any, ...], Any, str]:
        np = self.np
        a = np.array(
            self._filled_i32(workload.m * workload.k, 1), dtype="int32"
        ).reshape(workload.m, workload.k)
        b = np.array(
            self._filled_i32(workload.k * workload.n, 2), dtype="int32"
        ).reshape(workload.k, workload.n)
        hidden = a.astype("int64") @ b.astype("int64")
        host_inputs: list[Any] = [a, b]
        reference = hidden
        if workload.family != "gemm":
            bias = np.array([index % 11 - 5 for index in range(workload.n)], dtype="int64")
            reference = np.maximum(hidden + bias, 0)
            host_inputs.append(bias)
            if workload.family == "mlp2":
                b2 = np.array(
                    self._filled_i32(workload.n * workload.k, 3), dtype="int32"
                ).reshape(workload.n, workload.k)
                reference = reference @ b2.astype("int64")
                host_inputs.append(b2)
        output = np.zeros(reference.shape, dtype="int64")
        tensors = tuple(self.tvm.runtime.tensor(value) for value in host_inputs)
        output_tensor = self.tvm.runtime.tensor(output)
        return (*tensors, output_tensor), output_tensor, self._checksum(reference)

    def prepare(self, manifest: BenchmarkManifest) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        for workload in manifest.workloads:
            for candidate in manifest.candidates:
                key = (workload.workload_id, candidate.candidate_id)
                function = self._prim_func(workload, candidate)
                module = self.tvm.IRModule({"main": function})
                schedule = self.database.query_schedule(module, self.target, "main")
                if schedule is None:
                    schedule = self._schedule(function, workload, candidate)
                    trial_module = self.tvm.build(schedule.mod, target=self.target)
                    arguments, _, _ = self._arrays(workload)
                    started = time.perf_counter()
                    trial_module(*arguments)
                    run_seconds = max(time.perf_counter() - started, 1e-12)
                    registered = self.database.commit_workload(module)
                    self.database.commit_tuning_record(
                        self.meta_schedule.database.TuningRecord(
                            schedule.trace,
                            registered,
                            run_secs=[run_seconds],
                            target=self.target,
                        )
                    )
                    schedule = self.database.query_schedule(module, self.target, "main")
                    if schedule is None:
                        raise RuntimeError("MetaSchedule database reuse query failed")
                compiled = self.tvm.build(schedule.mod, target=self.target)
                arguments, output, reference_checksum = self._arrays(workload)
                self._prepared[key] = _PreparedKernel(
                    compiled, arguments, output, reference_checksum
                )

    def measure(self, context: WorkloadSpec, candidate: BenchmarkCandidate) -> NativeMeasurement:
        prepared = self._prepared.get((context.workload_id, candidate.candidate_id))
        if prepared is None:
            return NativeMeasurement(None, None, None, False, "TVM candidate not prepared")
        for _ in range(self.warmups):
            prepared.module(*prepared.arguments)
        started = time.perf_counter_ns()
        for _ in range(context.inner_iterations):
            prepared.module(*prepared.arguments)
        latency = max(1, (time.perf_counter_ns() - started) // context.inner_iterations)
        checksum = self._checksum(prepared.output.numpy())
        return NativeMeasurement(
            latency,
            checksum,
            prepared.reference_checksum,
            checksum == prepared.reference_checksum,
            "" if checksum == prepared.reference_checksum else "TVM semantic checksum mismatch",
        )
