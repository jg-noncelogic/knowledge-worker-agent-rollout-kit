#!/usr/bin/env python3
"""Render a privacy-aware pilot decision card from a validated aggregate."""
import argparse
import json
from pathlib import Path

from validate_aggregate import validate


def ratio_line(label, numerator, denominator, denominator_label):
    if denominator == 0:
        return f"{label}: n/a (0 {denominator_label})"
    return f"{label}: {numerator}/{denominator} {denominator_label} ({numerator / denominator:.1%})"


def summarize(data):
    useful = data["usefulness"]["accepted"] + data["usefulness"]["edited"]
    assessed = data["assessed_usefulness_runs"]
    reuse = data["reuse"]
    observed_reuse = reuse["reused"] + reuse["declined"]
    threshold = data["small_group_suppression_threshold"]
    workflow = " ".join(data["workflow"].split())

    if observed_reuse < threshold:
        noun = "decision" if observed_reuse == 1 else "decisions"
        reuse_line = f"Reuse: suppressed ({observed_reuse} observed {noun}; threshold {threshold})"
    else:
        reuse_line = ratio_line("Observed reuse", reuse["reused"], observed_reuse, "observed decisions")

    edit = data["edit_effort"]
    bucket_order = ("0", "1-5", "6-15", "16-30", "31+")
    distribution = ", ".join(f"{key}={edit['distribution'].get(key, 0)}" for key in bucket_order)
    edit_line = f"Edit effort ({edit['mode']}, {edit['assessed_runs']} assessed): {distribution}"

    lines = [
        f"# Pilot evidence card: {workflow}",
        "",
        f"Window: {data['from']} to {data['through_exclusive']} (exclusive)",
        ratio_line("Attempt coverage", data["attempted_runs"], data["eligible_opportunities"], "eligible"),
        ratio_line("Useful outputs", useful, assessed, "assessed"),
        f"Pending reviews: {data['missingness']['pending_reviews']}",
        edit_line,
        f"Unassessed edit effort: {data['missingness']['unassessed_edit_effort']}",
        reuse_line,
        f"Unobserved reuse decisions: {data['missingness']['unobserved_reuse']}",
        "",
        "Decision: not inferred",
        "Compare these observations with the thresholds declared before the pilot.",
        "Choose exactly one: expand, revise, retire, or format-test.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("aggregate", type=Path)
    args = parser.parse_args()
    data = json.loads(args.aggregate.read_text())
    errors = validate(data)
    if errors:
        raise SystemExit("INVALID aggregate:\n- " + "\n- ".join(errors))
    print(summarize(data), end="")


if __name__ == "__main__":
    main()
