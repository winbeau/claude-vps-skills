# Academic Rebuttal

`academic-rebuttal` 是一个两阶段学术 rebuttal skill：先诊断审稿意见和规划高价值实验，再根据作者提供的真实结果起草可核验的回复。它面向 NeurIPS、ICML、ACL、CVPR 等同行评审场景。

> 完整执行规则见 [`SKILL.md`](../../skills/academic-rebuttal/SKILL.md)。本 Skill 原样引入自 [TobiasLee/Rebuttal-Skill](https://github.com/TobiasLee/Rebuttal-Skill)；固定版本、作者和许可状态见 [`ATTRIBUTION.md`](../../skills/academic-rebuttal/ATTRIBUTION.md)。

## 工作流

1. **Stage 0：rebuttal / resubmission 判断**
   - 结合会议评分尺度、分数分布、审稿意见和剩余资源，判断为 `PROMISING`、`BORDERLINE / UNCERTAIN` 或 `LOW EXPECTED RETURN`。
2. **Stage 1：分诊与实验规划**
   - 把审稿意见拆成原子问题，区分表面评论和潜在决策性担忧。
   - 标注严重程度、共享程度、决策影响和解释置信度。
   - 将实验与分析排为 `P0`–`P3` 或 `DO NOT RUN`，避免无优先级的愿望清单。
3. **Stage 2：结果整合与回复撰写**
   - 只使用作者提供且可核验的实验、分析和论文位置。
   - 按 **Direct Answer → Evidence → Revision** 组织主要回应。
   - 对负面、混合或不充分结果收窄论断，不伪造或掩盖证据。

## 输出模式

- `TRIAGE_AND_EXPERIMENT_PLAN`
- `RESULT_INTEGRATION`
- `FULL_REBUTTAL`
- `RESUBMISSION_PLAN`
- `QUALITY_REVIEW`

## 最低输入

初次分诊最好提供：

- 论文摘要；
- 完整审稿意见、分数及置信度；
- 会议名称、评分尺度和已知 borderline；
- rebuttal 截止时间；
- 可用算力、数据和作者时间；
- 字数或字符限制，以及会议是否允许新增实验。

结果整合阶段还需提供实验协议、对照、指标、运行次数或随机种子、结果与不确定性，以及确定的论文修改位置。

## 示例

```text
使用 $academic-rebuttal 分诊下面的审稿意见，先判断 rebuttal 是否值得投入，
再给出 P0–P3 实验计划；不要在我提供结果前直接写最终回复。

会议和评分尺度：...
截止时间与资源：...
摘要：...
审稿意见、分数和置信度：...
```

## 证据约束

Skill 明确禁止编造实验数值、审稿人原话、引用、论文位置或完成状态。缺失信息必须用可见占位符标记；计划中的实验不得写成已经完成。
