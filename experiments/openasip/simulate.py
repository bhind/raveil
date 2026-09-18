#!/usr/bin/env python3
"""Run the three sealed T-0191 inputs through a hardened OpenASIP boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import shutil
import subprocess
import tempfile
import time
from typing import Callable
import uuid

import lifecycle
import oracle
from verify_manifest import ROOT, load_manifest, validate

IMAGE = "raveil-openasip:toolchain"
DOCKER = "/usr/local/bin/docker"
RECEIPT = ROOT / "toolchain-receipt.json"
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
SOURCE_RECEIPT = ROOT / "source-receipt.json"
ADF = "/opt/openasip/share/openasip/data/mach/minimal.adf"
MARKERS = {
    "result_hex": re.compile(r"^RAVEIL_RESULT=(0x[0-9A-Fa-f]{8})$"),
    "cycles": re.compile(r"^RAVEIL_CYCLES=([0-9]+)$"),
    "register_reads": re.compile(r"^RAVEIL_REGISTER_READS=([0-9]+(?:\.0)?)$"),
    "register_writes": re.compile(r"^RAVEIL_REGISTER_WRITES=([0-9]+(?:\.0)?)$"),
}
SIM_SCRIPT = (
    "run; set r [x /n 1 /u w result]; set c [info proc cycles]; "
    "set rr [info stats register_reads]; set rw [info stats register_writes]; "
    'puts "RAVEIL_RESULT=$r"; puts "RAVEIL_CYCLES=$c"; '
    'puts "RAVEIL_REGISTER_READS=$rr"; '
    'puts "RAVEIL_REGISTER_WRITES=$rw"; puts RAVEIL_DONE; quit;'
)
LOAD_SCRIPT = "puts RAVEIL_LOADED; quit;"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_log(path: Path, value: str) -> str:
    path.write_text(value, encoding="utf-8")
    return sha256(path)


ExternalProcessCancelled = lifecycle.ExternalProcessCancelled
ExternalProcessCleanupError = lifecycle.ExternalProcessCleanupError
POLL_INTERVAL_SECONDS = 0.05
STOP_TIMEOUT_SECONDS = 2
CLEANUP_TIMEOUT_SECONDS = 5
CREATE_TIMEOUT_SECONDS = 5


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGTERM)
    else:
        process.terminate()
    try:
        process.communicate(timeout=STOP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.communicate(timeout=STOP_TIMEOUT_SECONDS)


def _check_cancel(cancel_requested: Callable[[], bool] | None) -> bool:
    if cancel_requested is None:
        return False
    try:
        return bool(cancel_requested())
    except Exception as error:
        raise ExternalProcessCleanupError("cancellation probe failed") from error


def run(
    argv: list[str], *, timeout: int = 300,
    cancel_requested: Callable[[], bool] | None = None,
) -> subprocess.CompletedProcess[str]:
    if cancel_requested is None:
        return subprocess.run(
            argv, check=True, capture_output=True, text=True, timeout=timeout
        )
    process = subprocess.Popen(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True,
    )
    deadline = time.monotonic() + timeout
    while True:
        try:
            cancelled = _check_cancel(cancel_requested)
        except ExternalProcessCleanupError:
            try:
                _stop_process(process)
            except Exception as error:
                raise ExternalProcessCleanupError(
                    "cancellation probe and client cleanup both failed"
                ) from error
            raise
        if cancelled:
            try:
                _stop_process(process)
            except Exception as error:
                raise ExternalProcessCleanupError(
                    "external client cleanup is uncertain"
                ) from error
            raise ExternalProcessCancelled("external process cancelled and reaped")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            try:
                _stop_process(process)
            except Exception as error:
                raise ExternalProcessCleanupError(
                    "external client timeout cleanup is uncertain"
                ) from error
            raise subprocess.TimeoutExpired(argv, timeout)
        try:
            stdout, stderr = process.communicate(
                timeout=min(POLL_INTERVAL_SECONDS, remaining)
            )
            break
        except subprocess.TimeoutExpired:
            continue
    completed = subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
    completed.check_returncode()
    return completed


def _owned_container(value: str) -> str:
    container_id = value.strip()
    if not re.fullmatch(r"[0-9a-f]{64}", container_id):
        raise ExternalProcessCleanupError("owned container ID is invalid")
    return container_id


def _cleanup_container(container_id: str) -> None:
    """Stop and remove exactly our created container, or report uncertainty."""
    try:
        state = subprocess.run(
            [DOCKER, "inspect", "--format", "{{.State.Running}}", container_id],
            capture_output=True, text=True, timeout=CLEANUP_TIMEOUT_SECONDS,
        )
        if state.returncode != 0 or state.stdout.strip() not in {"true", "false"}:
            raise ExternalProcessCleanupError("owned container state is unknown")
        if state.stdout.strip() == "true":
            stopped = subprocess.run(
                [DOCKER, "stop", "--time", str(STOP_TIMEOUT_SECONDS), container_id],
                capture_output=True, text=True, timeout=CLEANUP_TIMEOUT_SECONDS,
            )
            if stopped.returncode != 0:
                raise ExternalProcessCleanupError("owned container did not stop")
            state = subprocess.run(
                [DOCKER, "inspect", "--format", "{{.State.Running}}", container_id],
                capture_output=True, text=True, timeout=CLEANUP_TIMEOUT_SECONDS,
            )
            if state.returncode != 0 or state.stdout.strip() != "false":
                raise ExternalProcessCleanupError("owned container stop is unverified")
        removed = subprocess.run(
            [DOCKER, "rm", container_id], capture_output=True, text=True,
            timeout=CLEANUP_TIMEOUT_SECONDS,
        )
        if removed.returncode != 0:
            raise ExternalProcessCleanupError("owned container removal is unverified")
    except subprocess.TimeoutExpired as error:
        raise ExternalProcessCleanupError("owned container cleanup timed out") from error


def run_container(
    argv: list[str], *, timeout: int = 300,
    cancel_requested: Callable[[], bool] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Create/start/clean up one exact Docker container; never touch others."""
    if len(argv) < 3 or argv[0] != DOCKER or argv[1] != "run":
        raise ValueError("expected a Docker run command")
    name = f"raveil-t0191-{uuid.uuid4().hex}"
    create_argv = [DOCKER, "create", "--name", name, "--label", "raveil.task=T-0191"]
    create_argv += [arg for arg in argv[2:] if arg != "--rm"]
    try:
        # Docker create is a short, non-cancellable ownership handshake.  Once
        # named, every later operation uses this exact name/returned ID only.
        created = run(create_argv, timeout=min(timeout, CREATE_TIMEOUT_SECONDS))
    except Exception as error:
        # A failed create may be a name conflict or a lost daemon response.
        # Without a returned ID we cannot prove ownership, so do not stop or
        # delete by name. Preserve the uncertainty and deny publication.
        raise ExternalProcessCleanupError(
            "Docker create ownership is uncertain"
        ) from error
    try:
        container_id = _owned_container(created.stdout)
    except ExternalProcessCleanupError as error:
        raise ExternalProcessCleanupError(
            "Docker create identity and cleanup are uncertain"
        ) from error
    try:
        started = run(
            [DOCKER, "start", "--attach", container_id], timeout=timeout,
            cancel_requested=cancel_requested,
        )
        state = subprocess.run(
            [DOCKER, "inspect", "--format", "{{.State.Running}} {{.State.ExitCode}}", container_id],
            capture_output=True, text=True, timeout=CLEANUP_TIMEOUT_SECONDS,
        )
        match = re.fullmatch(r"false ([0-9]+)", state.stdout.strip())
        if state.returncode != 0 or match is None:
            raise ExternalProcessCleanupError("owned container completion is unverified")
        if int(match.group(1)) != 0:
            raise subprocess.CalledProcessError(int(match.group(1)), started.args, started.stdout, started.stderr)
        return started
    finally:
        _cleanup_container(container_id)


