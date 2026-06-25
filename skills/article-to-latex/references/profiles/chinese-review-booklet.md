# Profile — chinese-review-booklet（中文期末复习手册 / 知识点速查）

逆向自一份手写的「期末复习页码定位」PDF 的视觉系统。用于把**中文复习资料**（知识点速查、
名词解释、简答题库、考点提纲）排成双色圆角卡片版式，而不是朴素的 Pandoc 黑白直转。

**何时用**：用户给的是中文复习/备考资料，且希望"好看 / 像那份毛概 / 卡片式 / 速查表 / 圆角彩框"。
触发词：复习手册、知识点速查、期末复习、名词解释题库、考点提纲、"做漂亮点"、"像 XX 那个 PDF"。
模板文件：[`assets/templates/chinese-review-booklet.tex`](../../assets/templates/chinese-review-booklet.tex)。
引擎：XeLaTeX / **Tectonic**（`scripts/compile_tectonic.sh foo.tex --preview`）。

## 设计令牌（design tokens）

| token | 值 | 用途 |
|---|---|---|
| `rvteal` | `#2F5C6E` | 主色：表头 / 提示框边 / 题号标签条底 / 页眉 |
| `rvrose` | `#C0504D` | 强调：定位框 / 正文外框 / 项目符号 / ★ |
| `rvtealbg` | `#EAF1F4` | 「使用说明」浅底 |
| `rvrosebg` | `#FBEEEE` | 「教材定位」底 / 表格斑马纹 |
| `rvgray` | `#6B6B6B` | 副标题 / 页码 |

- 类：`ctexart` 11pt，A4，`margin=2.4cm`；中文走 ctex 默认 fandol（Tectonic 自动下载），无需装字体。
- 字体升级（可选）：装了思源宋体可加 `\setCJKmainfont{Source Han Serif SC}` 更贴近原版。

## 版式构件（模板已定义的宏 / 环境）

| 构件 | 用法 | 对应原版元素 |
|---|---|---|
| 运行页眉 | `\renewcommand{\rvrunhead}{标题文字}` | 左青标题 + 右灰「第 N 页」+ 细线 |
| 主标题块 | `\rvtitle{主标题}{副标题}` | 居中大标题 + 灰副标题 |
| 居中小节标题 | `\rvsectitle{知识点速查表}` | 表格上方的居中粗标题 |
| 青提示框 | `\begin{rvnote}...\end{rvnote}` | 「使用说明」蓝圆角框 |
| 玫红定位框 | `\begin{rvlocator}...\end{rvlocator}` | 「教材定位：…」一行小框 |
| 玫红正文框 | `\begin{rvbody}...\end{rvbody}` | 题目正文外框（裹要点 bullet） |
| 题号标签条 | `\rvq{第 1 题}{标题}` | 青底白字圆角「第 N 题 …」 |
| 重点星标 | `\imp`（= ★ 重要）/ `\impstar`（仅星） | 红色 ★ 标记重点题 |

## 速查表写法

navy 表头 + 斑马纹：列宽用 `m{}`，表头行 `\rowcolor{rvteal}\rvth{...}`，
`\rowcolors{2}{rvrosebg}{white}` 起斑马纹。**`\PassOptionsToPackage{table}{xcolor}` 必须在
`tcolorbox` 之前**（模板已处理），否则 `\rowcolor` 不可用。

## 生成约定（skill 怎么产出）

1. 复制模板 → 用 `\rvtitle` / `\rvrunhead` 填课程名。
2. 速查表：每个知识点一行（题号 / 名称 / 页码…），重点行加 `\imp`。
3. 每个知识点：`\rvq{第 N 题}{名称}` → `rvlocator`（定位）→ `rvbody`（要点 itemize，bullet 自动玫红）。
4. ★ 必须用 `\imp`/`\ding{72}`（pifont），**不要**直接打 `★`——Latin 字体缺该字形会丢字。
5. 代码/ASCII 图：若内容含代码，正文框内用 `\texttt` 或 `listings`；流程/结构图优先 TikZ，**避免 ASCII 字符画**（原版无字符画，字符画是"丑"的主因之一）。
