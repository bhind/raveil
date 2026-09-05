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
READY_STATUS = "Ready"
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
    "sprint",
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
        """Read only queue fields; reject partial snapshots before any transition."""
        query = """
        query($id: ID!, $cursor: String) {
          node(id: $id) { ... on ProjectV2 {
            items(first: 100, after: $cursor) {
              totalCount pageInfo { hasNextPage endCursor }
              nodes {
                id
                content {
                  __typename
                  ... on Issue { id number title url }
                  ... on DraftIssue { id title body }
                  ... on PullRequest { id number title url }
                }
                fieldValues(first: 100) {
                  pageInfo { hasNextPage }
                  nodes {
                    ... on ProjectV2ItemFieldTextValue {
                      text field { ... on ProjectV2Field { name } }
                    }
                    ... on ProjectV2ItemFieldNumberValue {
                      number field { ... on ProjectV2Field { name } }
                    }
                    ... on ProjectV2ItemFieldDateValue {
                      date field { ... on ProjectV2Field { name } }
                    }
                    ... on ProjectV2ItemFieldSingleSelectValue {
                      name field { ... on ProjectV2SingleSelectField { name } }
                    }
                    ... on ProjectV2ItemFieldIterationValue {
                      title startDate duration iterationId
                      field { ... on ProjectV2IterationField { name } }
                    }
                  }
                }
              }
            }
          } }
        }
        """
        identity = self.project_identity()
        cursor: str | None = None
        seen_cursors: set[str] = set()
        seen_items: set[str] = set()
        items: list[dict[str, Any]] = []
        total: int | None = None
        while True:
            arguments = ["api", "graphql", "-f", f"query={query}", "-f", f"id={identity}"]
            if cursor is not None:
                arguments.extend(("-f", f"cursor={cursor}"))
            payload = gh_json(arguments)
            try:
                connection = payload["data"]["node"]["items"]
                count = connection["totalCount"]
                page = connection["pageInfo"]
                nodes = connection["nodes"]
                if payload.get("errors") or type(count) is not int or not 0 <= count <= 1000:
                    raise ValueError("invalid or oversized inventory")
                if total is not None and total != count:
                    raise ValueError("Project changed while paginating")
                total = count
                if not isinstance(nodes, list) or type(page["hasNextPage"]) is not bool:
                    raise ValueError("malformed page")
                for node in nodes:
                    item_id = node["id"]
                    if not isinstance(item_id, str) or not item_id or item_id in seen_items:
                        raise ValueError("missing or duplicate item identity")
                    seen_items.add(item_id)
                    content = dict(node["content"] or {})
                    content["type"] = content.pop("__typename", "Redacted")
                    entry: dict[str, Any] = {
                        "id": item_id, "title": content.get("title", "Unavailable item"),
                        "content": content,
                    }
                    values = node["fieldValues"]
                    if values["pageInfo"]["hasNextPage"] is not False:
                        raise ValueError("truncated item fields")
                    for value in values["nodes"]:
                        if not value:
                            continue  # Unused built-in fields have no selected fragments.
                        field_name = value["field"]["name"]
                        if not isinstance(field_name, str) or not field_name:
                            raise ValueError("invalid field name")
                        key = field_name[0].lower() + field_name[1:]
                        if key == "title" and value.get("text") == entry["title"]:
                            continue  # GitHub repeats content.title as its built-in Title field.
                        if key in entry:
                            raise ValueError(f"duplicate or inconsistent normalized field: {key}")
                        if "iterationId" in value:
                            result = {k: value[k] for k in ("title", "startDate", "duration", "iterationId")}
                        else:
                            kinds = [k for k in ("text", "number", "date", "name") if k in value]
                            if len(kinds) != 1:
                                raise ValueError("ambiguous field value")
                            result = value[kinds[0]]
                        entry[key] = result
                    items.append(entry)
                if len(items) > total:
                    raise ValueError("inventory exceeds declared count")
                if not page["hasNextPage"]:
                    if len(items) != total:
                        raise ValueError("incomplete Project inventory")
                    return {"items": items, "totalCount": total}
                cursor = page["endCursor"]
                if not nodes or not isinstance(cursor, str) or not cursor or cursor in seen_cursors:
                    raise ValueError("missing or repeated pagination cursor")
                seen_cursors.add(cursor)
            except (KeyError, TypeError, ValueError) as error:
                raise QueueError(f"incomplete or inconsistent Project read: {error}") from error

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
                "number,title,url,state,body,headRefName,mergedAt",
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
        query = """
        query($id: ID!) {
          node(id: $id) { ... on ProjectV2 {
            fields(first: 100) {
              pageInfo { hasNextPage }
              nodes {
                __typename
                ... on ProjectV2Field { id name }
                ... on ProjectV2SingleSelectField { id name options { id name } }
                ... on ProjectV2IterationField { id name }
              }
            }
          } }
        }
        """
        payload = gh_json(("api", "graphql", "-f", f"query={query}",
                           "-f", f"id={self.project_identity()}"))
        try:
            connection = payload["data"]["node"]["fields"]
            if payload.get("errors") or connection["pageInfo"]["hasNextPage"] is not False:
                raise ValueError("truncated Project fields")
            result: dict[str, dict[str, Any]] = {}
            identities: set[str] = set()
            for node in connection["nodes"]:
                field = dict(node)
                field["type"] = field.pop("__typename")
                name, identity = field["name"], field["id"]
                if (not isinstance(name, str) or not name.strip() or name in result
                        or not isinstance(identity, str) or not identity.strip() or identity in identities):
                    raise ValueError("missing, malformed or duplicate Project field")
                identities.add(identity)
                if field["type"] not in {
                    "ProjectV2Field", "ProjectV2SingleSelectField", "ProjectV2IterationField"
                }:
                    raise ValueError("unknown Project field type")
                if field["type"] == "ProjectV2SingleSelectField":
                    options = field["options"]
                    if not isinstance(options, list):
                        raise ValueError("malformed single-select options")
                    option_names: set[str] = set()
                    option_ids: set[str] = set()
                    for option in options:
                        option_name, option_identity = option["name"], option["id"]
                        if (not isinstance(option_name, str) or not option_name.strip()
                                or not isinstance(option_identity, str) or not option_identity.strip()
                                or option_name in option_names or option_identity in option_ids):
                            raise ValueError("missing, malformed or duplicate single-select option")
                        option_names.add(option_name)
                        option_ids.add(option_identity)
                result[name] = field
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise QueueError(f"incomplete or inconsistent Project fields: {error}") from error

    def iteration_id(self, title: str) -> str:
        query = """
        query($login: String!, $number: Int!) {
          user(login: $login) {
            projectV2(number: $number) {
              field(name: "Sprint") {
                ... on ProjectV2IterationField {
                  configuration {
                    iterations { id title }
                  }
                }
              }
            }
          }
        }
        """
        payload = gh_json(
            (
                "api",
                "graphql",
                "-f",
                f"query={query}",
                "-F",
                f"login={self.owner}",
                "-F",
                f"number={self.project_number}",
            )
        )
        try:
            iterations = payload["data"]["user"]["projectV2"]["field"][
                "configuration"
            ]["iterations"]
        except (KeyError, TypeError) as error:
            raise QueueError("Project Sprint iteration configuration is unavailable") from error
        matches = [entry for entry in iterations if entry.get("title") == title]
        if len(matches) != 1:
            raise QueueError(f"Project Sprint has no unique current iteration {title!r}")
        return matches[0]["id"]

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
        elif field["type"] == "ProjectV2IterationField":
            command.extend(("--iteration-id", str(value)))
        elif field["name"] in {"Story Points", "Initial SP"}:
            command.extend(("--number", str(value)))
        else:
            command.extend(("--text", str(value)))
        run(command)


