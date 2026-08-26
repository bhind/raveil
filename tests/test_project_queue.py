from __future__ import annotations

import unittest

from scripts.project_queue import audit_state, closing_reference, task_id


def issue(number: int, title: str, state: str = "OPEN") -> dict:
    return {
        "number": number,
        "title": title,
        "url": f"https://github.com/bhind/raveil/issues/{number}",
        "state": state,
        "labels": [{"name": "work-item"}],
    }


def item(number: int, title: str, status: str, parent: str) -> dict:
    return {
        "title": title,
        "status": status,
        "priority": "P0",
        "parent T-ID": parent,
        "owner Role": "Chisel Implementer",
        "story Points": 5,
        "demo Command": "./demo.sh",
        "evidence Class": "RTL Simulation",
        "content": {
            "type": "Issue",
            "title": title,
            "url": f"https://github.com/bhind/raveil/issues/{number}",
        },
    }


class ProjectQueueAuditTest(unittest.TestCase):
    def test_accepts_two_real_issue_lanes_and_matching_branch(self) -> None:
        issues = [issue(27, "T-0125 — Playable"), issue(28, "T-0126 — Queue")]
        project = {
            "items": [
                item(27, issues[0]["title"], "In Progress", "T-0125"),
                item(28, issues[1]["title"], "Review", "T-0126"),
            ]
        }
        self.assertEqual([], audit_state(project, issues, "chore/t-0126-project-dispatch"))

    def test_rejects_active_draft_and_excess_wip(self) -> None:
        issues = [issue(27 + offset, f"T-{125 + offset:04d} — Work") for offset in range(3)]
        items = [
            item(27 + offset, entry["title"], "In Progress", f"T-{125 + offset:04d}")
            for offset, entry in enumerate(issues)
        ]
        items[0]["content"] = {"type": "DraftIssue", "title": items[0]["title"]}
        errors = audit_state({"items": items}, issues)
        self.assertTrue(any("not a real Issue" in error for error in errors))
        self.assertTrue(any("exceeds two" in error for error in errors))

    def test_rejects_open_issue_missing_from_project(self) -> None:
        errors = audit_state({"items": []}, [issue(27, "T-0125 — Playable")])
        self.assertEqual(1, len(errors))
        self.assertIn("missing from Project", errors[0])

    def test_rejects_task_and_lifecycle_mismatches(self) -> None:
        open_issue = issue(27, "T-0125 — Playable")
        closed_issue = issue(28, "T-0126 — Queue", state="CLOSED")
        project = {
            "items": [
                item(27, open_issue["title"], "Done", "T-9999"),
                item(28, closed_issue["title"], "Review", "T-0126"),
            ]
        }
        errors = audit_state(project, [open_issue, closed_issue])
        self.assertTrue(any("still has an open Issue" in error for error in errors))
        self.assertTrue(any("Parent T-ID mismatch" in error for error in errors))
        self.assertTrue(any("not an open Issue" in error for error in errors))

    def test_rejects_branch_without_matching_active_issue(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        project = {"items": [item(27, one_issue["title"], "In Progress", "T-0125")]}
        errors = audit_state(project, [one_issue], "chore/t-0126-project-dispatch")
        self.assertTrue(any("no matching active" in error for error in errors))

    def test_requires_visible_execution_fields(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        one_item = item(27, one_issue["title"], "In Progress", "T-0125")
        one_item["demo Command"] = ""
        errors = audit_state({"items": [one_item]}, [one_issue])
        self.assertIn(
            "active work-item lacks demo Command: https://github.com/bhind/raveil/issues/27",
            errors,
        )

    def test_task_and_closing_reference_parsing(self) -> None:
        self.assertEqual("T-0125", task_id("feat/t-0125-graph-device-playable"))
        self.assertTrue(closing_reference("Closes #27", 27))
        self.assertTrue(closing_reference("Fixes #27 after review", 27))
        self.assertFalse(closing_reference("Related to #27", 27))
        self.assertFalse(closing_reference("Closes #28", 27))


if __name__ == "__main__":
    unittest.main()
