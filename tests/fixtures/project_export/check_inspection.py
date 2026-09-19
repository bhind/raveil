"""Planning-fixture checks only; never extract, export, import or execute."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).parent


def check(entries):
    if type(entries) is not list or len(entries) > 1024:
        raise ValueError("entry budget")
    seen, total = set(), 0
    for entry in entries:
        if type(entry) is not dict or set(entry) != {"path", "bytes", "sha256"}:
            raise ValueError("member fields")
        name, size, digest = entry["path"], entry["bytes"], entry["sha256"]
        if (type(name) is not str or not name.isascii() or "\\" in name
                or ":" in name or any(ord(c) < 32 for c in name)
                or any(p in {"", ".", ".."} for p in name.split("/"))):
            raise ValueError("relative canonical path")
        if name.casefold() in seen:
            raise ValueError("duplicate member")
        seen.add(name.casefold())
        if type(size) is not int or size < 0:
            raise ValueError("byte count")
        if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("digest")
        total += size
    if total > 16 * 1024 * 1024:
        raise ValueError("byte budget")
    return total


def inspected_entries():
    manifest = json.loads((ROOT / "native-logs-inspection.json").read_text())
    sizes = json.loads((ROOT / "native-logs-sizes.json").read_text())
    files = {k[1:]: v for k, v in manifest["members"].items() if v != "directory"}
    if set(files) != set(sizes["bytes"]):
        raise ValueError("fixture file sets differ")
    entries = [{"path": k, "bytes": sizes["bytes"][k], "sha256": v}
               for k, v in files.items()]
    if check(entries) != sizes["total_bytes"]:
        raise ValueError("fixture byte total differs")
    return entries


class InspectionTests(unittest.TestCase):
    def test_actual_snapshot(self):
        entries = inspected_entries()
        self.assertEqual(len(entries), 20)
        self.assertIn("inputs/left.txt", {e["path"] for e in entries})

    def test_paths(self):
        for name in ("/absolute", "../escape", "a/../b", "a//b", "./a",
                     "a\\b", "C:drive", "a\x00b", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                check([dict(inspected_entries()[0], path=name)])

    def test_duplicates(self):
        entry = inspected_entries()[0]
        with self.assertRaises(ValueError):
            check([entry, dict(entry, path=entry["path"].upper())])

    def test_limits_types_and_links(self):
        base = inspected_entries()[0]
        for override in ({"bytes": -1}, {"bytes": True}, {"sha256": "bad"},
                         {"bytes": 16 * 1024 * 1024 + 1}, {"link": "target"}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                check([dict(base, **override)])
        with self.assertRaises(ValueError):
            check([base] * 1025)


if __name__ == "__main__":
    unittest.main()
