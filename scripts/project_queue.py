#!/usr/bin/env python3
"""Fail-closed GitHub Project queue checks and lifecycle transitions.

GitHub is coordination metadata.  TODO, STATUS, ADR, RFC, EXP, and executable
evidence remain authoritative.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Sequence


ACTIVE_STATUSES = {"In Progress", "Review"}
WORK_ID_RE = re.compile(r"\b(T-\d{4})(?:/(S\d{2}))?\b", re.IGNORECASE)
BRANCH_ID_RE = re.compile(r"\b(t-\d{4})(?:-(s\d{2}))?(?:-|$)", re.IGNORECASE)
CLOSING_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(?P<number>\d+)\b",
    re.IGNORECASE,
)
REQUIRED_ACTIVE_FIELDS = (
    "priority",
    "parent T-ID",
    "owner Role",
    "depends On",
    "story Points",
    "demo Command",
    "evidence Class",
)
REQUIRED_PACKET_MARKERS = {
    "Authority": r"\bauthority\s*:",
    "Dependencies": r"\b(?:dependencies|depends on|read-only dependencies)\s*:",
    "Mutation owner": r"\bmutation owner\s*:",
    "Allowlist": r"\b(?:mutation )?allowlist\s*:",
    "Artifacts": r"\bartifacts?\s*:",
    "Acceptance": r"\bacceptance\s*:",
    "Evidence class": r"\bevidence class\s*:",
    "Stop rule": r"\bstop(?: rule)?\s*:",
    "Non-claims": r"\bnon-claims?\s*:",
}


class QueueError(RuntimeError):
    """A queue invariant or GitHub command failed."""


def run(command: Sequence[str]) -> str:
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise QueueError(f"command failed ({completed.returncode}): {' '.join(command)}: {detail}")
    return completed.stdout


def gh_json(arguments: Sequence[str]) -> Any:
    raw = run(("gh", *arguments))
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise QueueError(f"gh returned invalid JSON: {error}") from error


def work_id(text: str) -> str | None:
    match = WORK_ID_RE.search(text)
    if match is None:
        return None
    task = match.group(1).upper()
    return f"{task}/{match.group(2).upper()}" if match.group(2) else task


def task_id(text: str) -> str | None:
    identity = work_id(text)
    return identity.split("/", 1)[0] if identity else None


def branch_work_id(branch: str) -> str | None:
    match = BRANCH_ID_RE.search(branch)
    if match is None:
        return None
    task = match.group(1).upper()
    return f"{task}/{match.group(2).upper()}" if match.group(2) else task


def missing_packet_markers(body: str) -> list[str]:
    matches = {
        name: re.search(pattern, body, re.IGNORECASE)
        for name, pattern in REQUIRED_PACKET_MARKERS.items()
    }
    missing: list[str] = []
    for name, match in matches.items():
        if match is None:
            missing.append(name)
            continue
        following = [
            other.start()
            for other in matches.values()
            if other is not None and other.start() > match.end()
        ]
        end = min(following, default=len(body))
        if not body[match.end() : end].strip().strip("-* "):
            missing.append(name)
    return missing


def issue_has_label(issue: dict[str, Any], label: str) -> bool:
    return any(
        entry == label or (isinstance(entry, dict) and entry.get("name") == label)
        for entry in issue.get("labels", [])
    )


def closing_reference(body: str, issue_number: int) -> bool:
    return any(int(match.group("number")) == issue_number for match in CLOSING_RE.finditer(body))


def audit_state(
    project: dict[str, Any],
    issues: list[dict[str, Any]],
    branch: str | None = None,
) -> list[str]:
    errors: list[str] = []
    items = project.get("items", [])
    issue_by_url = {issue["url"]: issue for issue in issues if issue.get("url")}
    item_by_url = {
        item.get("content", {}).get("url"): item
        for item in items
        if item.get("content", {}).get("url")
    }

    for issue in issues:
        if (
            issue.get("state") == "OPEN"
            and issue_has_label(issue, "work-item")
            and issue.get("url") not in item_by_url
        ):
            errors.append(f"open work-item issue missing from Project: {issue.get('url')}")

    active_items = [item for item in items if item.get("status") in ACTIVE_STATUSES]
    if len(active_items) > 2:
        errors.append(f"delivery WIP exceeds two: {len(active_items)} active items")

    active_task_ids: set[str] = set()
    for item in items:
        content = item.get("content", {})
        status = item.get("status")
        url = content.get("url")
        if status in ACTIVE_STATUSES and content.get("type") != "Issue":
            errors.append(f"active Project item is not a real Issue: {item.get('title')}")
            continue
        if content.get("type") != "Issue" or not url:
            continue

        issue = issue_by_url.get(url)
        if issue is None:
            if status in ACTIVE_STATUSES:
                errors.append(f"active Project Issue missing from issue inventory: {url}")
            continue
        is_work = issue_has_label(issue, "work-item")
        if status in ACTIVE_STATUSES and not is_work:
            errors.append(f"active Issue lacks work-item label: {url}")
        if not is_work:
            continue

        state = issue.get("state")
        if status in ACTIVE_STATUSES and state != "OPEN":
            errors.append(f"active Project item is not an open Issue: {url}")
        if status == "Done" and state != "CLOSED":
            errors.append(f"Done Project item still has an open Issue: {url}")
        if state == "CLOSED" and status != "Done":
            errors.append(f"closed work-item Issue is not Done in Project: {url}")

        title_work_id = work_id(issue.get("title", ""))
        title_tid = task_id(issue.get("title", ""))
        parent_tid = item.get("parent T-ID")
        if title_tid is None:
            errors.append(f"work-item title lacks stable T-ID: {url}")
        elif status in ACTIVE_STATUSES or status == "Done":
            if parent_tid != title_tid:
                errors.append(
                    f"Project Parent T-ID mismatch for {url}: expected {title_tid}, got {parent_tid!r}"
                )
        elif parent_tid not in (None, "") and parent_tid != title_tid:
            errors.append(
                f"Project Parent T-ID mismatch for {url}: expected {title_tid}, got {parent_tid!r}"
            )
        if status in ACTIVE_STATUSES:
            if title_work_id:
                active_task_ids.add(title_work_id)
            missing_markers = missing_packet_markers(issue.get("body", ""))
            if missing_markers:
                errors.append(
                    f"active work-item has incomplete independence packet ({', '.join(missing_markers)}): {url}"
                )
            if item.get("priority") != "P0":
                errors.append(f"active work-item is not Priority P0: {url}")
            for field in REQUIRED_ACTIVE_FIELDS:
                if item.get(field) in (None, ""):
                    errors.append(f"active work-item lacks {field}: {url}")

    if branch and branch not in {"main", "HEAD"}:
        branch_identity = branch_work_id(branch)
        if branch_identity is None:
            errors.append(f"task branch lacks a stable T-ID: {branch}")
        elif branch_identity not in active_task_ids:
            errors.append(f"branch {branch} has no matching active Project Issue")

    return errors


class ProjectQueue:
    def __init__(self, owner: str, repository: str, project_number: int) -> None:
        self.owner = owner
        self.repository = repository
        self.project_number = project_number

    def project(self) -> dict[str, Any]:
        return gh_json(
            (
                "project",
                "item-list",
                str(self.project_number),
                "--owner",
                self.owner,
                "--limit",
                "200",
                "--format",
                "json",
            )
        )

    def issues(self) -> list[dict[str, Any]]:
        return gh_json(
            (
                "issue",
                "list",
                "--repo",
                self.repository,
                "--label",
                "work-item",
                "--state",
                "all",
                "--limit",
                "200",
                "--json",
                "number,title,url,state,labels,body",
            )
        )

    def issue(self, number: int) -> dict[str, Any]:
        return gh_json(
            (
                "issue",
                "view",
                str(number),
                "--repo",
                self.repository,
                "--json",
                "number,title,url,state,labels,body",
            )
        )

    def pull_request(self, number: int) -> dict[str, Any]:
        return gh_json(
            (
                "pr",
                "view",
                str(number),
                "--repo",
                self.repository,
                "--json",
                "number,title,url,state,body,headRefName",
            )
        )

    def branch(self) -> str:
        return run(("git", "branch", "--show-current")).strip()

    def project_identity(self) -> str:
        return gh_json(
            (
                "project",
                "view",
                str(self.project_number),
                "--owner",
                self.owner,
                "--format",
                "json",
            )
        )["id"]

    def fields(self) -> dict[str, dict[str, Any]]:
        payload = gh_json(
            (
                "project",
                "field-list",
                str(self.project_number),
                "--owner",
                self.owner,
                "--limit",
                "100",
                "--format",
                "json",
            )
        )
        return {field["name"]: field for field in payload["fields"]}

    @staticmethod
    def find_item(project: dict[str, Any], issue_url: str) -> dict[str, Any] | None:
        return next(
            (
                item
                for item in project.get("items", [])
                if item.get("content", {}).get("url") == issue_url
            ),
            None,
        )

    @staticmethod
    def option_id(field: dict[str, Any], name: str) -> str:
        option = next((entry for entry in field.get("options", []) if entry["name"] == name), None)
        if option is None:
            raise QueueError(f"Project field {field['name']} has no option {name!r}")
        return option["id"]

    def edit_field(
        self,
        item_id: str,
        field: dict[str, Any],
        *,
        value: str | int,
    ) -> None:
        command = [
            "gh",
            "project",
            "item-edit",
            "--id",
            item_id,
            "--project-id",
            self.project_identity(),
            "--field-id",
            field["id"],
        ]
        if field["type"] == "ProjectV2SingleSelectField":
            command.extend(("--single-select-option-id", self.option_id(field, str(value))))
        elif field["name"] in {"Story Points", "Initial SP"}:
            command.extend(("--number", str(value)))
        else:
            command.extend(("--text", str(value)))
        run(command)


def validate_issue_for_start(issue: dict[str, Any], branch: str) -> str:
    if issue.get("state") != "OPEN":
        raise QueueError("work item must be an open Issue")
    if not issue_has_label(issue, "work-item"):
        raise QueueError("Issue must carry the work-item label")
    issue_identity = work_id(issue.get("title", ""))
    if issue_identity is None:
        raise QueueError("Issue title must contain a stable T-ID")
    if branch_work_id(branch) != issue_identity:
        raise QueueError(f"branch {branch!r} does not match Issue work item {issue_identity}")
    missing_markers = missing_packet_markers(issue.get("body", ""))
    if missing_markers:
        raise QueueError(f"Issue independence packet lacks: {', '.join(missing_markers)}")
    return task_id(issue_identity) or issue_identity


def validate_start_arguments(args: argparse.Namespace) -> None:
    required = {
        "owner-role": args.owner_role,
        "depends-on": args.depends_on,
        "demo": args.demo,
        "evidence-class": args.evidence_class,
    }
    for name, value in required.items():
        if not isinstance(value, str) or not value.strip():
            raise QueueError(f"--{name} must be nonblank")
    if args.story_points <= 0:
        raise QueueError("--story-points must be a positive integer")


def start(queue: ProjectQueue, args: argparse.Namespace) -> int:
    validate_start_arguments(args)
    issue = queue.issue(args.issue)
    issue_tid = validate_issue_for_start(issue, queue.branch())
    project = queue.project()
    item = queue.find_item(project, issue["url"])
    if item is None:
        raise QueueError("Issue must be linked to the Project before start")
    if item.get("status") not in {"Ready", "In Progress"}:
        raise QueueError("start requires Project status Ready (or idempotent In Progress)")
    current_errors = audit_state(project, queue.issues())
    if current_errors:
        raise QueueError(f"current Project audit failed: {'; '.join(current_errors)}")
    active_count = sum(
        entry.get("status") in ACTIVE_STATUSES for entry in project.get("items", [])
    )
    if item.get("status") != "In Progress" and active_count >= 2:
        raise QueueError("start would exceed the two-item delivery WIP limit")

    actions = (
        "set Priority=P0",
        f"set Parent T-ID={issue_tid}",
        f"set Owner Role={args.owner_role}",
        f"set Depends On={args.depends_on}",
        f"set Story Points={args.story_points}",
        f"set Demo Command={args.demo}",
        f"set Evidence Class={args.evidence_class}",
        "set Status=In Progress last",
    )
    if not args.apply:
        print("dry-run:")
        for action in actions:
            print(f"- {action}")
        return 0

    fields = queue.fields()
    metadata_values = {
        "Priority": "P0",
        "Parent T-ID": issue_tid,
        "Owner Role": args.owner_role,
        "Depends On": args.depends_on,
        "Story Points": args.story_points,
        "Demo Command": args.demo,
        "Evidence Class": args.evidence_class,
    }
    for name, value in metadata_values.items():
        if name not in fields:
            raise QueueError(f"Project is missing required field {name!r}")
        if fields[name]["type"] == "ProjectV2SingleSelectField":
            queue.option_id(fields[name], str(value))
    if "Status" not in fields:
        raise QueueError("Project is missing required field 'Status'")
    queue.option_id(fields["Status"], "In Progress")
    for name, value in metadata_values.items():
        queue.edit_field(item["id"], fields[name], value=value)
    queue.edit_field(item["id"], fields["Status"], value="In Progress")
    print(f"started Issue #{args.issue}: {issue_tid}")
    return 0


def review(queue: ProjectQueue, args: argparse.Namespace) -> int:
    issue = queue.issue(args.issue)
    issue_tid = validate_issue_for_start(issue, queue.branch())
    pull = queue.pull_request(args.pr)
    if pull.get("state") != "OPEN":
        raise QueueError("review transition requires an open pull request")
    if branch_work_id(pull.get("headRefName", "")) != work_id(issue.get("title", "")):
        raise QueueError("pull-request branch T-ID does not match the Issue")
    if not closing_reference(pull.get("body", ""), args.issue):
        raise QueueError(f"pull request must contain Closes #{args.issue}")
    project = queue.project()
    item = queue.find_item(project, issue["url"])
    if item is None:
        raise QueueError("Issue is missing from the Project")
    if item.get("status") not in {"In Progress", "Review"}:
        raise QueueError("review requires Project status In Progress")
    current_errors = audit_state(project, queue.issues(), queue.branch())
    if current_errors:
        raise QueueError(f"current Project audit failed: {'; '.join(current_errors)}")
    if not args.apply:
        print(f"dry-run:\n- set {issue['url']} Status=Review for {pull['url']}")
        return 0
    fields = queue.fields()
    if "Status" not in fields:
        raise QueueError("Project is missing required field 'Status'")
    queue.option_id(fields["Status"], "Review")
    queue.edit_field(item["id"], fields["Status"], value="Review")
    print(f"moved Issue #{args.issue} to Review for PR #{args.pr}")
    return 0


def audit(queue: ProjectQueue, args: argparse.Namespace) -> int:
    if args.fixture:
        payload = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        project = payload["project"]
        issues = payload["issues"]
        branch = payload.get("branch")
    else:
        project = queue.project()
        issues = queue.issues()
        branch = queue.branch() if args.check_branch else None
    errors = audit_state(project, issues, branch)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    active = sum(item.get("status") in ACTIVE_STATUSES for item in project.get("items", []))
    print(f"project queue audit passed: {active} active delivery item(s)")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--owner", default="bhind")
    result.add_argument("--repo", default="bhind/raveil")
    result.add_argument("--project", type=int, default=1)
    subparsers = result.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--fixture")
    audit_parser.add_argument("--check-branch", action="store_true")
    audit_parser.set_defaults(handler=audit)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("issue", type=int)
    start_parser.add_argument("--owner-role", required=True)
    start_parser.add_argument("--depends-on", required=True)
    start_parser.add_argument("--story-points", type=int, required=True)
    start_parser.add_argument("--demo", required=True)
    start_parser.add_argument("--evidence-class", required=True)
    start_parser.add_argument("--apply", action="store_true")
    start_parser.set_defaults(handler=start)

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("issue", type=int)
    review_parser.add_argument("--pr", type=int, required=True)
    review_parser.add_argument("--apply", action="store_true")
    review_parser.set_defaults(handler=review)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    queue = ProjectQueue(args.owner, args.repo, args.project)
    try:
        return args.handler(queue, args)
    except (QueueError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
