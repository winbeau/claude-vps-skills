# Optional domain profile: World Models

Select only checks relevant to the candidate.

## Discriminating controls

- teacher-forced versus open-loop rollout;
- same initial state with different actions;
- action-shuffled, action-removed, or counterfactual-action control;
- memory reset, detached memory, short-memory, or matched-capacity memory control;
- parameter-, data-, context-, and compute-matched baselines;
- short versus long horizon degradation;
- observation leaves and re-enters view to test state persistence;
- reconstruction or perceptual quality versus planning/control performance;
- uncertainty calibration and model-exploitation stress tests;
- reward and termination prediction where they affect downstream decisions.

## Metrics

Choose metrics that test the claim. Depending on the idea, combine:

- open-loop prediction and horizon-conditioned degradation;
- action sensitivity or counterfactual consistency;
- state/object persistence;
- downstream planning return, success rate, or sample efficiency;
- uncertainty calibration and failure detection;
- latency, memory, parameters, and compute budget.

Image or reconstruction quality alone is rarely sufficient evidence that a world model is useful.
