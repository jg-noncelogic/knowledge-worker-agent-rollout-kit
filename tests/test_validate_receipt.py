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

if __name__ == "__main__": unittest.main()
