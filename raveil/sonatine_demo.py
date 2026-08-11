from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any


RESULT_SCHEMA = "raveil.sonatine-demo-result/v1"
EVIDENCE_CLASS = "qemu-emulation-correctness"
FRAME_VERSION = "RAVEIL-SONATINE-DEMO-V1"
FRAME_PREFIX = FRAME_VERSION + " "
MAX_FRAME_BYTES = 171
MAX_OUTPUT_BYTES = 64 * 1024
MAX_STDERR_BYTES = 16 * 1024
MAX_KERNEL_BYTES = 16 * 1024 * 1024
MAX_TIMEOUT_SECONDS = 60.0
MAX_COMMAND_COMPONENT_BYTES = 4096
MAX_COMMAND_BYTES = 8192
MAX_TOOL_VERSION_BYTES = 512
UINT64_MAX = (1 << 64) - 1
COMPLETED_CHECKSUM = "efc0623db432d01f"

# This is the complete fixed U-mode command transcript.  Kernel boot prose and
# other pre-shell diagnostics are deliberately not authority.
COMMAND_TRANSCRIPT = (
    "ls", "cat", "echo", "write", "stat", "jobs", "result", "run", "run",
    "jobs", "result", "cancel", "result", "run", "cancel", "jobs", "result",
    "cancel", "exit",
)
INPUT_TRANSCRIPT = "".join(f"{command}\r" for command in COMMAND_TRANSCRIPT).encode("ascii")
INPUT_SHA256 = hashlib.sha256(INPUT_TRANSCRIPT).hexdigest()

_QEMU_ARGS = (
    "-machine", "virt", "-cpu", "rv64", "-m", "128M", "-smp", "1",
    "-bios", "none", "-nographic", "-kernel", "<pinned-kernel-sha256>",
)

_COMMANDS = {"ls", "cat", "echo", "write", "stat", "jobs", "run", "cancel", "result", "invalid"}
_STATUSES = {
    "OK", "EMPTY", "BUSY", "TOO_LATE", "DENIED", "NO_SPACE", "INVALID_ORDER",
    "COMPLETED", "CANCELLED", "FAULT",
}
_STATES = {"EMPTY", "DISPATCHED", "CANCEL_REQUESTED", "COMPLETED", "CANCELLED", "FAULT"}
_FRAME_PATTERN = re.compile(
    r"^RAVEIL-SONATINE-DEMO-V1 "
    r"command=(ls|cat|echo|write|stat|jobs|run|cancel|result|invalid) "
    r"seq=(0|[1-9][0-9]*) "
    r"status=(OK|EMPTY|BUSY|TOO_LATE|DENIED|NO_SPACE|INVALID_ORDER|COMPLETED|CANCELLED|FAULT) "
    r"job=(0|[1-9][0-9]*) "
    r"state=(EMPTY|DISPATCHED|CANCEL_REQUESTED|COMPLETED|CANCELLED|FAULT) "
    r"semantic=([01]) checksum=([0-9a-f]{16})$"
)

# The Ciste-owned native slice is deterministic.  Binding each expected frame
# prevents a previous boot's valid-looking output from becoming this run's
# authority.
_EXPECTED = (
    ("ls", "OK", "EMPTY", 0),
    ("cat", "OK", "EMPTY", 0),
    ("echo", "OK", "EMPTY", 0),
    ("write", "OK", "EMPTY", 0),
    ("stat", "OK", "EMPTY", 0),
    ("jobs", "EMPTY", "EMPTY", 0),
    ("result", "EMPTY", "EMPTY", 0),
    ("run", "OK", "DISPATCHED", 1),
    ("run", "BUSY", "DISPATCHED", 1),
    ("jobs", "OK", "DISPATCHED", 1),
    ("result", "COMPLETED", "COMPLETED", 1),
    ("cancel", "TOO_LATE", "COMPLETED", 1),
    ("result", "COMPLETED", "COMPLETED", 1),
    ("run", "OK", "DISPATCHED", 2),
    ("cancel", "OK", "CANCEL_REQUESTED", 2),
    ("jobs", "OK", "CANCEL_REQUESTED", 2),
    ("result", "CANCELLED", "CANCELLED", 2),
    ("cancel", "TOO_LATE", "CANCELLED", 2),
)


