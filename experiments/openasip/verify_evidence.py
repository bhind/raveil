#!/usr/bin/env python3
"""Verify complete private T-0191 run or generated-RTL evidence directories."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from generate_rtl import EXPECTED_FILES, normalized_digest
from lifecycle import EXPECTED
from verify_manifest import MANIFEST, ROOT, load_manifest


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"evidence file is not exact: {path.name}")


def read_json(path: Path) -> dict[str, Any]:
    regular(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("evidence receipt is not an object")
    return value


def verify_run(root: Path) -> dict[str, Any]:
    private = read_json(root / "run-receipt.json")
    authorized = read_json(root / "authorized-receipt.json")
    manifest = load_manifest()
    toolchain = read_json(ROOT / "toolchain-receipt.json")
    if not (
        private.get("schema") == "raveil.t0191-openasip-run/v1"
        and private.get("task") == "T-0191"
        and private.get("evidence_class") == "host-functional-external-simulator"
        and private.get("manifest_sha256") == digest(MANIFEST)
        and private.get("machine_sha256") == manifest["machine"]["sha256"]
        and private.get("local_image_id") == toolchain["local_image_id"]
        and private.get("published") is False
    ):
        raise ValueError("candidate receipt crossed the publication boundary")
    expected_authorized = dict(private)
    expected_authorized.update({
        "backend": "openasip-ttasim", "status": "accepted",
        "publication_authority": "raveil", "published": True,
    })
    if authorized != expected_authorized:
        raise ValueError("authorized receipt is incomplete")
    implementation = private.get("implementation_sha256")
    expected_implementation = {
        name: digest(ROOT / name)
        for name in ("simulate.py", "verify_manifest.py", "lifecycle.py", "run_authorized.py")
    }
    if implementation != expected_implementation:
        raise ValueError("run implementation identity mismatch")
    programs = private.get("programs")
    if not isinstance(programs, dict) or set(programs) != set(EXPECTED):
        raise ValueError("program receipt set is not exact")
    expected_files = {"run-receipt.json", "authorized-receipt.json"}
    log_fields = {
        "compile.stdout": "compile_stdout_sha256",
        "compile.stderr": "compile_stderr_sha256",
        "tpef.disassembly": "disassembly_sha256",
        "load-probe.stdout": "load_probe_stdout_sha256",
        "load-probe.stderr": "load_probe_stderr_sha256",
        "simulator.stdout": "simulator_stdout_sha256",
        "simulator.stderr": "simulator_stderr_sha256",
    }
    for name, expected in EXPECTED.items():
        record = programs[name]
        relative = next(item for item in manifest["programs"] if Path(item).stem == name)
        source_receipt = manifest["program_receipts"][relative]
        if (
            record.get("result_u32") != expected
            or record.get("source_sha256") != source_receipt["sha256"]
            or record.get("staged_source_sha256") != source_receipt["sha256"]
            or record.get("staged_source_bytes") != source_receipt["bytes"]
            or any(record.get(field) != 0 for field in (
                "compile_exit_code", "disasm_exit_code", "load_probe_exit_code",
                "simulator_exit_code",
            ))
        ):
            raise ValueError(f"oracle mismatch: {name}")
        directory = root / name
        tpef = directory / f"{name}.tpef"
        regular(tpef)
        if digest(tpef) != record.get("tpef_sha256") or tpef.stat().st_size != record.get("tpef_bytes"):
            raise ValueError(f"TPEF identity mismatch: {name}")
        expected_files.add(f"{name}/{name}.tpef")
        for filename, field in log_fields.items():
            path = directory / filename
            regular(path)
            if digest(path) != record.get(field):
                raise ValueError(f"raw log mismatch: {name}/{filename}")
            expected_files.add(f"{name}/{filename}")
    actual_files = {
        str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()
    }
    if actual_files != expected_files:
        raise ValueError("run evidence file set is not exact")
    return {
        "kind": "run", "private_receipt_sha256": digest(root / "run-receipt.json"),
        "authorized_receipt_sha256": digest(root / "authorized-receipt.json"),
        "files": len(actual_files), "verified": True,
    }


def verify_rtl(root: Path) -> dict[str, Any]:
    receipt = read_json(root / "rtl-receipt.json")
    manifest = load_manifest()
    toolchain = read_json(ROOT / "toolchain-receipt.json")
    if not (
        receipt.get("schema") == "raveil.t0191-openasip-rtl/v1"
        and receipt.get("task") == "T-0191"
        and receipt.get("evidence_class") == "host-functional-generated-rtl"
        and receipt.get("machine_sha256") == manifest["machine"]["sha256"]
        and receipt.get("local_image_id") == toolchain["local_image_id"]
        and receipt.get("published") is False
    ):
        raise ValueError("RTL evidence crossed the publication boundary")
    files = receipt.get("files")
    if not isinstance(files, dict) or set(files) != EXPECTED_FILES:
        raise ValueError("RTL receipt file set is not exact")
    for relative, record in files.items():
        path = root / "rtl" / relative
        regular(path)
        if (
            digest(path) != record.get("sha256")
            or normalized_digest(path) != record.get("normalized_sha256")
            or path.stat().st_size != record.get("bytes")
        ):
            raise ValueError(f"RTL identity mismatch: {relative}")
    for filename, field in (
        ("generator.stdout", "generator_stdout_sha256"),
        ("generator.stderr", "generator_stderr_sha256"),
    ):
        path = root / filename
        regular(path)
        if digest(path) != receipt.get(field):
            raise ValueError(f"generator log mismatch: {filename}")
    expected = {
        "rtl-receipt.json", "generator.stdout", "generator.stderr",
        *(f"rtl/{relative}" for relative in EXPECTED_FILES),
    }
    actual = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError("RTL evidence file set is not exact")
    tree = hashlib.sha256(
        json.dumps(
            {name: files[name]["normalized_sha256"] for name in sorted(files)},
            separators=(",", ":"), sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    if tree != receipt.get("normalized_tree_sha256"):
        raise ValueError("normalized RTL tree identity mismatch")
    return {
        "kind": "rtl", "receipt_sha256": digest(root / "rtl-receipt.json"),
        "normalized_tree_sha256": receipt.get("normalized_tree_sha256"),
        "files": len(files) + 3, "verified": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("run", "rtl"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = verify_run(args.directory) if args.kind == "run" else verify_rtl(args.directory)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
