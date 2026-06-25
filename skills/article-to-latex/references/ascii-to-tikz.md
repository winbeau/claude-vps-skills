# Reference — ASCII 框图 → 精美 TikZ（批量用 workflow）

很多 Markdown/Pandoc 转出来的中文技术文档里有 ASCII 字符画（`┌─┐│└┘═║╔╝▲→` 画的框图）。它们
**又丑又脆**：等宽 CJK 对不齐、box-drawing 字符常缺字渲染成 `□`/`�`、复制易错位。遇到这类图，
**转成 TikZ**。

## 何时触发

文档里出现 `\begin{verbatim}` 块且含 box-drawing 字符（`─│┌┐└┘═║╔╗╚╝▲▼→`）；或用户说
"这些 ASCII 图丑/容易出错/用精美 tex 排版一下"。

## 标准流程（中等规模 N≥4 张图 → 用 workflow 并行）

1. **抽取**：脚本扫出所有含 box-drawing 字符的 verbatim 块，记 `(idx, start, end, 图题)`。
2. **共享样式**：`\input` [`assets/tikz-style-cn-review.tex`](../assets/tikz-style-cn-review.tex)（青/玫红
   节点样式 rvmod/rvbase/rvaccent/rvann/rvarr + `\rvcap`）。正文 preamble 也要加同一份，拼回后才编得过。
3. **并行转换（workflow）**：一张图一个 agent。每个 agent：读源码行段 → 用**显式坐标**画 TikZ →
   **必须渲染 PNG 并 Read 图片自检** → 迭代到无重叠 → 回传片段。schema：`{idx, tikz, compiled, visualok, note}`。
4. **拼回**：把每个 verbatim 块整段替换成对应 TikZ。**从下往上（start 降序）替换**，避免行号漂移。
5. **全量编译 + 逐图目检**：人工再扫一遍每张图。

## 血泪教训（务必遵守）

- **`compiled=true` ≠ 好看**。第一轮只让 agent"编译通过"，结果用 `fit`/`label` 做密集嵌套的图
  全部**框塌陷/批注重叠**却照样编译通过。**agent 必须真的渲染 PNG → 用 Read 读图 → 肉眼确认无
  重叠/塌陷/溢出**，再迭代。把这一步写进 agent prompt 并要求返回 `visualok`（读过图才可 true）。
- **密集/嵌套布局用显式坐标 `(x,y)`，别用 `fit`+多个 `label`**——后者正是重叠的根因。
- **拼回前重新抽取行边界**：抽取之后若又改过 preamble（哪怕加几行），所有 verbatim 行号都会
  整体漂移，旧 `start/end` 会错位。拼回前在当前文件上重抽一次。
- **缺字**：`\xeCJKDeclareCharClass{CJK}{"2460->"2469, "2264->"2265, "2605->"2606}` 让 ①–⑩/≤≥/★
  走 CJK(fandol) 字体；范围别开太大（整段 `"2200->"22FF` 会把 `− negative`/`∗`/`⊇` 也误送 fandol 而丢字）。
  **绝不直接打 `★ ✓ ✗ ✅ ❌`**（Latin/mono 缺字）——要星用 `\ding{72}`(pifont) 或 `$\star$`。

## 模型与成本

- 转换/修复涉及代码生成 + 视觉判断，用 `opus`（sonnet 第一轮易出重叠）。N 张图并行，token 与质量换。
- 小图、结构简单可先 sonnet 出草稿、再 opus 修问题图（两段式）。

> 实战记录：一份 77pp 的 Java 复习册 10 张 ASCII 图，sonnet 首轮转换 6 张直接好、4 张（用 fit/label 的）
> 重叠；opus 二轮带视觉自检全部修好。配套版式见 [`profiles/chinese-review-booklet.md`](profiles/chinese-review-booklet.md)。
