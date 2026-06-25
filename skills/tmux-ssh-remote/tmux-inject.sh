#!/usr/bin/env bash
# tmux-inject.sh — inject a command into a persistent tmux session and capture
# its output via unique sentinel markers.
#
# Designed for: an attached SSH shell living inside a tmux session, so we can
# preserve cwd/env/state across invocations instead of paying connection +
# shell-init cost each turn.
#
# Usage:
#   tmux-inject.sh [-t TIMEOUT_SEC] [-q] [--auto-recover] <session-name> <command>
#
#   -t N            max seconds to wait for completion (default 90)
#   -q              quiet: only print captured output, omit the trailing
#                   [tmux-inject] rc=N line
#   --auto-recover  on timeout (rc=124), call tmux-ensure.sh to (kill +)
#                   respawn the session using its saved ssh-cmd, then retry
#                   the original command ONCE. No-op if no ssh-cmd is saved
#                   for the session.
#
# Exit code: the remote command's exit code. Local errors return non-zero
# with a [tmux-inject] prefix on stderr. Timeout returns 124.
#
# Implementation notes:
#   - Markers live in two shell variables (B, E) on the remote side; only the
#     printf-generated lines contain the literal marker substring, so the
#     shell-echoed command line is NOT matched by the end-pattern scanner.
#   - Output is extracted from `tmux capture-pane -S -5000`, between the
#     printed begin and end markers.
#   - This script intentionally does NOT create the tmux session. Use
#     tmux-ensure.sh first to bind the ssh-cmd and create the session.

set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

TIMEOUT=90
QUIET=0
AUTO_RECOVER=0

# parse flags. getopts doesn't do long flags, so handle --auto-recover by hand.
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    -t) TIMEOUT="$2"; shift 2 ;;
    -q) QUIET=1; shift ;;
    --auto-recover) AUTO_RECOVER=1; shift ;;
    --) shift; ARGS+=("$@"); break ;;
    -*) echo "[tmux-inject] bad flag: $1" >&2; exit 2 ;;
    *)  ARGS+=("$1"); shift ;;
  esac
done
set -- "${ARGS[@]:-}"

