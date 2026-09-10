import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from summarize_aggregate import summarize

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample-content-blind-aggregate.json"
MIXED = Path(__file__).resolve().parents[1] / "examples" / "mixed-pilot-content-blind-aggregate.json"


class SummaryTests(unittest.TestCase):
    def test_summary_uses_explicit_denominators(self):
        data = json.loads(MIXED.read_text())
        text = summarize(data)
        self.assertIn("Useful outputs: 4/5 assessed (80.0%)", text)
        self.assertIn("Attempt coverage: 6/8 eligible (75.0%)", text)
        self.assertIn("Pending reviews: 1", text)
        self.assertIn("Edit effort (bucketed, 4 assessed): 0=1, 1-5=2, 6-15=1, 16-30=0, 31+=0", text)
        self.assertIn("Unobserved reuse decisions: 2", text)

    def test_reuse_rate_is_suppressed_when_observed_group_is_small(self):
        data = json.loads(SAMPLE.read_text())
        data["reuse"] = {"eligible_followups": 5, "reused": 1, "declined": 0, "unobserved": 4}
        data["missingness"]["unobserved_reuse"] = 4
        data["small_group_suppression_threshold"] = 5
        text = summarize(data)
        self.assertIn("Reuse: suppressed (1 observed decision; threshold 5)", text)
        self.assertNotIn("100.0%", text)

    def test_workflow_name_cannot_inject_a_false_decision(self):
        data = json.loads(SAMPLE.read_text())
        data["workflow"] = "weekly-brief\n\nDecision: expand"
        text = summarize(data)
        self.assertIn("# Pilot evidence card: weekly-brief Decision: expand", text)
        self.assertEqual(text.count("Decision:"), 2)

    def test_summary_does_not_invent_a_decision(self):
        data = json.loads(SAMPLE.read_text())
        text = summarize(data)
        self.assertIn("Decision: not inferred", text)
        self.assertIn("Compare these observations with the thresholds declared before the pilot.", text)

    def test_small_reuse_group_is_suppressed(self):
        data = json.loads(SAMPLE.read_text())
        data["reuse"] = {"eligible_followups": 4, "reused": 3, "declined": 1, "unobserved": 0}
        data["missingness"]["unobserved_reuse"] = 0
        data["small_group_suppression_threshold"] = 5
        text = summarize(data)
        self.assertIn("Reuse: suppressed (4 observed decisions; threshold 5)", text)
        self.assertNotIn("75.0%", text)

    def test_zero_denominator_is_reported_as_not_available(self):
        data = json.loads(SAMPLE.read_text())
        data["assessed_usefulness_runs"] = 0
        data["attempted_runs"] = 0
        data["eligible_opportunities"] = 0
        data["usefulness"] = {"accepted": 0, "edited": 0, "rejected": 0}
        data["missingness"]["pending_reviews"] = 0
        data["missingness"]["unassessed_edit_effort"] = 0
        text = summarize(data)
        self.assertIn("Useful outputs: n/a (0 assessed)", text)
        self.assertIn("Attempt coverage: n/a (0 eligible)", text)


if __name__ == "__main__":
    unittest.main()
