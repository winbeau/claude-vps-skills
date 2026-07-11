# Scan artifact template

Use the suite-wide envelope and keep the following body sections.

```markdown
# Research Landscape

## Decision Summary

- Scope covered:
- Coverage cutoff:
- Strongest opportunity signals:
- Important missing coverage:

## Stage Output

### Search log

| query | lane | searched_at | notes |
|---|---|---|---|

### Problem clusters

#### GAP-001: Short problem name

- **Research family:**
- **Problem:**
- **Reported evidence:** `SRC-...`
- **Counterevidence or tension:**
- **Why unresolved:**
- **Affected settings:**
- **Resource relevance:**
- **Confidence:** high | medium | low

### Opportunity signals

#### OPP-001: Short signal

- **gap_ids:** `GAP-...`
- **Observation:**
- **Why now:**
- **Potentially measurable outcome:**
- **Evidence type:** reported | inferred | unknown
- **Evidence IDs:** `EVD-...`
- **Uncertainties:**

## Claims

| claim_id | statement | type | evidence_ids |
|---|---|---|---|
| CLM-SCAN-001 | ... | reported / inferred / unknown | EVD-001 |

## Evidence

### SRC-001

- **Type:** paper | official-code | benchmark | dataset | authoritative-doc
- **Title:**
- **Authors/project:**
- **Published:**
- **Persistent ID:** DOI/arXiv/other
- **URL:**
- **Accessed:**

### EVD-001

- **source_id:** `SRC-001`
- **claim_ids:** `CLM-SCAN-001`
- **relation:** supports | contradicts | overlaps | context
- **locator:** section, table, figure, page, or commit
- **finding:** concise paraphrase
- **confidence:** high | medium | low

## Limitations

- Missing sources, inaccessible papers, weak coverage, and unresolved terminology.

## Handoff

- Gap IDs and opportunity IDs suitable for candidate generation.
- User constraints that generation must preserve.
```

Do not include concrete proposed architectures in opportunity signals. That belongs to candidate generation.