def image_id(*, cancel_requested: Callable[[], bool] | None = None) -> str:
    value = run(
        [DOCKER, "image", "inspect", "--format", "{{.Id}}", IMAGE],
        cancel_requested=cancel_requested,
    ).stdout.strip()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise RuntimeError("toolchain image identity is not exact")
    return value


def installed_adf_sha256(*, cancel_requested: Callable[[], bool] | None = None) -> str:
    value = run_container([
        DOCKER, "run", "--rm", "--platform", "linux/amd64",
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true", "--pids-limit", "32",
        "--memory", "128m", "--cpus", "1", "--user", "65534:65534",
        IMAGE, "/usr/bin/sha256sum", ADF,
    ], cancel_requested=cancel_requested).stdout.split()
    if len(value) != 2 or not re.fullmatch(r"[0-9a-f]{64}", value[0]):
        raise RuntimeError("installed ADF hash envelope is invalid")
    return value[0]


def validate_toolchain(
    manifest: dict[str, object], identities: dict[str, object], *,
    cancel_requested: Callable[[], bool] | None = None,
) -> str:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    before = image_id(cancel_requested=cancel_requested)
    program_hashes = identities.get("program_sha256")
    if not isinstance(program_hashes, dict):
        raise RuntimeError("program identity receipt is incomplete")
    if (
        receipt.get("schema") != "raveil.t0191-openasip-toolchain/v1"
        or receipt.get("task") != "T-0191"
        or receipt.get("local_image_id") != before
        or receipt.get("toolchain_built") is not True
        or receipt.get("build_exit") != 0
        or receipt.get("dockerfile_sha256") != sha256(DOCKERFILE)
        or receipt.get("dockerignore_sha256") != sha256(DOCKERIGNORE)
        or receipt.get("input_manifest_sha256") != identities["manifest_sha256"]
        or receipt.get("plugin_prewarm_source_sha256")
        != program_hashes.get("programs/reduction.c")
        or receipt.get("source_receipt_sha256") != sha256(SOURCE_RECEIPT)
        or receipt.get("openasip_revision") != manifest["upstream"]["revision"]
        or receipt.get("llvm_revision") != manifest["llvm"]["revision"]
        or receipt.get("image_platform") != "linux/amd64"
        or receipt.get("ttasim_version") != "2.2-r1"
        or receipt.get("publication") is not False
    ):
        raise RuntimeError("toolchain receipt does not authorize this exact local image")
    if installed_adf_sha256(cancel_requested=cancel_requested) != manifest["machine"]["sha256"]:
        raise RuntimeError("installed ADF identity does not match the manifest")
    return before


