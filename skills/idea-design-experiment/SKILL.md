---
name: idea-design-experiment
description: Design minimal, falsifiable, resource-bounded experiments for shortlisted research ideas in any domain, including baselines or comparators, controls, ablations or sensitivity analyses, metrics, thresholds, budgets, and kill criteria. Use after an idea passes novelty and review, when a user asks how to test a hypothesis, or when creating the experiment artifact in the idea workflow. Design experiments only; do not execute the study unless separately requested.
---

# Idea Design Experiment

Design the cheapest experiment that can discriminate the proposed mechanism from credible alternatives. Prefer early falsification over a full implementation.

## Inputs

- Matching `40-review/<candidate_id>.md` and its experiment-design brief.
- `20-candidates.md` and matching `30-novelty/<candidate_id>.md`.
- User resource envelope and available data, code, equipment, environments, participants, samples, or checkpoints.

Only design full experiments for candidates with `review_verdict: advance`. A revised candidate must return through novelty and review first.

## Workflow

1. Restate the causal hypothesis and define a null or competing explanation.
2. Define a staged test:
   - `E0 smoke`: hours; verify pipeline, signal, and metric behavior;
   - `E1 probe`: normally 1–3 days; smallest decisive comparison;
   - `E2 confirm`: multi-seed and broader evaluation only if E1 passes.
3. Select the strongest practical baselines, comparators, or control groups, including matched controls for important confounders.
4. Specify interventions, held-constant variables, datasets, samples, environments, instruments, metrics, time horizons, and evaluation protocol as applicable.
5. Add ablations, sensitivity analyses, negative controls, or subgroup checks that isolate the claimed mechanism.
6. Pre-register success, failure, and kill thresholds before execution.
7. Estimate wall time, compute or lab resources, storage, API or participant cost, sample requirements, and implementation effort. Stay inside the user's hard constraints.
8. Define the analysis plan, uncertainty reporting, seeds, and reproducibility metadata.

## Output contract

Write one artifact per candidate at `50-experiments/<candidate_id>.md` using `references/experiment-template.md` and common frontmatter:

```yaml
---
schema: idea-research/v1
suite_version: 1.0.0
run_id: idea-YYYYMMDD-slug
artifact_id: ART-EXPERIMENT-IDEA-001
artifact_type: experiment
stage: experiment
producer: idea-design-experiment
candidate_id: IDEA-001
idea_revision: 1
status: complete | partial | blocked | failed
created_at: ISO-8601 timestamp
input_refs:
  - 40-review/IDEA-001.md
warnings: []
blockers: []
---
```

Assign stable IDs `EXP-<candidate-number>-E0`, `EXP-<candidate-number>-E1`, and `EXP-<candidate-number>-E2`.
Always emit the complete envelope shown above. If a matching advanced review is missing, use `status: blocked` and route to `$idea-review` instead of silently bypassing the gate.

## Quality gates

Every E1 plan must specify:

- hypothesis and counter-hypothesis;
- baseline and matched control;
- independent and dependent variables;
- primary metric plus decision threshold;
- key ablations and confounders;
- seeds or uncertainty plan;
- resource estimate and stop conditions;
- expected interpretation for positive, null, and contradictory outcomes.

If no affordable discriminating experiment exists, mark the candidate `experiment-blocked`; do not disguise a full project as a minimal probe.

If experiment design reveals that the problem, mechanism, main claim, or evaluation setting must change, do not silently edit the idea. Create a revised or descendant candidate and send it through novelty and review again.

If the topic is World Models, read `references/domain-profile-world-model.md` for field-specific controls and metrics.

## Handoff

Pass the candidate experiment artifact to `$idea-synthesize`. Do not execute experiments without a separate user request and explicit approval for consequential spending, external recruitment, deployment, or compute use.
