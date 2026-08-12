#!/usr/bin/env python3
"""Show that one DCache source class does not identify one ELF semantics."""

from hashlib import sha256
from pathlib import Path
import sys


SOURCE_RANGES = {
    "rocket": (8224, 8256),
    "boom": (8288, 8320),
}


def read_signature(path: str, words: int) -> tuple[bytes, tuple[int, ...]]:
    raw = Path(path).read_bytes()
    try:
        lines = [line.strip() for line in raw.decode("ascii").splitlines() if line.strip()]
        observed = tuple(int(line, 16) for line in lines)
    except (UnicodeDecodeError, ValueError) as exc:
        raise SystemExit(f"signature is not ASCII hexadecimal: {exc}") from exc
    if len(observed) != words:
        raise SystemExit(f"expected {words} signature words, got {len(observed)}")
    return raw, observed


def main() -> int:
    if len(sys.argv) != 6 or sys.argv[1] not in SOURCE_RANGES:
        raise SystemExit(
            "usage: verify_owned_cpu_source_nonidentity.py "
            "rocket|boom CPU_SIGNATURE LOADER_SIGNATURE CPU_ELF LOADER_ELF"
        )

    cpu = sys.argv[1]
    cpu_raw, cpu_signature = read_signature(sys.argv[2], 30)
    loader_raw, loader_signature = read_signature(sys.argv[3], 33)
    cpu_elf = Path(sys.argv[4]).read_bytes()
    loader_elf = Path(sys.argv[5]).read_bytes()
    source_start, source_end = SOURCE_RANGES[cpu]

    cpu_sources = cpu_signature[26:28]
    loader_sources = loader_signature[26:28]
    if cpu_sources != loader_sources:
        raise SystemExit(
            f"DCache source differs across workloads: cpu={cpu_sources!r} "
            f"loader={loader_sources!r}"
        )
    if not all(source_start <= source < source_end for source in cpu_sources):
        raise SystemExit(
            f"shared DCache source is outside [{source_start},{source_end}): "
            f"{cpu_sources!r}"
        )
    if (
        cpu_signature[22:24] != (8, 8)
        or cpu_signature[24:26] != (0, 0)
        or loader_signature[22:24] != (1, 1)
        or loader_signature[24:26] != (2, 2)
    ):
        raise SystemExit("workload origin accounting does not match the bounded controls")
    if cpu_signature[2] == loader_signature[15]:
        raise SystemExit("workload payload witnesses unexpectedly match")
    cpu_elf_sha = sha256(cpu_elf).hexdigest()
    loader_elf_sha = sha256(loader_elf).hexdigest()
    if cpu_elf_sha == loader_elf_sha:
        raise SystemExit("ELF inputs are not distinct")
    if sha256(cpu_raw).digest() == sha256(loader_raw).digest():
        raise SystemExit("signature inputs are not distinct")

    print(
        "OWNED-CPU-SOURCE-NONIDENTITY-V1 status=OK "
        f"cpu={cpu} shared_dcache_sources={cpu_sources[0]},{cpu_sources[1]} "
        f"source_range={source_start}:{source_end} distinct_elf=1 "
        f"cpu_elf_sha256={cpu_elf_sha} loader_elf_sha256={loader_elf_sha} "
        "distinct_semantic_witness=1 source_client_class=shared "
        "semantic_identity=not-carried evidence=rtl-simulation-functional "
        "performance=not-measured"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