def common_container_args(
    *, work: Path, source: Path | None, readonly_work: bool = False
) -> list[str]:
    args = [
        DOCKER, "run", "--rm", "--platform", "linux/amd64",
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true", "--pids-limit", "128",
        "--memory", "1g", "--cpus", "1", "--user", "65534:65534",
        "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=268435456",
        "--workdir", "/tmp", "--env", "HOME=/opt/openasip-home",
        "--mount", (
            f"type=bind,src={work},dst=/evidence,readonly"
            if readonly_work else f"type=bind,src={work},dst=/evidence"
        ),
    ]
    if source is not None:
        args.extend(["--mount", f"type=bind,src={source},dst=/input/program.c,readonly"])
    return args + [IMAGE]


def parse_simulator_output(stdout: str) -> dict[str, int]:
    lines = stdout.splitlines()
    if lines.count("RAVEIL_DONE") != 1 or lines[-1:] != ["RAVEIL_DONE"]:
        raise RuntimeError("simulator completion marker is absent, duplicate, or not final")
    parsed: dict[str, int] = {}
    for key, pattern in MARKERS.items():
        matches = [match.group(1) for line in lines if (match := pattern.fullmatch(line))]
        if len(matches) != 1:
            raise RuntimeError(f"simulator marker is absent or duplicate: {key}")
        if key == "result_hex":
            parsed[key] = int(matches[0], 16)
        else:
            parsed[key] = int(float(matches[0]))
    return parsed


