# Idea suite contract

## Architecture

```text
idea-scan
  -> idea-generate
  -> idea-check-novelty [one artifact per candidate]
  -> idea-review [one artifact per candidate]
  -> idea-design-experiment [advanced candidates only]
  -> idea-synthesize
```

Stage boundaries are strict:

- Scan maps problems; it does not propose methods.
- Generate proposes candidates and hypotheses; it does not claim novelty.
- Novelty checks prior art online; it does not judge overall feasibility or value.
- Review decides value and feasibility; it does not redo searches or write full protocols.
- Experiment designs tests; it does not execute or rerank ideas.
- Synthesize validates, connects, and summarizes existing verdicts only.

## Run layout

```text
research/idea-runs/<run-id>/
├── 00-brief.md
├── 10-scan.md
├── 20-candidates.md
├── 30-novelty/
│   └── IDEA-001.md
├── 40-review/
│   └── IDEA-001.md
├── 50-experiments/
│   └── IDEA-001.md
└── 60-summary.md
```

Use `run_id: idea-YYYYMMDD-<slug>`. IDs are immutable and never reused:

- gaps: `GAP-001`
- opportunities: `OPP-001`
- candidates: `IDEA-001`
- claims: `CLM-<scope>-001`
- sources: `SRC-001`
- evidence: `EVD-001`
- experiments: `EXP-<candidate-number>-E0|E1|E2`

A materially changed candidate receives a new ID and records `parent_id`. Rejected IDs remain in the lineage and cannot be recycled.
Minor clarification increments `idea_revision`. Every novelty, review, and experiment artifact binds to one exact candidate revision; changing that revision invalidates downstream artifacts.

## Artifact envelope

Every artifact uses:

```yaml
---
schema: idea-research/v1
suite_version: 1.0.0
run_id: idea-YYYYMMDD-slug
artifact_id: ART-<stage>-NNN
artifact_type: brief | scan | candidates | novelty | review | experiment | summary
stage: brief | scan | generate | novelty | review | experiment | synthesize
producer: idea-<stage-name>
candidate_id: IDEA-001 # omit for run-level artifacts
idea_revision: 1      # omit for run-level artifacts
status: complete | partial | blocked | failed
created_at: ISO-8601 timestamp
input_refs:
  - path/to/input.md
warnings: []
blockers: []
---
```

Ad hoc stage calls must create the same complete envelope. Use standard `IDEA-NNN` IDs; do not invent alternate ID namespaces for one-off requests.

Use these body headings so the coordinator can load selectively:

1. `Decision Summary`
2. `Stage Output`
3. `Claims`
4. `Evidence`
5. `Limitations`
6. `Handoff`

## Status and verdict semantics

- `complete`: the stage exit gates are satisfied.
- `partial`: useful output exists, but named coverage gaps remain; warnings flow downstream.
- `blocked`: reliable work cannot continue because of missing input, network, permission, or user decision.
- `failed`: a tool or format error occurred; record whether retry is possible.

Artifact status is operational. Candidate decisions are scientific and use separate values:

- novelty: `likely-novel | incremental | collision-risk | known | unresolved`
- review: `advance | revise | hold | reject`
- experiment: `experiment-ready | experiment-blocked`

## Brief contract

`00-brief.md` records:

- the user's original request and exact hint;
- hint mode: `seed | constraint | preference | avoid | none`;
- research scope and explicit exclusions;
- time, compute or lab resources, data, equipment, participants, ethics, API, and implementation constraints;
- desired candidate count and maximum regeneration rounds;
- assumptions made without user input;
- the definition of a viable idea.

## Iteration rules

When novelty or review rejects a candidate:

1. Preserve its artifact and verdict.
2. Create a rejection memo containing the collision or fatal flaw.
3. Feed the memo to generation as a negative constraint.
4. Assign new IDs to regenerated candidates.
5. Run novelty and review again; regenerated candidates receive no automatic pass.

Default to at most three generation rounds. If nothing qualifies, report `no viable idea yet` rather than forcing a winner.

## Lightweight synthesis

Read artifact frontmatter plus `Decision Summary` and `Handoff` first. Open full bodies only for finalists or inconsistencies. Never overwrite upstream verdicts. Route missing or invalid artifacts to their owning skill.
