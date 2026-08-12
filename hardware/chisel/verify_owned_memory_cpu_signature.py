#!/usr/bin/env python3
from pathlib import Path
import hashlib
import sys


EXPECTED = (
    1,
    0,
    0x11223344,
    0x5522AA44,
    0xCAFEBABE,
    2,
    8,
    8,
    2,
    3,
    2,
    1,
)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_owned_memory_cpu_signature.py SIGNATURE")
    raw = Path(sys.argv[1]).read_bytes()
    lines = [line.strip() for line in raw.decode("ascii").splitlines()]
    observed = tuple(int(line, 16) for line in lines if line)
    if observed != EXPECTED:
        raise SystemExit(
            f"owned memory CPU signature mismatch: observed={observed!r} "
            f"expected={EXPECTED!r}"
        )
    print(
        "OWNED-MEMORY-CPU-SIGNATURE-V1 status=OK "
        "tohost=1 reset_phase=0 data=11223344,5522aa44,cafebabe "
        "phase=2 accepted=8 completed=8 "
        "installation_reads=2 installation_writes=3 "
        "execution_reads=2 execution_writes=1 "
        f"signature_sha256={hashlib.sha256(raw).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
