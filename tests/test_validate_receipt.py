import json
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_receipt import validate

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample-receipt.json"

class ReceiptTests(unittest.TestCase):
    def setUp(self): self.data = json.loads(SAMPLE.read_text())
    def test_sample_is_valid(self): self.assertEqual(validate(self.data), [])
    def test_missing_key_fails(self):
        del self.data["evidence"]
        self.assertTrue(any("missing evidence" in e for e in validate(self.data)))
    def test_out_of_range_rung_fails(self):
        self.data["rung"] = 5
        self.assertIn("rung: expected integer from 0 to 4", validate(self.data))
    def test_extra_review_key_fails(self):
        self.data["review"]["secret"] = "no"
        self.assertTrue(any("unexpected secret" in e for e in validate(self.data)))
    def test_rounded_minutes_require_five_minute_increment(self):
        self.data["review"]["edit_minutes"] = 4.5
        self.assertIn("review.edit_minutes: rounded measurement must use 5-minute increments", validate(self.data))
    def test_bucketed_mode_requires_bucket_and_hides_exact_minutes(self):
        self.data["review"].update({"measurement_mode": "bucketed", "edit_minutes": None, "edit_minutes_bucket": "1-5"})
        self.assertEqual(validate(self.data), [])
    def test_unassessed_reuse_preserves_missingness(self):
        self.data["review"].update({"measurement_mode": "unassessed", "edit_minutes": None, "voluntary_reuse": None})
        self.assertEqual(validate(self.data), [])
    def test_pending_review_allows_predeclared_mode_without_measurement(self):
        self.data["review"].update({"status": "pending", "edit_minutes": None, "edit_minutes_bucket": None, "voluntary_reuse": None})
        self.assertEqual(validate(self.data), [])
    def test_legacy_receipt_without_new_fields_remains_valid(self):
        for key in ("measurement_mode", "edit_minutes_bucket", "voluntary_reuse"):
            del self.data["review"][key]
        self.assertEqual(validate(self.data), [])
    def test_unhashable_mode_returns_error_not_exception(self):
        self.data["review"]["measurement_mode"] = []
        self.assertIn("review.measurement_mode: invalid value", validate(self.data))
    def test_non_finite_minutes_fail(self):
        self.data["review"].update({"measurement_mode": "exact", "edit_minutes": float("inf")})
        self.assertIn("review.edit_minutes: expected finite non-negative number or null", validate(self.data))

if __name__ == "__main__": unittest.main()
