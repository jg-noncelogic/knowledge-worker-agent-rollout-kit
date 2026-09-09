import json
import csv
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_aggregate import validate

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample-content-blind-aggregate.json"
MIXED = Path(__file__).resolve().parents[1] / "examples" / "mixed-pilot-content-blind-aggregate.json"
MIXED_OPPORTUNITIES = Path(__file__).resolve().parents[1] / "examples" / "mixed-pilot-opportunities.csv"
MIXED_SCORECARD = Path(__file__).resolve().parents[1] / "examples" / "mixed-pilot-scorecard.csv"
MIXED_REUSE = Path(__file__).resolve().parents[1] / "examples" / "mixed-reuse-opportunities.csv"

class AggregateTests(unittest.TestCase):
    def setUp(self): self.data = json.loads(SAMPLE.read_text())
    def test_sample_is_valid(self): self.assertEqual(validate(self.data), [])
    def test_usefulness_counts_reconcile(self):
        self.data["usefulness"]["accepted"] += 1
        self.assertIn("usefulness: counts must sum to assessed_usefulness_runs", validate(self.data))
    def test_attempts_cannot_exceed_opportunities(self):
        self.data["attempted_runs"] = 15
        self.assertIn("attempted_runs: cannot exceed eligible_opportunities", validate(self.data))
    def test_reuse_outcomes_reconcile(self):
        self.data["reuse"]["declined"] += 1
        self.assertIn("reuse: outcome counts must sum to eligible_followups", validate(self.data))
    def test_identifying_fields_are_rejected(self):
        self.data["reviewer"] = "person@example.com"
        self.assertTrue(any("unexpected reviewer" in e for e in validate(self.data)))
    def test_unhashable_mode_returns_error_not_exception(self):
        self.data["edit_effort"]["mode"] = []
        self.assertIn("edit_effort.mode: invalid value", validate(self.data))
    def test_unbounded_distribution_keys_are_rejected(self):
        self.data["edit_effort"]["distribution"] = {"person@example.com": 10}
        self.assertIn("edit_effort.distribution: expected bounded effort buckets", validate(self.data))
    def test_pending_review_missingness_reconciles(self):
        self.data["missingness"]["pending_reviews"] = 0
        self.assertIn("missingness.pending_reviews: assessed plus pending must equal attempted_runs", validate(self.data))
    def test_edit_effort_missingness_reconciles(self):
        self.data["missingness"]["unassessed_edit_effort"] = 0
        self.assertIn("missingness.unassessed_edit_effort: assessed plus unassessed must equal attempted_runs", validate(self.data))

    def test_mixed_window_reconciles_to_source_ledgers(self):
        aggregate = json.loads(MIXED.read_text())
        with MIXED_OPPORTUNITIES.open(newline="") as handle:
            opportunities = list(csv.DictReader(handle))
        with MIXED_SCORECARD.open(newline="") as handle:
            scorecard = list(csv.DictReader(handle))
        with MIXED_REUSE.open(newline="") as handle:
            reuse = list(csv.DictReader(handle))

        for rows in (opportunities, scorecard, reuse):
            self.assertTrue(all(None not in row.values() for row in rows))
        reviewed = [row for row in scorecard if row["review_status"] in {"accepted", "edited", "rejected"}]
        effort = [row for row in scorecard if row["edit_minutes_bucket"]]

        self.assertEqual(validate(aggregate), [])
        self.assertEqual(aggregate["eligible_opportunities"], len(opportunities))
        self.assertEqual(aggregate["attempted_runs"], len(scorecard))
        self.assertEqual(aggregate["assessed_usefulness_runs"], len(reviewed))
        self.assertEqual(aggregate["missingness"]["pending_reviews"], sum(row["review_status"] == "pending" for row in scorecard))
        self.assertEqual(aggregate["edit_effort"]["assessed_runs"], len(effort))
        self.assertEqual(aggregate["missingness"]["unassessed_edit_effort"], len(scorecard) - len(effort))
        for status in ("accepted", "edited", "rejected"):
            self.assertEqual(aggregate["usefulness"][status], sum(row["review_status"] == status for row in reviewed))
        for decision in ("reused", "declined", "unobserved"):
            self.assertEqual(aggregate["reuse"][decision], sum(row["decision"] == decision for row in reuse))

if __name__ == "__main__": unittest.main()