def validate_issue_for_start(issue: dict[str, Any], branch: str) -> str:
    issue_identity = validate_issue_packet(issue)
    if branch_work_id(branch) != issue_identity:
        raise QueueError(f"branch {branch!r} does not match Issue work item {issue_identity}")
    return task_id(issue_identity) or issue_identity


def validate_issue_packet(issue: dict[str, Any]) -> str:
    if issue.get("state") != "OPEN":
        raise QueueError("work item must be an open Issue")
    if not issue_has_label(issue, "work-item"):
        raise QueueError("Issue must carry the work-item label")
    issue_identity = work_id(issue.get("title", ""))
    if issue_identity is None:
        raise QueueError("Issue title must contain a stable T-ID")
    missing_markers = missing_packet_markers(issue.get("body", ""))
    if missing_markers:
        raise QueueError(f"Issue independence packet lacks: {', '.join(missing_markers)}")
    return issue_identity


def validate_closed_issue_packet(issue: dict[str, Any]) -> str:
    if issue.get("state") != "CLOSED":
        raise QueueError("completion requires a closed work-item Issue")
    if not issue_has_label(issue, "work-item"):
        raise QueueError("Issue must carry the work-item label")
    issue_identity = work_id(issue.get("title", ""))
    if issue_identity is None:
        raise QueueError("Issue title must contain a stable T-ID")
    missing_markers = missing_packet_markers(issue.get("body", ""))
    if missing_markers:
        raise QueueError(f"Issue independence packet lacks: {', '.join(missing_markers)}")
    return issue_identity


