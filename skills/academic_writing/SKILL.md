---
name: academic_writing
description: >
  Audit and rewrite academic prose to kill AI-slop (canned vocabulary, em-dash
  abuse, forced-contrast filler) AND enforce logic closure (Claim -> Evidence/
  Mechanism -> Impact/Limitation, no qualitative filler, quantitative placeholders
  required). Domain-aware for CS / deep learning (Transformer, KV cache, attention,
  quantization): replaces grand narrative with concrete physical/mathematical
  actions. Trigger when the user asks to polish / 润色 / 改写 / 降AI味 / 学术化
  a paper, abstract, intro, related work, method, or results paragraph; or says
  "make this sound less like AI", "tighten the argument", "academic rewrite".
  Fuses three open-source skills: conorbronsdon/avoid-ai-writing (lexicon+punct),
  WantongC/journal-adapt-writing-skill (journal register+priority resolution),
  Imbad0202/academic-research-skills (CER/TEEL logic chains).
---

# academic_writing — Anti-Slop · Logic-Closure · Domain-Semantic

> 三个硬门禁(GATE)是无条件的。任何输出在交付前必须依次通过 G1→G2→G3,
> 并在结尾打印 `<self-check>` 通过表。门禁不是建议,是 PASS/FAIL。

<principles>
1. 你是副驾,不是机长(AI is copilot, not pilot)。**绝不新增事实/引用/数字/结论**;
   缺数据就插占位符 `[X]` 并标 `[MATERIAL GAP]`,不要编。
2. 改写不改技术内容:公式、变量名、citation key、数值结果一律逐字保留(verbatim)。
3. 结构规整性是 AI 检测的**头号信号**(强于词汇)。只换词不改节奏,仍读作 AI。
4. 过度打磨也是 AI 味:把所有不规则都磨平,反而推向 AI 统计画像。保留必要的人味。
</principles>

<workflow>
模式 `mode`(默认 rewrite):
- `detect` — 只标问题,不改写。按 P0/P1/P2 分级列出+引用原文。
- `rewrite` — 两遍改写(改写 + 一次纠正回扫,N=2;第三遍收益递减,停)。
- `edit`   — 最小原地修改,逐处 before→after,并说明哪些故意不动。

每次执行顺序:① 跑 G1 词汇/标点扫描 → ② 跑 G2 逻辑闭环压测 → ③ 跑 G3 领域语义检查
→ ④ 改写 → ⑤ 第二遍回扫(只 rewrite 模式)→ ⑥ 打印 self-check 表。
</workflow>

---

## GATE 1 — Anti-Slop 词汇与标点门禁 〔来源:avoid-ai-writing〕

<gate id="G1" verdict="PASS|FAIL">

<lexicon tiers="3">
三档判定(形态变体一并命中:-ly/-ing/复数/比较级/动词变位):

**Tier 1 — 见即杀(always replace)。** AI 文本中出现频率为人类 5–20×:
`delve / delve into`, `leverage` (动词), `tapestry`, `realm`, `paradigm`,
`pivotal`, `moreover`, `furthermore`, `additionally`, `it's worth noting / worth noting`,
`underscore(s)`, `meticulous(ly)`, `seamless(ly)`, `robust`, `comprehensive`,
`cutting-edge`, `harness` (动词), `embark`, `beacon`, `testament to`, `game-changer`,
`utilize`, `showcase`, `deep dive / dive into`, `unpack`, `holistic`, `actionable`,
`impactful`, `synergy`, `foster`, `elevate`, `unleash`, `streamline`, `empower`,
`bolster`, `spearhead`, `resonate`, `revolutionize`, `facilitate`, `underpin`,
`crucial`, `multifaceted`, `myriad`, `plethora`, `catalyze`, `cornerstone`,
`paramount`, `transformative`, `nuanced`, `at its core`, `in order to`,
`due to the fact that`, `serves as`, `boasts`.

**Tier 2 — 成簇才标(同段出现 ≥2 个即 AI 信号):**
`landscape`(隐喻), `ecosystem`(隐喻), `vibrant`, `thriving`, `intricate`,
`ever-evolving`, `interplay`, `navigate`, `cultivate`, `illuminate`, `juxtapose`,
`burgeoning`, `nascent`, `overarching`, `embrace`(隐喻), `symphony`(隐喻)。

**Tier 3 — 按密度标(占总词数 ~3%+ 或同篇 ≥3 个不同短语即强信号):**
`significant(ly)`, `innovative`, `effective(ly)`, `dynamic`, `scalable`,
`compelling`, `unprecedented`, `remarkable`, `sophisticated`, `instrumental`,
`world-class / state-of-the-art / best-in-class`, `notably`, `interestingly`,
`importantly`, `undoubtedly`, `fundamentally`。
> 密度规则示例:2000 字里一个 `notably` 没问题;500 字里三个就是 AI 堆叠。
</lexicon>

