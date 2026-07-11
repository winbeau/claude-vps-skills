# Optional domain profile: World Models

Use these checks in addition to the generic review rubric.

## Mechanism and validity risks

- Is action information actually used, or can an action-shuffled model perform similarly?
- Are long-horizon gains measured open-loop, or only with teacher forcing?
- Does a memory mechanism improve persistence beyond a matched-capacity recurrent or attention baseline?
- Could the result come from extra parameters, compute, context, or data?
- Does perceptual quality translate to planning, control, state estimation, or another claimed utility?
- Are stochastic futures represented and evaluated appropriately?
- Are termination, reward, uncertainty, and out-of-distribution behavior considered when relevant?
- Could a planner exploit model errors?
- Does the benchmark test the claimed capability rather than short-horizon reconstruction?

## High-value negative results

Reward candidates whose failure would resolve a useful uncertainty, such as whether memory helps only observation prediction but not control, whether action conditioning is ignored, or whether a reported gain disappears under matched compute.
