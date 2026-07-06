# claude-vps-skills — 新机器同步仓库

本仓库用于在**新机器**上一键部署我的 Claude Code 环境（skills + 全局提示词 + 终端滚动设置）。

## 「部署」指令

当我说「**部署**」「deploy」「同步环境」这类词时，**直接执行仓库根目录的 `./deploy.sh`**，然后把它的输出反馈给我。不需要再问细节。

`deploy.sh` 是**幂等**的（可反复运行），会完成三件事：

1. **同步 skills** — 把 `skills/*` 全部软链到 `~/.claude/skills/`
2. **全局 CLAUDE.md** — 把 `global/CLAUDE.md` 软链到 `~/.claude/CLAUDE.md`（原有非软链文件会先备份）
3. **终端原生滚动** — 更新 `~/.claude/settings.json`：`tui=default` + `env.CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1`，关闭 fullscreen/alternate screen，改用终端自己的滚动条

跑完后**提醒我**：滚动模式改动需要**重开 claude** 才生效（当前会话可先输入 `/tui default` 立即切换）。

> 全部用**软链**而非拷贝：以后在本仓库 `git pull` 更新，`~/.claude` 里的内容自动跟着更新。

## 仓库结构

- `skills/` — 各技能，每个目录含 `SKILL.md`
- `global/CLAUDE.md` — 机器级全局提示词的 canonical 版本
- `deploy.sh` — 一键部署脚本
