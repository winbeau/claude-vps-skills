# global

跨 session 生效的全局 Claude Code 配置(非某个项目专属)。

## `CLAUDE.md`

`~/.claude/CLAUDE.md` 全局提示词的 canonical 版本。对所有 session 生效(项目级 CLAUDE.md 优先级更高)。

安装(软链,便于 `git pull` 自动同步):

```bash
ln -sfn "$PWD/global/CLAUDE.md" ~/.claude/CLAUDE.md
```
