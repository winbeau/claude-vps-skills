# claude-vps-skills

自封装的 [Claude Code](https://claude.com/claude-code) / Codex **Skills** 合集，跑在我的 lab VPS 工作流里。每个 skill 一个目录，含 `SKILL.md`（YAML frontmatter + 指令），部分附带脚本 / 模板 / 参考资料。

## Skills（自封装）

| Skill | 作用 | 触发 |
|---|---|---|
| [`academic_writing`](skills/academic_writing/) | 学术润色：三道硬门禁——杀 AI 味词汇/标点 (G1) → 逻辑闭环 Claim→Evidence→Impact (G2) → CS/DL 领域语义 (G3)；`detect` / `rewrite` / `edit` 三模式，绝不新增事实/引用/数字 | 润色 / 改写 / 降AI味 / 学术化 / "make this sound less like AI" |
| [`article-to-html`](skills/article-to-html/) | 把 markdown 草稿或对话内容渲染成**单文件**「论文提案」风 HTML：衬线正文 + 等宽元信息 + 编号节 + 内联 SVG 图 + callout + 表格 + 可选 JS 交互 | "渲染成网页 / turn this into HTML / 排版这段 / paper-style HTML" |
| [`humanizer-zh`](skills/humanizer-zh/) | 中文文本去 AI 生成痕迹：检查宣传性语言、破折号滥用、三段式法则、AI 词汇、模糊归因和过度连接短语 | 去 AI 味 / 人性化 / 自然一点 / humanize / 编辑或审阅文本 |
| [`notify-win`](skills/notify-win/) | 经 SSH 在 Windows 桌面弹**静音 toast + 响亮报警铃**，长任务（训练/构建/下载）跑完提醒回桌面 | 通知到 win / 做完通知我 / "notify me on windows" |
| [`set-localhost`](skills/set-localhost/) | 一次性把用户自己的 Tailscale 设备绑定到 `mybox`，并完成 SSH 公钥安装与 `tmux-ssh-remote` 验证 | 设置本机 / 绑定本机 / 配置我的电脑 / set localhost / 初始化 mybox |
| [`tmux-ssh-remote`](skills/tmux-ssh-remote/) | 用**持久化 tmux 会话**驱动远程主机，保留 cwd / env / state，超时自动 kill+重连+重试 | 同时出现 "tmux" + "ssh"，或"连接/远程控制/drive"某台机器 |
| [`update-docs`](skills/update-docs/) | 更新飞跃项目 README 与 GitHub Pages「发展历程」页，维护 `VERSIONS.md` 版本记忆并按最近提交归纳变更 | 更新 README / 更新 Pages / 更新发展历程 / changelog / 发个版 |
| [`xju-docx`](skills/xju-docx/) | 按**新疆大学论文规范**生成/规范化/校验/润色 docx：框架生成器（封面+目录域+GB8567 九章骨架）、Word97 `.doc` 提取器（**免 LibreOffice**）、python-docx 排版库（三级标题/分节页码/三线表）、机检器（`--json`/`--fix`/`--content`） | 规范论文格式 / 排版 docx / 生成论文框架 / 论文格式检查 / 三线表 / "按学校格式排版" |

## Vendored（第三方，MIT）

| Skill | 作用 | 来源 |
|---|---|---|
| [`article-to-latex`](skills/article-to-latex/) | 通用 LaTeX 文档：生成 / 编译 / PDF↔LaTeX 转换；彩色 **tcolorbox**、**中文 xeCJK**、TikZ/pgfplots 图表、简历/论文/海报/Beamer 等。本仓 fork 自 `latex-document-skill`、改名以与 `article-to-html` 配对，并加了 [`compile_tectonic.sh`](skills/article-to-latex/scripts/compile_tectonic.sh) 适配 Tectonic 引擎 | [ndpvt-web/latex-document-skill](https://github.com/ndpvt-web/latex-document-skill)（MIT）；改动见 [ATTRIBUTION.md](skills/article-to-latex/ATTRIBUTION.md) |

> vendored 副本为减重已去掉上游 `examples/` 与吉祥物 PNG（~19MB，对功能无影响），完整版见上游仓库。

## 安装

Claude Code 默认从 `~/.claude/skills/` 加载。把需要的目录拷过去即可：

```bash
git clone https://github.com/winbeau/claude-vps-skills.git
mkdir -p ~/.claude/skills

# 全部安装
cp -a claude-vps-skills/skills/. ~/.claude/skills/

# 或单个
cp -a claude-vps-skills/skills/academic_writing ~/.claude/skills/
```

之后在 Claude Code 里用 `/<skill-name>` 调用，或命中 `description` 里的触发短语时自动加载。

Codex 默认从 `~/.codex/skills/` 加载。本仓保留 Claude Code 原始 skill 目录；直接用于 Codex 时，若遇到严格校验，需要按 Codex 规则把 frontmatter 规范为仅含 `name` 和 `description`。

## 备注

- **`notify-win`** 目录自带完整实现：Linux CLI（`notify-win`）+ Windows 端脚本（`show.ps1` / `launcher.vbs` / `notify-setup-v2.ps1` / `notify-finish.ps1`）+ `config.example`，部署/架构/踩坑见该目录 `README.md`。所有主机/用户均为 `YOUR_WIN_HOST` / `YOUR_WIN_USER` / `<user>@<win-host>` 占位，按自己的 Tailscale 主机替换。上游 canonical 仓库：[`winbeau/notify-win`](https://github.com/winbeau/notify-win)。
- **`tmux-ssh-remote`** 的 `.sessions/` 运行时状态不入库；脚本里的 `user@host:2222` 均为占位。
- **`article-to-html`** 改编自 [`MagicCube/article-to-html-skill`](https://github.com/MagicCube/article-to-html-skill)，沿用其 "paper proposal" 设计系统。
- **`xju-docx`** canonical 源在 [`XjuSelab/xju-feiyue`](https://github.com/XjuSelab/xju-feiyue) 的 `skills/xju-docx/`（可随该仓 `./skills/install.sh --global` 软链安装），本仓为独立拷贝。依赖 `python3 -m pip install --user python-docx olefile`（**无需 sudo / LibreOffice**）；配置方法与快速上手见该目录 [`README.md`](skills/xju-docx/README.md)。

## License

MIT — 见 [LICENSE](LICENSE)。
