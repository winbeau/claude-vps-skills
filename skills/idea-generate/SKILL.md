---
name: idea-generate
description: Generate diverse, testable research candidates in any domain from an evidence-backed scan, with optional user hints and hard resource constraints. Use when the user asks for research ideas, wants candidates based on a specific intuition or prompt, needs alternatives after a rejected idea, or needs the candidates artifact in the idea workflow. Do not claim novelty or make final acceptance decisions.
---

# Idea Generate

Turn gaps and user hints into mechanistic, falsifiable candidates. Treat a user hint as a seed or constraint, not as a conclusion that must be validated.

## Inputs

- `10-scan.md` when available.
- `00-brief.md` or explicit user constraints.
- Optional user hint in the user's original wording.
- Optional rejection memo from a previous novelty or review round.

If a scan is unavailable, clearly mark candidates as provisional and request or invoke `$idea-scan` before downstream novelty decisions.

Load a domain profile only when it matches the request. For World Model research, read `references/domain-profile-world-model.md`.

## Workflow

1. Preserve three evidence classes:
   - user-provided hypothesis or preference;
   - literature-backed observation;
   - model-generated inference.
2. Convert each selected gap into a causal chain:

   `problem -> proposed mechanism -> measurable prediction -> discriminating test`

3. Generate structurally different candidates, not paraphrases. Vary the bottleneck, mechanism, intervention, system component, data or measurement regime, population or setting, and evaluation target as appropriate to the domain.
4. When a user hint is present:
   - honor explicit constraints;
   - expand synonyms and adjacent mechanisms;
   - explain any narrowing or reinterpretation;
   - include a `hint_alignment` field for every candidate.
5. Reject vague forms such as “apply A to B” unless the candidate explains why A changes a known failure mechanism in B.
6. Include a minimum viable probe and a kill criterion for every candidate.
7. When regenerating after rejection, carry forward the rejection as a negative constraint. Change the problem or mechanism materially; renaming modules, datasets, or titles is insufficient.

## Portfolio

Unless the user specifies a count, produce 12 candidates:

- 6 evidence-adjacent, lower-risk candidates;
- 4 cross-family combinations with an explicit mechanism;
- 2 high-risk candidates with cheap falsification paths.

Do not force the quota when evidence is weak. Fewer defensible candidates are better than filler.

## Output contract

Write `20-candidates.md` using `references/candidate-template.md` and common frontmatter:

```yaml
---
schema: idea-research/v1
suite_version: 1.0.0
run_id: idea-YYYYMMDD-slug
artifact_id: ART-GENERATE-001
artifact_type: candidates
stage: generate
producer: idea-generate
status: complete | partial | blocked | failed
created_at: ISO-8601 timestamp
input_refs:
  - 10-scan.md
warnings: []
blockers: []
---
```

Assign stable IDs `IDEA-001`, `IDEA-002`, and so on. Set `idea_revision: 1`. Increment the revision for clarification that does not change the core mechanism; assign a new ID plus `parent_id` when the problem, mechanism, main claim, or evaluation setting changes materially. Downstream artifacts are valid only for the exact ID and revision they reviewed.
Always emit the complete envelope shown above, including when generation starts directly from a user hint.

## Quality gates

Every candidate must contain:

- a source `gap_id` or explicit user-only origin;
- problem, mechanism, and testable prediction;
- closest expected baseline family;
- minimum probe, budget estimate, and kill criterion;
- key assumptions and likely failure mode;
- `hint_alignment` when a user hint exists.

Do not label a candidate novel. Use `novelty_hypothesis`, which must be tested by `$idea-check-novelty`.

## Handoff

Pass all active candidates and their unchanged IDs to `$idea-check-novelty`. Write in the user's language unless requested otherwise.
