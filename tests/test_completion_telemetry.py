from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from raveil.cli import main as cli_main
from raveil.completion_telemetry import (
    CompletionTelemetryStore,
    EVIDENCE_CLASS,
    SCHEMA,
    parse_qemu_log,
)


LINE = (
    "RAVEIL-COMPLETION-V1 job=9223372036854775809 epoch=1 sequence=2 "
    "cookie=0102030405060708090a0b0c0d0e0f10 status=1 detail=0 "
    "smoke_path_ticks=37 outputs=2:4:6\n"
)


class CompletionTelemetryTests(unittest.TestCase):
    def write_log(self, root: Path, line: str = LINE) -> Path:
        path=root / "smoke.log"
        path.write_text("unrelated console\n"+line,encoding="ascii")
        return path

    def test_parse_and_hash_chained_idempotent_ingest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); log=self.write_log(root); store_path=root/"cold.jsonl"
            digest,events=parse_qemu_log(log)
            self.assertEqual(len(digest),64); self.assertEqual(events[0].job_id,2**63+1)
            store=CompletionTelemetryStore(store_path)
            self.assertEqual(store.ingest_qemu_log(log,"run-1"),1)
            before=store_path.read_bytes()
            self.assertEqual(store.ingest_qemu_log(log,"run-1"),0)
            self.assertEqual(store_path.read_bytes(),before)
            records=store.load(); self.assertEqual(len(records),1)
            record=records[0]
            self.assertEqual(record.schema,SCHEMA)
            self.assertEqual(record.evidence_class,EVIDENCE_CLASS)
            self.assertEqual(record.observed_outputs[0].version,6)
            self.assertNotIn("semantic_valid",record.to_dict())
            self.assertNotIn("committed",record.to_dict())
            self.assertNotIn("path",record.to_dict())
            self.assertEqual(stat_mode(store_path),0o600)

    def test_parser_rejects_malformed_claims_and_oversize(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            bad=(
                LINE.replace("status=1 detail=0","status=1 detail=3"),
                LINE.replace("cookie=01","cookie=00").replace(
                    "02030405060708090a0b0c0d0e0f10","000000000000000000000000000000"),
                LINE.replace("smoke_path_ticks=37","smoke_path_ticks=0"),
                LINE.replace("outputs=2:4:6","outputs=2:4:6,2:4:7"),
                "RAVEIL-COMPLETION-V2 x\n",
                "RAVEIL-COMPLETION-V1 "+"x"*1100+"\n",
                LINE+LINE,
                LINE.rstrip("\n"),
            )
            for index,line in enumerate(bad):
                path=root/f"bad-{index}.log"; path.write_text(line,encoding="ascii")
                with self.assertRaises(ValueError,msg=str(index)):
                    parse_qemu_log(path)

    def test_corrupt_chain_and_nonregular_store_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); log=self.write_log(root); store_path=root/"cold.jsonl"
            store=CompletionTelemetryStore(store_path); store.ingest_qemu_log(log,"run-1")
            value=json.loads(store_path.read_text())
            value["observed_smoke_path_ticks"]=38
            store_path.write_text(json.dumps(value)+"\n")
            before=store_path.read_bytes()
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                store.ingest_qemu_log(log,"run-2")
            self.assertEqual(store_path.read_bytes(),before)
            store_path.unlink(); target=root/"target"; target.write_text("")
            store_path.symlink_to(target)
            with self.assertRaises(OSError):
                store.ingest_qemu_log(log,"run-1")

    def test_conflict_types_and_log_size_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); log=self.write_log(root); path=root/"cold.jsonl"
            store=CompletionTelemetryStore(path); self.assertEqual(store.ingest_qemu_log(log,"run-1"),1)
            before=path.read_bytes()
            conflicting=root/"conflict.log"
            conflicting.write_text(LINE.replace("smoke_path_ticks=37","smoke_path_ticks=38"),
                                   encoding="ascii")
            with self.assertRaisesRegex(ValueError,"conflicting telemetry"):
                store.ingest_qemu_log(conflicting,"run-1")
            self.assertEqual(path.read_bytes(),before)
            # Exact same source event remains idempotent even if caller metadata changes.
            self.assertEqual(store.ingest_qemu_log(log,"run-2"),0)
            value=json.loads(before)
            for field,replacement in (("sequence",True),("raw_line",1.0),
                                      ("job_id","9223372036854775809")):
                damaged=dict(value); damaged[field]=replacement
                path.write_text(json.dumps(damaged)+"\n")
                with self.assertRaisesRegex(ValueError,"exact"):
                    store.load()
            path.write_bytes(before)
            oversized=root/"oversized.log"
            with oversized.open("wb") as output:
                output.truncate(16*1024*1024+1)
            with self.assertRaisesRegex(ValueError,"bounded"):
                parse_qemu_log(oversized)

    def test_cli_ingest_and_inspect(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); log=self.write_log(root); store=root/"cold.jsonl"
            args=["experience","ingest-completions","--input",str(log),
                  "--store",str(store),"--run-id","qemu-smoke"]
            self.assertEqual(cli_main(args),0); self.assertEqual(cli_main(args),0)
            self.assertEqual(cli_main(["experience","inspect-completions",
                                       "--store",str(store)]),0)


def stat_mode(path: Path) -> int:
    return os.stat(path).st_mode & 0o777


if __name__ == "__main__":
    unittest.main()
