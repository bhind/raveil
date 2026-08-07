from __future__ import annotations

import math

from .model import Candidate, Context, Metrics


class ToyDaphnis:
    """Deterministic analytical backend. It is a harness, not hardware evidence."""

    def measure(self, context: Context, candidate: Candidate) -> Metrics:
        if candidate.vector_width <= 0 or candidate.vector_width & (candidate.vector_width - 1):
            return self._invalid("vector width is not a power of two")
        if candidate.vector_width > context.hardware.lanes:
            return self._invalid("vector width exceeds hardware lanes")

        shape = context.shape
        width = candidate.vector_width
        operations = shape * 5
        compute_cycles = math.ceil(operations / width)
        tile_count = math.ceil(shape / candidate.tile_length)
        scheduling_cycles = tile_count * 12 + width * 10

        external_bytes = 0
        resident = min(shape, candidate.tile_length)
        if candidate.memory_policy == "keep":
            peak_bytes = resident * 16 + candidate.tile_length * 4
        elif candidate.memory_policy == "rematerialize":
            peak_bytes = resident * 6 + candidate.tile_length * 4
            compute_cycles += math.ceil(shape * 1.5 / width)
        elif candidate.memory_policy == "spill":
            peak_bytes = resident * 4 + candidate.tile_length * 2
            external_bytes = shape * 16
        else:
            return self._invalid(f"unknown memory policy: {candidate.memory_policy}")

        peak_kib = peak_bytes / 1024.0
        if peak_kib > context.memory_budget_kib:
            return Metrics(
                cycles=2**63 - 1,
                peak_memory_kib=peak_kib,
                external_bytes=external_bytes,
                energy_units=0.0,
                valid=False,
                reason="memory budget exceeded",
            )

        memory_cycles = math.ceil(
            external_bytes / max(1, context.hardware.external_bytes_per_cycle)
        )
        cycles = compute_cycles + scheduling_cycles + memory_cycles + 8
        energy = operations + compute_cycles * 0.2 + external_bytes * 2.0
        return Metrics(
            cycles=cycles,
            peak_memory_kib=peak_kib,
            external_bytes=external_bytes,
            energy_units=energy,
            valid=True,
        )

    @staticmethod
    def _invalid(reason: str) -> Metrics:
        return Metrics(
            cycles=2**63 - 1,
            peak_memory_kib=0.0,
            external_bytes=0,
            energy_units=0.0,
            valid=False,
            reason=reason,
        )
