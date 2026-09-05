from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import json
import subprocess
import sys
import unittest

from scripts.project_daily import DailyError, END, Gh, START, daily_block, jst, replace_events, render_readme, run_daily, telemetry, validate_usage


README = "Intro\n<!-- raveil-daily:start -->\nold\n<!-- raveil-daily:end -->\nTail\n"


class FakeGh(Gh):
    def __init__(self, *, closed=True, total=1):
        super().__init__("bhind", "bhind/raveil", 1, lambda *_: "")
        self.calls: list[str] = []
        self._readme = README
        self._project = {"totalCount": total, "items": [{"id": "item-1", "status": "Review", "observed Cycle": "human note", "content": {"type": "Issue", "url": "https://github.com/bhind/raveil/issues/115"}}]}
        self._issues = [{"number": 115, "title": "T-0151", "html_url": "https://github.com/bhind/raveil/issues/115", "state": "closed" if closed else "open", "closed_at": "2026-09-04T15:30:00Z" if closed else None, "labels": [{"name": "work-item"}]}]
        self._pulls = [{"number": 120, "body": "Closes #115", "merged_at": "2026-09-04T16:00:00Z"}]
    def project_items(self): self.calls.append("project"); return self._project
    def item_cycle(self, item_id): self.calls.append("item_cycle"); return self._project["items"][0]["observed Cycle"]
    def paged(self, endpoint): self.calls.append(endpoint); return self._issues if "/issues" in endpoint else self._pulls
    def readme(self): self.calls.append("readme"); return self._readme
    def project_view(self): return {"id": "PVT_test", "readme": self._readme}
    def fields(self): return [{"name": "Observed Cycle", "id": "field-cycle"}]
    def write_text(self, project_id, item, field, value): self.calls.append("write_text"); self._project["items"][0]["observed Cycle"] = value
    def write_readme(self, value): self.calls.append("write_readme"); self._readme = value


def args(apply=False): return argparse.Namespace(apply=apply, owner="bhind", repo="bhind/raveil", project=1)
def usage(_): return {"windowMinutes": 10080, "usedPercent": 52, "remainingPercent": 48, "observedAt": datetime.now(timezone.utc).isoformat()}


