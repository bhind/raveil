#!/usr/bin/env python3
"""Offline T-0200 functional probe. No downloads, timing, tuning or Graph install.

Private source directory contains the hash-pinned weight.f16 and bias.f16.
--self-test needs neither those files nor an Accelerate library.
"""
import argparse
import ctypes
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
import struct

ROWS, COLS = 512, 128
SCALE = 1 << 48
GAMMA_N, GAMMA_D = 258, (1 << 24) - 258
REVISION = "cf967c0a9a04383db6f7b1108d86b2962634b4ac"
FILES = {
    "weight.f16": (131072, "baedbed93e260f3f6b7400ae07ee6267b4c5e72894c8b1e6d1bbd70e994b6016"),
    "bias.f16": (1024, "d98a70ee37d0750e71fe7b16f02c0b8d1155075ac1f7b9e522289265244d9d40"),
}
LIBRARY = "/System/Library/Frameworks/Accelerate.framework/Accelerate"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def half_integer(bits):
    """Independent bit decoder: exact value times 2**24, including subnormals."""
    exponent, fraction = (bits >> 10) & 31, bits & 1023
    require(exponent != 31, "nonfinite binary16")
    magnitude = fraction if exponent == 0 else (1024 + fraction) << (exponent - 1)
    return -magnitude if bits & 0x8000 else magnitude


def decode(raw):
    require(len(raw) % 2 == 0, "odd binary16 length")
    integers = [half_integer(x[0]) for x in struct.iter_unpack("<H", raw)]
    # Separate library decoder feeds implementations, never the integer oracle.
    floats = [x[0] for x in struct.iter_unpack("<e", raw)]
    require(all(v * (1 << 24) == i for v, i in zip(floats, integers)), "decoder disagreement")
    return floats, integers


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def oracle(weights, bias, inputs):
    columns = len(inputs)
    require(len(weights) == len(bias) * columns, "oracle shape mismatch")
    exact, scales = [], []
    for row, b in enumerate(bias):
        products = [weights[row * columns + j] * x for j, x in enumerate(inputs)]
        exact.append(sum(products) + (b << 24))
        scales.append(sum(abs(p) for p in products) + (abs(b) << 24))
    return exact, scales


def validate(outputs, exact, scales):
    require(len(outputs) == len(exact) == len(scales), "output shape mismatch")
    for y, z, scale in zip(outputs, exact, scales):
        require(math.isfinite(y) and f32(y) == y, "output is not finite binary32")
        numerator, denominator = y.as_integer_ratio()
        error_numerator = abs(numerator * SCALE - z * denominator)
        require(error_numerator * GAMMA_D <= GAMMA_N * scale * denominator,
                "binary32 error envelope exceeded")


def serial(weights, bias, inputs):
    outputs = []
    for row, b in enumerate(bias):
        value = b  # Fresh bias on EVERY invocation.
        for j, x in enumerate(inputs):
            value = f32(value + f32(weights[row * len(inputs) + j] * x))
        outputs.append(value)
    return outputs


def blas_control(weights, bias):
    require(platform.system() == "Darwin", "this control requires installed Apple Accelerate")
    library = ctypes.CDLL(LIBRARY)
    fn = library.cblas_sgemv
    fp, ci, cf = ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_float
    fn.argtypes = [ci, ci, ci, ci, cf, fp, ci, fp, ci, cf, fp, ci]
    fn.restype = None
    matrix = (cf * len(weights))(*weights)

    def invoke(inputs):
        require(len(inputs) == COLS, "BLAS input shape mismatch")
        x = (cf * COLS)(*inputs)
        y = (cf * ROWS)(*bias)  # Count this reset; do not reuse an old output.
        fn(101, 111, ROWS, COLS, 1.0, matrix, COLS, x, 1, 1.0, y, 1)
        return list(y)
    return invoke


def dyadic(seed):
    values, state = [], seed
    for _ in range(COLS):
        state ^= (state << 13) & 0xffffffff
        state ^= state >> 17
        state ^= (state << 5) & 0xffffffff
        state &= 0xffffffff
        values.append(((state % 65) - 32) / 4)
    return values


def inputs():
    for name, values in (
        ("zero", [0.0] * COLS), ("one", [1.0] * COLS),
        ("negative-one", [-1.0] * COLS),
        ("alternating-eight", [8.0 if j % 2 == 0 else -8.0 for j in range(COLS)]),
        ("basis-0", [float(j == 0) for j in range(COLS)]),
        ("basis-127", [float(j == 127) for j in range(COLS)]),
        ("xorshift-2000", dyadic(2000)), ("xorshift-2001", dyadic(2001)),
    ):
        require(all(abs(x) <= 8 for x in values), "input domain")
        raw = struct.pack("<128e", *values)
        yield name, raw, decode(raw)