if [ $# -lt 2 ]; then
  cat >&2 <<EOF
usage: $0 [-t N] [-q] [--auto-recover] <session-name> <command>
  <session-name>  existing tmux session holding the remote shell
  <command>       command string to inject (quote as one arg)
EOF
  exit 2
fi

SESSION="$1"; shift
CMD="$*"

# Acquire a per-session non-blocking lock. send-keys + capture-pane on the
# same tmux session are NOT concurrency-safe: two injectors racing will
# interleave their marker setup with each other's commands and corrupt both
# captures. flock makes the second caller fail fast (rc 3) instead of
# trampling an in-flight injection.
LOCK_DIR="$SCRIPT_DIR/.sessions"
mkdir -p "$LOCK_DIR"
LOCK_FILE="$LOCK_DIR/$SESSION.lock"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[tmux-inject] another injection is already in flight on session '$SESSION'" >&2
  echo "[tmux-inject] wait for it to finish (or release the lock at $LOCK_FILE)" >&2
  exit 3
fi

# --- Core injection (one attempt). Sets globals: BODY, RC. Exit code 0 if
# the marker was seen (RC = remote rc), 124 if timed out (BODY = pane tail).
_inject_once() {
  local _session="$1" _cmd="$2" _timeout="$3"

  if ! tmux has-session -t "$_session" 2>/dev/null; then
    BODY="[tmux-inject] session '$_session' does not exist"
    RC=255
    return 255
  fi

  # Unique markers. Use only [A-Za-z0-9_] so they're sed/grep-friendly.
  local TAG_B="WBEGIN${$}x${RANDOM}x${RANDOM}"
  local TAG_E="WSEND${$}x${RANDOM}x${RANDOM}"

  # 1) define markers as remote shell vars (so typed-echo of the printf line
  #    shows '$B' / '$E', NOT the literal marker)
  tmux send-keys -t "$_session" "B=${TAG_B}; E=${TAG_E}" Enter
  # 2) emit begin marker
  tmux send-keys -t "$_session" "printf '\\n__%s__\\n' \"\$B\"" Enter
  sleep 0.1
  # 3) the user command
  tmux send-keys -t "$_session" "$_cmd" Enter
  # 4) end marker with exit code
  tmux send-keys -t "$_session" "__rc=\$?; printf '\\n__%s__rc=%s\\n' \"\$E\" \"\$__rc\"" Enter

  local deadline=$(( $(date +%s) + _timeout ))
  local end_pat="__${TAG_E}__rc="
  local begin_pat="__${TAG_B}__"
  local out=""
  while :; do
    out=$(tmux capture-pane -t "$_session" -p -S -5000 2>/dev/null || true)
    if printf '%s' "$out" | grep -E "${end_pat}[0-9]+" >/dev/null; then
      break
    fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
      BODY=$(printf '%s' "$out" | tail -120)
      RC=124
      return 124
    fi
    sleep 0.4
  done

  local body
  body=$(printf '%s' "$out" | awk -v b="${begin_pat}" -v e="${end_pat}" '
    index($0, b) > 0 && match($0, b "$") { capturing=1; next }
    index($0, e) > 0 && $0 ~ (e "[0-9]+$") { rc_line=$0; capturing=0; exit }
    capturing { print }
    END { if (rc_line != "") print rc_line }
  ')
  local rc
  rc=$(printf '%s' "$body" | grep -E "${end_pat}[0-9]+$" | tail -1 | sed -E "s/.*${end_pat}([0-9]+).*/\1/")
  body=$(printf '%s' "$body" | grep -v "${end_pat}")
  BODY="$body"
  RC="${rc:-1}"
  return 0
}

BODY=""
RC=1

_inject_once "$SESSION" "$CMD" "$TIMEOUT"
inject_status=$?

if [ "$AUTO_RECOVER" = "1" ] && { [ "$inject_status" = "124" ] || [ "$inject_status" = "255" ]; }; then
  if [ "$inject_status" = "124" ]; then
    # Distinguish "session hung" from "command merely slow" before destroying
    # an actually-healthy session. Send Ctrl-C first to abort the slow
    # command, then probe in-process with `true` (we still hold the flock, so
    # we cannot call this script recursively — use _inject_once directly).
    echo "[tmux-inject] TIMEOUT after ${TIMEOUT}s — health-probing session" >&2
    tmux send-keys -t "$SESSION" C-c 2>/dev/null || true
    sleep 0.5
    _inject_once "$SESSION" 'true' 5
    probe_status=$?
    if [ "$probe_status" = "0" ]; then
      echo "[tmux-inject] session is responsive — your command was just slow." >&2
      echo "[tmux-inject] NOT recovering; re-run with a larger -t. Propagating rc 124." >&2
      ensure_rc=99   # signal: do not retry
    else
      echo "[tmux-inject] session unresponsive — force-respawning" >&2
      "$SCRIPT_DIR/tmux-ensure.sh" --force "$SESSION" >&2
      ensure_rc=$?
    fi
  else
    echo "[tmux-inject] session '$SESSION' missing — attempting auto-recover" >&2
    "$SCRIPT_DIR/tmux-ensure.sh" "$SESSION" >&2
    ensure_rc=$?
  fi
  if [ "$ensure_rc" -eq 0 ]; then
    echo "[tmux-inject] retrying command once after recover" >&2
    _inject_once "$SESSION" "$CMD" "$TIMEOUT"
    inject_status=$?
  elif [ "$ensure_rc" -ne 99 ]; then
    echo "[tmux-inject] recover failed (ensure rc=$ensure_rc); not retrying" >&2
  fi
fi

if [ "$inject_status" = "124" ]; then
  [ "$QUIET" = "0" ] && echo "[tmux-inject] TIMEOUT after ${TIMEOUT}s" >&2
  printf '%s\n' "$BODY" >&2
  exit 124
fi

if [ "$QUIET" = "0" ]; then
  printf '%s\n' "$BODY"
  echo "[tmux-inject] rc=${RC}"
else
  printf '%s\n' "$BODY"
fi
exit "$RC"
