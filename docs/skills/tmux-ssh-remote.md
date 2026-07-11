# tmux-ssh-remote

用**持久化 tmux 会话**驱动远程主机（WSL / GPU box / lab server）的 skill。比每回合一条 `ssh host cmd` 强——后者丢 cwd / virtualenv / history，且每次付连接开销。

> 完整工作流见 [`SKILL.md`](../../skills/tmux-ssh-remote/SKILL.md)。

## 它做什么

每个项目开**一个**以项目名命名的 tmux 会话，里面常驻一条 SSH 连接；之后所有命令经 helper 注入到该会话，跨回合保留 cwd / env / state。注入超时会自动 kill 并用保存的 ssh-cmd 重建会话，再重试一次。

## 触发

消息里**同时**出现 "tmux" + "ssh"，或明确要 tmux+ssh 驱动远程主机（"连接看看 / remote control my GPU box / run X on the lab machine via ssh"）。只提一个工具、且单次诊断 ssh 就够时——跳过本 skill，用普通 `ssh`。

## 用法（3 步）

```bash
# 1. 会话名 = 项目目录名（一项目一会话，别用 wsl/remote 这种通用名）
SESSION=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")

# 2. 确保会话存在（幂等；首次落盘 ssh-cmd，健康则 no-op，--force 强制重建）
./scripts/tmux-ensure.sh "$SESSION" 'ssh -p 2222 user@host'

# 3. 注入每条后续命令（-t 超时秒，--auto-recover 超时自愈重试一次）
./scripts/tmux-inject.sh -t 120 --auto-recover "$SESSION" 'cd ~/proj && uv run pytest'
```

> 安装到 `~/.claude/skills/` 后，实际路径为 `~/.claude/skills/tmux-ssh-remote/scripts/tmux-{ensure,inject}.sh`。

## 文件

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 触发判定、完整工作流、恢复契约、坑 |
| `scripts/tmux-ensure.sh` | 幂等创建/探活会话，落盘 ssh-cmd（`--force` 重建） |
| `scripts/tmux-inject.sh` | 向会话注入命令，带超时 + `--auto-recover` 自愈重试 |

> 运行时状态 `.sessions/*.cmd|.lock`（含真实 ssh 命令/主机）**不入库**，已被 `.gitignore` 排除。
