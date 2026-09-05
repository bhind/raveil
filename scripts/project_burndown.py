#!/usr/bin/env python3
"""Update a private Project draft with daily aggregate burndown data.

The draft is coordination metadata. It never changes repository records,
Project lifecycle fields, or evidence state.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
import subprocess
from typing import Any, Callable, Sequence


TITLE = "Raveil iteration burndown"
START = "<!-- raveil-burndown-data:"
END = ":raveil-burndown-data -->"
ACTIVE = {"Backlog", "Ready", "In Progress", "Blocked", "Review"}


class BurndownError(RuntimeError):
    pass


def run(command: Sequence[str]) -> str:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise BurndownError(completed.stderr.strip() or "GitHub command failed")
    return completed.stdout


def graphql(runner: Callable[[Sequence[str]], str], query: str) -> dict[str, Any]:
    try:
        payload = json.loads(runner(("gh", "api", "graphql", "-f", f"query={query}")))
    except json.JSONDecodeError as error:
        raise BurndownError("GitHub returned malformed JSON") from error
    if payload.get("errors"):
        raise BurndownError("GitHub GraphQL query failed")
    return payload


def inventory(owner: str, project: int, runner=run) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    cursor: str | None = None
    project_data: dict[str, Any] | None = None
    for _ in range(20):
        after = "null" if cursor is None else json.dumps(cursor)
        query = f'''query {{ user(login:{json.dumps(owner)}) {{ projectV2(number:{project}) {{
      id
      fields(first:50) {{ nodes {{ ... on ProjectV2IterationField {{
        name configuration {{ iterations {{ id title startDate duration }} completedIterations {{ id title startDate duration }} }}
      }} }} }}
      items(first:100,after:{after}) {{ totalCount pageInfo {{ hasNextPage endCursor }} nodes {{
        content {{ __typename ... on DraftIssue {{ id title body }} ... on Issue {{ id title }} }}
        status:fieldValueByName(name:"Status") {{ ... on ProjectV2ItemFieldSingleSelectValue {{ name }} }}
        sprint:fieldValueByName(name:"Sprint") {{ ... on ProjectV2ItemFieldIterationValue {{ title startDate duration }} }}
        points:fieldValueByName(name:"Story Points") {{ ... on ProjectV2ItemFieldNumberValue {{ number }} }}
        work:fieldValueByName(name:"Work Type") {{ ... on ProjectV2ItemFieldSingleSelectValue {{ name }} }}
      }} }}
    }} }} }}'''
        page_project = graphql(runner, query)["data"]["user"]["projectV2"]
        if project_data is None:
            project_data = page_project
        nodes.extend(page_project["items"]["nodes"])
        page = page_project["items"]["pageInfo"]
        if not page["hasNextPage"]:
            if page_project["items"]["totalCount"] != len(nodes):
                raise BurndownError("Project inventory is incomplete")
            project_data["items"] = {"totalCount": len(nodes), "nodes": nodes}
            return project_data
        cursor = page.get("endCursor")
        if not cursor:
            raise BurndownError("Project pagination cursor is missing")
    raise BurndownError("Project inventory exceeded the bounded page limit")


def parse_history(body: str) -> list[dict[str, Any]]:
    if START not in body and END not in body:
        return []
    if body.count(START) != 1 or body.count(END) != 1:
        raise BurndownError("burndown draft has malformed data markers")
    raw = body.split(START, 1)[1].split(END, 1)[0]
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise BurndownError("burndown history is malformed") from error
    if not isinstance(value, list):
        raise BurndownError("burndown history is not a list")
    return value


def current_iteration(project: dict[str, Any], today: date) -> dict[str, Any]:
    iterations: list[dict[str, Any]] = []
    for field in project["fields"]["nodes"]:
        if field and field.get("name") == "Sprint":
            config = field["configuration"]
            iterations = config["completedIterations"] + config["iterations"]
    matches = []
    for iteration in iterations:
        start = date.fromisoformat(iteration["startDate"])
        if start <= today < start + timedelta(days=iteration["duration"]):
            matches.append(iteration)
    if len(matches) != 1:
        raise BurndownError("Sprint has no unique current iteration")
    return matches[0]


def snapshot(project: dict[str, Any], today: date) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    iteration = current_iteration(project, today)
    selected, draft_id, old_body = [], "", ""
    for node in project["items"]["nodes"]:
        content = node.get("content") or {}
        if content.get("__typename") == "DraftIssue" and content.get("title") == TITLE:
            if draft_id:
                raise BurndownError("duplicate burndown drafts")
            draft_id, old_body = content["id"], content.get("body") or ""
        value = node.get("sprint") or {}
        if value.get("title") == iteration["title"] and content.get("title") != TITLE:
            selected.append(node)
    status = Counter((node.get("status") or {}).get("name") or "Unset" for node in selected)
    work = Counter((node.get("work") or {}).get("name") or "Unset" for node in selected)
    remaining = [node for node in selected if (node.get("status") or {}).get("name") in ACTIVE]
    result = {
        "date": today.isoformat(), "iteration": iteration["title"],
        "remainingIssues": len(remaining),
        "remainingPoints": sum(float((node.get("points") or {}).get("number") or 0) for node in remaining),
        "completedIssues": status.get("Done", 0), "status": dict(sorted(status.items())),
        "workType": dict(sorted(work.items())),
        "scopeIssues": len(selected),
        "scopePoints": sum(float((node.get("points") or {}).get("number") or 0) for node in selected),
    }
    return iteration, result, draft_id, old_body


def merge(history: list[dict[str, Any]], point: dict[str, Any]) -> list[dict[str, Any]]:
    kept = [row for row in history if not (row.get("iteration") == point["iteration"] and row.get("date") == point["date"])]
    kept.append(point)
    return sorted(kept, key=lambda row: (row["iteration"], row["date"]))[-180:]


def render(iteration: dict[str, Any], history: list[dict[str, Any]]) -> str:
    rows = [row for row in history if row["iteration"] == iteration["title"]]
    start = date.fromisoformat(iteration["startDate"])
    duration = int(iteration["duration"])
    initial_issues = max((row["scopeIssues"] for row in rows), default=0)
    initial_points = max((row["scopePoints"] for row in rows), default=0)
    labels, issues, points, ideal_issues, ideal_points = [], [], [], [], []
    by_day = {row["date"]: row for row in rows}
    last = rows[0] if rows else {"remainingIssues": 0, "remainingPoints": 0}
    for offset in range(duration):
        day = start + timedelta(days=offset)
        last = by_day.get(day.isoformat(), last)
        labels.append(day.strftime("%a")); issues.append(last["remainingIssues"]); points.append(last["remainingPoints"])
        fraction = (duration - 1 - offset) / max(duration - 1, 1)
        ideal_issues.append(round(initial_issues * fraction, 2)); ideal_points.append(round(initial_points * fraction, 2))
    latest = rows[-1]
    body = [
        f"# {TITLE}", "", "Private coordination view; repository records and evidence remain authoritative.", "",
        f"Iteration: **{iteration['title']}** ({iteration['startDate']}, {duration} days)", "",
        f"Remaining: **{latest['remainingIssues']} issues / {latest['remainingPoints']:g} SP** · Completed: **{latest['completedIssues']} issues**", "",
        "```mermaid", "xychart-beta", f"  x-axis [{', '.join(labels)}]", "  y-axis \"Remaining issues\" 0 --> " + str(max(initial_issues, 1)),
        "  line [" + ", ".join(map(str, ideal_issues)) + "]", "  line [" + ", ".join(map(str, issues)) + "]", "```", "",
        "```mermaid", "xychart-beta", f"  x-axis [{', '.join(labels)}]", "  y-axis \"Remaining SP\" 0 --> " + str(max(initial_points, 1)),
        "  line [" + ", ".join(map(str, ideal_points)) + "]", "  line [" + ", ".join(map(str, points)) + "]", "```", "",
        "Lines are ideal then actual. Missing days carry the latest observed value.", "",
        "| Date | Remaining issues | Remaining SP | Completed | Status composition | Work type composition |", "|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        statuses = ", ".join(f"{k}={v}" for k, v in row["status"].items())
        work = ", ".join(f"{k}={v}" for k, v in row["workType"].items())
        body.append(f"| {row['date']} | {row['remainingIssues']} | {row['remainingPoints']:g} | {row['completedIssues']} | {statuses} | {work} |")
    body += ["", START + json.dumps(history, separators=(",", ":")) + END]
    return "\n".join(body) + "\n"


def update(owner: str, project_number: int, today: date, apply: bool, runner=run) -> dict[str, Any]:
    project = inventory(owner, project_number, runner)
    iteration, point, draft_id, old_body = snapshot(project, today)
    if not draft_id:
        raise BurndownError(f"missing unique Project draft {TITLE!r}")
    history = merge(parse_history(old_body), point)
    body = render(iteration, history)
    if apply and body != old_body:
        query = f'''mutation {{ updateProjectV2DraftIssue(input:{{draftIssueId:{json.dumps(draft_id)},body:{json.dumps(body)}}}) {{ draftIssue {{ id }} }} }}'''
        graphql(runner, query)
    return {"changed": body != old_body, "applied": apply, "iteration": iteration["title"], "snapshot": point}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--project", required=True, type=int)
    parser.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = update(args.owner, args.project, args.date, args.apply)
    if args.apply:
        print("private Project burndown update completed")
    else:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
