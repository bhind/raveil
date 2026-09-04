from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import patch

from scripts.project_queue import (
    QueueError,
    ProjectQueue,
    audit,
    audit_state,
    branch_work_id,
    closing_reference,
    complete,
    missing_packet_markers,
    prepare,
    pullable_ready_items,
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
        "sprint": {"title": "S-0001"},
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
            "Status": select_field(
                "Status", "Backlog", "Ready", "In Progress", "Review", "Done"
            ),
            "Priority": select_field("Priority", "P0", "P1"),
            "Parent T-ID": {"id": "parent", "name": "Parent T-ID", "type": "ProjectV2Field"},
            "Owner Role": select_field("Owner Role", "Chisel Implementer"),
            "Depends On": {"id": "depends", "name": "Depends On", "type": "ProjectV2Field"},
            "Sprint": {"id": "sprint", "name": "Sprint", "type": "ProjectV2IterationField"},
            "Story Points": {"id": "points", "name": "Story Points", "type": "ProjectV2Field"},
            "Initial SP": {"id": "initial", "name": "Initial SP", "type": "ProjectV2Field"},
            "Demo Command": {"id": "demo", "name": "Demo Command", "type": "ProjectV2Field"},
            "Evidence Class": select_field("Evidence Class", "Host Functional"),
            "Review Outcome": {
                "id": "review-outcome",
                "name": "Review Outcome",
                "type": "ProjectV2Field",
            },
            "Observed Cycle": {
                "id": "observed-cycle",
                "name": "Observed Cycle",
                "type": "ProjectV2Field",
            },
            "Resource Use": {
                "id": "resource-use",
                "name": "Resource Use",
                "type": "ProjectV2Field",
            },
        }
        self._pull_request = {
            "number": 30,
            "state": "OPEN",
            "mergedAt": None,
            "url": "https://github.com/bhind/raveil/pull/30",
            "body": "Closes #27",
            "headRefName": self._branch,
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

    @staticmethod
    def iteration_id(title: str) -> str:
        if title != "S-0001":
            raise QueueError(f"Project Sprint has no unique current iteration {title!r}")
        return "iteration-s-0001"

    def pull_request(self, number: int) -> dict:
        return {**self._pull_request, "number": number}

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
        sprint="S-0001",
        story_points=5,
        demo="./demo.sh",
        evidence_class="Host Functional",
        apply=apply,
    )


def prepare_args(*, apply: bool = True) -> argparse.Namespace:
    return start_args(apply=apply)


def audit_args(*, require_horizon: bool) -> argparse.Namespace:
    return argparse.Namespace(
        fixture=None,
        check_branch=False,
        require_horizon=require_horizon,
    )


def complete_args(*, apply: bool = True) -> argparse.Namespace:
    return argparse.Namespace(
        issue=27,
        pr=30,
        review_outcome="Accepted at exact head",
        observed_cycle="One bounded session",
        resource_use="Host only; no paid resources",
        apply=apply,
    )