def self_test():
    finite = 0
    for bits in range(65536):
        if (bits >> 10) & 31 == 31:
            try:
                half_integer(bits)
            except ValueError:
                continue
            raise ValueError("nonfinite accepted")
        integer = half_integer(bits)
        value = struct.unpack("<e", struct.pack("<H", bits))[0]
        require(value * (1 << 24) == integer, "half decoder mismatch")
        finite += 1
    # Actual largest finite halves, tiny subnormals and exact cancellation.
    patterns = ([0x7bff] * COLS, [0x7bff, 0xfbff] * 64,
                [1, 0x8001] * 64)
    cases = 0
    for pattern in patterns:
        wf, wi = decode(struct.pack("<128H", *pattern))
        for xvalue in (8.0, -8.0, 2.0 ** -24, -(2.0 ** -24)):
            xf, xi = decode(struct.pack("<128e", *([xvalue] * COLS)))
            bf, bi = decode(struct.pack("<H", 0x7bff))
            z, scale = oracle(wi, bi, xi)
            validate(serial(wf, bf, xf), z, scale)
            cases += 1
    for bad in (float("nan"), float("inf"), 1.0):
        try:
            validate([bad], [0], [0])
        except ValueError:
            continue
        raise ValueError("invalid output accepted")
    return {"finite_binary16_patterns_checked": finite,
            "boundary_affine_cases": cases, "invalid_outputs_rejected": 3}


def run(source):
    arrays = {}
    for name, (length, digest) in FILES.items():
        path = source / name
        require(path.stat().st_size == length, "source byte length mismatch")
        raw = path.read_bytes()
        require(sha256(raw).hexdigest() == digest, "source SHA-256 mismatch")
        arrays[name] = decode(raw)
    wf, wi = arrays["weight.f16"]
    bf, bi = arrays["bias.f16"]
    blas = blas_control(wf, bf)
    rows = []
    for name, raw, (xf, xi) in inputs():
        exact, scales = oracle(wi, bi, xi)
        outputs = {"serial-f32-diagnostic": serial(wf, bf, xf),
                   "accelerate-sgemv": blas(xf)}
        for values in outputs.values():
            validate(values, exact, scales)
        repeated = blas(xf)
        validate(repeated, exact, scales)
        require(repeated == outputs["accelerate-sgemv"], "repeat/reset mismatch")
        rows.append({"input": name, "input_sha256": sha256(raw).hexdigest(),
                     "exact_scaled_integer_sha256": sha256(json.dumps(exact).encode()).hexdigest(),
                     "output_sha256": {k: sha256(struct.pack("<512f", *v)).hexdigest()
                                       for k, v in outputs.items()}})
    return {"schema": "raveil.immutable-affine-commissioning/v1",
            "evidence_class": "host-functional", "revision": REVISION,
            "source_sha256": {k: v[1] for k, v in FILES.items()},
            "probe_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "environment": {"platform": platform.platform(), "python": platform.python_version(),
                            "library": LIBRARY, "blas_symbol": "cblas_sgemv",
                            "thread_policy": "library default; not a timing run",
                            "library_binary_hash": None},
            "self_test": self_test(), "functional_inputs": len(rows),
            "validated_output_components": len(rows) * ROWS * 3,
            "repeat_bias_reset_checked": True, "gamma": [GAMMA_N, GAMMA_D],
            "cases": rows, "raw_parameter_bytes": sum(v[0] for v in FILES.values()),
            "widened_parameter_bytes": (ROWS * COLS + ROWS) * 4,
            "source_input_bytes": COLS * 2, "runtime_input_bytes": COLS * 4,
            "output_bytes": ROWS * 4, "per_invocation_bias_copy_bytes": ROWS * 4,
            "timing_measured": False, "holdouts_evaluated": False,
            "fixed_parameter_compiler_control_implemented": False,
            "whole_model_equivalence_claimed": False, "hardware_advantage_established": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.source_dir is not None:
        result = run(args.source_dir)
    elif args.self_test:
        result = self_test()
    else:
        parser.error("provide --source-dir or --self-test")
    print(json.dumps(result, indent=2, sort_keys=True))
