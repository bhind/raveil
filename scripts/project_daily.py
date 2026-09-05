#!/usr/bin/env python3
"""Daily factual reconciliation for GitHub Project #1 (dry-run by default).

This is deliberately not a lifecycle transition tool.  It only records
timestamped GitHub events in the existing evidence fields and Project README.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import math
import os
import json
from pathlib import Path
import re
import select
import subprocess
import sys
import time
import uuid
from typing import Any, Callable, Sequence
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
START = "<!-- raveil-daily:start -->"
END = "<!-- raveil-daily:end -->"
MAX_ITEMS = 1000
MAX_PAGES = 20
MAX_TEXT = 1024
CLOSING = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)\b", re.I)


class DailyError(RuntimeError): pass


def jst(value: str | None) -> str | None:
    if not value: return None
    if not isinstance(value, str): raise DailyError("GitHub timestamp is not a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None: raise ValueError("naive timestamp")
        return parsed.astimezone(JST).isoformat()
    except ValueError as error: raise DailyError(f"malformed GitHub timestamp: {value!r}") from error


def daily_block(text: str, replacement: str) -> str:
    count = text.count(START)
    end_count = text.count(END)
    if count == 0 and end_count == 0:
        return text.rstrip() + f"\n\n{START}\n{replacement.rstrip()}\n{END}\n"
    if count != 1 or end_count != 1 or text.index(START) > text.index(END):
        raise DailyError("Project README must contain exactly one raveil-daily block")
    first, rest = text.split(START, 1)
    _, last = rest.split(END, 1)
    return f"{first}{START}\n{replacement.rstrip()}\n{END}{last}"

def managed_content(text: str) -> str | None:
    if START not in text and END not in text: return None
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
        raise DailyError("Project README has malformed raveil-daily markers")
    return text.split(START, 1)[1].split(END, 1)[0]


def event_block(issue: dict[str, Any], pulls: list[dict[str, Any]]) -> str:
    lines = ["<!-- raveil-github-events:start -->", "GitHub events (coordination facts; not technical acceptance time):"]
    if issue.get("closed_at"): lines.append(f"- Issue #{issue['number']} closed at {jst(issue['closed_at'])}")
    for pull in pulls:
        if pull.get("merged_at"): lines.append(f"- PR #{pull['number']} merged at {jst(pull['merged_at'])}")
    lines.append("<!-- raveil-github-events:end -->")
    return "\n".join(lines)


def replace_events(observed: str, events: str) -> str:
    start, end = "<!-- raveil-github-events:start -->", "<!-- raveil-github-events:end -->"
    if observed.count(start) > 1 or observed.count(end) > 1:
        raise DailyError("duplicate GitHub-events block in Observed Cycle")
    if start in observed or end in observed:
        if start not in observed or end not in observed: raise DailyError("malformed GitHub-events block")
        result = re.sub(re.escape(start) + r".*?" + re.escape(end), events, observed, flags=re.S)
    else:
        result = (observed.rstrip() + "\n\n" + events).lstrip()
    if len(result) > MAX_TEXT:
        raise DailyError("Observed Cycle has no room for factual GitHub events (1024-character limit)")
    return result


def linked_pulls(issue: dict[str, Any], pulls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    number = str(issue["number"])
    return [p for p in pulls if number in CLOSING.findall(p.get("body") or "")]


def findings(project: dict[str, Any], issues: list[dict[str, Any]], pulls: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    issue_by_url = {i.get("html_url") or i.get("url"): i for i in issues}
    factual, notes = [], []
    for item in project.get("items", []):
        content = item.get("content", {})
        if content.get("type") != "Issue": continue
        issue = issue_by_url.get(content.get("url"))
        if not issue or not any((x.get("name") if isinstance(x, dict) else x) == "work-item" for x in issue.get("labels", [])):
            continue
        related = linked_pulls(issue, pulls)
        factual.append({"item": item, "issue": issue, "pulls": related})
        state = str(issue.get("state", "")).lower()
        if state == "closed" and item.get("status") != "Done":
            notes.append(f"Issue #{issue['number']} is closed while Project status is {item.get('status')!r}; use project_queue complete after canonical evidence.")
        if state == "open" and item.get("status") == "Done":
            notes.append(f"Issue #{issue['number']} is open while Project status is Done; preserve state and reconcile canonically.")
        if item.get("status") == "Done" and not str(item.get("review Outcome") or "").strip():
            notes.append(f"Issue #{issue['number']} is Done without Review Outcome evidence.")
        if state == "closed" and not any(p.get("merged_at") for p in related):
            notes.append(f"Issue #{issue['number']} has no closing-reference association to a merged PR; inspect canonical records.")
    return factual, notes


@dataclass
class Gh:
    owner: str; repo: str; project: int; runner: Callable[[Sequence[str], str | None], str]
    _project_id: str | None = None
    def json(self, args: Sequence[str]) -> Any:
        try: return json.loads(self.runner(("gh", *args), None))
        except json.JSONDecodeError as e: raise DailyError("GitHub returned malformed JSON") from e
    def project_items(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []; cursor: str | None = None; total: int | None = None
        for _ in range(10):
            after = "null" if cursor is None else json.dumps(cursor)
            query = """query {
  user(login: %s) {
    projectV2(number: %d) {
      items(first: 100, after: %s) {
        totalCount
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content { __typename ... on Issue { url title } ... on DraftIssue { title } }
          status: fieldValueByName(name: \"Status\") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
          cycle: fieldValueByName(name: \"Observed Cycle\") { ... on ProjectV2ItemFieldTextValue { text } }
          review: fieldValueByName(name: \"Review Outcome\") { ... on ProjectV2ItemFieldTextValue { text } }
        }
      }
    }
  }
}""" % (json.dumps(self.owner), self.project, after)
            data = self.json(("api", "graphql", "-f", f"query={query}"))
            try: page = data["data"]["user"]["projectV2"]["items"]
            except (KeyError, TypeError) as error: raise DailyError("narrow Project inventory schema is missing") from error
            nodes, page_info = page.get("nodes"), page.get("pageInfo")
            if not isinstance(page.get("totalCount"), int) or not isinstance(nodes, list) or not isinstance(page_info, dict): raise DailyError("narrow Project inventory is malformed")
            total = page["totalCount"] if total is None else total
            if total != page["totalCount"] or total > MAX_ITEMS: raise DailyError("Project inventory is truncated or inconsistent")
            for node in nodes:
                try:
                    content = node["content"]; typename = content["__typename"]
                    items.append({"id": node["id"], "status": (node.get("status") or {}).get("name"), "observed Cycle": (node.get("cycle") or {}).get("text"), "review Outcome": (node.get("review") or {}).get("text"), "content": {"type": typename, "url": content.get("url"), "title": content.get("title")}})
                except (KeyError, TypeError) as error: raise DailyError("narrow Project item schema is missing") from error
            if not page_info.get("hasNextPage"):
                if len(items) != total: raise DailyError("Project inventory totalCount does not match pages")
                return {"totalCount": total, "items": items}
            cursor = page_info.get("endCursor")
            if not isinstance(cursor, str) or not cursor: raise DailyError("Project pagination cursor is missing")
        raise DailyError("Project inventory reached bounded page limit")

    def item_cycle(self, item_id: str) -> str:
        query = """query { node(id: %s) { ... on ProjectV2Item { cycle: fieldValueByName(name: \"Observed Cycle\") { ... on ProjectV2ItemFieldTextValue { text } } } } }""" % json.dumps(item_id)
        data = self.json(("api", "graphql", "-f", f"query={query}"))
        try: value = data["data"]["node"]["cycle"]
        except (KeyError, TypeError) as error: raise DailyError("Project item cycle preflight schema is missing") from error
        if value is None: return ""
        if not isinstance(value, dict) or not isinstance(value.get("text"), str): raise DailyError("Project item cycle preflight is malformed")
        return value["text"]
    def paged(self, endpoint: str) -> list[dict[str, Any]]:
        all_rows: list[dict[str, Any]] = []
        separator = "&" if "?" in endpoint else "?"
        for page in range(1, MAX_PAGES + 1):
            data = self.json(("api", f"{endpoint}{separator}per_page=100&page={page}"))
            if not isinstance(data, list) or any(not isinstance(row, dict) for row in data): raise DailyError("REST inventory is malformed")
            all_rows.extend(data)
            if len(data) < 100: return all_rows
        raise DailyError("REST inventory reached its bounded page limit")
    def project_view(self) -> dict[str, Any]:
        query = """query { user(login: %s) { projectV2(number: %d) { id readme } } }""" % (json.dumps(self.owner), self.project)
        data = self.json(("api", "graphql", "-f", f"query={query}"))
        try: project = data["data"]["user"]["projectV2"]
        except (KeyError, TypeError) as error: raise DailyError("narrow Project view schema is missing") from error
        if not isinstance(project, dict) or not isinstance(project.get("id"), str) or not isinstance(project.get("readme"), str): raise DailyError("narrow Project view is malformed")
        self._project_id = project["id"]
        return project
    def readme(self) -> str:
        data = self.project_view()
        text = data.get("readme")
        if not isinstance(text, str): raise DailyError("Project README is unavailable")
        return text
    def fields(self) -> list[dict[str, Any]]:
        query = """query { user(login: %s) { projectV2(number: %d) { field(name: \"Observed Cycle\") { ... on ProjectV2Field { id name } } } } }""" % (json.dumps(self.owner), self.project)
        data = self.json(("api", "graphql", "-f", f"query={query}"))
        try: field = data["data"]["user"]["projectV2"]["field"]
        except (KeyError, TypeError) as error: raise DailyError("Observed Cycle field schema is missing") from error
        if not isinstance(field, dict) or field.get("name") != "Observed Cycle" or not isinstance(field.get("id"), str): raise DailyError("Project lacks Observed Cycle field")
        return [field]
    def write_text(self, project_id: str, item: str, field: str, value: str) -> None:
        query = """mutation { updateProjectV2ItemFieldValue(input: { projectId: %s, itemId: %s, fieldId: %s, value: { text: %s } }) { projectV2Item { id } } }""" % (json.dumps(project_id), json.dumps(item), json.dumps(field), json.dumps(value))
        self.json(("api", "graphql", "-f", f"query={query}"))
    def write_readme(self, value: str) -> None:
        project_id = self._project_id or self.project_view()["id"]
        query = """mutation { updateProjectV2(input: { projectId: %s, readme: %s }) { projectV2 { id } } }""" % (json.dumps(project_id), json.dumps(value))
        self.json(("api", "graphql", "-f", f"query={query}"))


def telemetry(_: Callable[[Sequence[str], str | None], str], *, now: Callable[[], datetime] = lambda: datetime.now(timezone.utc), popen=subprocess.Popen) -> dict[str, Any]:
    """Read only the weekly rate-limit percentage through the app-server protocol."""
    proc = popen(("codex", "app-server"), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False, bufsize=0)
    assert proc.stdin is not None and proc.stdout is not None
    messages = (
        {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"raveil-project-daily","version":"1"}}},
        {"jsonrpc":"2.0","method":"initialized","params":{}},
        {"jsonrpc":"2.0","id":2,"method":"account/rateLimits/read","params":{}},
    )
    for message in messages: proc.stdin.write((json.dumps(message) + "\n").encode())
    proc.stdin.flush(); deadline = time.monotonic() + 20; pending = b""; max_bytes = 1024 * 1024
    try:
        while time.monotonic() < deadline:
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                response = json.loads(line.decode())
                if response.get("id") != 2: continue
                limits = response.get("result", {}).get("rateLimits", {})
                candidates = [limits.get(name) for name in ("primary", "secondary") if isinstance(limits.get(name), dict)]
                weekly = [entry for entry in candidates if entry.get("windowDurationMins") == 10080]
                if len(weekly) != 1: raise DailyError("usage telemetry lacks exactly one weekly window")
                used = weekly[0].get("usedPercent")
                if isinstance(used, bool) or not isinstance(used, (int, float)) or not math.isfinite(used) or not 0 <= used <= 100:
                    raise DailyError("usage telemetry has invalid used percentage")
                observed = now()
                if observed.tzinfo is None: raise DailyError("telemetry clock is naive")
                return {"windowMinutes":10080, "usedPercent":float(used), "remainingPercent":100-float(used), "observedAt":observed.astimezone(timezone.utc).isoformat()}
            ready, _, _ = select.select([proc.stdout.fileno()], [], [], max(0.0, deadline - time.monotonic()))
            if not ready: break
            chunk = os.read(proc.stdout.fileno(), 65536)
            if not chunk: break
            pending += chunk
            if len(pending) > max_bytes: raise DailyError("usage telemetry exceeded bounded response size")
        raise DailyError("usage telemetry EOF or deadline before rate-limit response")
    except json.JSONDecodeError as error: raise DailyError("usage telemetry is malformed") from error
    finally:
        proc.terminate()
        try: proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(timeout=1)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None: stream.close()


def validate_usage(reading: Any, now: datetime) -> dict[str, Any]:
    if not isinstance(reading, dict): raise DailyError("usage telemetry is malformed")
    window, used, remaining, observed = (reading.get(k) for k in ("windowMinutes", "usedPercent", "remainingPercent", "observedAt"))
    if isinstance(window, bool) or not isinstance(window, (int, float)) or window != 10080: raise DailyError("usage telemetry has invalid weekly window")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 100 for v in (used, remaining)):
        raise DailyError("usage telemetry has invalid percentages")
    if abs(remaining - (100 - used)) > 1e-9 or remaining < 5: raise DailyError("usage telemetry is inconsistent or below the five-percent stop")
    if not isinstance(observed, str): raise DailyError("usage telemetry has invalid observation timestamp")
    try:
        stamp = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        if stamp.tzinfo is None: raise ValueError("naive")
    except ValueError as error: raise DailyError("usage telemetry has invalid observation timestamp") from error
    age = (now.astimezone(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds()
    if age > 300 or age < -60: raise DailyError("usage telemetry observation is stale or implausibly future")
    return {"windowMinutes":10080, "usedPercent":float(used), "remainingPercent":float(remaining), "observedAt":stamp.astimezone(timezone.utc).isoformat()}


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_readme(now: datetime, entries: list[dict[str, Any]], notes: list[str], previous: str = "") -> str:
    day = now.astimezone(JST).date().isoformat()
    rows = ["## Daily delivery facts", "", f"Last reconciled: {day} (Asia/Tokyo)", "", "| JST date | work item | Project status | GitHub event |", "|---|---|---|---|"]
    cutoff = now.astimezone(JST).date() - timedelta(days=13)
    event_rows: list[tuple[str, str]] = []
    for entry in entries:
        issue, item = entry["issue"], entry["item"]
        events = [("Issue closed", issue.get("closed_at"))] + [(f"PR #{pull['number']} merged", pull.get("merged_at")) for pull in entry["pulls"]]
        for label, timestamp in events:
            if not timestamp: continue
            event_time = jst(timestamp)
            if datetime.fromisoformat(event_time).date() < cutoff: continue
            event_rows.append((event_time, f"| {event_time[:10]} | #{issue['number']} {cell(issue.get('title', ''))} | {cell(item.get('status', ''))} | {label} at {event_time} |"))
    rows.extend(line for _, line in sorted(event_rows))
    if not event_rows: rows.append(f"| {day} | — | — | no linked real work-item event |")
    active = [f"#{e['issue']['number']} {cell(e['issue'].get('title',''))} ({e['item'].get('status')})" for e in entries if e['item'].get('status') in {"In Progress", "Ready"}]
    rows += ["", "### Active and Ready"] + [f"- {entry}" for entry in (active or ["None observed."])]
    rows += ["", "### Findings"] + [f"- {note}" for note in (notes or ["No missing evidence or stale lifecycle found."])]
    return "\n".join(rows)


def run_daily(args: argparse.Namespace, gh: Gh, now: datetime, usage=telemetry) -> dict[str, Any]:
    receipt: dict[str, Any] = {"dry_run": not args.apply, "success": False, "findings": [], "actions": [], "partial_edits": [], "observedAt": now.astimezone(timezone.utc).isoformat(), "owner": args.owner, "repo": args.repo, "project": args.project}
    try:
        if args.apply:
            receipt["usage"] = validate_usage(usage(gh.runner), now)
        project = gh.project_items()
        if not isinstance(project.get("items"), list) or not isinstance(project.get("totalCount"), int) or project["totalCount"] > MAX_ITEMS or len(project["items"]) != project["totalCount"]:
            raise DailyError("Project inventory is truncated or lacks a reliable totalCount")
        issues = gh.paged(f"repos/{args.repo}/issues?state=all")
        pulls = gh.paged(f"repos/{args.repo}/pulls?state=all")
        entries, notes = findings(project, issues, pulls); receipt["findings"] = notes
        planned = []
        for entry in entries:
            if not entry["issue"].get("closed_at"): continue
            observed = str(entry["item"].get("observed Cycle") or "")
            try: updated = replace_events(observed, event_block(entry["issue"], entry["pulls"]))
            except DailyError as error:
                notes.append(f"Issue #{entry['issue']['number']}: {error}")
                continue
            if updated != observed: planned.append(entry)
        readme = gh.readme(); updated_readme = daily_block(readme, render_readme(now, entries, notes, readme))
        receipt["planned_event_updates"] = len(planned); receipt["readme_changed"] = updated_readme != readme
        if args.apply:
            fields = {f.get("name"): f for f in gh.fields()}
            if "Observed Cycle" not in fields: raise DailyError("Project lacks Observed Cycle field")
            project_id = gh.project_view().get("id")
            if not isinstance(project_id, str) or not project_id: raise DailyError("Project node ID is unavailable")
            written: dict[str, str] = {}
            for entry in planned:
                item = entry["item"]
                current = gh.item_cycle(item["id"])
                value = replace_events(current, event_block(entry["issue"], entry["pulls"]))
                if value == current: continue
                gh.write_text(project_id, item["id"], fields["Observed Cycle"]["id"], value)
                receipt["partial_edits"].append(f"Observed Cycle item {item['id']}")
                written[item["id"]] = value
            if written:
                readback = {row.get("id"): row.get("observed Cycle") for row in gh.project_items()["items"]}
                if any(readback.get(item_id) != value for item_id, value in written.items()): raise DailyError("Observed Cycle batch readback mismatch")
            if updated_readme != readme:
                current_readme = gh.readme()
                if managed_content(current_readme) != managed_content(readme): raise DailyError("Project README managed block drifted before edit")
                latest = daily_block(current_readme, render_readme(now, entries, notes, current_readme))
                gh.write_readme(latest)
                receipt["partial_edits"].append("Project README")
                if gh.readme() != latest: raise DailyError("Project README readback mismatch")
        receipt["success"] = True
        receipt["actions"].append("dry-run planned" if not args.apply else "remote edits read back")
    except (DailyError, OSError, subprocess.SubprocessError) as error: receipt["error"] = str(error)
    return receipt


def subprocess_runner(command: Sequence[str], stdin: str | None) -> str:
    result = subprocess.run(command, input=stdin, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode: raise DailyError(result.stderr.strip() or "command failed")
    return result.stdout


def write_receipt(directory: Path, now: datetime, receipt: dict[str, Any]) -> Path:
    receipt["scriptSha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    directory.mkdir(parents=True, exist_ok=True); stem = f"project-daily-{now.astimezone(JST):%Y%m%dT%H%M%S%z}-{uuid.uuid4().hex}"
    path = directory / f"{stem}.json"; path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.with_suffix(".md").write_text("# Project daily receipt\n\n```json\n" + path.read_text() + "```\n", encoding="utf-8")
    return path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--apply", action="store_true"); p.add_argument("--output-dir", type=Path, default=Path("artifacts/project_daily")); p.add_argument("--owner", default="bhind"); p.add_argument("--project", type=int, default=1); p.add_argument("--repo", default="bhind/raveil"); return p

def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv); now = datetime.now(timezone.utc); gh = Gh(args.owner, args.repo, args.project, subprocess_runner)
    receipt = run_daily(args, gh, now); path = write_receipt(args.output_dir, now, receipt); print(path)
    return 0 if receipt["success"] else 2

if __name__ == "__main__": raise SystemExit(main())