@dataclass(frozen=True)
class DemoFrame:
    command: str
    sequence: int
    status: str
    job: int
    state: str
    semantic: int
    checksum: str

    def validate(self) -> None:
        if self.command not in _COMMANDS or self.status not in _STATUSES or self.state not in _STATES:
            raise ValueError("demo frame has an unknown enum value")
        if type(self.sequence) is not int or not 1 <= self.sequence <= UINT64_MAX:
            raise ValueError("demo frame sequence is outside uint64")
        if type(self.job) is not int or not 0 <= self.job <= UINT64_MAX:
            raise ValueError("demo frame job is outside uint64")
        if type(self.semantic) is not int or self.semantic not in {0, 1}:
            raise ValueError("demo frame semantic value is invalid")
        if not re.fullmatch(r"[0-9a-f]{16}", self.checksum):
            raise ValueError("demo frame checksum is invalid")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DemoFrame":
        if type(value) is not dict:
            raise ValueError("demo frame is not an object")
        if set(value) != set(cls.__dataclass_fields__):
            raise ValueError("demo frame fields are not exact")
        frame = cls(**value)
        frame.validate()
        return frame


@dataclass(frozen=True)
class SonatineDemoResult:
    repo_revision: str
    kernel_sha256: str
    command_transcript: tuple[str, ...]
    input_sha256: str
    frame_version: str
    qemu_command: tuple[str, ...]
    tool_versions: dict[str, str]
    frames: tuple[DemoFrame, ...]
    final_job_state: str
    semantic: int
    checksum: str
    exit_status: int
    schema: str = RESULT_SCHEMA
    evidence_class: str = EVIDENCE_CLASS

    def validate(self) -> None:
        if self.schema != RESULT_SCHEMA or self.evidence_class != EVIDENCE_CLASS:
            raise ValueError("demo result provenance is invalid")
        if any(type(value) is not str for value in (
            self.repo_revision, self.kernel_sha256, self.input_sha256, self.frame_version,
            self.final_job_state, self.checksum, self.schema, self.evidence_class,
        )):
            raise ValueError("demo result scalar types are invalid")
        if not re.fullmatch(r"[0-9a-f]{40,64}", self.repo_revision):
            raise ValueError("demo result repository revision is invalid")
        if not re.fullmatch(r"[0-9a-f]{64}", self.kernel_sha256):
            raise ValueError("demo result kernel hash is invalid")
        if self.command_transcript != COMMAND_TRANSCRIPT:
            raise ValueError("demo result transcript is not the fixed T-0092 transcript")
        if self.input_sha256 != INPUT_SHA256:
            raise ValueError("demo result input hash does not bind the fixed transcript")
        if self.frame_version != FRAME_VERSION:
            raise ValueError("demo result frame version is invalid")
        if (len(self.qemu_command) != len(_QEMU_ARGS) + 1 or
                self.qemu_command[1:] != _QEMU_ARGS or
                any(type(item) is not str or not item or len(item) > MAX_COMMAND_COMPONENT_BYTES
                    or "\x00" in item for item in self.qemu_command) or
                sum(len(item) for item in self.qemu_command) > MAX_COMMAND_BYTES):
            raise ValueError("demo result QEMU command is invalid")
        if set(self.tool_versions) != {"python", "qemu"} or any(
            type(value) is not str or not value or len(value) > MAX_TOOL_VERSION_BYTES
            for value in self.tool_versions.values()
        ):
            raise ValueError("demo result tool versions are invalid")
        if type(self.exit_status) is not int or self.exit_status != 0:
            raise ValueError("demo result exit status is invalid")
        if (self.final_job_state not in _STATES or type(self.semantic) is not int or
                self.semantic not in {0, 1}):
            raise ValueError("demo result final state is invalid")
        if not re.fullmatch(r"[0-9a-f]{16}", self.checksum):
            raise ValueError("demo result checksum is invalid")
        for frame in self.frames:
            frame.validate()
        _validate_expected_frames(self.frames)
        final = self.frames[-1]
        if (self.final_job_state, self.semantic, self.checksum) != (
            final.state, final.semantic, final.checksum
        ):
            raise ValueError("demo result final state does not bind the final frame")

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["command_transcript"] = list(self.command_transcript)
        value["qemu_command"] = list(self.qemu_command)
        value["frames"] = [frame.to_dict() for frame in self.frames]
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SonatineDemoResult":
        if type(value) is not dict:
            raise ValueError("demo result is not an object")
        if set(value) != set(cls.__dataclass_fields__):
            raise ValueError("demo result fields are not exact")
        copied = dict(value)
        for name in ("command_transcript", "qemu_command", "frames"):
            if type(copied[name]) is not list:
                raise ValueError(f"demo result {name} is not an array")
        if type(copied["tool_versions"]) is not dict:
            raise ValueError("demo result tool_versions is not an object")
        copied["command_transcript"] = tuple(copied["command_transcript"])
        copied["qemu_command"] = tuple(copied["qemu_command"])
        copied["frames"] = tuple(DemoFrame.from_dict(item) for item in copied["frames"])
        result = cls(**copied)
        result.validate()
        return result


