# Attribution — article-to-latex (fork of latex-document-skill)

This directory is a **vendored, lightly modified copy of a third-party skill**. It is *not*
original work in this repo; it is redistributed here under its upstream MIT license.
Locally **renamed to `article-to-latex`** (skill `name:` + directory) to pair with this repo's
`article-to-html`; upstream is `latex-document-skill`. Functionality is unchanged.

## Upstream source

- **Repo**: https://github.com/ndpvt-web/latex-document-skill
- **Author**: `ndpvt-web` ("Made with Claude Code on HappyCapy AI")
- **License**: MIT (declared in the upstream `README.md` → "## License / MIT"; upstream ships
  no standalone `LICENSE` file)
- **Vendored at**: commit fetched 2026-06-25 via `git clone --depth 1`

## What it does

Universal LaTeX document skill: create / compile / convert documents to PDF — resumes, papers,
theses, posters, exams, cheat sheets, books, Beamer, etc. Colored **tcolorbox** boxes, **CJK**
typesetting (xeCJK + auto XeLaTeX), TikZ/pgfplots charts, PDF→LaTeX OCR, mail merge, latexdiff.
See `SKILL.md` and `references/` for the full feature set.

## Modifications made in this repo

1. **Added `scripts/compile_tectonic.sh`** — a Tectonic-engine compile wrapper (drop-in for the
   upstream `scripts/compile_latex.sh`), because the downstream environment uses
   [Tectonic](https://tectonic-typesetting.github.io) instead of a TeX Live install (no
   pdflatex/xelatex/lualatex/latexmk on PATH). Mirrors the `--preview / --preview-dir / --scale /
   --outdir / --quiet / --verbose` interface; adds `--shell-escape` and `--keep`. Tested
   end-to-end on a Chinese `ctexart` + `tcolorbox` document.
2. **Added a "本机适配（Tectonic）" note** at the top of `SKILL.md` pointing compilation at
   `compile_tectonic.sh` on Tectonic machines.
3. **Trimmed for repo size** (functionally lossless): removed `examples/` (~12 MB sample outputs),
   the `assets/capy-*.png` / `assets/happycapy-*.png` mascot branding images (~6.5 MB; not
   referenced by any template or script), and the upstream `.git/`, `.github/`, `tests/`, `stats/`
   directories. Kept `SKILL.md`, `README.md`, `references/`, `scripts/`, `assets/templates/`,
   `setup.sh`, `requirements.txt`, `.chktexrc`. **Full untrimmed skill is at the upstream repo.**

## License notice

Copyright (c) `ndpvt-web` — latex-document-skill, MIT License.
The MIT license text is reproduced in the upstream repository's README. This vendored copy is
redistributed under the same terms; the parent repo's top-level `LICENSE` covers only the
first-party skills, not this directory.
