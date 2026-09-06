from datetime import date
import unittest

from scripts.project_burndown import BurndownError, END, START, draft_title, merge, parse_history, render, snapshot


class ProjectBurndownTest(unittest.TestCase):
    def test_history_is_idempotent_per_iteration_day(self):
        first = {"iteration":"S-1", "date":"2026-09-05", "remainingIssues":2}
        second = dict(first, remainingIssues=1)
        self.assertEqual(merge(merge([], first), second), [second])

    def test_markers_round_trip_and_fail_closed(self):
        data = [{"iteration":"S-1", "date":"2026-09-05"}]
        body = START + '[{"iteration":"S-1","date":"2026-09-05"}]' + END
        self.assertEqual(parse_history(body), data)
        with self.assertRaises(BurndownError):
            parse_history(START + "[]")

    def test_render_keeps_private_authority_warning_and_ideal_actual_lines(self):
        iteration = {"title":"S-1", "startDate":"2026-09-01", "duration":7}
        point = {"iteration":"S-1", "date":"2026-09-05", "remainingIssues":2,
                 "remainingPoints":3.0, "completedIssues":4, "scopeIssues":6,
                 "scopePoints":10.0, "status":{"Done":4,"Ready":2},
                 "workType":{"Product Slice":6}}
        text = render(iteration, [point])
        self.assertIn("repository records and evidence remain authoritative", text)
        self.assertEqual(text.count("xychart-beta"), 2)
        self.assertEqual(text.count("  line ["), 4)
        self.assertIn("Remaining: **2 issues / 3 SP**", text)

    def test_render_observed_decrease_without_inventing_pre_observation_values(self):
        iteration = {"title":"S-1", "startDate":"2026-09-01", "duration":7}
        first = {"iteration":"S-1", "date":"2026-09-03", "remainingIssues":4,
                 "remainingPoints":8.0, "completedIssues":1, "scopeIssues":5,
                 "scopePoints":10.0, "status":{"Done":1,"Ready":4},
                 "workType":{"Product Slice":5}}
        second = dict(first, date="2026-09-05", remainingIssues=2,
                      remainingPoints=3.0, completedIssues=3,
                      status={"Done":3,"Ready":2})
        text = render(iteration, [first, second])
        self.assertIn("x-axis [09-03, 09-04, 09-05]", text)
        self.assertIn("line [4, 4, 2]", text)
        self.assertIn("line [8.0, 8.0, 3.0]", text)
        axis_lines = [line for line in text.splitlines() if line.startswith("  x-axis")]
        self.assertEqual(axis_lines, ["  x-axis [09-03, 09-04, 09-05]"] * 2)

    def test_draft_title_exposes_live_remainder_on_project_card(self):
        point = {"iteration":"S-3", "date":"2026-09-08",
                 "remainingIssues":3, "remainingPoints":5.0}
        self.assertEqual(
            draft_title(point),
            "Raveil iteration burndown — S-3: 3 issues / 5 SP (2026-09-08)",
        )

    def test_dynamic_burndown_draft_is_never_counted_as_work(self):
        project = {
            "fields":{"nodes":[{"name":"Sprint","configuration":{"completedIterations":[],
                "iterations":[{"id":"s3","title":"S-3","startDate":"2026-09-07","duration":7}]}}]},
            "items":{"nodes":[{
                "content":{"__typename":"DraftIssue","id":"draft","title":
                    "Raveil iteration burndown — S-3: 3 issues / 5 SP (2026-09-08)","body":""},
                "sprint":{"title":"S-3"},"status":{"name":"Ready"},"points":{"number":5},
                "work":{"name":"Operations"},
            }]},
        }
        _, point, _, _ = snapshot(project, date(2026, 9, 8))
        self.assertEqual(point["scopeIssues"], 0)
        self.assertEqual(point["remainingIssues"], 0)


if __name__ == "__main__":
    unittest.main()
