# Optional domain profile: World Models

Use this profile only for World Model research candidate generation.

## Candidate variation axes

Generate meaningful diversity by changing one or more of:

- state representation and temporal abstraction;
- deterministic versus stochastic dynamics;
- observation, action, reward, termination, or value prediction objectives;
- memory write, retention, retrieval, and reset mechanisms;
- action sensitivity and counterfactual prediction;
- planning interface, uncertainty use, or model exploitation defense;
- training curriculum, horizon, masking, or data mixture;
- evaluation target: perception, persistence, controllability, physics, or downstream control.

## Required causal specificity

For every candidate state:

1. the observed failure mode;
2. why the proposed mechanism should change that failure;
3. an outcome that distinguishes the mechanism from extra capacity, more data, or easier optimization;
4. a minimal probe using public data, environments, or checkpoints when required by the user.

Reject candidates that merely add a Transformer, memory module, diffusion loss, JEPA objective, or larger context without a mechanism-specific prediction.
