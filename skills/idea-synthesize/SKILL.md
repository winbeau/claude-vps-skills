---
name: idea-synthesize
description: "Coordinate the domain-agnostic idea skill suite and produce a concise, traceable final ranking from existing scan, candidate, novelty, review, and experiment artifacts. Use when the user asks to run the full idea-discovery workflow, continue an interrupted run, summarize results, compare finalists, or select the next idea to test. Keep this skill lightweight: delegate stage work to the named sibling skills and never redo their analysis."
---

# Idea Synthesize

Provide the suite's thin orchestration and final decision layer. Read `references/workflow-contract.md` when starting or resuming a full run.

The suite is self-contained. When compatible external research skills are installed or the user asks to reuse them, read `references/external-adapters.md` and normalize their outputs into this suite's artifact contract.

## Full workflow

1. Create `research/idea-runs/<run-id>/00-brief.md` containing the user's original hint, goals, constraints, assumptions, and success definition.
2. Invoke stages in order when their valid artifact is missing:
   1. `$idea-scan` -> `10-scan.md`
   2. `$idea-generate` -> `20-candidates.md`
   3. `$idea-check-novelty` -> `30-novelty/<candidate_id>.md`
   4. `$idea-review` -> `40-review/<candidate_id>.md`
   5. `$idea-design-experiment` -> `50-experiments/<candidate_id>.md`
3. Stop on `blocked`. Surface the blocker instead of filling missing evidence.
4. If all candidates are rejected, return the rejection memos to generation as negative constraints. Allow at most three rounds unless the user requests otherwise.
5. Never send a `known`, `reject`, or `experiment-blocked` candidate forward as the winner.

For inline or ad hoc inputs without a run directory, create `run_id: idea-YYYYMMDD-adhoc-<slug>`, include `inline-user-request` or another explicit label in `input_refs`, and return the `60-summary.md` structure in the response. Missing upstream artifacts produce `status: blocked`; they do not remove the artifact contract.

## Synthesis

When Python is available, first run the bundled validator, resolving it relative to this SKILL.md: `python3 <skill-dir>/scripts/validate_run.py <run-dir> --json`. Route missing artifacts to the reported owning skills and stop on schema or revision errors. If Python is unavailable, perform the same checks from `references/workflow-contract.md` manually.

Read artifact frontmatter plus `Decision Summary` and `Handoff` first. Open full bodies only for finalists, warnings, or cross-stage inconsistencies. Read upstream verdicts without changing them. Rank only candidates that have:

- novelty verdict `likely-novel` or justified `incremental`;
- review verdict `advance`;
- an affordable E1 experiment with a decision threshold.

Require matching `candidate_id` and `idea_revision` across generation, novelty, review, and experiment artifacts. Route stale revisions back to the owning stage.

Write `60-summary.md` containing:

- one recommended candidate, when one legitimately qualifies;
- up to two backups;
- one-paragraph rationale per finalist;
- novelty confidence and closest-work risk;
- cheapest decisive experiment, cost, and kill criterion;
- unresolved questions and the next action;
- a trace table linking `gap_id -> candidate_id -> novelty verdict -> review verdict -> experiment_id`.

Use this envelope:

```yaml
---
schema: idea-research/v1
suite_version: 1.0.0
run_id: idea-YYYYMMDD-slug
artifact_id: ART-SYNTHESIZE-001
artifact_type: summary
stage: synthesize
producer: idea-synthesize
status: complete | partial | blocked | failed
created_at: ISO-8601 timestamp
input_refs: []
warnings: []
blockers: []
---
```

The response or file must begin with the complete envelope. Never emit prose alone or an abbreviated summary envelope, even when blocked or when the user provides artifacts inline instead of as files. Put every missing stage in `blockers` and the human-readable routing instructions in `Handoff`.

If nothing qualifies, report `no viable idea yet` and identify the narrowest next search or regeneration action. Do not force a winner.

## Boundaries

- Do not search literature, generate ideas, reassess novelty, rescore reviews, or redesign experiments inside this skill.
- Do not revive rejected candidates or silently alter stable IDs.
- Keep the user-facing summary concise; detailed evidence remains in upstream artifacts.
- Write in the user's language unless requested otherwise.
- If the host cannot invoke sibling skills, report the exact missing artifact and the skill that should create it instead of simulating that stage.
