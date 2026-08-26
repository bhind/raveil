from __future__ import annotations

import argparse
import unittest

from scripts.project_queue import (
    QueueError,
    audit_state,
    branch_work_id,
    closing_reference,
    missing_packet_markers,
    task_id,
    review,
    start,
    work_id,
)


PACKET = """Authority: main
Dependencies: none
Mutation owner: Chisel Implementer
Allowlist: demo.py
Artifacts: demo receipt
Acceptance: demo passes
Evidence class: Host Functional
Stop rule: boundary drift
Non-claims: no hardware claim
"""


def issue(number: int, title: str, state: str = "OPEN") -> dict:
    return {
        "number": number,
        "title": title,
        "url": f"https://github.com/bhind/raveil/issues/{number}",
        "state": state,
        "labels": [{"name": "work-item"}],
        "body": PACKET,
    }


def item(number: int, title: str, status: str, parent: str) -> dict:
    return {
        "id": f"item-{number}",
        "title": title,
        "status": status,
        "priority": "P0",
        "parent T-ID": parent,
        "owner Role": "Chisel Implementer",
        "depends On": "None",
        "story Points": 5,
        "demo Command": "./demo.sh",
        "evidence Class": "RTL Simulation",
        "content": {
            "type": "Issue",
            "title": title,
            "url": f"https://github.com/bhind/raveil/issues/{number}",
        },
    }


def select_field(name: str, *options: str) -> dict:
    return {
        "id": f"field-{name}",
        "name": name,
        "type": "ProjectV2SingleSelectField",
        "options": [{"id": f"option-{option}", "name": option} for option in options],
    }


class FakeQueue:
    project_number = 1

    def __init__(self, project: dict, issues: list[dict], branch: str) -> None:
        self._project = project
        self._issues = issues
        self._branch = branch
        self.edits: list[tuple[str, str, object]] = []
        self._fields = {
            "Status": select_field("Status", "Ready", "In Progress", "Review"),
            "Priority": select_field("Priority", "P0"),
            "Parent T-ID": {"id": "parent", "name": "Parent T-ID", "type": "ProjectV2Field"},
            "Owner Role": select_field("Owner Role", "Chisel Implementer"),
            "Depends On": {"id": "depends", "name": "Depends On", "type": "ProjectV2Field"},
            "Story Points": {"id": "points", "name": "Story Points", "type": "ProjectV2Field"},
            "Demo Command": {"id": "demo", "name": "Demo Command", "type": "ProjectV2Field"},
            "Evidence Class": select_field("Evidence Class", "Host Functional"),
        }

    def issue(self, number: int) -> dict:
        return next(entry for entry in self._issues if entry["number"] == number)

    def issues(self) -> list[dict]:
        return self._issues

    def project(self) -> dict:
        return self._project

    def branch(self) -> str:
        return self._branch

    def fields(self) -> dict:
        return self._fields

    def pull_request(self, number: int) -> dict:
        return {
            "number": number,
            "state": "OPEN",
            "url": f"https://github.com/bhind/raveil/pull/{number}",
            "body": "Closes #27",
            "headRefName": self._branch,
        }

    @staticmethod
    def find_item(project: dict, issue_url: str) -> dict | None:
        return next(
            (entry for entry in project["items"] if entry.get("content", {}).get("url") == issue_url),
            None,
        )

    @staticmethod
    def option_id(field: dict, name: str) -> str:
        return next(option["id"] for option in field["options"] if option["name"] == name)

    def edit_field(self, item_id: str, field: dict, *, value: object) -> None:
        self.edits.append((item_id, field["name"], value))