def _parse_frame(line: str) -> DemoFrame:
    match = _FRAME_PATTERN.fullmatch(line)
    if match is None:
        raise ValueError("malformed Sonatine demo frame")
    command, sequence, status, job, state, semantic, checksum = match.groups()
    frame = DemoFrame(command, int(sequence), status, int(job), state, int(semantic), checksum)
    frame.validate()
    return frame


def parse_demo_frames(output: bytes) -> tuple[DemoFrame, ...]:
    if len(output) > MAX_OUTPUT_BYTES:
        raise ValueError("Sonatine demo output exceeds the bounded limit")
    frames: list[DemoFrame] = []
    prefix_bytes = FRAME_VERSION.encode("ascii")
    reserved_prefix = b"RAVEIL-SONATINE-DEMO-"
    for encoded_line in output.splitlines(keepends=True):
        if reserved_prefix not in encoded_line:
            continue
        if prefix_bytes not in encoded_line:
            raise ValueError("unknown Sonatine demo frame version")
        # The NS16550A console maps the kernel's logical LF to CRLF on the
        # serial stream.  Normalize only that final transport CR before
        # applying the frozen logical-line length and grammar.
        if encoded_line.endswith(b"\r\n"):
            canonical_line = encoded_line[:-2] + b"\n"
        elif encoded_line.endswith(b"\n"):
            canonical_line = encoded_line
        else:
            raise ValueError("Sonatine demo frame terminator is not canonical")
        if len(canonical_line) > MAX_FRAME_BYTES:
            raise ValueError("Sonatine demo frame exceeds the bounded limit")
        try:
            raw_line = canonical_line[:-1].decode("ascii")
        except UnicodeDecodeError as error:
            raise ValueError("Sonatine demo output is not ASCII") from error
        if not raw_line.startswith(FRAME_PREFIX):
            raise ValueError("malformed Sonatine demo frame placement")
        frames.append(_parse_frame(raw_line))
    _validate_expected_frames(tuple(frames))
    return tuple(frames)


def _validate_expected_frames(frames: tuple[DemoFrame, ...]) -> None:
    if len(frames) != len(_EXPECTED):
        raise ValueError("missing, duplicate, or late Sonatine demo frame")
    prior_sequence = 0
    first_job: int | None = None
    second_job: int | None = None
    for index, (frame, expected) in enumerate(zip(frames, _EXPECTED), start=1):
        command, status, state, job_group = expected
        if frame.sequence != index or frame.sequence <= prior_sequence:
            raise ValueError("stale or out-of-order Sonatine demo frame")
        prior_sequence = frame.sequence
        if (frame.command, frame.status, frame.state) != (command, status, state):
            raise ValueError("unexpected Sonatine demo frame command or state")
        if job_group == 0:
            if frame.job != 0 or frame.semantic != 0 or frame.checksum != "0" * 16:
                raise ValueError("empty Sonatine demo frame is not canonical")
            continue
        if job_group == 1:
            if first_job is None:
                if frame.job == 0:
                    raise ValueError("Sonatine demo dispatched frame lacks a job")
                first_job = frame.job
            elif frame.job != first_job:
                raise ValueError("stale Sonatine demo job binding")
        else:
            if second_job is None:
                if frame.job == 0 or first_job is None or frame.job != first_job + 1:
                    raise ValueError("Sonatine demo second job binding is invalid")
                second_job = frame.job
            elif frame.job != second_job:
                raise ValueError("stale Sonatine demo job binding")
        if frame.state == "COMPLETED":
            if frame.semantic != 1 or frame.checksum != COMPLETED_CHECKSUM:
                raise ValueError("completed Sonatine demo frame lacks semantic approval")
        elif frame.semantic != 0 or frame.checksum != "0" * 16:
            raise ValueError("non-completed Sonatine demo frame is not canonical")


def _validate_timeout(timeout_seconds: float) -> None:
    if (type(timeout_seconds) not in {int, float} or isinstance(timeout_seconds, bool) or
            not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= MAX_TIMEOUT_SECONDS):
        raise ValueError(
            f"Sonatine demo timeout must be finite and between 0 and {MAX_TIMEOUT_SECONDS:g} seconds"
        )


def _validate_command(command: tuple[str, ...]) -> None:
    if (not command or len(command) > 32 or
            any(type(item) is not str or not item or len(item) > MAX_COMMAND_COMPONENT_BYTES
                or "\x00" in item for item in command) or
            sum(len(item) for item in command) > MAX_COMMAND_BYTES):
        raise ValueError("Sonatine demo command is outside the bounded contract")


