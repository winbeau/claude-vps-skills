#!/usr/bin/env bash
# deploy.sh — 在新机器上一键部署本仓库到 ~/.claude（幂等，可反复运行）
#
#   1) 把 bin/* 全部软链到 ~/bin/（CLI 工具，如 mybox）
#   2) 把 skills/* 全部软链到 ~/.claude/skills/
#   3) 把 global/CLAUDE.md 软链到 ~/.claude/CLAUDE.md（原有非软链文件先备份）
#   4) 写 ~/.claude/settings.json：终端原生滚动（关闭 fullscreen / alternate screen）
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
SKILLS_DIR="${CLAUDE_DIR}/skills"
BIN_DIR="${HOME}/bin"

echo "==> 仓库: $REPO"
mkdir -p "$SKILLS_DIR" "$BIN_DIR"

# 1) 同步 bin/CLI 工具 ------------------------------------------------------
# 「注册」新命令 = 往 bin/ 丢一个可执行文件，重跑本脚本即自动软链到 ~/bin。
if compgen -G "$REPO/bin/*" > /dev/null; then
  echo "==> 同步 bin -> $BIN_DIR"
  for f in "$REPO"/bin/*; do
    [ -f "$f" ] || continue
    chmod +x "$f"
    name="$(basename "$f")"
    ln -sfn "$f" "$BIN_DIR/$name"
    echo "    linked bin: $name"
  done
fi

# 2) 同步 skills ------------------------------------------------------------
echo "==> 同步 skills -> $SKILLS_DIR"
for d in "$REPO"/skills/*/; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  ln -sfn "$d" "$SKILLS_DIR/$name"
  echo "    linked skill: $name"
done

# 3) 全局 CLAUDE.md ---------------------------------------------------------
echo "==> 链接全局 CLAUDE.md"
target="$CLAUDE_DIR/CLAUDE.md"
if [ -e "$target" ] && [ ! -L "$target" ]; then
  cp -a "$target" "${target}.bak.$(date +%s)"
  echo "    已备份原有 CLAUDE.md -> ${target}.bak.*"
fi
ln -sfn "$REPO/global/CLAUDE.md" "$target"
echo "    linked CLAUDE.md -> $REPO/global/CLAUDE.md"

# 4) 终端原生滚动 + 默认 auto 放行模式 --------------------------------------
echo "==> 配置终端原生滚动 + 默认 auto 放行模式"
python3 - "$CLAUDE_DIR/settings.json" <<'PY'
import json, os, shutil, sys
p = sys.argv[1]
s = {}
if os.path.exists(p):
    try:
        with open(p) as f:
            s = json.load(f)
    except json.JSONDecodeError:
        shutil.copyfile(p, p + ".bak")
        print("    原 settings.json 无法解析，已备份为 settings.json.bak，重建")
        s = {}
s["tui"] = "default"
env = s.get("env") or {}
env["CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN"] = "1"
s["env"] = env
# 默认放行模式 auto（分类器守护全自动；必须在用户级 ~/.claude/settings.json，项目级会被忽略）
perm = s.get("permissions") or {}
perm["defaultMode"] = "auto"
s["permissions"] = perm
os.makedirs(os.path.dirname(p), exist_ok=True)
with open(p, "w") as f:
    json.dump(s, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("    settings.json: tui=default, CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1, permissions.defaultMode=auto")
PY

echo
echo "==> 完成 ✅"
echo "    · bin/CLI、skills 与全局 CLAUDE.md 已软链，git pull 后自动同步"
echo "    · 滚动模式改动需【重开 claude】生效（当前会话可先输入 /tui default）"
