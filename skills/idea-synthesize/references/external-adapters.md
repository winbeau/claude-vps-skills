# Optional external skill adapters

The `idea-*` suite is an independent, domain-agnostic workflow. External skills may supply stage work, but they are optional dependencies and must return artifacts that conform to `workflow-contract.md`.

## Adapter map

| idea stage | compatible external capability | normalization requirement |
|---|---|---|
| `idea-scan` | ARIS `research-lit`; Academic Research Skills `three-way-scan` or deep research | Convert sources, claims, gaps, counterevidence, and queries into `10-scan.md`; do not emit final ideas |
| `idea-generate` | ARIS `idea-discovery`; other hypothesis-generation skills | Preserve the exact user hint and create stable candidate cards; remove unsupported novelty claims |
| `idea-check-novelty` | ARIS `novelty-check`; Academic Research Skills `fact-check`; live scholarly search tools | Record current queries and primary-source evidence in one artifact per candidate |
| `idea-review` | Academic Research Skills methodology or paper reviewer; `ml-review` for ML topics | Apply the suite hard gates and rubric; do not redo novelty search inside review |
| `idea-design-experiment` | world-model-lab `research-cycle` or `run-experiment`; domain experiment-planning skills | Produce the staged E0/E1/E2 design and resource-bounded kill criteria; do not execute unless separately authorized |

## Rules

- Use at most one full-workflow orchestrator. Do not run ARIS auto-pipeline and `idea-synthesize` as competing controllers.
- External stage output never bypasses the suite's IDs, revision checks, status semantics, or hard gates.
- Preserve source provenance and user constraints during normalization.
- A stale literature report cannot satisfy live novelty checking.
- Domain reviewers may add criteria, but cannot silently alter upstream verdicts.
- If an external skill changes a candidate's problem, mechanism, main claim, or setting, create a new candidate ID or revision and invalidate downstream artifacts.
