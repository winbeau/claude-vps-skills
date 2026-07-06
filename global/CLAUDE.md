# ~/.claude/CLAUDE.md — 全局提示词

本文件对所有 session 生效（项目级 CLAUDE.md 优先级更高，会覆盖冲突条目）。

## Workflow 模型选择与 Token 控制

> **背景**：Workflow 子 agent 默认继承父 session 模型，但可以 `{model: "haiku"|"sonnet"|"opus"}` 逐 agent 覆盖。**Opus 计费约 Sonnet 5×、Haiku 30×，滥用会清空周额度。**

### 三档模型分配

| 任务类型 | 模型 | 典型例子 |
|---|---|---|
| 检索 / 提取 / 分类 / 格式转换 / 简单总结 | `haiku` | 文件列出、字段抽取、grep 结果整理、标题/年份提取 |
| 推理摘要 / 草稿生成 / 文档综合 / 中等分析 | `sonnet`（默认） | 方向调研、related-work 摘要、方法草稿、reviewer 模拟 |
| 多步推理 / 代码生成 / 对抗式核实 / 关键判断 | `opus` | 代码实现与 debug、scoop check、linchpin 实验设计、最终综合 |

### Token 节省规则

1. **`pipeline()` 优先**：无阻塞，wall-clock = 最慢单链；`parallel()` 是 barrier，只在真正需要全量结果时用。
2. **两段式流水线**：haiku 做 finder/extractor 初筛 → 候选再送 sonnet/opus 深分析，比全量 opus 省 ~80%。
3. **`schema` 最小化**：每个 `agent()` 指定 schema，字段只留下游需要的，避免 free-text 膨胀。
4. **数量上限**：finder agent ≤ 8（通常 4–6）；verifier ≤ 3 票（majority-vote 足够）。
5. **`budget` 守门**：长循环必须有 `budget.total && budget.remaining() > N` 守卫。
6. **截断必须 `log()`**：top-N 抽样或限量 finder，必须 log 说明，不能让结果看起来像全覆盖。
7. **避免重复调研**：同 session 内已有调研结果（task output / 落盘文件）先读，不要重跑 workflow。

### 写脚本检查清单

- [ ] 每个 `agent()` 都显式标注 `model`，或明确知道继承 sonnet 合适？
- [ ] 有无不必要的 `parallel()`（能改 `pipeline()` 的改掉）？
- [ ] schema 字段数最小化？
- [ ] finder/verifier 数量有上限，或循环有 `budget` 守门？
- [ ] 脚本写好后先展示给用户确认，再 launch `Workflow()`？