class ProjectQueueAuditTest(unittest.TestCase):
    def test_horizon_audit_fails_when_no_pullable_successor_exists(self) -> None:
        active_issue = issue(27, "T-0125 — Playable")
        active = item(27, active_issue["title"], "In Progress", "T-0125")
        queue = FakeQueue({"items": [active]}, [active_issue], "feat/t-0125-playable")
        output = io.StringIO()
        errors = io.StringIO()
        with redirect_stdout(output), patch("sys.stderr", errors):
            self.assertEqual(1, audit(queue, audit_args(require_horizon=True)))
        self.assertIn("0 pullable-Ready", output.getvalue())
        self.assertIn("do not return idle", errors.getvalue())

    def test_horizon_audit_accepts_one_complete_successor(self) -> None:
        active_issue = issue(27, "T-0125 — Playable")
        next_issue = issue(28, "T-0126 — Queue")
        active = item(27, active_issue["title"], "In Progress", "T-0125")
        successor = item(28, next_issue["title"], "Ready", "T-0126")
        successor["priority"] = "P1"
        successor["initial SP"] = 5
        queue = FakeQueue(
            {"items": [active, successor]},
            [active_issue, next_issue],
            "feat/t-0125-playable",
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, audit(queue, audit_args(require_horizon=True)))

    def test_pullable_ready_requires_complete_p1_successor(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        ready_item = item(27, one_issue["title"], "Ready", "T-0125")
        ready_item["priority"] = "P1"
        ready_item["initial SP"] = 5
        pullable, excluded = pullable_ready_items({"items": [ready_item]}, [one_issue])
        self.assertEqual([ready_item], pullable)
        self.assertEqual([], excluded)

        ready_item["demo Command"] = ""
        pullable, excluded = pullable_ready_items({"items": [ready_item]}, [one_issue])
        self.assertEqual([], pullable)
        self.assertIn("missing demo Command", excluded[0])

        ready_item["demo Command"] = "./demo.sh"
        ready_item["initial SP"] = None
        pullable, excluded = pullable_ready_items({"items": [ready_item]}, [one_issue])
        self.assertEqual([], pullable)
        self.assertIn("missing initial SP", excluded[0])

    def test_prepare_writes_complete_p1_metadata_before_ready(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        backlog = item(27, one_issue["title"], "Backlog", "T-0125")
        queue = FakeQueue({"items": [backlog]}, [one_issue], "main")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, prepare(queue, prepare_args()))
        self.assertEqual(("item-27", "Status", "Ready"), queue.edits[-1])
        self.assertIn(("item-27", "Priority", "P1"), queue.edits[:-1])
        self.assertIn(("item-27", "Initial SP", 5), queue.edits[:-1])

    def test_prepare_accepts_new_project_item_with_unset_status(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        unclassified = item(27, one_issue["title"], "", "T-0125")
        unclassified["status"] = None
        queue = FakeQueue({"items": [unclassified]}, [one_issue], "main")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, prepare(queue, prepare_args()))
        self.assertEqual(("item-27", "Status", "Ready"), queue.edits[-1])

    def test_prepare_refuses_a_second_ready_successor(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        other_issue = issue(28, "T-0126 — Queue")
        backlog = item(27, one_issue["title"], "Backlog", "T-0125")
        ready = item(28, other_issue["title"], "Ready", "T-0126")
        queue = FakeQueue({"items": [backlog, ready]}, [one_issue, other_issue], "main")
        with self.assertRaisesRegex(QueueError, "existing Ready successor"):
            prepare(queue, prepare_args())
        self.assertEqual([], queue.edits)

    def test_prepare_refuses_to_rewrite_initial_points(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        backlog = item(27, one_issue["title"], "Backlog", "T-0125")
        backlog["initial SP"] = 8
        queue = FakeQueue({"items": [backlog]}, [one_issue], "main")
        with self.assertRaisesRegex(QueueError, "cannot rewrite Initial SP"):
            prepare(queue, prepare_args())
        self.assertEqual([], queue.edits)

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

    def test_ready_issue_may_have_no_metadata_before_start(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        ready_item = item(27, one_issue["title"], "Ready", "T-0125")
        for field in (
            "priority",
            "parent T-ID",
            "owner Role",
            "depends On",
            "sprint",
            "story Points",
            "demo Command",
            "evidence Class",
        ):
            ready_item.pop(field)
        self.assertEqual([], audit_state({"items": [ready_item]}, [one_issue]))

        queue = FakeQueue({"items": [ready_item]}, [one_issue], "feat/t-0125-playable")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, start(queue, start_args()))
        self.assertEqual("Parent T-ID", queue.edits[1][1])
        self.assertEqual("T-0125", queue.edits[1][2])
        self.assertEqual(("item-27", "Status", "In Progress"), queue.edits[-1])

    def test_ready_issue_rejects_incorrect_existing_parent(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        ready_item = item(27, one_issue["title"], "Ready", "T-9999")
        errors = audit_state({"items": [ready_item]}, [one_issue])
        self.assertTrue(any("Parent T-ID mismatch" in error for error in errors))

    def test_active_issue_requires_sprint(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        active_item = item(27, one_issue["title"], "In Progress", "T-0125")
        active_item.pop("sprint")
        errors = audit_state({"items": [active_item]}, [one_issue])
        self.assertIn(
            "active work-item lacks sprint: https://github.com/bhind/raveil/issues/27",
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

    def test_packet_marker_values_cannot_be_empty(self) -> None:
        empty_dependencies = PACKET.replace("Dependencies: none", "Dependencies:\n")
        self.assertIn("Dependencies", missing_packet_markers(empty_dependencies))

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
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, start(queue, start_args()))
        self.assertEqual("Status", queue.edits[-1][1])
        self.assertEqual("In Progress", queue.edits[-1][2])
        self.assertIn(("item-27", "Sprint", "iteration-s-0001"), queue.edits[:-1])

    def test_start_rejects_unknown_sprint_without_remote_edit(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        project = {"items": [item(27, one_issue["title"], "Ready", "T-0125")]}
        queue = FakeQueue(project, [one_issue], "feat/t-0125-playable")
        args = start_args()
        args.sprint = "S-9999"
        with self.assertRaisesRegex(QueueError, "no unique current iteration"):
            start(queue, args)
        self.assertEqual([], queue.edits)

        args.apply = False
        with self.assertRaisesRegex(QueueError, "no unique current iteration"):
            start(queue, args)
        self.assertEqual([], queue.edits)

    def test_start_rejects_non_iteration_sprint_field_without_remote_edit(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        project = {"items": [item(27, one_issue["title"], "Ready", "T-0125")]}
        queue = FakeQueue(project, [one_issue], "feat/t-0125-playable")
        queue._fields["Sprint"]["type"] = "ProjectV2Field"
        with self.assertRaisesRegex(QueueError, "not an Iteration field"):
            start(queue, start_args())
        self.assertEqual([], queue.edits)

    def test_iteration_field_uses_iteration_id_flag(self) -> None:
        queue = ProjectQueue("bhind", "bhind/raveil", 1)
        field = {
            "id": "field-sprint",
            "name": "Sprint",
            "type": "ProjectV2IterationField",
        }
        with (
            patch.object(queue, "project_identity", return_value="project-id"),
            patch("scripts.project_queue.run") as run_command,
        ):
            queue.edit_field("item-id", field, value="iteration-id")
        run_command.assert_called_once_with(
            [
                "gh",
                "project",
                "item-edit",
                "--id",
                "item-id",
                "--project-id",
                "project-id",
                "--field-id",
                "field-sprint",
                "--iteration-id",
                "iteration-id",
            ]
        )

    def test_start_rejects_blank_required_values_without_remote_edit(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        project = {"items": [item(27, one_issue["title"], "Ready", "T-0125")]}
        for attribute in ("owner_role", "depends_on", "sprint", "demo", "evidence_class"):
            with self.subTest(attribute=attribute):
                queue = FakeQueue(project, [one_issue], "feat/t-0125-playable")
                args = start_args()
                setattr(args, attribute, "  ")
                with self.assertRaisesRegex(QueueError, "must be nonblank"):
                    start(queue, args)
                self.assertEqual([], queue.edits)

    def test_start_rejects_nonpositive_points_without_remote_edit(self) -> None:
        one_issue = issue(27, "T-0125 — Playable")
        project = {"items": [item(27, one_issue["title"], "Ready", "T-0125")]}
        for points in (0, -1):
            with self.subTest(points=points):
                queue = FakeQueue(project, [one_issue], "feat/t-0125-playable")
                args = start_args()
                args.story_points = points
                with self.assertRaisesRegex(QueueError, "positive integer"):
                    start(queue, args)
                self.assertEqual([], queue.edits)

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
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, review(queue, args))
        self.assertEqual([("item-27", "Status", "Review")], queue.edits)

    def test_complete_writes_evidence_before_done(self) -> None:
        closed = issue(27, "T-0125 — Playable", state="CLOSED")
        review_item = item(27, closed["title"], "Review", "T-0125")
        queue = FakeQueue(
            {"items": [review_item]}, [closed], "feat/t-0125-playable"
        )
        queue._pull_request.update(state="MERGED", mergedAt="2026-09-04T00:00:00Z")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, complete(queue, complete_args()))
        self.assertEqual(("item-27", "Status", "Done"), queue.edits[-1])
        self.assertEqual(
            ["Review Outcome", "Observed Cycle", "Resource Use"],
            [entry[1] for entry in queue.edits[:-1]],
        )

    def test_complete_dry_run_does_not_edit(self) -> None:
        closed = issue(27, "T-0125 — Playable", state="CLOSED")
        review_item = item(27, closed["title"], "Review", "T-0125")
        queue = FakeQueue(
            {"items": [review_item]}, [closed], "feat/t-0125-playable"
        )
        queue._pull_request.update(state="MERGED", mergedAt="2026-09-04T00:00:00Z")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, complete(queue, complete_args(apply=False)))
        self.assertEqual([], queue.edits)

    def test_complete_is_idempotent_after_done(self) -> None:
        closed = issue(27, "T-0125 — Playable", state="CLOSED")
        done_item = item(27, closed["title"], "Done", "T-0125")
        queue = FakeQueue({"items": [done_item]}, [closed], "main")
        queue._pull_request.update(
            state="MERGED",
            mergedAt="2026-09-04T00:00:00Z",
            headRefName="feat/t-0125-playable",
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, complete(queue, complete_args()))
        self.assertEqual([], queue.edits)

    def test_complete_rejects_open_issue_or_unmerged_pr(self) -> None:
        open_issue = issue(27, "T-0125 — Playable")
        review_item = item(27, open_issue["title"], "Review", "T-0125")
        queue = FakeQueue(
            {"items": [review_item]}, [open_issue], "feat/t-0125-playable"
        )
        with self.assertRaisesRegex(QueueError, "closed work-item Issue"):
            complete(queue, complete_args())
        self.assertEqual([], queue.edits)

        closed = issue(27, "T-0125 — Playable", state="CLOSED")
        queue = FakeQueue(
            {"items": [review_item]}, [closed], "feat/t-0125-playable"
        )
        with self.assertRaisesRegex(QueueError, "merged pull request"):
            complete(queue, complete_args())
        self.assertEqual([], queue.edits)

    def test_complete_rejects_mismatch_before_remote_edit(self) -> None:
        closed = issue(27, "T-0125 — Playable", state="CLOSED")
        review_item = item(27, closed["title"], "Review", "T-0125")
        queue = FakeQueue(
            {"items": [review_item]}, [closed], "feat/t-0125-playable"
        )
        queue._pull_request.update(
            state="MERGED",
            mergedAt="2026-09-04T00:00:00Z",
            headRefName="feat/t-0999-other",
        )
        with self.assertRaisesRegex(QueueError, "does not match"):
            complete(queue, complete_args())
        self.assertEqual([], queue.edits)

    def test_complete_rejects_missing_close_reference(self) -> None:
        closed = issue(27, "T-0125 — Playable", state="CLOSED")
        review_item = item(27, closed["title"], "Review", "T-0125")
        queue = FakeQueue(
            {"items": [review_item]}, [closed], "feat/t-0125-playable"
        )
        queue._pull_request.update(
            state="MERGED",
            mergedAt="2026-09-04T00:00:00Z",
            body="Related to #27",
        )
        with self.assertRaisesRegex(QueueError, "must contain Closes"):
            complete(queue, complete_args())
        self.assertEqual([], queue.edits)

    def test_complete_rejects_blank_evidence_or_wrong_status(self) -> None:
        closed = issue(27, "T-0125 — Playable", state="CLOSED")
        backlog = item(27, closed["title"], "Backlog", "T-0125")
        queue = FakeQueue({"items": [backlog]}, [closed], "feat/t-0125-playable")
        queue._pull_request.update(state="MERGED", mergedAt="2026-09-04T00:00:00Z")
        args = complete_args()
        args.review_outcome = "  "
        with self.assertRaisesRegex(QueueError, "review-outcome.*nonblank"):
            complete(queue, args)
        self.assertEqual([], queue.edits)

        args.review_outcome = "Accepted"
        with self.assertRaisesRegex(QueueError, "status Review"):
            complete(queue, args)
        self.assertEqual([], queue.edits)

    def test_complete_preflights_fields_before_remote_edit(self) -> None:
        closed = issue(27, "T-0125 — Playable", state="CLOSED")
        review_item = item(27, closed["title"], "Review", "T-0125")
        queue = FakeQueue(
            {"items": [review_item]}, [closed], "feat/t-0125-playable"
        )
        queue._pull_request.update(state="MERGED", mergedAt="2026-09-04T00:00:00Z")
        del queue._fields["Resource Use"]
        with self.assertRaisesRegex(QueueError, "missing required field"):
            complete(queue, complete_args())
        self.assertEqual([], queue.edits)

    def test_complete_remote_evidence_failure_never_writes_done(self) -> None:
        closed = issue(27, "T-0125 — Playable", state="CLOSED")
        review_item = item(27, closed["title"], "Review", "T-0125")
        queue = FakeQueue(
            {"items": [review_item]}, [closed], "feat/t-0125-playable"
        )
        queue._pull_request.update(state="MERGED", mergedAt="2026-09-04T00:00:00Z")
        writes: list[str] = []

        def fail_second_write(item_id: str, field: dict, *, value: object) -> None:
            del item_id, value
            writes.append(field["name"])
            if field["name"] == "Observed Cycle":
                raise QueueError("simulated remote write failure")

        queue.edit_field = fail_second_write  # type: ignore[method-assign]
        with self.assertRaisesRegex(QueueError, "simulated remote write failure"):
            complete(queue, complete_args())
        self.assertEqual(["Review Outcome", "Observed Cycle"], writes)
        self.assertNotIn("Status", writes)


if __name__ == "__main__":
    unittest.main()
