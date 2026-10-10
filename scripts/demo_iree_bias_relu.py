#!/usr/bin/env python3
"""Real pinned-compiler admission and owned native replay, not VMFB execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from raveil.graph_mvp import GraphProgram, PavaneSemanticOracle
from raveil.iree_import import ImportRecord


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(a: list[int], b: list[int], bias: list[int]) -> list[int]:
    """Independent scalar contract, checking every signed C intermediate."""
    output = []
    for row in range(8):
        for col in range(8):
            total = 0
            for k in range(8):
                product = a[8 * row + k] * b[8 * k + col]
                assert -(1 << 63) <= product < 1 << 63
                total += product
                assert -(1 << 63) <= total < 1 << 63
            total += bias[col]
            assert -(1 << 63) <= total < 1 << 63
            output.append(max(0, total))
    return output


def cases():
    yield "zero-boundaries", [0] * 64, [0] * 64, [-4, -3, -2, -1, 0, 1, 2, 3]
    a = [row - 4 for row in range(8) for _ in range(8)]
    identity = [int(row == col) for row in range(8) for col in range(8)]
    yield "rows-and-column-bias", a, identity, [-9, -3, -1, 0, 1, 2, 4, 11]
    # One nonzero product per cell: widens before multiply, without i64 overflow.
    a = [0] * 64
    for row in range(8):
        a[row * 8] = -(1 << 31) if row % 2 == 0 else (1 << 31) - 1
    b = [-1, 2, 0, 1, -2, 3, -3, 4] + [0] * 56
    yield "signed-widening", a, b, [0, 1 << 33, -1, 7, -(1 << 33), 0, 9, 2]
    a = [((i * 13 + 5) % 19) - 9 for i in range(64)]
    b = [((i * 7 + 3) % 17) - 8 for i in range(64)]
    yield "mixed-reduction", a, b, [i * 3 - 10 for i in range(8)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iree-compile", type=Path, required=True)
    parser.add_argument("--compiler", default="cc")
    parser.add_argument("--output", type=Path, required=True,
                        help="new private evidence directory (must not exist)")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sources = ["raveil/iree_import.py", "raveil/graph_mvp.py", "raveil/native_backend.py",
               "raveil/cli.py", "benchmarks/native/benchmark.c", "scripts/demo_iree_bias_relu.py"]
    stems = ("gemm-8x8x8-i32-i64", "gemm-bias-relu-8x8x8-i32-i64")
    for stem in stems:
        sources += [f"benchmarks/iree/{stem}.mlir", f"benchmarks/iree/{stem}.import.json"]
    identities = {p: digest(ROOT / p) for p in sources}
    commands = []

    def run(label, argv, input_text=None):
        result = subprocess.run(argv, cwd=ROOT, input=input_text, capture_output=True,
                                text=True, timeout=120)
        (out / f"{label}.stdout").write_text(result.stdout)
        (out / f"{label}.stderr").write_text(result.stderr)
        commands.append({"argv": argv, "exit": result.returncode, "label": label})
        (out / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        if result.returncode:
            raise RuntimeError(f"{label} failed; raw logs retained in {out}")
        return result.stdout

    run("compiler-version", [str(args.iree_compile), "--version"])
    run("native-version", [args.compiler, "--version"])
    results = []
    for family, stem in zip(("gemm", "gemm_bias_relu"), stems):
        target = out / f"{family}.json"
        run(f"import-{family}", [sys.executable, "-m", "raveil", "graph-mvp",
            "--backend", "native", "--compiler", args.compiler,
            "--import-manifest", str(ROOT / f"benchmarks/iree/{stem}.import.json"),
            "--iree-compile", str(args.iree_compile), "--minimum-predicted-improvement", "0.99",
            "--output", str(target)])
        result = json.loads(target.read_text())
        record = ImportRecord.from_dict(json.loads(Path(str(target) + ".import.json").read_text()))
        program = GraphProgram.create(family, 8, 8, 8)
        expected = PavaneSemanticOracle().expected_checksum(program)
        assert record.graph_sha256 == program.identity == result["program_sha256"]
        assert result["outcome"] == "abstained"
        assert result["selected_variant"] == "baseline-ijk"
        assert len(result["observations"]) == 1
        observation = result["observations"][0]
        assert observation["checksum"] == observation["reference_checksum"] == expected
        results.append({"family": family, "graph_sha256": program.identity,
                        "checksum": expected, "outcome": result["outcome"],
                        "source_sha256": record.source_sha256,
                        "artifact_sha256": record.artifact_sha256,
                        "artifact_size": record.artifact_size})

    # Private harness calls unchanged owned C functions, exposing every result.
    # This does not execute the compiler's VMFB or change the production input API.
    harness = out / "replay.c"
    harness.write_text("#define main raveil_benchmark_entry\n#include " +
        json.dumps(str(ROOT / "benchmarks/native/benchmark.c")) + '''
#undef main
int main(void) {
    int32_t a[64], b[64]; int64_t bias[8], materialized[64], fused[64];
    for (int i=0; i<64; ++i) if (scanf("%" SCNd32, &a[i]) != 1) return 2;
    for (int i=0; i<64; ++i) if (scanf("%" SCNd32, &b[i]) != 1) return 2;
    for (int i=0; i<8; ++i) if (scanf("%" SCNd64, &bias[i]) != 1) return 2;
    gemm_reference(a,b,materialized,8,8,8);
    bias_relu(materialized,bias,8,8);
    options_t options = {"gemm_bias_relu",8,8,8,"ijk",0,"fused",0,1};
    gemm_bias_relu_fused(&options,a,b,bias,fused);
    for (int i=0; i<64; ++i) printf("%" PRId64 " %" PRId64 "\\n", materialized[i],fused[i]);
    return 0;
}
''')
    binary = out / "replay"
    run("compile-replay", [args.compiler, "-O2", "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-D_POSIX_C_SOURCE=200809L", str(harness), "-o", str(binary)])
    replay = []
    for label, a, b, bias in cases():
        expected = reference(a, b, bias)
        payload = " ".join(map(str, a + b + bias)) + "\n"
        (out / f"{label}.input").write_text(payload)
        actual = [int(word) for word in run(label, [str(binary)], payload).split()]
        assert len(actual) == 128
        assert actual[0::2] == actual[1::2] == expected
        replay.append({"case": label, "input": {"a": a, "b": b, "bias": bias},
                       "expected": expected, "checked_cells": 128})
    (out / "replay.json").write_text(json.dumps(replay, indent=2) + "\n")
    assert identities == {p: digest(ROOT / p) for p in sources}, "source changed during demo"
    receipt = {"schema": "raveil.iree-bias-relu-demo/v1", "status": "passed",
               "evidence_class": "compiler-import-and-owned-host-functional",
               "platform": platform.platform(), "python": platform.python_version(),
               "source_sha256": identities, "imports": results,
               "native_checked_cells": sum(case["checked_cells"] for case in replay),
               "artifacts": {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()},
               "limits": "Exact-fixture admission; VMFB not executed; no RTL/QEMU or performance claim."}
    (out / "demo-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"PASS: two real compiler imports; {receipt['native_checked_cells']} native cell checks; {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
