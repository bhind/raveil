from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

from .experiment_schema import validate_backend_evidence


SCHEMA = "raveil.completion-telemetry/v1"
SOURCE = "sonatine-qemu"
BACKEND = "qemu-telemetry"
EVIDENCE_CLASS = "emulation"
PLATFORM = "qemu-virt-rv64-v1"
ZERO_HASH = "0" * 64
MAX_LINE_BYTES = 1024
MAX_LOG_BYTES = 16 * 1024 * 1024
UINT64_MAX = (1 << 64) - 1
_FRAME = re.compile(
    r"^RAVEIL-COMPLETION-V1 "
    r"job=([1-9][0-9]*) epoch=([1-9][0-9]*) sequence=([1-9][0-9]*) "
    r"cookie=([0-9a-f]{32}) status=([1-4]) detail=([0-3]) "
    r"smoke_path_ticks=([1-9][0-9]*) outputs=(-|[0-9:,]+)$"
)


@dataclass(frozen=True)
class CompletionOutput:
    object_id: int
    generation: int
    version: int

    def validate(self) -> None:
        if any(type(value) is not int for value in
               (self.object_id,self.generation,self.version)):
            raise ValueError("completion output values must be exact integers")
        if (min(self.object_id, self.generation, self.version) < 1 or
                max(self.object_id, self.generation, self.version) > UINT64_MAX):
            raise ValueError("completion output values must be positive")


@dataclass(frozen=True)
class ParsedCompletion:
    job_id: int
    execution_epoch: int
    execution_sequence: int
    cookie: str
    status: int
    detail: int
    smoke_path_ticks: int
    outputs: tuple[CompletionOutput, ...]
    raw_line: int

    def validate(self) -> None:
        counters=(self.job_id,self.execution_epoch,self.execution_sequence,self.smoke_path_ticks)
        if min(*counters,self.raw_line) < 1 or max(counters) > UINT64_MAX:
            raise ValueError("completion identifiers and counters must be positive")
        if (len(self.cookie) != 32 or self.cookie == "0" * 32 or
                any(value not in "0123456789abcdef" for value in self.cookie)):
            raise ValueError("completion cookie must be 16-byte lowercase hex")
        expected_detail = {1: 0, 2: 1, 3: 2, 4: 3}.get(self.status)
        if expected_detail is None or self.detail != expected_detail:
            raise ValueError("completion status/detail is invalid")
        if len(self.outputs) > 4 or (self.status != 1 and self.outputs):
            raise ValueError("completion outputs are invalid for status")
        pairs: set[tuple[int, int]] = set()
        for output in self.outputs:
            output.validate()
            pair = (output.object_id, output.generation)
            if pair in pairs:
                raise ValueError("completion outputs contain duplicates")
            pairs.add(pair)


@dataclass(frozen=True)
class CompletionTelemetryRecord:
    sequence: int
    run_id: str
    captured_at_utc: str
    raw_log_sha256: str
    raw_line: int
    event_id: str
    binding_id: str
    job_id: int
    execution_epoch: int
    execution_sequence: int
    cookie_sha256: str
    observed_status: int
    observed_detail: int
    observed_smoke_path_ticks: int
    observed_outputs: tuple[CompletionOutput, ...]
    previous_hash: str
    record_hash: str = ""
    schema: str = SCHEMA
    source: str = SOURCE
    backend: str = BACKEND
    evidence_class: str = EVIDENCE_CLASS
    platform: str = PLATFORM

    def payload(self) -> dict[str, Any]:
        value = asdict(self)
        value["observed_outputs"] = [asdict(output) for output in self.observed_outputs]
        value.pop("record_hash")
        return value

    def with_hash(self) -> "CompletionTelemetryRecord":
        digest = hashlib.sha256(_canonical(self.payload())).hexdigest()
        return replace(self, record_hash=digest)

    def to_dict(self) -> dict[str, Any]:
        value = self.payload()
        value["record_hash"] = self.record_hash
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CompletionTelemetryRecord":
        expected = set(cls.__dataclass_fields__)
        if set(value) != expected:
            raise ValueError("completion telemetry fields are not exact")
        if type(value["observed_outputs"]) is not list:
            raise ValueError("observed_outputs must be a list")
        outputs_list=[]
        for item in value["observed_outputs"]:
            if type(item) is not dict or set(item)!={"object_id","generation","version"}:
                raise ValueError("completion output fields are not exact")
            outputs_list.append(CompletionOutput(**item))
        outputs=tuple(outputs_list)
        record = cls(**{**value, "observed_outputs": outputs})
        record.validate()
        return record

    def validate(self) -> None:
        string_fields=(self.run_id,self.captured_at_utc,self.raw_log_sha256,
                       self.event_id,self.binding_id,self.cookie_sha256,
                       self.previous_hash,self.record_hash,self.schema,self.source,
                       self.backend,self.evidence_class,self.platform)
        if any(type(value) is not str for value in string_fields):
            raise ValueError("completion telemetry strings must be exact strings")
        integer_fields=(self.sequence,self.raw_line,self.job_id,self.execution_epoch,
                        self.execution_sequence,self.observed_status,
                        self.observed_detail,self.observed_smoke_path_ticks)
        if any(type(value) is not int for value in integer_fields):
            raise ValueError("completion telemetry integers must be exact integers")
        validate_backend_evidence(self.backend, self.evidence_class)
        if (self.schema != SCHEMA or self.source != SOURCE or self.backend != BACKEND or
                self.evidence_class != EVIDENCE_CLASS or self.platform != PLATFORM):
            raise ValueError("completion telemetry provenance is invalid")
        if (self.sequence < 1 or self.sequence > UINT64_MAX or self.raw_line < 1 or
                self.raw_line > UINT64_MAX or not _bounded_token(self.run_id, 128)):
            raise ValueError("completion telemetry sequence/run is invalid")
        _parse_utc(self.captured_at_utc)
        for digest in (self.raw_log_sha256, self.event_id, self.binding_id,
                       self.cookie_sha256,
                       self.previous_hash, self.record_hash):
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("completion telemetry hash is invalid")
        parsed = ParsedCompletion(
            self.job_id, self.execution_epoch, self.execution_sequence, "1" + "0" * 31,
            self.observed_status, self.observed_detail, self.observed_smoke_path_ticks,
            self.observed_outputs, self.raw_line,
        )
        # Cookie form was validated before hashing; use a valid placeholder here.
        parsed.validate()
        if self.with_hash().record_hash != self.record_hash:
            raise ValueError("completion telemetry record hash mismatch")


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _bounded_token(value: str, limit: int) -> bool:
    return 0 < len(value) <= limit and all(char.isalnum() or char in "._:-" for char in value)


