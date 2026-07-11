---
name: tmux-ssh-remote
description: >
  Operate a remote host through SSH in a persistent tmux session, preserving cwd,
  environment, shell state, and history across turns. Use when the user mentions
  tmux with SSH, asks to connect to or control a remote WSL, GPU box, lab server,
  or wants multiple commands run in one persistent remote shell. Includes one-shot
  recovery when a session is missing or unresponsive.
---

# tmux-ssh-remote

Persistent-shell pattern for remote control. Reach for this whenever the user
wants more than one command run on a remote host — fresh `ssh host cmd` per
turn loses cwd, virtualenv, history, and pays connect cost each call.

## Trigger

Invoke when the user message contains BOTH of "tmux" + "ssh", OR clearly
asks to drive a remote host with tmux+ssh. Examples that should trigger:

- "ssh tailscale 连接看看", "tmux 守护 ssh"
- "connect to my WSL", "remote control my GPU box"
- "run X on the lab machine via ssh"

If only one tool is mentioned and a persistent shell isn't needed (single
diagnostic ssh call), skip this skill and use plain `ssh`.

## Workflow

### 1. Pick a session name from the project

Use the current project's basename. From the repo root:

```bash
SESSION=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
```

The user's expectation is **one tmux session per project**, named after the
project. Do NOT reuse a generic name like `wsl` or `remote`.

### 2. Ensure the session exists (idempotent)

```bash
~/.claude/skills/tmux-ssh-remote/scripts/tmux-ensure.sh "$SESSION" 'ssh -p 2222 user@host'
```

- First time: persists the ssh-cmd to
  `~/.claude/skills/tmux-ssh-remote/scripts/.sessions/<session>.cmd` and creates the
  session.
- Subsequent calls: no-op if the session is healthy (1s `true` probe).
- `--force` flag: kill + recreate even if healthy.

When the user names the host indirectly (e.g. "tailscale 那台 WSL"), use
`tailscale status` to discover the peer hostname/IP, then SSH with whatever
port/user the user mentioned (e.g. "注意 2222 端口").

### 2.5 "连到本机 / my machine" — resolve via mybox

When the user says **连到本机 / 连我电脑 / 我自己的机器 / my machine / my
box** without naming a host, do NOT guess from `tailscale status`. Resolve
the ssh command with `mybox`. Its rule is purely pwd-based (claude always
runs as uid winbeau, so identity comes from where you run it):
`/home/winbeau/<name>/...` → reads `/home/winbeau/<name>/.mybox.conf`;
`/home/<user>/...` → reads `/home/<user>/.mybox.conf`.

```bash
SSH_CMD=$(/home/winbeau/bin/mybox ssh-cmd) &&
~/.claude/skills/tmux-ssh-remote/scripts/tmux-ensure.sh "$SESSION" "$SSH_CMD"
```

Rules:
- Run `mybox` **from the project/workspace directory** — identity is the
  first path segment under /home/winbeau (or /home). A `cd /tmp && mybox`
  errors out by design.
- If it exits non-zero ("未找到 ...mybox.conf"), offer the guided setup:
  invoke the **set-localhost** skill (picks the machine from tailscale
  peers, writes the config, walks the user through key install, then
  verifies). Quick manual alternative:
  `mybox set <远端用户名>@<tailscale-ip>[:端口]`. Never invent an IP on
  the user's behalf.
