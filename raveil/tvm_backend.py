from __future__ import annotations

from .experiment_schema import BenchmarkCandidate, WorkloadSpec
from .native_backend import NativeMeasurement


class TVMMetaScheduleBackend:
    """Version gate for the isolated official apache-tvm adapter."""

    def __init__(self, pinned_version: str) -> None:
        self.pinned_version = pinned_version
        try:
            import tvm  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError(
                "apache-tvm is not installed; create the isolated Gate 1 TVM environment"
            ) from error
        installed = getattr(tvm, "__version__", "unknown")
        if installed != pinned_version:
            raise RuntimeError(
                f"apache-tvm version mismatch: expected {pinned_version}, found {installed}"
            )

    def measure(self, context: WorkloadSpec, candidate: BenchmarkCandidate) -> NativeMeasurement:
        raise NotImplementedError(
            "TVM MetaSchedule measurement remains gated on the fixed-C contract pilot"
        )
