---
name: idea-scan
description: Scan a current research landscape and produce an evidence-backed map of open problems, tensions, failed approaches, benchmark or measurement gaps, and opportunity signals. Use when starting idea discovery, refreshing a literature landscape, exploring a user-specified topic in any research domain, or creating the scan artifact consumed by the idea workflow. Do not use this skill to generate or rank concrete research proposals.
---

# Idea Scan

Map the research space before proposing solutions. Separate reported evidence from inference and preserve enough provenance for later novelty checking.

## Inputs

Collect or infer without blocking:

- User hint or target topic, if any.
- Resource envelope: time, compute, data access, implementation constraints.
- Preferred domain, subfield, application setting, or open exploration.
- Existing run directory or prior notes.

When no hint is provided, cover multiple subfields or problem framings instead of silently choosing one. If the topic is World Models, read `references/domain-profile-world-model.md` for a domain-specific scan map.

## Workflow

1. Create or reuse `research/idea-runs/<run-id>/`, where `<run-id>` is `idea-YYYYMMDD-<slug>`.
2. Search three lanes:
   - foundations and strongest baselines;
   - recent primary work, normally the latest 24 months;
   - limitations, negative evidence, benchmark failures, and unresolved disagreements.
3. Expand user terms into synonyms, mechanisms, measurement terms, adjacent fields, and contrary framings. Preserve the user's exact wording separately from the expansion.
4. Prefer primary papers, official repositories, benchmark pages, and authoritative project documentation. Record URLs, publication dates, search date, and queries.
5. Organize findings into problem clusters. Assign stable gap IDs such as `GAP-001`.
6. Distinguish:
   - `reported`: directly supported by a cited source;
   - `inferred`: reasoned from multiple observations;
   - `unknown`: evidence is insufficient.
7. End with opportunity signals, not finished ideas. Do not prescribe a method at this stage.

## Output contract

Write `10-scan.md` using `references/scan-template.md`. Use this common frontmatter:

```yaml
---
schema: idea-research/v1
suite_version: 1.0.0
run_id: idea-YYYYMMDD-slug
artifact_id: ART-SCAN-001
artifact_type: scan
stage: scan
producer: idea-scan
status: complete | partial | blocked | failed
created_at: ISO-8601 timestamp
input_refs:
  - 00-brief.md
warnings: []
blockers: []
---
```

Each opportunity signal must reference at least one `gap_id` and its supporting evidence. A lack of search results is not evidence that a gap is novel.
Always emit the complete envelope shown above, including for a one-off scan without an existing run.

## Quality gates

- Include more than one research family unless the user explicitly narrows scope.
- Include counterevidence and failed or weak approaches, not only successful papers.
- Keep source claims traceable to links.
- Mark the artifact `partial` if recent coverage, primary sources, or important subfields are missing.
- Mark it `blocked` if online research is required but unavailable; never invent citations.

## Handoff

Pass `10-scan.md`, `00-brief.md`, and all user constraints to `$idea-generate`. Write in the user's language unless requested otherwise.
