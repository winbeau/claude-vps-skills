# xju-docx — 新疆大学论文 docx 规范化工具链

按《新疆大学本科毕业论文（设计）规范及格式要求》**生成 / 规范化 / 校验 / 润色**论文与软工课程文档 docx（学年论文、毕业论文、开题报告、需求/概设/详设/测试文档等）。

五件套（全程**免 sudo、免 LibreOffice**）：

| 组件 | 作用 |
|---|---|
| `scripts/build_framework.py` | 框架生成器：封面 + 文档修改记录 + 目录域 + GB8567 九章骨架，每节带【待填】写作指引 |
| `scripts/extract_doc.py` | Word97 二进制 `.doc` 文本提取器（FIB→piece table，仅依赖 olefile） |
| `scripts/xju_format.py` | python-docx 排版库：规范字号体系、三级标题样式、分节页码（封面无→前置罗马→正文阿拉伯）、页眉 0.5 磅横线、三线表 |
| `scripts/validate_docx.py` | 格式机检器：25+ 项检查；`--json` 结构化输出 / `--fix` 自动修复机械项 / `--content` 占位符残留门禁 |
| `scripts/check_docx_package.py` | OOXML 包健康检查：ZIP/XML/关系目标/外链/临时路径与元数据破坏 |

规范条款速查在 [`references/spec-digest.md`](../../skills/xju-docx/references/spec-digest.md)（页面/页码/标题/图表公式/GB.T 7714 引用/文字细则）。

## 配置方法

### 1. 依赖（用户级 pip，无需 sudo）

```bash
python3 -m pip install --user python-docx olefile
```

### 2. 安装 skill 到 Claude Code

从本仓拷贝（独立快照）：

```bash
cp -r self-skills/skills/xju-docx ~/.claude/skills/
```

或从 canonical 源软链安装（推荐，跟随上游更新）：

```bash
git clone https://github.com/XjuSelab/xju-feiyue.git
./xju-feiyue/skills/install.sh --global   # 软链到 ~/.claude/skills/
```

### 3. 验证安装

```bash
python3 ~/.claude/skills/xju-docx/scripts/build_framework.py -o /tmp/t.docx --name 测试
python3 ~/.claude/skills/xju-docx/scripts/validate_docx.py /tmp/t.docx --framework   # 应全绿、exit 0
```

之后在 Claude Code 里说「生成论文框架 / 按学校格式排版 / 论文格式对不对 / 这篇 .doc 转成 docx」等即自动触发，或直接 `/xju-docx`。

## 快速上手

```bash
S=~/.claude/skills/xju-docx/scripts
python3 $S/build_framework.py -o 论文.docx --name 姓名 --title 题目    # 生成规范框架
python3 $S/extract_doc.py 老文件.doc > 全文.txt                        # 读老 .doc（免 LibreOffice）
python3 $S/validate_docx.py 论文.docx --framework                     # 机检
python3 $S/validate_docx.py 论文.docx --fix --framework               # 自动修复机械项
python3 $S/validate_docx.py 论文.docx --content                       # 定稿前：扫【待填】残留
python3 $S/check_docx_package.py 论文.docx                            # Word 修复前后检查 OOXML 包
```

## 同步说明

canonical 源在 [`XjuSelab/xju-feiyue`](https://github.com/XjuSelab/xju-feiyue) 的 `skills/xju-docx/`，本仓为独立拷贝；两边不一致时以 canonical 为准。规范原文以学校下发《附件1：新疆大学本科毕业论文（设计）规范及格式要求》为准。
