# Novelty artifact template

Create one file per candidate at `30-novelty/<candidate_id>.md`.

```markdown
# Novelty Check: IDEA-001

## Decision Summary

- **candidate_id:** IDEA-001
- **idea_revision:** 1
- **verdict:** likely-novel | incremental | collision-risk | known | unresolved
- **confidence:** high | medium | low
- **differentiating core:**
- **strongest collision:** `SRC-...`
- **what would change the verdict:**

## Stage Output

### Claim decomposition

| claim_id | problem | mechanism | setting | claimed outcome |
|---|---|---|---|---|

### Search log

| query | source/index | searched_at | result notes |
|---|---|---|---|

### Nearest works

| source_id | problem overlap | mechanism overlap | setting overlap | evaluation overlap | remaining delta |
|---|---:|---:|---:|---:|---|

Use `none`, `low`, `medium`, or `high` for overlap columns and explain the rating below the table.

### Collision analysis

- Core claim already known:
- Component combination already known:
- Experimental setting already known:
- Remaining defensible distinction:
- Adjacent-field collision risk:

## Claims

List only claims needed for the novelty verdict.

## Evidence

For each source record title, authors/project, date, persistent ID, URL, access date, locator, relation to the candidate, and a concise paraphrase. Prefer primary sources.

## Limitations

- Inaccessible sources, terminology uncertainty, coverage gaps, and recency cutoff.

## Handoff

- Whether review may proceed.
- Exact revision question or rejection memo.
- Negative constraints for a regeneration round.
```

Never use absolute language such as “guaranteed novel.” `likely-novel` means no close collision was found within the documented coverage.
