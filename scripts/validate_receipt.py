#!/usr/bin/env python3
"""Validate an agent run receipt without third-party packages."""
import json
import math
import sys
from datetime import datetime
from pathlib import Path

ROOT_KEYS = {"run_id", "started_at", "completed_at", "workflow", "rung", "actor", "inputs", "actions", "outputs", "evidence", "outcome", "review"}
REVIEW_KEYS = {"status", "reviewer", "measurement_mode", "edit_minutes", "edit_minutes_bucket", "voluntary_reuse", "unsupported_claims", "reversal", "notes"}
REVIEW_REQUIRED = {"status", "reviewer", "edit_minutes", "unsupported_claims", "reversal", "notes"}
MODES = {"exact", "rounded", "bucketed", "unassessed"}
BUCKETS = {"0", "1-5", "6-15", "16-30", "31+"}

def iso_datetime(value, name, errors):
    if not isinstance(value, str):
        errors.append(f"{name}: expected string")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{name}: expected ISO 8601 date-time")

def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ["root: expected object"]
    missing = ROOT_KEYS - data.keys()
    extra = data.keys() - ROOT_KEYS
    if missing: errors.append("root: missing " + ", ".join(sorted(missing)))
    if extra: errors.append("root: unexpected " + ", ".join(sorted(extra)))
    for key in ("run_id", "workflow", "actor"):
        if key in data and (not isinstance(data[key], str) or not data[key].strip()): errors.append(f"{key}: expected non-empty string")
    for key in ("started_at", "completed_at"):
        if key in data: iso_datetime(data[key], key, errors)
    if "rung" in data and (not isinstance(data["rung"], int) or isinstance(data["rung"], bool) or not 0 <= data["rung"] <= 4): errors.append("rung: expected integer from 0 to 4")
    for key in ("inputs", "actions", "outputs", "evidence"):
        if key in data and (not isinstance(data[key], list) or not all(isinstance(x, str) for x in data[key])): errors.append(f"{key}: expected array of strings")
    if data.get("outcome") not in {"completed", "failed", "stopped"}: errors.append("outcome: expected completed, failed, or stopped")
    review = data.get("review")
    if not isinstance(review, dict): errors.append("review: expected object")
    else:
        missing = REVIEW_REQUIRED - review.keys(); extra = review.keys() - REVIEW_KEYS
        if missing: errors.append("review: missing " + ", ".join(sorted(missing)))
        if extra: errors.append("review: unexpected " + ", ".join(sorted(extra)))
        status = review.get("status")
        if status not in {"pending", "accepted", "edited", "rejected"}: errors.append("review.status: invalid value")
        if review.get("reviewer") is not None and not isinstance(review.get("reviewer"), str): errors.append("review.reviewer: expected string or null")
        mode = review.get("measurement_mode")
        if "measurement_mode" in review and (not isinstance(mode, str) or mode not in MODES): errors.append("review.measurement_mode: invalid value")
        n = review.get("edit_minutes")
        if n is not None and (not isinstance(n, (int, float)) or isinstance(n, bool) or not math.isfinite(n) or n < 0): errors.append("review.edit_minutes: expected finite non-negative number or null")
        bucket = review.get("edit_minutes_bucket")
        if "edit_minutes_bucket" in review and bucket is not None and (not isinstance(bucket, str) or bucket not in BUCKETS): errors.append("review.edit_minutes_bucket: invalid value")
        if isinstance(mode, str) and mode in MODES:
            if status == "pending":
                if n is not None: errors.append("review.edit_minutes: must be null while review is pending")
                if bucket is not None: errors.append("review.edit_minutes_bucket: must be null while review is pending")
                if review.get("voluntary_reuse") is not None: errors.append("review.voluntary_reuse: must be null while review is pending")
            elif mode in {"exact", "rounded"}:
                if n is None: errors.append("review.edit_minutes: required for exact or rounded measurement")
                if mode == "rounded" and n is not None and isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) and n % 5 != 0: errors.append("review.edit_minutes: rounded measurement must use 5-minute increments")
                if bucket is not None: errors.append("review.edit_minutes_bucket: must be null unless measurement is bucketed")
            elif mode == "bucketed":
                if n is not None: errors.append("review.edit_minutes: must be null for bucketed or unassessed measurement")
                if bucket is None: errors.append("review.edit_minutes_bucket: required for bucketed measurement")
            elif mode == "unassessed":
                if n is not None: errors.append("review.edit_minutes: must be null for bucketed or unassessed measurement")
                if bucket is not None: errors.append("review.edit_minutes_bucket: must be null unless measurement is bucketed")
        reuse = review.get("voluntary_reuse")
        if "voluntary_reuse" in review and reuse is not None and not isinstance(reuse, bool): errors.append("review.voluntary_reuse: expected boolean or null")
        unsupported = review.get("unsupported_claims")
        if not isinstance(unsupported, int) or isinstance(unsupported, bool) or unsupported < 0: errors.append("review.unsupported_claims: expected non-negative integer")
        if not isinstance(review.get("reversal"), bool): errors.append("review.reversal: expected boolean")
        if not isinstance(review.get("notes"), str): errors.append("review.notes: expected string")
    return errors

def reject_constant(value):
    raise ValueError(f"non-standard numeric constant {value}")

def main():
    if len(sys.argv) != 2:
        print("usage: validate_receipt.py RECEIPT.json", file=sys.stderr); return 2
    path = Path(sys.argv[1])
    try: data = json.loads(path.read_text(), parse_constant=reject_constant)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr); return 1
    errors = validate(data)
    if errors:
        print("INVALID")
        for error in errors: print(f"- {error}")
        return 1
    print(f"VALID: {path} ({data['workflow']}, rung {data['rung']}, outcome {data['outcome']})")
    return 0

if __name__ == "__main__": raise SystemExit(main())