def pullable_ready_items(
    project: dict[str, Any], issues: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return completely prepared successor items and reasons Ready items are excluded."""
    issue_by_url = {issue["url"]: issue for issue in issues if issue.get("url")}
    pullable: list[dict[str, Any]] = []
    excluded: list[str] = []
    for item in project.get("items", []):
        if item.get("status") != READY_STATUS:
            continue
        content = item.get("content", {})
        url = content.get("url")
        problems: list[str] = []
        if content.get("type") != "Issue" or not url:
            problems.append("not a real Issue")
            issue = None
        else:
            issue = issue_by_url.get(url)
            if issue is None:
                problems.append("missing from issue inventory")
            else:
                if issue.get("state") != "OPEN":
                    problems.append("Issue is not open")
                if not issue_has_label(issue, "work-item"):
                    problems.append("Issue lacks work-item label")
                identity = work_id(issue.get("title", ""))
                if identity is None:
                    problems.append("Issue title lacks stable T-ID")
                elif item.get("parent T-ID") != task_id(identity):
                    problems.append("Parent T-ID differs")
                missing = missing_packet_markers(issue.get("body", ""))
                if missing:
                    problems.append(f"incomplete packet: {', '.join(missing)}")
        if item.get("priority") != "P1":
            problems.append("Priority is not P1")
        if item.get("initial SP") in (None, ""):
            problems.append("missing initial SP")
        for field in REQUIRED_ACTIVE_FIELDS:
            if item.get(field) in (None, ""):
                problems.append(f"missing {field}")
        if problems:
            excluded.append(f"{url or item.get('title')}: {', '.join(problems)}")
        else:
            pullable.append(item)
    return pullable, excluded


def validate_start_arguments(args: argparse.Namespace) -> None:
    required = {
        "owner-role": args.owner_role,
        "depends-on": args.depends_on,
        "sprint": args.sprint,
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

    fields = queue.fields()
    required_fields = (
        "Priority",
        "Parent T-ID",
        "Owner Role",
        "Depends On",
        "Sprint",
        "Story Points",
        "Demo Command",
        "Evidence Class",
        "Status",
    )
    for name in required_fields:
        if name not in fields:
            raise QueueError(f"Project is missing required field {name!r}")
    if fields["Sprint"]["type"] != "ProjectV2IterationField":
        raise QueueError("Project field 'Sprint' is not an Iteration field")
    sprint_id = queue.iteration_id(args.sprint)
    metadata_values = {
        "Priority": "P0",
        "Parent T-ID": issue_tid,
        "Owner Role": args.owner_role,
        "Depends On": args.depends_on,
        "Sprint": sprint_id,
        "Story Points": args.story_points,
        "Demo Command": args.demo,
        "Evidence Class": args.evidence_class,
    }
    for name, value in metadata_values.items():
        if fields[name]["type"] == "ProjectV2SingleSelectField":
            queue.option_id(fields[name], str(value))
    queue.option_id(fields["Status"], "In Progress")

    actions = (
        "set Priority=P0",
        f"set Parent T-ID={issue_tid}",
        f"set Owner Role={args.owner_role}",
        f"set Depends On={args.depends_on}",
        f"set Sprint={args.sprint}",
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

    for name, value in metadata_values.items():
        queue.edit_field(item["id"], fields[name], value=value)
    queue.edit_field(item["id"], fields["Status"], value="In Progress")
    print(f"started Issue #{args.issue}: {issue_tid}")
    return 0


def prepare(queue: ProjectQueue, args: argparse.Namespace) -> int:
    """Prepare one complete P1 successor and move it to Ready last."""
    validate_start_arguments(args)
    issue = queue.issue(args.issue)
    issue_identity = validate_issue_packet(issue)
    issue_tid = task_id(issue_identity) or issue_identity
    project = queue.project()
    item = queue.find_item(project, issue["url"])
    if item is None:
        raise QueueError("Issue must be linked to the Project before prepare")
    if item.get("status") not in {None, "", "Backlog", READY_STATUS}:
        raise QueueError(
            "prepare requires an unset/Backlog status (or idempotent Ready)"
        )
    other_ready = [
        entry
        for entry in project.get("items", [])
        if entry.get("status") == READY_STATUS and entry.get("id") != item.get("id")
    ]
    if other_ready:
        raise QueueError("prepare requires the existing Ready successor to be resolved first")
    current_errors = audit_state(project, queue.issues())
    if current_errors:
        raise QueueError(f"current Project audit failed: {'; '.join(current_errors)}")
    existing_initial = item.get("initial SP")
    if existing_initial not in (None, "") and int(existing_initial) != args.story_points:
        raise QueueError("prepare cannot rewrite Initial SP")

    fields = queue.fields()
    required_fields = (
        "Priority",
        "Parent T-ID",
        "Owner Role",
        "Depends On",
        "Sprint",
        "Initial SP",
        "Story Points",
        "Demo Command",
        "Evidence Class",
        "Status",
    )
    for name in required_fields:
        if name not in fields:
            raise QueueError(f"Project is missing required field {name!r}")
    if fields["Sprint"]["type"] != "ProjectV2IterationField":
        raise QueueError("Project field 'Sprint' is not an Iteration field")
    sprint_id = queue.iteration_id(args.sprint)
    metadata_values = {
        "Priority": "P1",
        "Parent T-ID": issue_tid,
        "Owner Role": args.owner_role,
        "Depends On": args.depends_on,
        "Sprint": sprint_id,
        "Initial SP": args.story_points,
        "Story Points": args.story_points,
        "Demo Command": args.demo,
        "Evidence Class": args.evidence_class,
    }
    for name, value in metadata_values.items():
        if fields[name]["type"] == "ProjectV2SingleSelectField":
            queue.option_id(fields[name], str(value))
    queue.option_id(fields["Status"], READY_STATUS)

    actions = tuple(
        [
            f"set {name}={args.sprint if name == 'Sprint' else value}"
            for name, value in metadata_values.items()
        ]
        + ["set Status=Ready last"]
    )
    if not args.apply:
        print("dry-run:")
        for action in actions:
            print(f"- {action}")
        return 0

    for name, value in metadata_values.items():
        queue.edit_field(item["id"], fields[name], value=value)
    queue.edit_field(item["id"], fields["Status"], value=READY_STATUS)
    print(f"prepared Issue #{args.issue}: {issue_tid}")
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


def complete(queue: ProjectQueue, args: argparse.Namespace) -> int:
    """Finalize one merged item with Done written last.

    GitHub field edits are not transactional. A failed evidence-field write
    may leave earlier evidence edits visible, but Status remains Review and a
    retry safely rewrites the evidence before attempting Done again.
    """
    evidence_values = {
        "Review Outcome": args.review_outcome,
        "Observed Cycle": args.observed_cycle,
        "Resource Use": args.resource_use,
    }
    for name, value in evidence_values.items():
        if not isinstance(value, str) or not value.strip():
            raise QueueError(f"--{name.lower().replace(' ', '-')} must be nonblank")

    issue = queue.issue(args.issue)
    issue_identity = validate_closed_issue_packet(issue)
    pull = queue.pull_request(args.pr)
    if pull.get("state") != "MERGED" or not pull.get("mergedAt"):
        raise QueueError("completion requires a merged pull request")
    if branch_work_id(pull.get("headRefName", "")) != issue_identity:
        raise QueueError("pull-request branch T-ID does not match the Issue")
    if not closing_reference(pull.get("body", ""), args.issue):
        raise QueueError(f"pull request must contain Closes #{args.issue}")

    project = queue.project()
    item = queue.find_item(project, issue["url"])
    if item is None:
        raise QueueError("Issue is missing from the Project")
    if item.get("status") not in {"Review", "Done"}:
        raise QueueError("completion requires Project status Review (or idempotent Done)")

    expected_target_errors = {
        f"active Project item is not an open Issue: {issue['url']}",
        f"closed work-item Issue is not Done in Project: {issue['url']}",
    }
    current_errors = [
        error
        for error in audit_state(project, queue.issues())
        if error not in expected_target_errors
    ]
    if current_errors:
        raise QueueError(f"current Project audit failed: {'; '.join(current_errors)}")

    fields = queue.fields()
    required_fields = (*evidence_values, "Status")
    for name in required_fields:
        if name not in fields:
            raise QueueError(f"Project is missing required field {name!r}")
    queue.option_id(fields["Status"], "Done")

    if item.get("status") == "Done":
        print(f"Issue #{args.issue} is already Done: {issue_identity}")
        return 0

    actions = tuple(
        [f"set {name}={value}" for name, value in evidence_values.items()]
        + ["set Status=Done last"]
    )
    if not args.apply:
        print("dry-run:")
        for action in actions:
            print(f"- {action}")
        return 0

    for name, value in evidence_values.items():
        queue.edit_field(item["id"], fields[name], value=value)
    queue.edit_field(item["id"], fields["Status"], value="Done")
    print(f"completed Issue #{args.issue}: {issue_identity} through PR #{args.pr}")
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
    ready = sum(item.get("status") == READY_STATUS for item in project.get("items", []))
    pullable, excluded = pullable_ready_items(project, issues)
    print(
        "project queue audit passed: "
        f"{active} active, {ready} Ready, {len(pullable)} pullable-Ready delivery item(s)"
    )
    if args.require_horizon and not pullable:
        print(
            "ERROR: delivery horizon is empty: replenish a complete P1 successor; do not return idle",
            file=sys.stderr,
        )
        for detail in excluded:
            print(f"ERROR: Ready item excluded: {detail}", file=sys.stderr)
        return 1
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
    audit_parser.add_argument("--require-horizon", action="store_true")
    audit_parser.set_defaults(handler=audit)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("issue", type=int)
    prepare_parser.add_argument("--owner-role", required=True)
    prepare_parser.add_argument("--depends-on", required=True)
    prepare_parser.add_argument("--sprint", required=True)
    prepare_parser.add_argument("--story-points", type=int, required=True)
    prepare_parser.add_argument("--demo", required=True)
    prepare_parser.add_argument("--evidence-class", required=True)
    prepare_parser.add_argument("--apply", action="store_true")
    prepare_parser.set_defaults(handler=prepare)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("issue", type=int)
    start_parser.add_argument("--owner-role", required=True)
    start_parser.add_argument("--depends-on", required=True)
    start_parser.add_argument("--sprint", required=True)
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

    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("issue", type=int)
    complete_parser.add_argument("--pr", type=int, required=True)
    complete_parser.add_argument("--review-outcome", required=True)
    complete_parser.add_argument("--observed-cycle", required=True)
    complete_parser.add_argument("--resource-use", required=True)
    complete_parser.add_argument("--apply", action="store_true")
    complete_parser.set_defaults(handler=complete)
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