<banned-openers-closers>
开头/过渡/结尾罐头句一律删或重写:
`In this paper/article, we will explore...`, `In today's ... / In an era where`,
`Let's dive in / explore / take a look / break this down`,
`It is important to note that`, `When it comes to`, `At the end of the day`,
`In conclusion / In summary / To summarize`,
`Experts believe / Studies show / Research suggests`(无具体出处的模糊归因),
`Future research should explore...`(无具体方向),
`Taken together, these findings suggest...`, `Our results highlight the importance of...`,
`To the best of our knowledge, this is the first...`(除非给出你做过的检索),
`Our method is simple yet effective`, `Extensive experiments demonstrate...`,
`As shown in Figure X, our method clearly outperforms...`.
</banned-openers-closers>

<punctuation hard-gates="true">
- **破折号(em-dash `—` 与双连字符 `--`):目标 0,硬上限 1/1000 字。** 含标题与小标题。
  替换为逗号、句号、括号,或拆成两句。〔每千字限 1〕
- **Forced-contrast 强行对比句式:硬上限 1/1000 字。** 拦截模板:
  `It's not X — it's Y` / `This isn't about X, it's about Y` /
  `While X is impressive, Y remains a challenge` / `Although X has made strides, Y is still open`.
  修法:要么把对比落到**具体可证伪**的内容(点名 X 强在哪、Y 的真实难点),要么选一边论证。
- **Hedge 叠用:禁。** `could potentially` / `may eventually` / `might ultimately` —
  modal 与 hedge 副词只能留一个。
- **列表标签用冒号不用句号:** `**Intros:**`(人) 而非 `**Intros.**`(AI);冒号后小写续写。
- **小标题用句子式大小写(sentence case)**,不要 Title Case;仅正文主标题可考虑标题式。
- **加粗克制:** 每大节最多一个加粗短语或零个;真重要就重构句子让它打头,而非加粗。
- **避免强迫性三连(rule of three):** `形容词, 形容词, and 形容词` 全篇 ≤1 次。
</punctuation>

<structure-tests note="结构信号 > 词汇信号,必须过">
- **段落重排免疫测试:** 任意交换两个正文段而文章不崩 ⇒ 你写的是要点清单不是论证。
  修法是结构性的:建立 through-line,每段依赖前一段。
- **跑步机/低信息密度测试:** 每段自问"这里有什么**新**事实/主张/转折?"。
  若删去 40–60% 不丢信息,就是跑步机式注水。每段只留一个新点并打头,砍掉清嗓子。
- **句长方差:** 多数句子落在 15–25 词 ⇒ 机器感。混入 3–8 词短句与 20+ 词长句。
- **何时整段重写而非补丁:** Tier1 命中 ≥5 + 不同模式类别 ≥3 + 句/段长高度均匀 ⇒
  结构本身就是 AI 生成,逐句换词无效。用一句话讲清核心点,再重建。
</structure-tests>

<severity>
P0 见即修(信誉杀手): cutoff 免责声明、聊天机器人残留(`Great question!`/`I hope this helps!`)、
无出处模糊归因、对日常事件夸大其辞、未填占位符 `[Your Name]`、引用标记泄漏(`citeturn0search0`)、
AI URL 参数(`utm_source=chatgpt.com`)。
P1 发表前修: Tier1 命中、模板句、`Let's` 开场、近义词轮换、破折号 >1/1000、generic future closer、hedge 叠用。
P2 有空再修: 泛泛结论、强迫三连、段长均匀、copula 回避(`serves as`→`is`)、过渡词(Moreover/Furthermore)。
</severity>

<verdict-rule>G1 FAIL 当且仅当:任一 Tier1 残留 / 破折号 >1每千字 / forced-contrast >1每千字 / P0 未清。</verdict-rule>
</gate>

---

## GATE 2 — 逻辑闭环压测 〔来源:academic-research-skills CER + journal-adapt〕

<gate id="G2" verdict="PASS|FAIL">

<core-chain>
每个实质性主张必须走完链条,缺一环即 FAIL:

  **CLAIM → EVIDENCE/MECHANISM → IMPACT/LIMITATION**
  (主张 → 证据/机理 → 影响/局限)

- **Claim:** 一句可证伪的断言,放段首。
- **Evidence/Mechanism:** 数据(带引用)**或**机理桥(为什么证据支撑主张)。
  ML 场景:`Smith (2024) found 23% reduction in variance` 这种**具体数字 + 出处**。
