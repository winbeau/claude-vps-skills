# academic_writing

学术散文审计与改写 skill：**杀 AI 味** + **强制逻辑闭环** + **领域语义具体化**。面向 CS / 深度学习（Transformer、KV cache、attention、量化）等方向，把"宏大叙事"换成具体的物理/数学动作。

> 完整指令与判定规则见 [`SKILL.md`](./SKILL.md)。本文件是给人看的概览。

## 它做什么

交付前无条件依次过 **3 道硬门禁（PASS/FAIL，不是建议）**，结尾打印 `<self-check>` 表：

| 门禁 | 内容 | 来源 |
|---|---|---|
| **G1 — Anti-Slop** | 三档词汇黑名单（`delve / leverage / pivotal / robust / underscore`…）+ em-dash 滥用 + 强行对比填充；结构规整性也被当作头号 AI 信号处理 | conorbronsdon/avoid-ai-writing |
| **G2 — 逻辑闭环** | 每个论断走 Claim → Evidence/Mechanism → Impact/Limitation（CER / TEEL）；禁定性填充，缺数据插 `[X]` 占位并标 `[MATERIAL GAP]` | Imbad0202/academic-research-skills + WantongC/journal-adapt |
| **G3 — 领域语义** | 把 "a powerful Transformer" 这类空话替换成 "decoder-only Transformer, [L] 层 / [H] 头 / d_model=[d]" 等可核实的具体描述 | 本 skill 的领域扩展 |

融合三个开源 skill 的优先级冲突解决（journal-adapt P1–P5）+ 学科基线。

## 三种模式（`mode`，默认 rewrite）

- `detect` — 只标问题不改写，按 P0/P1/P2 分级 + 引原文。
- `rewrite` — 两遍改写（改写 + 一次纠正回扫，N=2）。
- `edit` — 最小原地修改，逐处 before→after，并说明哪些故意不动。

## 铁律

- **副驾不是机长**：绝不新增事实/引用/数字/结论；缺数据插占位符，不编。
- 公式、变量名、citation key、数值结果一律**逐字保留**。
- 不过度打磨——把所有不规则磨平反而更像 AI，保留必要人味。

## 触发

润色 / 改写 / 降AI味 / 学术化 一段论文（abstract / intro / related work / method / results），或 "make this sound less like AI" / "tighten the argument" / "academic rewrite"。

## 文件

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 全部门禁规则、词表、输出契约、before→after 示例 |
