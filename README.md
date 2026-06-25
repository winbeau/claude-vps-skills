# claude-vps-skills

自封装的 [Claude Code](https://claude.com/claude-code) / Codex **Skills** 合集，跑在我的 lab VPS 工作流里。每个 skill 一个目录，含 `SKILL.md`（YAML frontmatter + 指令），部分附带脚本 / 模板 / 参考资料。

## Skills

| Skill | 作用 | 触发 |
|---|---|---|
| [`academic_writing`](skills/academic_writing/) | 学术润色：三道硬门禁——杀 AI 味词汇/标点 (G1) → 逻辑闭环 Claim→Evidence→Impact (G2) → CS/DL 领域语义 (G3)；`detect` / `rewrite` / `edit` 三模式，绝不新增事实/引用/数字 | 润色 / 改写 / 降AI味 / 学术化 / "make this sound less like AI" |
| [`article-to-html`](skills/article-to-html/) | 把 markdown 草稿或对话内容渲染成**单文件**「论文提案」风 HTML：衬线正文 + 等宽元信息 + 编号节 + 内联 SVG 图 + callout + 表格 + 可选 JS 交互 | "渲染成网页 / turn this into HTML / 排版这段 / paper-style HTML" |
| [`notify-win`](skills/notify-win/) | 经 SSH 在 Windows 桌面弹**静音 toast + 响亮报警铃**，长任务（训练/构建/下载）跑完提醒回桌面 | 通知到 win / 做完通知我 / "notify me on windows" |
| [`tmux-ssh-remote`](skills/tmux-ssh-remote/) | 用**持久化 tmux 会话**驱动远程主机，保留 cwd / env / state，超时自动 kill+重连+重试 | 同时出现 "tmux" + "ssh"，或"连接/远程控制/drive"某台机器 |

## 安装

Skills 默认从 `~/.claude/skills/`（Claude Code）加载。把需要的目录拷过去即可：

```bash
git clone https://github.com/winbeau/claude-vps-skills.git
# 全部安装
cp -r claude-vps-skills/skills/* ~/.claude/skills/
# 或单个
cp -r claude-vps-skills/skills/academic_writing ~/.claude/skills/
```

之后在 Claude Code 里用 `/<skill-name>` 调用，或命中 `description` 里的触发短语时自动加载。

## 备注

- **`notify-win`** 需要预先在本机装好 `notify-win` CLI（`~/.config/notify-win/config` 配主机/用户/端口/密钥）+ Windows 端 PowerShell 通知与计划任务桥接；SKILL.md 里的主机用 `<user>@<win-host>` 占位，按自己的 Tailscale 主机替换。
- **`tmux-ssh-remote`** 的 `.sessions/` 运行时状态不入库；脚本里的 `user@host:2222` 均为占位。
- **`article-to-html`** 改编自 [`MagicCube/article-to-html-skill`](https://github.com/MagicCube/article-to-html-skill)，沿用其 "paper proposal" 设计系统。

## License

MIT — 见 [LICENSE](LICENSE)。