def _stop_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (AttributeError, ProcessLookupError, PermissionError):
        process.terminate()
    try:
        process.wait(timeout=1)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (AttributeError, ProcessLookupError, PermissionError):
        process.kill()
    process.wait()


def _run_bounded_process(
    command: tuple[str, ...], *, input_data: bytes | None, timeout_seconds: float,
) -> subprocess.CompletedProcess[bytes]:
    """Run one process with bounded stdout/stderr and a killable process group."""
    _validate_timeout(timeout_seconds)
    _validate_command(command)
    if input_data is not None and (type(input_data) is not bytes or len(input_data) > 4096):
        raise ValueError("Sonatine demo process input is outside the bounded contract")
    try:
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        )
    except OSError as error:
        raise RuntimeError(f"unable to launch {command[0]}") from error
    try:
        if input_data is not None:
            assert process.stdin is not None
            process.stdin.write(input_data)
            process.stdin.close()
        assert process.stdout is not None and process.stderr is not None
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        captured = {"stdout": bytearray(), "stderr": bytearray()}
        limits = {"stdout": MAX_OUTPUT_BYTES, "stderr": MAX_STDERR_BYTES}
        deadline = time.monotonic() + timeout_seconds
        try:
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    _stop_process_group(process)
                    raise RuntimeError("Sonatine demo process timed out")
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    target = captured[key.data]
                    target.extend(chunk)
                    if len(target) > limits[key.data]:
                        _stop_process_group(process)
                        raise RuntimeError(f"Sonatine demo process {key.data} exceeds the bounded limit")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _stop_process_group(process)
                raise RuntimeError("Sonatine demo process timed out")
            try:
                returncode = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired as error:
                _stop_process_group(process)
                raise RuntimeError("Sonatine demo process timed out") from error
        finally:
            selector.close()
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    stream.close()
    except BaseException:
        _stop_process_group(process)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()
        raise
    return subprocess.CompletedProcess(command, returncode, bytes(captured["stdout"]), bytes(captured["stderr"]))


def _command_version(
    command: tuple[str, ...], timeout_seconds: float, process_runner: Any,
) -> str:
    try:
        completed = process_runner(command, input_data=None, timeout_seconds=timeout_seconds)
    except (OSError, RuntimeError) as error:
        raise RuntimeError(f"unable to determine {' '.join(command)} version") from error
    if completed.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} version command exited {completed.returncode}")
    raw = completed.stdout if isinstance(completed.stdout, bytes) else str(completed.stdout).encode()
    try:
        version = raw.decode("utf-8").splitlines()[0]
    except (UnicodeDecodeError, IndexError) as error:
        raise RuntimeError(f"{' '.join(command)} returned no usable version") from error
    if not version or len(version) > MAX_TOOL_VERSION_BYTES:
        raise RuntimeError(f"{' '.join(command)} returned no usable version")
    return version


def _repository_revision(repository: Path, timeout_seconds: float, process_runner: Any) -> str:
    try:
        completed = process_runner(
            ("git", "-C", str(repository), "rev-parse", "HEAD"),
            input_data=None, timeout_seconds=timeout_seconds,
        )
    except (OSError, RuntimeError) as error:
        raise RuntimeError("unable to determine repository revision") from error
    raw = completed.stdout if isinstance(completed.stdout, bytes) else str(completed.stdout).encode()
    revision = raw.decode("ascii", "strict").strip()
    if completed.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", revision):
        raise RuntimeError("repository revision is unavailable or invalid")
    return revision