def start_args(*, apply: bool = True) -> argparse.Namespace:
    return argparse.Namespace(
        issue=27,
        owner_role="Chisel Implementer",
        depends_on="None",
        story_points=5,
        demo="./demo.sh",
        evidence_class="Host Functional",
        apply=apply,
    )


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

    def test_requires_complete_independence_packet(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        one_issue["body"] = "Authority: main\nAcceptance: pass"
        errors = audit_state(
            {"items": [item(27, one_issue["title"], "In Progress", "T-0125")]},
            [one_issue],
        )
        self.assertTrue(any("incomplete independence packet" in error for error in errors))
        self.assertIn("Dependencies", missing_packet_markers(one_issue["body"]))

    def test_child_slice_identity_is_not_collapsed(self) -> None:
        child = issue(27, "T-0123/S03 — Bounded DAG")
        child_item = item(27, child["title"], "In Progress", "T-0123")
        self.assertEqual([], audit_state({"items": [child_item]}, [child], "feat/t-0123-s03-dag"))
        errors = audit_state({"items": [child_item]}, [child], "feat/t-0123-s02-affine")
        self.assertTrue(any("no matching active" in error for error in errors))

    def test_task_and_closing_reference_parsing(self) -> None:
        self.assertEqual("T-0125", task_id("feat/t-0125-graph-device-playable"))
        self.assertEqual("T-0123/S03", work_id("T-0123/S03 — bounded DAG"))
        self.assertEqual("T-0123/S03", branch_work_id("feat/t-0123-s03-bounded-dag"))
        self.assertTrue(closing_reference("Closes #27", 27))
        self.assertTrue(closing_reference("Fixes #27 after review", 27))
        self.assertFalse(closing_reference("Related to #27", 27))
        self.assertFalse(closing_reference("Closes #28", 27))

    def test_start_rejects_third_wip_without_remote_edit(self) -> None:
        issues = [
            issue(27, "T-0125 — Playable"),
            issue(28, "T-0126 — Queue"),
            issue(29, "T-0127 — Other"),
        ]
        project = {
            "items": [
                item(27, issues[0]["title"], "Ready", "T-0125"),
                item(28, issues[1]["title"], "In Progress", "T-0126"),
                item(29, issues[2]["title"], "Review", "T-0127"),
            ]
        }
        queue = FakeQueue(project, issues, "feat/t-0125-playable")
        with self.assertRaisesRegex(QueueError, "exceed the two-item"):
            start(queue, start_args())
        self.assertEqual([], queue.edits)

    def test_start_preflights_all_fields_before_remote_edit(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        project = {"items": [item(27, one_issue["title"], "Ready", "T-0125")]}
        queue = FakeQueue(project, [one_issue], "feat/t-0125-playable")
        del queue._fields["Evidence Class"]
        with self.assertRaisesRegex(QueueError, "missing required field"):
            start(queue, start_args())
        self.assertEqual([], queue.edits)

    def test_start_writes_status_only_after_metadata(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        project = {"items": [item(27, one_issue["title"], "Ready", "T-0125")]}
        queue = FakeQueue(project, [one_issue], "feat/t-0125-playable")
        self.assertEqual(0, start(queue, start_args()))
        self.assertEqual("Status", queue.edits[-1][1])
        self.assertEqual("In Progress", queue.edits[-1][2])

    def test_review_rejects_ready_to_review_jump(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        project = {"items": [item(27, one_issue["title"], "Ready", "T-0125")]}
        queue = FakeQueue(project, [one_issue], "feat/t-0125-playable")
        args = argparse.Namespace(issue=27, pr=30, apply=True)
        with self.assertRaisesRegex(QueueError, "requires Project status In Progress"):
            review(queue, args)
        self.assertEqual([], queue.edits)

    def test_review_moves_only_in_progress_item(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        project = {"items": [item(27, one_issue["title"], "In Progress", "T-0125")]}
        queue = FakeQueue(project, [one_issue], "feat/t-0125-playable")
        args = argparse.Namespace(issue=27, pr=30, apply=True)
        self.assertEqual(0, review(queue, args))
        self.assertEqual([("item-27", "Status", "Review")], queue.edits)


if __name__ == "__main__":
    unittest.main()
