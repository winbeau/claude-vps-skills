# self-skills

Personal Agent Skills shared by Claude Code and Codex. Each directory under `skills/` is independently installable and follows the same layout:

```text
skills/<kebab-case-name>/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/       # optional executable helpers
├── references/    # optional on-demand guidance
└── assets/        # optional output resources and templates
```

Human-facing manuals live in `docs/skills/`. License and attribution files remain beside vendored Skill code when redistribution requires them.

## Skills

| Skill | Purpose |
|---|---|
| [`academic-writing`](skills/academic-writing/) | Audit and rewrite academic prose without inventing evidence |
| [`article-to-html`](skills/article-to-html/) | Render a document as a self-contained paper-style HTML file |
| [`article-to-latex`](skills/article-to-latex/) | Create, compile, debug, and convert LaTeX/PDF documents |
| [`humanizer-zh`](skills/humanizer-zh/) | Make Chinese writing natural and less formulaic |
| [`idea-scan`](skills/idea-scan/) | Map evidence-backed research gaps and opportunity signals |
| [`idea-generate`](skills/idea-generate/) | Generate testable candidates from scans and user hints |
| [`idea-check-novelty`](skills/idea-check-novelty/) | Check candidates against current online prior art |
| [`idea-review`](skills/idea-review/) | Review novelty, value, rigor, and feasibility |
| [`idea-design-experiment`](skills/idea-design-experiment/) | Design low-cost falsifiable experiments |
| [`idea-synthesize`](skills/idea-synthesize/) | Coordinate and summarize the idea discovery workflow |
| [`notify-win`](skills/notify-win/) | Send a Windows desktop toast and sound alert |
| [`set-localhost`](skills/set-localhost/) | Bind a tailnet device for the `mybox` remote workflow |
| [`ship-wpf-github-release`](skills/ship-wpf-github-release/) | Build, package, and release WPF apps on GitHub |
| [`tmux-ssh-remote`](skills/tmux-ssh-remote/) | Operate remote hosts through persistent tmux SSH sessions |
| [`update-docs`](skills/update-docs/) | Update Feiyue release notes and public documentation |
| [`xju-docx`](skills/xju-docx/) | Format, validate, and repair XJU academic DOCX files |

The `idea-*` suite is domain-agnostic. World Model checks are loaded through optional domain profiles inside the relevant Skills.

## Install

Clone the repository and run the idempotent deployer:

```bash
git clone git@github.com:winbeau/self-skills.git
cd self-skills

./deploy.sh                  # Claude Code only
./deploy.sh --target codex   # Codex only
./deploy.sh --target both    # Claude Code and Codex
```

The deployer creates symlinks, so later `git pull` updates become visible immediately. It backs up a conflicting real file or directory before replacing it and does not modify unrelated third-party Skills.

Default destinations:

- Claude Code: `${CLAUDE_HOME:-$HOME/.claude}/skills`
- Codex: `${CODEX_HOME:-$HOME/.codex}/skills`

`bin/*` is linked to `~/bin`. The `notify-win` CLI is linked from `skills/notify-win/scripts/notify-win` to `~/bin/notify-win`.

## Validate

Run the repository-level structural validator:

```bash
python3 scripts/validate_skills.py
```

It checks directory names, `SKILL.md` frontmatter, matching Skill names, required `agents/openai.yaml` fields, default-prompt references, and disallowed runtime artifacts.

Useful focused checks:

```bash
bash -n deploy.sh skills/*/scripts/*.sh
python3 -m compileall -q skills scripts

python3 skills/xju-docx/scripts/build_framework.py -o /tmp/xju-smoke.docx --name 测试
python3 skills/xju-docx/scripts/validate_docx.py /tmp/xju-smoke.docx --framework
python3 skills/xju-docx/scripts/check_docx_package.py /tmp/xju-smoke.docx
```

## Documentation

Per-Skill manuals are under [`docs/skills/`](docs/skills/). Notable provenance:

- `article-to-latex` is a vendored, modified MIT Skill; see [ATTRIBUTION.md](skills/article-to-latex/ATTRIBUTION.md).
- `humanizer-zh` keeps its upstream [LICENSE](skills/humanizer-zh/LICENSE).
- `xju-docx` is synchronized from the local working copy and includes OOXML repair diagnostics. Its upstream canonical project remains [XjuSelab/xju-feiyue](https://github.com/XjuSelab/xju-feiyue).

## License

First-party content is MIT unless a Skill-local license or attribution notice says otherwise. See [LICENSE](LICENSE).
