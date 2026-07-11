---
name: idea-review
description: Critically review and rank research candidates in any domain using novelty evidence, scientific value, mechanism clarity, falsifiability, feasibility, and evaluation integrity. Use when deciding which ideas to advance, revise, hold, or reject, when requesting a skeptical research review, or when creating the review artifact in the idea workflow. This skill reviews experimentability but delegates detailed protocols to idea-design-experiment.
---

# Idea Review

Act as a skeptical program committee and lab lead. Reward clear causal claims and cheap decisive tests; penalize vague novelty, hidden resource costs, and evaluations that cannot distinguish the proposed mechanism.

## Inputs

- `20-candidates.md`.
- Matching artifacts from `30-novelty/<candidate_id>.md`; do not finalize acceptance without them.
- `00-brief.md` resource and scope constraints.
- `10-scan.md` for evidence provenance.

## Workflow

1. Validate that candidate IDs and novelty verdicts are preserved.
2. Apply the rubric in `references/review-rubric.md`.
3. Review each candidate independently before comparing candidates.
4. Identify the strongest reason to reject and the cheapest evidence that could change the verdict.
5. Check whether the proposed evidence can distinguish the claimed mechanism from credible confounders such as capacity, sample size, exposure, leakage, measurement choice, implementation effort, or easier optimization.
6. Assign one verdict:
   - `advance`: ready for detailed experiment design;
   - `revise`: promising but requires a specified change;
   - `hold`: blocked by evidence, resources, or dependencies;
   - `reject`: fails novelty, value, falsifiability, or feasibility.
7. Rank only `advance` candidates. Do not revive `known` candidates from the novelty stage.

If the topic is World Models, read `references/domain-profile-world-model.md` for additional failure modes and review checks.

## Output contract

Write one artifact per candidate at `40-review/<candidate_id>.md` with common frontmatter:

```yaml
---
schema: idea-research/v1
suite_version: 1.0.0
run_id: idea-YYYYMMDD-slug
artifact_id: ART-REVIEW-IDEA-001
artifact_type: review
stage: review
producer: idea-review
candidate_id: IDEA-001
idea_revision: 1
status: complete | partial | blocked | failed
created_at: ISO-8601 timestamp
input_refs:
  - 20-candidates.md
  - 30-novelty/IDEA-001.md
warnings: []
blockers: []
---
```

For each candidate include:

- `candidate_id`, novelty verdict, and review verdict;
- rubric scores with short evidence-based explanations;
- fatal flaw or primary risk;
- cheapest decision-changing evidence;
- required revision, if any;
- experiment-design brief for advanced candidates.

Always emit the complete envelope shown above. If novelty evidence is missing, use `status: blocked` and route to `$idea-check-novelty`; do not return an abbreviated or final review.

## Boundaries

- Do not perform a fresh novelty search; return evidence gaps to `$idea-check-novelty`.
- Do not write a full experiment protocol; issue a concise design brief to `$idea-design-experiment`.
- Do not average away fatal flaws. A high total score cannot compensate for an unfalsifiable claim or impossible resource requirement.
- Do not review a revision that differs from the novelty artifact. Route it back to novelty first.

## Handoff

Send only `advance` candidates to `$idea-design-experiment`. Send `revise` candidates back to generation or novelty with explicit constraints. Write in the user's language unless requested otherwise.
