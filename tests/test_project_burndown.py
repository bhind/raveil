from datetime import date
import unittest

from scripts.project_burndown import BurndownError, END, START, merge, parse_history, render


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


if __name__ == "__main__":
    unittest.main()
