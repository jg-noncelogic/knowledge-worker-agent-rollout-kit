#!/usr/bin/env python3
"""Validate a content-blind rollout aggregate and its count reconciliations."""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT_KEYS = {"from", "through_exclusive", "workflow", "eligible_opportunities", "attempted_runs", "assessed_usefulness_runs", "usefulness", "edit_effort", "reuse", "missingness", "small_group_suppression_threshold"}
USEFULNESS_KEYS = {"accepted", "edited", "rejected"}
EDIT_KEYS = {"mode", "assessed_runs", "distribution"}
REUSE_KEYS = {"eligible_followups", "reused", "declined", "unobserved"}
MISSING_KEYS = {"pending_reviews", "unassessed_edit_effort", "unobserved_reuse"}
MODES = {"exact", "rounded", "bucketed", "unassessed"}
BUCKETS = {"0", "1-5", "6-15", "16-30", "31+"}

def nonnegative_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0

def validate(data):
    errors = []
    if not isinstance(data, dict): return ["root: expected object"]
    missing = ROOT_KEYS - data.keys(); extra = data.keys() - ROOT_KEYS
    if missing: errors.append("root: missing " + ", ".join(sorted(missing)))
    if extra: errors.append("root: unexpected " + ", ".join(sorted(extra)))
    for key in ("from", "through_exclusive"):
        value = data.get(key)
        if not isinstance(value, str): errors.append(f"{key}: expected ISO 8601 date-time")
        else:
            try: datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError: errors.append(f"{key}: expected ISO 8601 date-time")
    if not isinstance(data.get("workflow"), str) or not data.get("workflow", "").strip(): errors.append("workflow: expected non-empty string")
    for key in ("eligible_opportunities", "attempted_runs", "assessed_usefulness_runs"):
        if not nonnegative_int(data.get(key)): errors.append(f"{key}: expected non-negative integer")
    threshold = data.get("small_group_suppression_threshold")
    if not nonnegative_int(threshold) or threshold < 1: errors.append("small_group_suppression_threshold: expected positive integer")

    usefulness = data.get("usefulness")
    if not isinstance(usefulness, dict): errors.append("usefulness: expected object")
    else:
        if set(usefulness) != USEFULNESS_KEYS: errors.append("usefulness: expected accepted, edited, rejected only")
        for key in USEFULNESS_KEYS:
            if not nonnegative_int(usefulness.get(key)): errors.append(f"usefulness.{key}: expected non-negative integer")
        if all(nonnegative_int(usefulness.get(k)) for k in USEFULNESS_KEYS) and nonnegative_int(data.get("assessed_usefulness_runs")):
            if sum(usefulness.values()) != data["assessed_usefulness_runs"]: errors.append("usefulness: counts must sum to assessed_usefulness_runs")

    edit = data.get("edit_effort")
    if not isinstance(edit, dict): errors.append("edit_effort: expected object")
    else:
        if set(edit) != EDIT_KEYS: errors.append("edit_effort: expected mode, assessed_runs, distribution only")
        mode = edit.get("mode")
        if not isinstance(mode, str) or mode not in MODES: errors.append("edit_effort.mode: invalid value")
        if not nonnegative_int(edit.get("assessed_runs")): errors.append("edit_effort.assessed_runs: expected non-negative integer")
        distribution = edit.get("distribution")
        if not isinstance(distribution, dict) or not all(isinstance(k, str) and k in BUCKETS and nonnegative_int(v) for k, v in distribution.items()): errors.append("edit_effort.distribution: expected bounded effort buckets")
        elif nonnegative_int(edit.get("assessed_runs")) and sum(distribution.values()) != edit["assessed_runs"]: errors.append("edit_effort: distribution must sum to assessed_runs")
        if edit.get("mode") == "unassessed" and edit.get("assessed_runs") != 0: errors.append("edit_effort: unassessed mode must have zero assessed runs")

    reuse = data.get("reuse")
    if not isinstance(reuse, dict): errors.append("reuse: expected object")
    else:
        if set(reuse) != REUSE_KEYS: errors.append("reuse: expected eligible_followups, reused, declined, unobserved only")
        for key in REUSE_KEYS:
            if not nonnegative_int(reuse.get(key)): errors.append(f"reuse.{key}: expected non-negative integer")
        if all(nonnegative_int(reuse.get(k)) for k in REUSE_KEYS):
            if reuse["reused"] + reuse["declined"] + reuse["unobserved"] != reuse["eligible_followups"]: errors.append("reuse: outcome counts must sum to eligible_followups")

    missingness = data.get("missingness")
    if not isinstance(missingness, dict): errors.append("missingness: expected object")
    else:
        if set(missingness) != MISSING_KEYS: errors.append("missingness: expected pending_reviews, unassessed_edit_effort, unobserved_reuse only")
        for key in MISSING_KEYS:
            if not nonnegative_int(missingness.get(key)): errors.append(f"missingness.{key}: expected non-negative integer")
        if isinstance(reuse, dict) and nonnegative_int(reuse.get("unobserved")) and nonnegative_int(missingness.get("unobserved_reuse")) and reuse["unobserved"] != missingness["unobserved_reuse"]: errors.append("missingness.unobserved_reuse: must match reuse.unobserved")

    if isinstance(missingness, dict) and nonnegative_int(data.get("attempted_runs")) and nonnegative_int(data.get("assessed_usefulness_runs")) and nonnegative_int(missingness.get("pending_reviews")):
        if data["assessed_usefulness_runs"] + missingness["pending_reviews"] != data["attempted_runs"]: errors.append("missingness.pending_reviews: assessed plus pending must equal attempted_runs")
    if isinstance(missingness, dict) and isinstance(edit, dict) and nonnegative_int(data.get("attempted_runs")) and nonnegative_int(edit.get("assessed_runs")) and nonnegative_int(missingness.get("unassessed_edit_effort")):
        if edit["assessed_runs"] + missingness["unassessed_edit_effort"] != data["attempted_runs"]: errors.append("missingness.unassessed_edit_effort: assessed plus unassessed must equal attempted_runs")

    if nonnegative_int(data.get("attempted_runs")) and nonnegative_int(data.get("eligible_opportunities")) and data["attempted_runs"] > data["eligible_opportunities"]: errors.append("attempted_runs: cannot exceed eligible_opportunities")
    if nonnegative_int(data.get("assessed_usefulness_runs")) and nonnegative_int(data.get("attempted_runs")) and data["assessed_usefulness_runs"] > data["attempted_runs"]: errors.append("assessed_usefulness_runs: cannot exceed attempted_runs")
    return errors

def reject_constant(value): raise ValueError(f"non-standard numeric constant {value}")

def main():
    if len(sys.argv) != 2:
        print("usage: validate_aggregate.py AGGREGATE.json", file=sys.stderr); return 2
    path = Path(sys.argv[1])
    try: data = json.loads(path.read_text(), parse_constant=reject_constant)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr); return 1
    errors = validate(data)
    if errors:
        print("INVALID")
        for error in errors: print(f"- {error}")
        return 1
    print(f"VALID: {path} ({data['workflow']}, {data['attempted_runs']} attempted runs)")
    return 0

if __name__ == "__main__": raise SystemExit(main())
