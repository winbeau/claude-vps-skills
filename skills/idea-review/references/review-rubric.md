# Review rubric

Score each dimension from 0 to 5. Compute `weighted_total = sum(weight * score / 5)`.

| dimension | weight | 0 | 3 | 5 |
|---|---:|---|---|---|
| scientific importance | 15 | trivial or unclear | useful narrow problem | important unresolved bottleneck |
| novelty | 15 | known | incremental but defensible | clear delta after strong search |
| mechanism plausibility | 15 | slogan only | plausible causal account | precise mechanism with discriminating prediction |
| falsifiability | 15 | cannot be disproved | measurable but ambiguous | cheap test separates competing explanations |
| resource fit | 20 | violates hard constraints | feasible with notable risk | comfortable fit with fallback |
| evaluation discrimination | 15 | evidence cannot isolate claim | partial controls | comparators and controls isolate mechanism |
| negative-result value | 5 | null result says little | narrows choices | resolves a meaningful uncertainty |

## Hard gates

Evaluate before total score:

- `duplicate`: fail when the core contribution is `known`.
- `differentiating_prediction`: fail when no observation separates the mechanism from a credible alternative.
- `testable_within_constraints`: fail when no affordable decisive probe exists.
- `evidence_integrity`: fail when the decision depends on fabricated, inaccessible, or untraceable evidence.

Any failed hard gate prevents `advance`, regardless of total score.

## Verdict guidance

- `advance`: all hard gates pass and normally total >= 75.
- `revise`: potentially strong, but one concrete repair is required before experiment design.
- `hold`: blocked by missing evidence, code, data, or resources.
- `reject`: fatal scientific or feasibility flaw.

Do not use thresholds mechanically. Explain the decisive reason and the cheapest evidence that could change the verdict.

## Review body template

```markdown
# Review: IDEA-001

## Decision Summary

- **candidate_id:** IDEA-001
- **idea_revision:** 1
- **novelty_verdict:**
- **review_verdict:** advance | revise | hold | reject
- **weighted_total:** 0-100
- **decisive reason:**

## Stage Output

### Scores

| dimension | weight | score | explanation |
|---|---:|---:|---|

### Hard gates

| gate | pass/fail | explanation |
|---|---|---|

### Critical assessment

- Strongest contribution:
- Fatal flaw or primary risk:
- Cheapest decision-changing evidence:
- Required revision:
- Experiment-design brief:

## Claims

## Evidence

Reference upstream evidence IDs; do not perform a new search.

## Limitations

## Handoff
```