def _parse_utc(value: str) -> None:
    if len(value) > 40 or not value.endswith("Z"):
        raise ValueError("captured_at_utc must be bounded UTC")
    datetime.fromisoformat(value[:-1] + "+00:00")


def _strict_json(raw: bytes) -> dict[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any]={}
        for key,value in values:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key]=value
        return result
    value=json.loads(raw,object_pairs_hook=pairs,
                     parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)))
    if not isinstance(value,dict):
        raise ValueError("telemetry journal record must be an object")
    return value


def parse_qemu_log(path: Path) -> tuple[str, list[ParsedCompletion]]:
    flags=os.O_RDONLY | getattr(os,"O_NOFOLLOW",0)
    descriptor=os.open(path,flags)
    try:
        info=os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or
                info.st_size>MAX_LOG_BYTES):
            raise ValueError("telemetry input must be a bounded single-link regular file")
        chunks=[]; total=0
        while True:
            chunk=os.read(descriptor,min(65536,MAX_LOG_BYTES+1-total))
            if not chunk: break
            chunks.append(chunk); total+=len(chunk)
            if total>MAX_LOG_BYTES:
                raise ValueError("telemetry input exceeds maximum size")
        data=b"".join(chunks)
    finally:
        os.close(descriptor)
    digest = hashlib.sha256(data).hexdigest()
    events: list[ParsedCompletion] = []
    bindings: set[tuple[int,int,int,str]] = set()
    lines=data.splitlines()
    for line_number, raw in enumerate(lines, start=1):
        if len(raw) > MAX_LINE_BYTES:
            if raw.startswith(b"RAVEIL-COMPLETION-"):
                raise ValueError(f"oversized completion telemetry at line {line_number}")
            continue
        if not raw.startswith(b"RAVEIL-COMPLETION-"):
            continue
        try:
            text = raw.decode("ascii").removesuffix("\r")
        except UnicodeDecodeError as error:
            raise ValueError(f"non-ASCII completion telemetry at line {line_number}") from error
        match = _FRAME.fullmatch(text)
        if match is None:
            raise ValueError(f"malformed completion telemetry at line {line_number}")
        output_text = match.group(8)
        outputs: tuple[CompletionOutput, ...]
        if output_text == "-":
            outputs = ()
        else:
            try:
                outputs = tuple(
                    CompletionOutput(*(int(part) for part in item.split(":")))
                    for item in output_text.split(",")
                )
            except (TypeError, ValueError) as error:
                raise ValueError(f"malformed completion outputs at line {line_number}") from error
        event = ParsedCompletion(
            *(int(match.group(index)) for index in (1, 2, 3)), match.group(4),
            *(int(match.group(index)) for index in (5, 6, 7)), outputs, line_number,
        )
        event.validate()
        binding=(event.job_id,event.execution_epoch,event.execution_sequence,event.cookie)
        if binding in bindings:
            raise ValueError(f"duplicate completion telemetry at line {line_number}")
        bindings.add(binding)
        events.append(event)
    if data and not data.endswith((b"\n",b"\r")) and lines and \
            lines[-1].startswith(b"RAVEIL-COMPLETION-"):
        raise ValueError("truncated completion telemetry final line")
    if not events:
        raise ValueError("no completion telemetry found")
    return digest, events