- **Impact/Limitation:** 这意味着什么 + 它**没有**证明什么(边界要说出口)。
</core-chain>

<no-qualitative-filler hard="true">
**严禁无数据/无机理支撑的定性夸赞(qualitative filler)。** 拦截并强制改写:
- `highly efficient and scalable`(无数字) → 必须给出 `[X]× throughput` / `[Y] ms latency`。
- `clearly outperforms` / `excellent performance` / `significantly better` → 给 `+[Δ] points on [benchmark]`。
- `results showed improvement` → 给具体量:`ICC rose from [a] to [b] (p = [.xxx], d = [x.xx])`。

**缺数据时不许糊弄:插入定量占位符,不要写定性话术。** 标准占位符:
`[X]% reduction` · `[N]× speedup` · `[Y]ms → [Z]ms latency` · `[A] GB → [B] GB` ·
`[k] tokens/s` · `p = [.xxx]` · `d = [x.xx]` · `95% CI [lo, hi]`,
并在该处加 `[MATERIAL GAP: 需补 <什么数据>]`。
</no-qualitative-filler>

<paragraph-template>
- 一段一 claim,先 claim 后证据(B);TEEL 结构 ≥80%:
  **T**opic(主句)→ **E**vidence(数据/引用)→ **E**xplanation(解释为何支撑)→ **L**ink(接下一节)。
- 结果段:先报结果,再讲机理/解释(lead with the result, then the mechanism)。
- "没证明的别断言"(do not assert what you have not shown)。
</paragraph-template>

<argument-strength score="0-100">
给关键论证打分,<50 触发停笔补证据:
- Compelling 90–100:≥3 条独立证据线收敛,主要反论已被反驳。
- Strong 70–89:≥2 条证据线,反论已被承认。
- Adequate 50–69:≥1 条证据线,反论被提及。
- Weak <50:不足一条完整证据线 / 单一来源依赖 ⇒ **停,补证据再写**。
</argument-strength>

<fallacy-halt>
检出下列即停笔报警(8 类):循环论证、诉诸权威而无数据、以偏概全、非黑即白、
相关当因果、地域过度泛化、术语前后不一致、反论强于本文立场。同时出现 ≥2 个弱论证指标 ⇒ 草稿暂停。
</fallacy-halt>

<gap-and-contribution>
- Gap 要精确:不是"this area is understudied",而是"no prior work addresses X under condition Y"。
- 用 CARS(Create A Research Space)开篇:**先讲 gap,别先堆背景**,否则易 desk-reject。
- 贡献要能**一句话说清 delta**:说不清,要么贡献弱,要么没表达清楚。ML 贡献 ≤3 条,写成事实
  (`We propose X that achieves Y`)不是意图(`We aim to address Z`)。
</gap-and-contribution>

<verdict-rule>G2 FAIL 当且仅当:存在断链 claim / 出现 qualitative filler 未配数字或占位符 / 关键论证 <50 分 / 触发任一 fallacy。</verdict-rule>
</gate>

---

## GATE 3 — 领域特异性语义感知(CS / 深度学习)〔本技能在 A/B/C 基础上的领域扩展〕

<gate id="G3" verdict="PASS|FAIL" domain="cs-deep-learning">

<principle>
**用具体的物理/数学动作,替代抽象宏大叙事。** 凡涉及 Transformer 架构、注意力、
KV 缓存、量化、并行、推理优化,必须落到:被改变的**资源**(显存/带宽/FLOPs/延迟)、
**量级**(big-O、bytes/token、tokens/s)、**机制**(为什么这样就更快/更省)。
</principle>

<rewrite-table>
| 抽象叙事(禁) | 具体物理/数学动作(改成) |
|---|---|
| "revolutionize attention" | "把注意力显存从 O(n²) 降到 O(n),用 blockwise softmax(FlashAttention)" |
| "leverage the KV cache" | "复用已缓存的 K/V 投影,免去每个 decode step 重算,降低 per-token FLOPs [X]%" |
| "a powerful Transformer" | "decoder-only Transformer,[L] 层 / [H] 头 / d_model=[d]" |
| "make it much faster" | "缓解内存带宽瓶颈:把 KV cache 存为 fp8,bytes-moved-per-token 减半" |
| "efficient and scalable" | "在 [GPU] 上 throughput [k] tokens/s,batch=[b] 时显存 [A]→[B] GB" |
| "optimize memory usage" | "降低 KV cache 占用:size = 2·L·H·d_head·seq·batch·bytes,fp16→int8 减半" |
| "improve performance" | 区分:throughput(tokens/s)/ latency(ms/token)/ 准确率(+[Δ] on [benchmark]),点名是哪个 |
</rewrite-table>

