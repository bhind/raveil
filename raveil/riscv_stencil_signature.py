"""Independent parser and oracle for RFC-0005 RISC-V signature output."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .static_region import static_stencil_oracle


class RiscvStencilSignatureError(ValueError):
    """The simulator signature is malformed or semantically incorrect."""


def input_words(seed: int = 1) -> list[int]:
    if type(seed) is not int or seed < 0 or seed > 0xFFFFFFFF:
        raise RiscvStencilSignatureError("seed must be uint32")
    return [
        (((index + 1) * ((seed * 2654435761) & 0xFFFFFFFF))
         ^ (index << (seed & 7)) ^ (seed * 17))
        & 0xFFFFFFFF
        for index in range(324)
    ]


def parse_signature(text: str) -> list[int]:
    lines = text.splitlines()
    if len(lines) != 256:
        raise RiscvStencilSignatureError("signature must contain 256 words")
    words: list[int] = []
    for line in lines:
        if len(line) != 8 or any(char not in "0123456789abcdefABCDEF" for char in line):
            raise RiscvStencilSignatureError("signature word must be eight hex digits")
        words.append(int(line, 16))
    return words


def validate_signature(text: str, seed: int = 1) -> list[int]:
    actual = parse_signature(text)
    expected = static_stencil_oracle(input_words(seed))
    if actual != expected:
        mismatch = next(index for index, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
        raise RiscvStencilSignatureError(f"signature mismatch at output {mismatch}")
    return actual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="validate one RFC-0005 RISC-V signature")
    parser.add_argument("--signature", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        words = validate_signature(args.signature.read_text(encoding="ascii"), args.seed)
    except (OSError, UnicodeError, RiscvStencilSignatureError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    checksum = sum(words) & 0xFFFFFFFFFFFFFFFF
    print(
        "RISCV-STENCIL-SIGNATURE-V1 status=OK outputs=256 "
        f"checksum={checksum:016x} oracle=independent-host performance=not-measured"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
