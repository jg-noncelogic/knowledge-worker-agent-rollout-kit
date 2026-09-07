#!/usr/bin/env python3
"""Validate an agent run receipt without third-party packages."""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT_KEYS = {"run_id", "started_at", "completed_at", "workflow", "rung", "actor", "inputs", "actions", "outputs", "evidence", "outcome", "review"}
REVIEW_KEYS = {"status", "reviewer", "edit_minutes", "unsupported_claims", "reversal", "notes"}

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
        missing = REVIEW_KEYS - review.keys(); extra = review.keys() - REVIEW_KEYS
        if missing: errors.append("review: missing " + ", ".join(sorted(missing)))
        if extra: errors.append("review: unexpected " + ", ".join(sorted(extra)))
        if review.get("status") not in {"pending", "accepted", "edited", "rejected"}: errors.append("review.status: invalid value")
        if review.get("reviewer") is not None and not isinstance(review.get("reviewer"), str): errors.append("review.reviewer: expected string or null")
        n = review.get("edit_minutes")
        if n is not None and (not isinstance(n, (int,float)) or isinstance(n,bool) or n < 0): errors.append("review.edit_minutes: expected non-negative number or null")
        n = review.get("unsupported_claims")
        if not isinstance(n, int) or isinstance(n,bool) or n < 0: errors.append("review.unsupported_claims: expected non-negative integer")
        if not isinstance(review.get("reversal"), bool): errors.append("review.reversal: expected boolean")
        if not isinstance(review.get("notes"), str): errors.append("review.notes: expected string")
    return errors

def main():
    if len(sys.argv) != 2:
        print("usage: validate_receipt.py RECEIPT.json", file=sys.stderr); return 2
    path = Path(sys.argv[1])
    try: data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr); return 1
    errors = validate(data)
    if errors:
        print("INVALID")
        for error in errors: print(f"- {error}")
        return 1
    print(f"VALID: {path} ({data['workflow']}, rung {data['rung']}, outcome {data['outcome']})")
    return 0

if __name__ == "__main__": raise SystemExit(main())
