import json
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_aggregate import validate

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample-content-blind-aggregate.json"

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

if __name__ == "__main__": unittest.main()