def _read_pinned_kernel(kernel: Path) -> bytes:
    try:
        before = os.stat(kernel, follow_symlinks=False)
    except OSError as error:
        raise ValueError("Sonatine demo kernel must be a non-symlink regular file") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValueError("Sonatine demo kernel must be a non-symlink regular file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(kernel, flags)
    except OSError as error:
        raise ValueError("Sonatine demo kernel must be a non-symlink regular file") from error
    try:
        info = os.fstat(descriptor)
        if ((info.st_dev, info.st_ino) != (before.st_dev, before.st_ino) or
                not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
                not 0 < info.st_size <= MAX_KERNEL_BYTES):
            raise ValueError("Sonatine demo kernel must be a bounded single-link regular file")
        chunks: list[bytes] = []
        total = 0
        while total <= MAX_KERNEL_BYTES:
            chunk = os.read(descriptor, min(65536, MAX_KERNEL_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        if total == 0 or total > MAX_KERNEL_BYTES:
            raise ValueError("Sonatine demo kernel exceeds the bounded limit")
        final_info = os.fstat(descriptor)
        if (not stat.S_ISREG(final_info.st_mode) or final_info.st_nlink != 1 or
                final_info.st_size != total):
            raise ValueError("Sonatine demo kernel changed while being pinned")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _open_output_target(output: Path) -> tuple[int, str]:
    absolute = output if output.is_absolute() else Path.cwd() / output
    parts = absolute.parts
    if not absolute.name or absolute.name in {".", ".."}:
        raise ValueError("Sonatine demo result target has no leaf name")
    descriptor = os.open("/", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        for component in parts[1:-1]:
            if component in {"", ".", ".."}:
                raise ValueError("Sonatine demo result parent is not canonical")
            before = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise ValueError("Sonatine demo result parent must not be a symlink")
            child = os.open(
                component,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=descriptor,
            )
            after = os.fstat(child)
            if (not stat.S_ISDIR(after.st_mode) or (before.st_dev, before.st_ino) !=
                    (after.st_dev, after.st_ino)):
                os.close(child)
                raise ValueError("Sonatine demo result parent changed while opening")
            os.close(descriptor)
            descriptor = child
        try:
            leaf_info = os.stat(absolute.name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return descriptor, absolute.name
        if stat.S_ISLNK(leaf_info.st_mode):
            raise FileExistsError("Sonatine demo result leaf symlink already exists")
        raise FileExistsError("Sonatine demo result target already exists")
    except BaseException:
        os.close(descriptor)
        raise


def _publish_result(parent_fd: int, leaf: str, encoded: str) -> None:
    temporary = f".{leaf}.{secrets.token_hex(16)}.tmp"
    descriptor = -1
    try:
        descriptor = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent_fd,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, leaf, src_dir_fd=parent_fd, dst_dir_fd=parent_fd,
                    follow_symlinks=False)
        except OSError as error:
            raise RuntimeError("Sonatine demo result could not be atomically published") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary, dir_fd=parent_fd)
        except FileNotFoundError:
            pass


def run_sonatine_demo(
    kernel: Path,
    output: Path,
    *,
    qemu: str = "qemu-system-riscv64",
    timeout_seconds: float = 30.0,
    repository: Path | None = None,
    process_runner: Any = _run_bounded_process,
) -> SonatineDemoResult:
    """Run the immutable T-0092 transcript and atomically create one result."""
    _validate_timeout(timeout_seconds)
    if type(qemu) is not str or not qemu or len(qemu) > MAX_COMMAND_COMPONENT_BYTES or "\x00" in qemu:
        raise ValueError("Sonatine demo QEMU executable is outside the bounded contract")
    parent_fd, leaf = _open_output_target(output)
    try:
        repository = repository or Path(__file__).resolve().parents[1]
        revision = _repository_revision(repository, timeout_seconds, process_runner)
        qemu_version = _command_version((qemu, "--version"), timeout_seconds, process_runner)
        kernel_bytes = _read_pinned_kernel(kernel)
        kernel_sha256 = hashlib.sha256(kernel_bytes).hexdigest()
        logical_command = (qemu, *_QEMU_ARGS)
        with tempfile.TemporaryDirectory(prefix="raveil-sonatine-demo-") as directory:
            pinned_kernel = Path(directory) / "sonatine.elf"
            pinned_kernel.write_bytes(kernel_bytes)
            command = (*logical_command[:-1], str(pinned_kernel))
            try:
                completed = process_runner(
                    command, input_data=INPUT_TRANSCRIPT, timeout_seconds=timeout_seconds,
                )
            except RuntimeError:
                raise
            except OSError as error:
                raise RuntimeError("unable to launch Sonatine demo QEMU") from error
        if completed.returncode != 0:
            raise RuntimeError(f"Sonatine demo QEMU exited {completed.returncode}")
        raw_output = completed.stdout if isinstance(completed.stdout, bytes) else str(completed.stdout).encode()
        frames = parse_demo_frames(raw_output)
        final = frames[-1]
        result = SonatineDemoResult(
            revision, kernel_sha256, COMMAND_TRANSCRIPT, INPUT_SHA256, FRAME_VERSION, logical_command,
            {"python": sys.version.split()[0], "qemu": qemu_version}, frames,
            final.state, final.semantic, final.checksum, completed.returncode,
        )
        result.validate()
        encoded = json.dumps(result.to_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n"
        _publish_result(parent_fd, leaf, encoded)
        return result
    finally:
        os.close(parent_fd)
