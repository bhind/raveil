"""Deterministic non-claim fixtures for the Native Command Graph demo."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .workspace import NativeWorkspace


@dataclass(frozen=True)
class CommandWorkload:
    workload_id: str
    source: str
    files: tuple[tuple[str, bytes], ...]
    expected_stdout_sha256: str | None
    workload_size: int
    node_count: int
    declared_concurrency: int
    expected_status: str = "executed"

    def generate(self, workspace: NativeWorkspace) -> None:
        for path, data in self.files:
            workspace.write_bytes(path, data, maximum=16 * 1024 * 1024)


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def preregistered_workloads(size: int = 128) -> tuple[CommandWorkload, ...]:
    if type(size) is not int or not 1 <= size <= 4096:
        raise ValueError("workload size is outside bounds")
    lines = [f"INFO row {index}\n" if index % 3 else f"ERROR row {index}\n" for index in range(size)]
    input_data = "".join(lines).encode()
    error_count = sum(1 for line in lines if line.startswith("ERROR"))
    word_repetitions = max(1, size // 4)
    words = ("pear\napple\npear\nbanana\n" * word_repetitions).encode()
    transform = "".join(f"line-{index}\n" for index in range(max(100, size))).encode()
    file_a = ("alpha\n" * size).encode(); file_b = ("beta\n" * size).encode()
    log_a = b"INFO a\nERROR a1\nERROR a2\n"; log_b = b"ERROR b1\nINFO b\n"
    sequential_stdout = f"{error_count}\n".encode()
    transformed_stdout = b"".join(line.upper().encode() for line in transform.decode().splitlines(True)[:100])
    word_counts = f"{word_repetitions} apple\n{word_repetitions} banana\n{word_repetitions * 2} pear\n".encode()
    hash_stdout = f"{_hash(file_a)}\n{_hash(file_b)}\n".encode()
    filtered_stdout = b"ERROR a1\nERROR a2\nERROR b1\n"
    return (
        CommandWorkload("sequential-text", "cat /a-input.txt | grep ERROR | wc -l",
                        (("/a-input.txt", input_data),), _hash(sequential_stdout), len(input_data), 3, 1),
        CommandWorkload("sort-deduplicate", "cat /b-words.txt | sort | uniq -c",
                        (("/b-words.txt", words),), _hash(word_counts), len(words), 3, 1),
        CommandWorkload("transform-head", "cat /c-input.txt | tr a-z A-Z | head -n 100",
                        (("/c-input.txt", transform),), _hash(transformed_stdout), len(transform), 3, 1),
        CommandWorkload("hash-fanout", "sha256sum /d-a.txt ||| sha256sum /d-b.txt",
                        (("/d-a.txt", file_a), ("/d-b.txt", file_b)), _hash(hash_stdout),
                        len(file_a) + len(file_b), 2, 2),
        CommandWorkload(
            "multi-input-filter",
            "grep ERROR /e-a.log > /e-a.filtered ||| grep ERROR /e-b.log > /e-b.filtered "
            "&& cat /e-a.filtered /e-b.filtered | sort",
            (("/e-a.log", log_a), ("/e-b.log", log_b)), _hash(filtered_stdout), len(log_a) + len(log_b), 4, 2,
        ),
        CommandWorkload("missing-input", "cat /does-not-exist", (), None, 0, 1, 1, "compile-failed"),
        CommandWorkload("grep-no-match", "grep NEVER /f-input.txt && wc -l",
                        (("/f-input.txt", input_data),), None, len(input_data), 2, 1, "failed"),
        CommandWorkload("output-collision", "cat /f-input.txt > /occupied.txt",
                        (("/f-input.txt", input_data), ("/occupied.txt", b"keep\n")), None,
                        len(input_data), 1, 1, "compile-failed"),
        CommandWorkload("injected-timeout", "cat /f-input.txt", (("/f-input.txt", input_data),),
                        None, len(input_data), 1, 1, "injected-timeout"),
        CommandWorkload("injected-stale-tool", "cat /f-input.txt", (("/f-input.txt", input_data),),
                        None, len(input_data), 1, 1, "injected-stale-tool"),
    )
