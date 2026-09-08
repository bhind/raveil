#!/usr/bin/env python3
"""Run the three Raveil-owned program inputs on the native CPU oracle path."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import oracle
from verify_manifest import load_manifest

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "host_runner.c"
EXPECTED = {
    "elementwise": oracle.elementwise(),
    "neighborhood": oracle.neighborhood(),
    "reduction": oracle.reduction(),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict[str, object]:
    compiler = shutil.which("cc")
    if compiler is None:
        raise RuntimeError("native C compiler is unavailable")
    manifest = load_manifest()
    observed: dict[str, dict[str, object]] = {}
    with tempfile.TemporaryDirectory(prefix="raveil-t0191-host-") as value:
        build = Path(value)
        for relative in manifest["programs"]:
            source = ROOT / relative
            name = source.stem
            program_object = build / f"{name}.o"
            runner_object = build / "host_runner.o"
            executable = build / name
            subprocess.run(
                [compiler, "-std=c11", "-O2", "-Dmain=t0191_program_main",
                 "-c", str(source), "-o", str(program_object)],
                check=True, timeout=30,
            )
            subprocess.run(
                [compiler, "-std=c11", "-O2", "-c", str(RUNNER),
                 "-o", str(runner_object)],
                check=True, timeout=30,
            )
            subprocess.run(
                [compiler, str(program_object), str(runner_object),
                 "-o", str(executable)],
                check=True, timeout=30,
            )
            result = subprocess.run(
                [str(executable)], check=True, timeout=30,
                capture_output=True, text=True,
            )
            word = int(result.stdout.strip())
            if word != EXPECTED[name]:
                raise RuntimeError(f"native oracle mismatch: {name}")
            observed[name] = {
                "expected_u32": EXPECTED[name],
                "observed_u32": word,
                "source_sha256": sha256(source),
            }
    return {
        "backend": "native-cpu",
        "programs": observed,
        "published": False,
        "status": "private-oracle-check",
    }


def main() -> None:
    print(json.dumps(run(), sort_keys=True))


if __name__ == "__main__":
    main()
