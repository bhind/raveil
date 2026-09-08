#!/usr/bin/env python3
"""Generate and seal one fixed-ADF OpenASIP VHDL tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from simulate import ADF, DOCKER, IMAGE, validate_toolchain
from verify_manifest import load_manifest, validate

EXPECTED_FILES = {
    "gcu_ic/decoder.vhdl", "gcu_ic/ic.vhdl", "gcu_ic/ifetch.vhdl",
    "gcu_ic/input_mux_1.vhdl", "gcu_ic/output_socket_1_1.vhdl",
    "vhdl/lsu_le.vhdl", "vhdl/rf_bool.vhd", "vhdl/rf_rf.vhd",
    "vhdl/tta0.vhdl", "vhdl/tta0_params_pkg.vhdl",
}
COPY_DIAGNOSTIC = (
    "Unable to copy file /evidence/rtl/vhdl/lsu_le.vhdl:Unable to copy "
    "'/opt/openasip/share/openasip/hdb/vhdl/fu/lsu_le.vhdl' to "
    "'/evidence/rtl/vhdl/lsu_le.vhdl'"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_digest(path: Path) -> str:
    data = path.read_bytes()
    if path.name in {"rf_bool.vhd", "rf_rf.vhd"}:
        data = re.sub(br"^-- Generated on .+$", b"-- Generated on <normalized>", data, flags=re.MULTILINE)
    return hashlib.sha256(data).hexdigest()


def container_prefix(output: Path) -> list[str]:
    return [
        DOCKER, "run", "--rm", "--platform", "linux/amd64",
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true", "--pids-limit", "128",
        "--memory", "1g", "--cpus", "1", "--user", "65534:65534", "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=268435456", "--workdir", "/tmp",
        "--env", "HOME=/opt/openasip-home", "--mount",
        f"type=bind,src={output},dst=/evidence", IMAGE,
    ]


def generate(output: Path) -> dict[str, object]:
    if any(os.environ.get(name) for name in ("DOCKER_HOST", "DOCKER_CONFIG", "DOCKER_CONTEXT")):
        raise RuntimeError("ambient Docker routing is not permitted")
    output.mkdir(parents=False, exist_ok=False)
    output.chmod(0o777)
    manifest = load_manifest()
    identities = validate(require_container=True)
    exact_image = validate_toolchain(manifest, identities)
    started = time.monotonic_ns()
    command = container_prefix(output) + [
        "/opt/openasip/bin/generateprocessor", "-l", "vhdl", "-o",
        "/evidence/rtl", ADF,
    ]
    result = subprocess.run(
        command, check=True, capture_output=True, text=True, timeout=300
    )
    (output / "generator.stdout").write_text(result.stdout, encoding="utf-8")
    (output / "generator.stderr").write_text(result.stderr, encoding="utf-8")
    rtl = output / "rtl"
    lsu = rtl / "vhdl" / "lsu_le.vhdl"
    repaired = False
    diagnostic = result.stdout.strip() or result.stderr.strip()
    if diagnostic == COPY_DIAGNOSTIC and lsu.is_file() and lsu.stat().st_size == 0:
        lsu.chmod(0o666)
        repair = container_prefix(output) + [
            "/bin/cp", "-f",
            "/opt/openasip/share/openasip/hdb/vhdl/fu/lsu_le.vhdl",
            "/evidence/rtl/vhdl/lsu_le.vhdl",
        ]
        subprocess.run(repair, check=True, capture_output=True, text=True, timeout=30)
        repaired = True
    elif result.stdout or result.stderr:
        raise RuntimeError("unexpected generator diagnostic")
    files = {str(path.relative_to(rtl)) for path in rtl.rglob("*") if path.is_file()}
    if files != EXPECTED_FILES:
        raise RuntimeError("generated RTL file set is not exact")
    receipts = {
        relative: {
            "bytes": (rtl / relative).stat().st_size,
            "sha256": digest(rtl / relative),
            "normalized_sha256": normalized_digest(rtl / relative),
        }
        for relative in sorted(files)
    }
    if any(item["bytes"] <= 0 for item in receipts.values()):
        raise RuntimeError("generated RTL contains an empty file")
    tree_sha256 = hashlib.sha256(
        json.dumps(
            {name: value["normalized_sha256"] for name, value in receipts.items()},
            separators=(",", ":"), sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    receipt = {
        "schema": "raveil.t0191-openasip-rtl/v1", "task": "T-0191",
        "evidence_class": "host-functional-generated-rtl",
        "local_image_id": exact_image, "machine_sha256": manifest["machine"]["sha256"],
        "generator": "OpenASIP generateprocessor 2.2-r1",
        "generator_argv": ["generateprocessor", "-l", "vhdl", "-o", "<rtl>", "<frozen-adf>"],
        "host_integration_duration_ns_diagnostic_only": time.monotonic_ns() - started,
        "docker_desktop_bind_copy_repaired": repaired,
        "generator_stdout_sha256": digest(output / "generator.stdout"),
        "generator_stderr_sha256": digest(output / "generator.stderr"),
        "files": receipts, "normalized_tree_sha256": tree_sha256,
        "known_nondeterminism": ["RF VHDL generated-on comment"],
        "published": False,
    }
    (output / "rtl-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(generate(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
