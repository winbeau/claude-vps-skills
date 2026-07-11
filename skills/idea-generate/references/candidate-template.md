# Candidate artifact template

Preserve the user's original hint and distinguish it from inferred constraints.

```markdown
# Research Candidates

## Decision Summary

- Candidates generated:
- Portfolio composition:
- User hint used: yes | no
- Provisional because scan is missing: yes | no

## Stage Output

### User hint interpretation

- **raw:** exact user wording
- **mode:** seed | constraint | preference | avoid | none
- **preserved requirements:**
- **interpretation:**
- **narrowing or relaxation:**

### IDEA-001: Candidate title

- **idea_revision:** 1
- **parent_id:** null or prior candidate ID
- **origin:** scan | user-hint | hybrid | regeneration
- **gap_ids:** `GAP-...`
- **opportunity_ids:** `OPP-...`
- **hint_alignment:** direct | partial | exploratory | not-applicable
- **Problem:**
- **Gap:**
- **Mechanism:**
- **Causal chain:** problem -> mechanism -> measurable effect
- **Hypothesis:**
- **Falsifiable predictions:**
- **Observable outcome:**
- **Novelty hypothesis:** unchecked claim to test online
- **Expected nearest prior-work or comparator family:**
- **Minimum viable probe:**
- **Kill criterion:**
- **Estimated resources:**
- **Dependencies:**
- **Key assumptions:**
- **Likely failure mode:**
- **Negative-result value:**
- **candidate_status:** proposed

## Claims

List generated hypotheses as `inference`; do not present them as established evidence.

## Evidence

Map each candidate to the scan evidence that motivated it. Do not add unsupported novelty evidence here.

## Limitations

- Missing scan coverage, uncertain assumptions, and resource estimates.

## Handoff

- Active candidate IDs for online novelty checking.
- Rejection constraints that must remain active in later regeneration rounds.
```

Candidate IDs are immutable. Minor clarification increments `idea_revision`; a materially changed problem, mechanism, claim, or setting receives a new ID and records `parent_id`.