def simulate(
    *, evidence_dir: Path | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> dict[str, object]:
    identities = validate(require_container=True)
    manifest = load_manifest()
    if any(os.environ.get(name) for name in ("DOCKER_HOST", "DOCKER_CONFIG", "DOCKER_CONTEXT")):
        raise RuntimeError("ambient Docker routing is not permitted")
    before = validate_toolchain(
        manifest, identities, cancel_requested=cancel_requested
    )
    expected = {
        "neighborhood": oracle.neighborhood(),
        "elementwise": oracle.elementwise(),
        "reduction": oracle.reduction(),
    }
    observed: dict[str, object] = {}
    if evidence_dir is not None:
        evidence_dir.mkdir(parents=False, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="raveil-t0191-sim-") as value:
        work = Path(value)
        os.chmod(work, 0o777)
        for relative in manifest["programs"]:
            source = (ROOT / relative).resolve(strict=True)
            name = source.stem
            staged_source = work / f"{name}.c"
            shutil.copyfile(source, staged_source)
            staged_source.chmod(0o444)
            staged_digest = sha256(staged_source)
            if staged_digest != identities["program_sha256"][relative]:
                raise RuntimeError(f"staged source identity mismatch: {name}")
            tpef = work / f"{name}.tpef"
            compile_argv = common_container_args(work=work, source=staged_source) + [
                "/opt/openasip/bin/oacc", "-O3", "-a", ADF,
                "-o", f"/evidence/{name}.tpef", "-k", "main,result",
                "/input/program.c",
            ]
            started = time.monotonic_ns()
            compiled = run_container(compile_argv, cancel_requested=cancel_requested)
            compile_ns = time.monotonic_ns() - started
            if not tpef.is_file() or tpef.is_symlink():
                raise RuntimeError(f"compiler output envelope is invalid: {name}")
            disasm_argv = common_container_args(
                work=work, source=None, readonly_work=True
            ) + [
                "/opt/openasip/bin/tcedisasm", "--flat", "--stdout", ADF,
                f"/evidence/{name}.tpef",
            ]
            disassembled = run_container(disasm_argv, cancel_requested=cancel_requested)
            if not disassembled.stdout.strip():
                raise RuntimeError(f"empty TPEF static witness: {name}")
            load_count = disassembled.stdout.count("lsu.in1t.ld32")
            minimum_loads = {"neighborhood": 20, "elementwise": 8, "reduction": 12}
            if load_count < minimum_loads[name]:
                raise RuntimeError(f"TPEF lacks the required load witness: {name}")
            multiply_witness = "__mulsi3" in disassembled.stdout
            if name == "elementwise" and not multiply_witness:
                raise RuntimeError("elementwise TPEF lacks a multiply witness")
            load_argv = common_container_args(
                work=work, source=None, readonly_work=True
            ) + [
                "/opt/openasip/bin/ttasim", "--no-debugmode", "-a", ADF,
                "-p", f"/evidence/{name}.tpef", "-e", LOAD_SCRIPT,
            ]
            load_started = time.monotonic_ns()
            loaded = run_container(load_argv, cancel_requested=cancel_requested)
            load_ns = time.monotonic_ns() - load_started
            if loaded.stdout.splitlines()[-1:] != ["RAVEIL_LOADED"]:
                raise RuntimeError(f"program load probe did not complete: {name}")
            sim_argv = common_container_args(
                work=work, source=None, readonly_work=True
            )
            sim_argv += [
                "/opt/openasip/bin/ttasim", "--no-debugmode", "-a", ADF,
                "-p", f"/evidence/{name}.tpef", "-e", SIM_SCRIPT,
            ]
            simulated = run_container(sim_argv, cancel_requested=cancel_requested)
            fields = parse_simulator_output(simulated.stdout)
            if fields["result_hex"] != expected[name]:
                raise RuntimeError(f"simulator oracle mismatch: {name}")
            record: dict[str, object] = {
                "source_sha256": identities["program_sha256"][relative],
                "tpef_sha256": sha256(tpef),
                "staged_source_sha256": staged_digest,
                "staged_source_bytes": staged_source.stat().st_size,
                "tpef_bytes": tpef.stat().st_size,
                "host_integration_duration_ns_diagnostic_only": compile_ns,
                "result_u32": fields["result_hex"],
                "ttasim_run_cycle_counter_n1": fields["cycles"],
                "ttasim_register_reads_statistic_n1": fields["register_reads"],
                "ttasim_register_writes_statistic_n1": fields["register_writes"],
                "compile_argv": compile_argv,
                "compile_exit_code": compiled.returncode,
                "disasm_argv": disasm_argv,
                "disasm_exit_code": disassembled.returncode,
                "load_probe_argv": load_argv,
                "load_probe_exit_code": loaded.returncode,
                "host_container_adf_tpef_load_duration_ns_diagnostic_only": load_ns,
                "simulator_argv": sim_argv,
                "simulator_exit_code": simulated.returncode,
                "static_ld32_witness_count": load_count,
                "static_mulsi3_witness": multiply_witness,
            }
            if evidence_dir is not None:
                program_dir = evidence_dir / name
                program_dir.mkdir()
                shutil.copy2(tpef, program_dir / tpef.name)
                record["compile_stdout_sha256"] = write_log(
                    program_dir / "compile.stdout", compiled.stdout
                )
                record["compile_stderr_sha256"] = write_log(
                    program_dir / "compile.stderr", compiled.stderr
                )
                record["disassembly_sha256"] = write_log(
                    program_dir / "tpef.disassembly", disassembled.stdout
                )
                record["load_probe_stdout_sha256"] = write_log(
                    program_dir / "load-probe.stdout", loaded.stdout
                )
                record["load_probe_stderr_sha256"] = write_log(
                    program_dir / "load-probe.stderr", loaded.stderr
                )
                record["simulator_stdout_sha256"] = write_log(
                    program_dir / "simulator.stdout", simulated.stdout
                )
                record["simulator_stderr_sha256"] = write_log(
                    program_dir / "simulator.stderr", simulated.stderr
                )
            observed[name] = record
    after = image_id(cancel_requested=cancel_requested)
    if after != before:
        raise RuntimeError("toolchain image identity changed during execution")
    result = {
        "schema": "raveil.t0191-openasip-run/v1", "task": "T-0191",
        "evidence_class": "host-functional-external-simulator",
        "manifest_sha256": identities["manifest_sha256"],
        "local_image_id": before, "machine_sha256": manifest["machine"]["sha256"],
        "implementation_sha256": {
            "simulate.py": sha256(Path(__file__)),
            "verify_manifest.py": sha256(ROOT / "verify_manifest.py"),
            "lifecycle.py": sha256(ROOT / "lifecycle.py"),
            "run_authorized.py": sha256(ROOT / "run_authorized.py"),
        },
        "programs": observed, "published": False,
        "host_platform": platform.platform(),
        "non_claims": [
            "no-performance-comparison", "no-memory-or-cache-traffic-claim",
            "no-ppa-claim", "no-generated-rtl-evidence", "no-adoption",
        ],
    }
    if evidence_dir is not None:
        (evidence_dir / "run-receipt.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(simulate(evidence_dir=args.evidence_dir), sort_keys=True))


if __name__ == "__main__":
    main()
