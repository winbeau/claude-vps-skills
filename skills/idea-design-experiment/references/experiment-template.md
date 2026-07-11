# Experiment artifact template

Create one file per advanced candidate at `50-experiments/<candidate_id>.md`.

```markdown
# Experiment Plan: IDEA-001

## Decision Summary

- **candidate_id:** IDEA-001
- **idea_revision:** 1
- **experiment_status:** experiment-ready | experiment-blocked
- **primary_experiment_id:** EXP-001-E1
- **estimated E1 cost:**
- **pass threshold:**
- **kill criterion:**

## Stage Output

### Claim under test

- **claim_id:**
- **causal hypothesis:**
- **null hypothesis:**
- **competing explanation:**

### E0 smoke test

- **experiment_id:** EXP-001-E0
- **purpose:** procedure, instrument, pipeline, or metric validation
- **duration/resources:**
- **checks:**
- **stop conditions:**

### E1 minimum viable experiment

- **experiment_id:** EXP-001-E1
- **data/sample/population/environment:**
- **available assets, code, equipment, records, or checkpoints:**
- **independent variables:**
- **held-constant variables:**
- **primary baseline/comparator:**
- **matched control or comparison:**
- **additional controls:**
- **primary metric:**
- **secondary diagnostics:**
- **evaluation horizon/follow-up period:**
- **replicates, seeds, sample size, or uncertainty plan:**
- **success threshold:**
- **failure threshold:**
- **kill criterion:**
- **wall-time/resource/storage/API/participant cost estimate:**

### Ablations and confounders

| test | confound isolated | expected result if mechanism is real |
|---|---|---|

### E2 confirmation, conditional on E1

- Replication, broader settings or populations, stronger comparators, sensitivity analyses, or stress tests.

### Outcome interpretation

| outcome | interpretation | next decision |
|---|---|---|
| positive | | advance / revise |
| null | | revise / reject |
| contradictory | | reject / investigate |

## Claims

## Evidence

Reference upstream claims, novelty evidence, established protocols, datasets, instruments, and implementation sources as applicable.

## Limitations

## Handoff

- Exact first implementation or study-preparation task only if the user later requests execution.
```

Select domain-appropriate negative controls, matched comparators, sensitivity analyses, and robustness checks. The primary outcome must test the claim rather than a convenient proxy.