<concrete-vocabulary>
鼓励使用的具体动作/概念(取代空话):
- **瓶颈定性:** memory-bandwidth bound vs compute bound(roofline);arithmetic intensity = FLOPs/byte。
- **KV cache:** 占用公式见上;PagedAttention 减碎片;MQA/GQA 减 KV 头数;量化 KV 减 bytes/token。
- **注意力:** O(n²)→O(n) 显存(FlashAttention 不物化 n×n 矩阵);稀疏/滑窗改变计算图。
- **量化:** fp16→int8 减半搬运字节;在带宽 bound 场景直接换成正比加速。
- **并行:** tensor / pipeline / sequence parallel —— 点明切的是哪一维、通信代价是什么。
- **指标三件套:** 延迟(ms/token)、吞吐(tokens/s)、显存(GB),改了哪个说哪个,别笼统说 "performance"。
</concrete-vocabulary>

<verdict-rule>G3 FAIL 当且仅当:技术句仍停留在抽象叙事(没点明资源/量级/机制),或把 latency/throughput/accuracy 混为一谈的笼统 "performance"。</verdict-rule>
</gate>

---

## 优先级冲突解决 〔来源:journal-adapt P1–P5〕

冲突时按优先级裁决,P1 永远赢:
- **P1 硬保留:** 事实、引用、公式、记号、数值结果(逐字)。
- **P2 目标期刊语料模式:** 若用户给了 5–8 篇目标期刊样本,其观察到的语体/结构优先于通用规则。
- **P3 次级语料 / 用户实验室范文。**
- **P4 本技能静态默认规则(G1–G3)。**
- **P5 清理规则(删罐头句等)。**
> P2 通常压过 P4:目标期刊若惯用某结构,服从它,而非本技能默认。

## 学科基线(按领域取用)
- **ML/CV/NLP:** 摘要须含 ≥1 个具体指标(`achieves 87.3% on [benchmark]`);
  禁 `novel/innovative/state-of-the-art` 自夸;贡献 ≤3 条且写成事实;架构图 1 张;伪码逐行编号。
- **CS/Engineering:** 贡献用具体动词(design/build/implement/evaluate,非 explore/investigate);
  报均值±标准差(多次运行);报延迟须带硬件配置;算法给时间/空间复杂度。
- **统计报告(APA 7):** 效应量必报;精确 p 值(`p = .032` 不是 `p < .05`);
  上限为 1 的统计量不带前导零(`.032`),可超 1 的带(`0.75`);M/SD/t/F/p/r/d 斜体。

---

## 输出契约(output contract)

<output mode="rewrite">
1. **Issues found** — 按 G1/G2/G3 + P0/P1/P2 列出,每条引用原文。
2. **Rewritten** — 完整干净版本。
3. **What changed** — 主要改动摘要(指明触发了哪个 GATE)。
4. **Second-pass audit** — 回扫改写稿,清残留并报告或确认 clean。
5. **`<self-check>`** — 见下,三门禁 PASS/FAIL 表 + 关键计数。
</output>

<self-check template="true">
```
G1 lexicon/punct : PASS|FAIL  | em-dash [n]/1000w  | forced-contrast [n]/1000w | Tier1 hits [n]
G2 logic-closure : PASS|FAIL  | broken chains [n]  | qualitative-filler [n]    | weak-arg(<50) [n]
G3 domain-semantic: PASS|FAIL | abstract-narrative残留 [n] | 占位符待补 [MATERIAL GAP] [n]
verdict          : SHIP | REWORK
```
</self-check>

---

## 示例(before → after)

<example type="ml-results">
BEFORE: "Our novel method is highly efficient and clearly outperforms baselines, leveraging
the KV cache to revolutionize inference."
AFTER: "Reusing cached K/V projections removes redundant recomputation each decode step,
cutting per-token FLOPs by [X]% and raising throughput from [a] to [b] tokens/s on [GPU]
(batch=[b]). [MATERIAL GAP: fill X, a, b from Table 2.]"
触发:G1(novel/efficient/leverage/revolutionize)、G2(filler→占位符)、G3(抽象→具体机制)。
</example>

<example type="intro-gap">
BEFORE: "Moreover, this area is understudied, and our pivotal work delves into a comprehensive
framework — a true game-changer for the field."
AFTER: "No prior work addresses long-context KV-cache eviction under fixed [B] GB memory.
We give an eviction rule that bounds attention error to [ε] while holding cache at [B] GB."
触发:G1(moreover/pivotal/comprehensive/破折号/game-changer)、G2(模糊 gap→精确 gap)。
</example>
