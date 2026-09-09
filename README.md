# Knowledge-Worker Agent Rollout Kit

A small, vendor-neutral kit for teams that already have an internal chat assistant and want to test more agentic workflows without starting with a platform rewrite.

This was built in response to a concrete practitioner question: after deploying an internal GPT, what agentic product features do knowledge workers actually use?[1]

## The short answer

Do not roll out a general-purpose "agent." Roll out one workflow at a time.

A good first workflow is:

- frequent enough to observe within 30 days;
- bounded by a clear input and output;
- reversible before it changes a system of record;
- verifiable by a person who already does the work;
- painful enough that saving 15 minutes matters.

Examples: turn notes into a draft brief, compare a submission against a checklist, prepare a case summary with source links, or draft a structured update from approved records.

## Rollout ladder

Move a workflow up one rung only when its evidence supports the move.

| Rung | Agent behavior | Human role | Promotion signal |
|---|---|---|---|
| 0. Observe | Records the current steps and baseline | Does the work normally | Stable baseline for time and error rate |
| 1. Draft | Produces an artifact but changes nothing | Reviews every output | At least 70% useful outputs and falling edit time |
| 2. Recommend | Proposes a decision with evidence | Accepts or rejects | Reasons for rejection are measurable and repeatable |
| 3. Act with approval | Prepares a reversible action | Approves before execution | Low rollback rate and no unclear ownership |
| 4. Scoped autonomy | Acts inside explicit limits | Reviews receipts and exceptions | Two pilot cycles without a stop-rule breach |

The thresholds are starting hypotheses, not universal benchmarks. Change them before the pilot, not after seeing the results.

## Run a 30-day pilot

1. **Days 1-3: choose one workflow.** Interview three people who perform it. Fill in [`templates/workflow-candidate.md`](templates/workflow-candidate.md).
2. **Days 4-7: establish a baseline.** Record five normal runs: cycle time, handoffs, corrections, and source systems.
3. **Week 2: run in draft mode.** Keep all writes disabled. Capture a receipt for every run.
4. **Week 3: tighten the workflow.** Turn recurring reviewer corrections into explicit checks or remove the use case if corrections remain ambiguous.
5. **Week 4: decide.** Expand, revise, retire, or format-test. Do not call a pilot successful because people logged in.

## Measure usefulness

Track these per run in [`templates/pilot-scorecard.csv`](templates/pilot-scorecard.csv):

- **useful output:** reviewer would use the result after normal editing;
- **edit minutes:** active time to make the output usable;
- **cycle minutes:** elapsed workflow time;
- **unsupported claims:** statements lacking an approved source;
- **reversal:** an agent-prepared action that had to be undone;
- **voluntary reuse:** the same person chose the workflow again.

Primary success signal: median edit minutes improve against the baseline while useful-output rate stays above the predeclared threshold.

### Collect reviewer effort without collecting reviewer content

Use the least detailed measurement that can answer the pilot decision. A content-blind rollout does not need prompts, outputs, reviewer notes, or a stable person identifier in its aggregate report.

Choose one `measurement_mode` before the pilot:

| Mode | Store per run | Use when |
|---|---|---|
| `exact` | active edit minutes | Reviewers already track time and the sample is large enough to aggregate safely |
| `rounded` | active edit minutes rounded to the nearest 5 minutes | Exact duration is unnecessarily identifying |
| `bucketed` | one of `0`, `1-5`, `6-15`, `16-30`, `31+` | Only the effort band is needed; report distributions, not a median |
| `unassessed` | `null` | Collection would be unreliable or too sensitive |

For voluntary reuse, store `true`, `false`, or `null`. A run receipt alone cannot show that someone declined to reuse the workflow. Register each eligible follow-up in [`templates/reuse-opportunities.csv`](templates/reuse-opportunities.csv): `reused` links to a new run, `declined` records an observed choice not to run it, and `unobserved` preserves missingness. Use a bounded cohort label or leave it blank instead of exporting a stable person identifier.

Keep the detailed run receipt under the team's normal access and retention controls. Publish only a bounded aggregate with the observation window, eligible-opportunity denominator, attempted-run denominator, assessed-run denominator, useful-output counts, edit-effort distribution, reuse counts, and explicit missingness. Suppress small groups according to the team's privacy policy. [`templates/content-blind-aggregate.json`](templates/content-blind-aggregate.json) structurally excludes run IDs, timestamps, reviewer identity, file paths, and notes; validate a populated copy with `python3 scripts/validate_aggregate.py FILE.json`. The sample aggregate shows the required count reconciliations.

`edit_minutes` measures human reviewer effort. It is not model, energy, infrastructure, or total economic cost. Keep those claims unknown until separately measured and calibrated.

## Stop rules

Stop or step down a rung when any of these occurs:

- the workflow owner cannot explain who is accountable for the result;
- required evidence is missing from the receipt;
- the agent reaches outside the declared systems or action limits;
- review time does not improve after ten runs;
- users bypass the workflow because a simpler form or script is better;
- a reversal exposes an irreversible path.

A retirement decision is useful evidence. It prevents a weak workflow from becoming infrastructure.

## Machine-readable run receipts

Validate the included example:

```bash
python3 scripts/validate_receipt.py examples/sample-receipt.json
python3 scripts/validate_aggregate.py examples/sample-content-blind-aggregate.json
```

The validators are Python standard-library only. The JSON Schemas in [`schemas/`](schemas/) can be used by systems that already support JSON Schema Draft 2020-12. Existing receipt fields remain valid; the privacy-aware measurement fields are optional for backward compatibility and enforced when present.

## Decision rule

At the end of the pilot, choose exactly one:

- **Expand:** usefulness and review-time targets passed; test the next rung.
- **Revise:** the need is real, but failure reasons cluster around a fixable constraint.
- **Retire:** the workflow is not useful enough or cannot be bounded.
- **Format-test:** the underlying information is useful, but the delivery format is wrong.

Record the decision before proposing another agent feature.

## Sources

[1] [Ask HN: How to roll out Agents for knowledge workers?](https://news.ycombinator.com/item?id=49596428)

## License

MIT
