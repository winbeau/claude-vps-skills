#!/usr/bin/env bash
# tmux-ensure.sh — make sure a named tmux session exists and is healthy.
#
# Persistent state: the ssh-cmd used to create a session is stored to
#   <skill-dir>/scripts/.sessions/<session>.cmd
# so subsequent calls (e.g. after a hang) can respawn without re-passing it.
#
# Usage:
#   tmux-ensure.sh <session>                    # use saved ssh-cmd
#   tmux-ensure.sh <session> '<ssh-cmd>'        # bind/update ssh-cmd, ensure session
#   tmux-ensure.sh --force <session> [<ssh-cmd>] # kill any existing session and recreate
#
# Behavior:
#   1. If <ssh-cmd> is given, save it to .sessions/<name>.cmd
#   2. Determine target ssh-cmd (arg or saved). Error if neither.
#   3. If session exists and is healthy (1s `true` probe via inject), no-op
#      (unless --force).
#   4. Otherwise: kill if exists, new-session with ssh-cmd, sleep 3s, probe,
#      report ok / failed.
#
# Exit codes:
#   0  session is healthy
#   1  failed to bring up session (target probably unreachable)
#   2  bad args
#
# Used by tmux-inject.sh --auto-recover to respawn hung sessions.

set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="$SCRIPT_DIR/.sessions"
mkdir -p "$STATE_DIR"

# Inline health probe — does NOT use tmux-inject.sh (which holds a per-session
# flock; calling inject.sh from a parent that holds that lock would deadlock).
_probe() {
  local _session="$1"
  if ! tmux has-session -t "$_session" 2>/dev/null; then
    return 1
  fi
  local TAG="HEALTH${$}x${RANDOM}x${RANDOM}"
  tmux send-keys -t "$_session" "printf '__%s__\\n' '$TAG'" Enter
  local deadline=$(( $(date +%s) + 5 ))
  while :; do
    if tmux capture-pane -t "$_session" -p -S -200 2>/dev/null | grep -q "__${TAG}__"; then
      return 0
    fi
    [ "$(date +%s)" -ge "$deadline" ] && return 1
    sleep 0.3
  done
}

FORCE=0
if [ "${1:-}" = "--force" ]; then
  FORCE=1
  shift
fi

if [ $# -lt 1 ]; then
  cat >&2 <<EOF
usage: $0 [--force] <session> [<ssh-cmd>]
  Persists ssh-cmd to $STATE_DIR/<session>.cmd on first call.
  Subsequent calls without ssh-cmd reuse the saved one.
EOF
  exit 2
fi

SESSION="$1"; shift
NEW_CMD="${1:-}"
CMD_FILE="$STATE_DIR/$SESSION.cmd"

if [ -n "$NEW_CMD" ]; then
  printf '%s\n' "$NEW_CMD" > "$CMD_FILE"
fi

if [ ! -s "$CMD_FILE" ]; then
  echo "[tmux-ensure] no saved ssh-cmd for session '$SESSION' and none provided" >&2
  exit 2
fi
SAVED_CMD=$(cat "$CMD_FILE")

# Health probe — only meaningful if session exists.
healthy=0
if _probe "$SESSION"; then
  healthy=1
fi

if [ "$FORCE" = "0" ] && [ "$healthy" = "1" ]; then
  echo "[tmux-ensure] session '$SESSION' healthy (ssh-cmd: $SAVED_CMD)"
  exit 0
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[tmux-ensure] killing stale session '$SESSION'"
  tmux kill-session -t "$SESSION" 2>/dev/null || true
fi

echo "[tmux-ensure] creating session '$SESSION' with: $SAVED_CMD"
if ! tmux new-session -d -s "$SESSION" -x 220 -y 50 "$SAVED_CMD"; then
  echo "[tmux-ensure] tmux new-session failed" >&2
  exit 1
fi
sleep 3
tmux send-keys -t "$SESSION" '' Enter 2>/dev/null || true
sleep 1

# Verify the new session is reachable.
if _probe "$SESSION"; then
  echo "[tmux-ensure] session '$SESSION' is up"
  exit 0
fi

echo "[tmux-ensure] session '$SESSION' came up but probe still fails — remote may be offline" >&2
exit 1