- On connect failures run `/home/winbeau/bin/mybox doctor` — it TCP-probes,
  tests key auth, and prints the exact public key the user must install on
  their device (outbound ssh uses winbeau's key regardless of `$HOME`).
- `mybox whoami` / `mybox show` are the debug views if the resolved
  workspace or target looks wrong.

### 3. Inject every subsequent command via the helper

```bash
~/.claude/skills/tmux-ssh-remote/scripts/tmux-inject.sh -t 120 --auto-recover \
    "$SESSION" 'cd ~/proj && uv run pytest'
```

Required args:
- `<session-name>` — created/ensured in step 2
- `<command>` — the command string (quote as one arg)

Optional flags:
- `-t N`            max wait seconds (default 90; bump for long builds /
                    package installs)
- `-q`              quiet: omit the trailing `[tmux-inject] rc=N` footer
- `--auto-recover`  on timeout (rc 124), call `tmux-ensure.sh --force` to
                    kill the (hung) session and respawn it with the saved
                    ssh-cmd, then retry the original command ONCE. Requires
                    that step 2 has bound an ssh-cmd. Use this for every
                    "real" command — the cost on the happy path is zero.

The script:
- waits for completion via unique sentinel markers
- captures output cleanly between markers (no shell prompt noise)
- propagates the remote command's exit code

### 4. Recovery contract

A hang can happen if:
- SSH connection drops (network blip, host reboot, Tailscale flap)
- Remote shell gets stuck on an interactive prompt (`npx playwright` install,
  `passwd`, `gh auth login`, etc.)
- A command genuinely exceeds `-t N`

`--auto-recover` ONLY rescues the first two — when the session itself is
hung. On timeout (rc 124) it does this:
1. send `C-c` to abort the running command in the session
2. health-probe the session with a 5s inline `true` check
3. if the probe **succeeds**: session is fine, the command was just slow →
   do NOT recover, propagate rc 124. You re-run with a bigger `-t`.
4. if the probe **fails**: session is genuinely hung → force-kill +
   respawn with the saved ssh-cmd → retry the command ONCE.

It does NOT extend `-t` — pick a realistic timeout for the actual command.
If the retry also times out, it propagates rc 124 to the caller.

If you suspect the remote is stuck on an interactive prompt, you can
recover BEFORE the timeout fires by sending a Ctrl-C explicitly:
`tmux send-keys -t "$SESSION" C-c`.

### 5. Common reasons to use a one-off ssh instead

Skip this skill (and use plain `ssh -p ... user@host 'cmd'`) only when:

- The very first connectivity probe (ping / `which sshd` / port scan) — too
  cheap to bother with tmux setup.
- Truly stateless single-shot commands the user explicitly asked for as
  one-offs.
- The remote shell is hostile to tmux send-keys (rare).

Even there, prefer setting up the tmux session early so subsequent work
uses the helpers.

## File layout

```
~/.claude/skills/tmux-ssh-remote/
├── SKILL.md           this file
└── scripts/
    ├── tmux-ensure.sh session lifecycle: bind ssh-cmd + create / health-check / respawn
    ├── tmux-inject.sh command injector with optional --auto-recover
    └── .sessions/     per-session saved ssh-cmd (created on first ensure)
        └── <session>.cmd
```

`.sessions/` is local state, not part of the skill code — safe to delete to
force re-binding.

## Pitfalls

- **Never run two `tmux-inject.sh` calls against the same session concurrently.**
  `tmux send-keys` writes into a shared pane: a second caller's marker setup
  interleaves with the first caller's command, corrupting both captures. The
  helper takes a per-session `flock`, so a second concurrent call fails fast
  with rc 3 (`another injection is already in flight`). If you need to do
  parallel work while a long command is running, either: (a) wait, (b)
  spin up a second session for the side task, or (c) `git push` from this
  side and `git pull` on the remote later. Do NOT run `tmux-inject.sh` in
  the background while issuing more commands to the same session.
- **Don't use one-letter or generic session names** (`wsl`, `r`, `s`) —
  collisions across projects. Stick to project basename.
- **Don't inject multi-line heredocs directly via the helper** — `tmux
  send-keys` treats them as one big paste. For multi-line scripts, write
  the script to a file on the remote (`cat > /tmp/x.py <<'PYEOF' ... PYEOF`)
  in one inject call, then run it in the next inject call.
- **Long-running commands**: pass `-t` matching the expected runtime, or
  the helper times out and the command keeps running in the session. With
  `--auto-recover`, a too-small `-t` will also force-kill a healthy session
  that was just slow — be deliberate.
- **Shell history-expansion (zsh `!`)** can mangle f-string `!r` etc. when
  pasted at the prompt. Prefer writing scripts to disk over complex inline
  one-liners.
- **tmux-inject.sh does NOT create the tmux session.** Use tmux-ensure.sh.
  Then inject's `--auto-recover` can leverage the saved ssh-cmd for respawn.