class ProjectDailyTest(unittest.TestCase):
    def test_utc_jst_midnight(self):
        self.assertEqual(jst("2026-09-04T15:30:00Z"), "2026-09-05T00:30:00+09:00")

    def test_dry_run_has_no_remote_writes_and_preserves_text(self):
        gh = FakeGh(); receipt = run_daily(args(), gh, datetime(2026, 9, 4, 15, 30, tzinfo=timezone.utc), usage)
        self.assertTrue(receipt["success"]); self.assertNotIn("write_text", gh.calls); self.assertNotIn("write_readme", gh.calls)
        self.assertEqual(gh._project["items"][0]["observed Cycle"], "human note")

    def test_apply_is_idempotent_and_keeps_prior_observation(self):
        gh = FakeGh(); first = run_daily(args(True), gh, datetime.now(timezone.utc), usage); self.assertTrue(first["success"])
        self.assertIn("human note", gh._project["items"][0]["observed Cycle"])
        writes = gh.calls.count("write_text"); second = run_daily(args(True), gh, datetime.now(timezone.utc), usage)
        self.assertTrue(second["success"]); self.assertEqual(writes, gh.calls.count("write_text"))

    def test_duplicate_or_truncated_inventory_fails_before_writes(self):
        gh = FakeGh(total=2); receipt = run_daily(args(True), gh, datetime.now(timezone.utc), usage)
        self.assertFalse(receipt["success"]); self.assertNotIn("write_text", gh.calls)
        with self.assertRaisesRegex(DailyError, "exactly one"):
            daily_block("<!-- raveil-daily:start --><!-- raveil-daily:start --><!-- raveil-daily:end -->", "x")

    def test_usage_stop_and_unclosed_issue_do_not_count_completion(self):
        gh = FakeGh(); stopped = run_daily(args(True), gh, datetime.now(timezone.utc), lambda _: {"windowMinutes": 10080, "usedPercent": 96, "remainingPercent": 4, "observedAt": "x"})
        self.assertFalse(stopped["success"]); self.assertNotIn("project", gh.calls)
        open_gh = FakeGh(closed=False); receipt = run_daily(args(), open_gh, datetime.now(timezone.utc), usage)
        self.assertTrue(receipt["success"]); self.assertEqual(receipt["planned_event_updates"], 0)

    def test_existing_event_block_is_replaced(self):
        observed = "note\n<!-- raveil-github-events:start -->\nold\n<!-- raveil-github-events:end -->"
        self.assertEqual(replace_events(observed, "<!-- raveil-github-events:start -->\nnew\n<!-- raveil-github-events:end -->").count("start"), 1)

    def test_no_room_preserves_evidence_and_status(self):
        gh = FakeGh()
        gh._project["items"][0]["observed Cycle"] = "x" * 1020
        receipt = run_daily(args(True), gh, datetime.now(timezone.utc), usage)
        self.assertTrue(receipt["success"])
        self.assertNotIn("write_text", gh.calls)
        self.assertEqual(gh._project["items"][0]["status"], "Review")
        self.assertTrue(any("no room" in finding for finding in receipt["findings"]))

    def test_readme_rebuilds_from_actual_event_dates_not_old_snapshots(self):
        old = START + "\n" + "\n".join(f"| 2026-08-{day:02d} | old | Done | closed |" for day in range(1, 16)) + "\n" + END
        text = render_readme(datetime(2026, 9, 5, tzinfo=timezone.utc), [], [], old)
        self.assertEqual(sum(line.startswith("| 20") for line in text.splitlines()), 1)
        self.assertNotIn("2026-08-15", text)

    def test_missing_markers_append_and_lowercase_payload_preserves_prose(self):
        self.assertIn(START, daily_block("outside text", "facts"))
        gh = FakeGh(); run_daily(args(True), gh, datetime.now(timezone.utc), usage)
        self.assertIn("human note", gh._project["items"][0]["observed Cycle"])
        self.assertNotIn("Observed Cycle", gh._project["items"][0])

    def test_done_evidence_and_open_done_are_findings(self):
        gh = FakeGh(closed=False); gh._project["items"][0]["status"] = "Done"
        receipt = run_daily(args(), gh, datetime.now(timezone.utc), usage)
        self.assertTrue(any("open while" in value for value in receipt["findings"]))
        self.assertTrue(any("Review Outcome" in value for value in receipt["findings"]))

    def test_rate_limit_protocol_reads_weekly_window_only(self):
        payload = json.dumps({"jsonrpc":"2.0", "id":2, "result":{"rateLimits":{"primary":{"windowDurationMins":10080, "usedPercent":52}}}})
        script = f"import os; os.write(1, b'{{\"jsonrpc\":\"2.0\",\"id\":1}}\\n' + {payload!r}.encode() + b'\\n')"
        result = telemetry(lambda *_: "", now=lambda: datetime(2026, 9, 5, tzinfo=timezone.utc), popen=lambda *_args, **_kwargs: subprocess.Popen([sys.executable, "-c", script], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False, bufsize=0))
        self.assertEqual(result["remainingPercent"], 48.0)

    def test_usage_validation_rejects_malformed_stale_future_and_nonfinite_values(self):
        now = datetime(2026, 9, 5, 0, 0, tzinfo=timezone.utc)
        valid = {"windowMinutes":10080, "usedPercent":52, "remainingPercent":48, "observedAt":"2026-09-05T00:00:00Z"}
        for key, value in (("observedAt", "not-a-date"), ("observedAt", "2026-09-05T00:00:00"), ("observedAt", "2026-09-04T23:54:59Z"), ("observedAt", "2026-09-05T00:01:01Z"), ("usedPercent", float("nan")), ("usedPercent", True), ("remainingPercent", 47)):
            reading = dict(valid); reading[key] = value
            with self.assertRaises(DailyError): validate_usage(reading, now)

    def test_bad_usage_stops_run_before_project_or_remote_writes(self):
        gh = FakeGh()
        receipt = run_daily(args(True), gh, datetime.now(timezone.utc), lambda _: {"windowMinutes":10080, "usedPercent":52, "remainingPercent":48, "observedAt":"not-a-date"})
        self.assertFalse(receipt["success"])
        self.assertEqual(gh.calls, [])

    def test_narrow_graphql_inventory_normalizes_payload_without_item_list(self):
        calls = []
        payload = {"data":{"user":{"projectV2":{"items":{"totalCount":1, "pageInfo":{"hasNextPage":False, "endCursor":None}, "nodes":[{"id":"PVTI_1", "content":{"__typename":"Issue", "url":"https://github.com/bhind/raveil/issues/115", "title":"T-0151"}, "status":{"name":"In Progress"}, "cycle":{"text":"prior prose"}, "review":{"text":"reviewed"}}]}}}}}
        def runner(command, _stdin): calls.append(command); return json.dumps(payload)
        project = Gh("bhind", "bhind/raveil", 1, runner).project_items()
        self.assertEqual(project["items"][0]["observed Cycle"], "prior prose")
        self.assertEqual(project["items"][0]["content"]["type"], "Issue")
        self.assertFalse(any("item-list" in command for command in calls))
        query = calls[0][-1].removeprefix("query=")
        self.assertEqual(query.count("{"), query.count("}"))

    def test_narrow_graphql_refuses_unbounded_partial_pages(self):
        payload = {"data":{"user":{"projectV2":{"items":{"totalCount":1001, "pageInfo":{"hasNextPage":True, "endCursor":"next"}, "nodes":[]}}}}}
        with self.assertRaises(DailyError):
            Gh("bhind", "bhind/raveil", 1, lambda *_: json.dumps(payload)).project_items()

    def test_apply_uses_item_preflight_then_one_batch_readback(self):
        gh = FakeGh(); receipt = run_daily(args(True), gh, datetime.now(timezone.utc), usage)
        self.assertTrue(receipt["success"])
        self.assertEqual(gh.calls.count("project"), 2)
        self.assertEqual(gh.calls.count("item_cycle"), 1)


if __name__ == "__main__": unittest.main()