class CompletionTelemetryStore:
    """Single-writer, hash-chained cold completion evidence; never online retrieval."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def ingest_qemu_log(self, log: Path, run_id: str) -> int:
        if not _bounded_token(run_id, 128):
            raise ValueError("run_id is invalid")
        raw_hash, events = parse_qemu_log(log)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _reject_symlink_parents(self.path)
        flags = os.O_RDWR | os.O_APPEND | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.path, flags, 0o600)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("telemetry store must be a single-link regular file")
            os.fchmod(descriptor, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            existing = self._load_descriptor(descriptor)
            known = {record.event_id for record in existing}
            bindings = {record.binding_id: record for record in existing}
            previous = existing[-1].record_hash if existing else ZERO_HASH
            additions: list[CompletionTelemetryRecord] = []
            captured = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
            for event in events:
                event_id = hashlib.sha256(
                    f"{raw_hash}:{event.raw_line}:{event.job_id}:{event.execution_epoch}:"
                    f"{event.execution_sequence}:{event.cookie}".encode()
                ).hexdigest()
                if event_id in known:
                    continue
                binding_id=hashlib.sha256(
                    f"{run_id}:{event.job_id}:{event.execution_epoch}:"
                    f"{event.execution_sequence}:{event.cookie}".encode()
                ).hexdigest()
                if binding_id in bindings:
                    raise ValueError("conflicting telemetry for an existing run binding")
                record = CompletionTelemetryRecord(
                    sequence=len(existing) + len(additions) + 1, run_id=run_id,
                    captured_at_utc=captured, raw_log_sha256=raw_hash,
                    raw_line=event.raw_line, event_id=event_id, binding_id=binding_id,
                    job_id=event.job_id,
                    execution_epoch=event.execution_epoch,
                    execution_sequence=event.execution_sequence,
                    cookie_sha256=hashlib.sha256(bytes.fromhex(event.cookie)).hexdigest(),
                    observed_status=event.status, observed_detail=event.detail,
                    observed_smoke_path_ticks=event.smoke_path_ticks,
                    observed_outputs=event.outputs, previous_hash=previous,
                ).with_hash()
                record.validate()
                additions.append(record); known.add(event_id); bindings[binding_id]=record
                previous=record.record_hash
            if additions:
                payload=b"".join(_canonical(record.to_dict())+b"\n" for record in additions)
                written=os.write(descriptor,payload)
                if written!=len(payload):
                    raise OSError("short telemetry journal write")
                os.fsync(descriptor)
            return len(additions)
        finally:
            os.close(descriptor)

    def load(self) -> tuple[CompletionTelemetryRecord, ...]:
        try:
            descriptor=os.open(self.path,os.O_RDONLY | (getattr(os,"O_NOFOLLOW",0)))
        except FileNotFoundError:
            return ()
        try:
            info=os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:
                raise ValueError("telemetry store must be a single-link regular file")
            return tuple(self._load_descriptor(descriptor))
        finally:
            os.close(descriptor)

    @staticmethod
    def _load_descriptor(descriptor: int) -> list[CompletionTelemetryRecord]:
        os.lseek(descriptor,0,os.SEEK_SET)
        chunks=[]
        while True:
            chunk=os.read(descriptor,65536)
            if not chunk: break
            chunks.append(chunk)
        data=b"".join(chunks)
        if data and not data.endswith(b"\n"):
            raise ValueError("telemetry journal has a partial final record")
        records=[]; previous=ZERO_HASH; events=set(); bindings=set()
        for line_number,raw in enumerate(data.splitlines(),start=1):
            if not raw or len(raw)>16384:
                raise ValueError(f"invalid telemetry journal line {line_number}")
            try:
                value=_strict_json(raw)
                record=CompletionTelemetryRecord.from_dict(value)
            except (TypeError,ValueError,json.JSONDecodeError) as error:
                raise ValueError(f"invalid telemetry journal line {line_number}: {error}") from error
            if (record.sequence!=line_number or record.previous_hash!=previous or
                    record.event_id in events or record.binding_id in bindings):
                raise ValueError(f"telemetry journal chain/sequence failure at line {line_number}")
            records.append(record); previous=record.record_hash
            events.add(record.event_id); bindings.add(record.binding_id)
        return records


def _reject_symlink_parents(path: Path) -> None:
    info=path.parent.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ValueError("telemetry store parent must be a real directory")
