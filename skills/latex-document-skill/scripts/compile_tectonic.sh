#!/usr/bin/env bash
# compile_tectonic.sh - Compile .tex to .pdf with Tectonic, optionally render PNG previews.
#
# Drop-in alternative to compile_latex.sh for systems that use Tectonic instead of
# a TeX Live install (no pdflatex/xelatex/lualatex/latexmk on PATH). Tectonic is a
# self-contained XeTeX-based engine that fetches packages/fonts on demand and runs
# the multi-pass / biber / makeindex loop itself, so most of compile_latex.sh's
# engine-detection and pass-management logic is handled natively here.
#
# Usage:
#   compile_tectonic.sh <input.tex> [OPTIONS]
#
# Options:
#   --preview            Render a PNG of each page (needs poppler's pdftoppm)
#   --preview-dir DIR    Directory for PNG output (default: same as the PDF)
#   --scale N            Max dimension of each PNG preview, in px (default: 1200)
#   --outdir DIR         Output directory for the PDF (default: same as input)
#   --shell-escape       Allow \write18 (minted, some tcblisting modes) via -Z shell-escape
#   --keep               Keep intermediate files (.aux/.log via --keep-intermediates --keep-logs)
#   --quiet              Only print errors and the final PDF path (tectonic --chatter minimal)
#   --verbose            Stream full Tectonic output
#   -h, --help           Show this help
#
# Engine is always Tectonic (XeTeX): ctex / xeCJK / fontspec / tcolorbox all work,
# CJK fonts (fandol) are fetched automatically.
#
# Tectonic is located via, in order: $TECTONIC env var, `tectonic` on PATH,
# then ~/.texbin, ~/wenbiao_zhao/.texbin, ~/.local/bin, ~/.cargo/bin, /usr/local/bin.
#
# Examples:
#   compile_tectonic.sh notes.tex
#   compile_tectonic.sh notes.tex --preview
#   compile_tectonic.sh notes.tex --preview --preview-dir ./out --scale 1600
#   compile_tectonic.sh deck.tex --shell-escape --keep

set -euo pipefail

usage() { sed -n '2,33p' "$0" | sed 's/^# \{0,1\}//'; }

# --- Locate the Tectonic binary ---
find_tectonic() {
  if [ -n "${TECTONIC:-}" ] && [ -x "${TECTONIC}" ]; then echo "$TECTONIC"; return; fi
  if command -v tectonic >/dev/null 2>&1; then command -v tectonic; return; fi
  for cand in "$HOME/.texbin/tectonic" "$HOME/wenbiao_zhao/.texbin/tectonic" \
              "$HOME/.local/bin/tectonic" "$HOME/.cargo/bin/tectonic" \
              "/usr/local/bin/tectonic"; do
    [ -x "$cand" ] && { echo "$cand"; return; }
  done
  return 1
}

# --- Parse args ---
INPUT=""
PREVIEW=0
PREVIEW_DIR=""
SCALE=1200
OUTDIR=""
SHELL_ESCAPE=0
KEEP=0
QUIET=0
VERBOSE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --preview)       PREVIEW=1 ;;
    --preview-dir)   PREVIEW_DIR="$2"; shift ;;
    --scale)         SCALE="$2"; shift ;;
    --outdir)        OUTDIR="$2"; shift ;;
    --shell-escape)  SHELL_ESCAPE=1 ;;
    --keep)          KEEP=1 ;;
    --quiet)         QUIET=1 ;;
    --verbose)       VERBOSE=1 ;;
    -h|--help)       usage; exit 0 ;;
    -*)              echo "compile_tectonic.sh: unknown option: $1" >&2; usage; exit 1 ;;
    *)               INPUT="$1" ;;
  esac
  shift
done

[ -z "$INPUT" ]   && { echo "compile_tectonic.sh: missing <input.tex>" >&2; usage; exit 1; }
[ -f "$INPUT" ]   || { echo "compile_tectonic.sh: no such file: $INPUT" >&2; exit 1; }

TECTONIC="$(find_tectonic)" || {
  echo "compile_tectonic.sh: tectonic not found." >&2
  echo "  Install from https://tectonic-typesetting.github.io or set \$TECTONIC=/path/to/tectonic" >&2
  exit 127
}

INPUT_DIR="$(cd "$(dirname "$INPUT")" && pwd)"
BASE="$(basename "${INPUT%.*}")"
OUTDIR="${OUTDIR:-$INPUT_DIR}"
mkdir -p "$OUTDIR"

# --- Build tectonic command ---
# --chatter is a GLOBAL option and must precede the `-X compile` subcommand;
# --outdir / --keep-* / --print / -Z belong to the subcommand itself.
GLOBAL_ARGS=()
[ "$QUIET" = "1" ] && GLOBAL_ARGS+=( --chatter minimal )

COMPILE_ARGS=( --outdir "$OUTDIR" )
[ "$KEEP" = "1" ]         && COMPILE_ARGS+=( --keep-intermediates --keep-logs )
[ "$SHELL_ESCAPE" = "1" ] && COMPILE_ARGS+=( -Z shell-escape )
[ "$VERBOSE" = "1" ]      && COMPILE_ARGS+=( --print )

[ "$QUIET" = "1" ] || echo ">> tectonic compiling $INPUT  (engine: Tectonic/XeTeX)"
# `if !` is exempt from set -e, so a compile failure surfaces with our message
# instead of an opaque early exit; --chatter minimal still lets real errors through.
if ! "$TECTONIC" "${GLOBAL_ARGS[@]+"${GLOBAL_ARGS[@]}"}" -X compile "$INPUT" "${COMPILE_ARGS[@]}"; then
  echo "compile_tectonic.sh: tectonic failed to compile $INPUT (see output above)" >&2
  exit 1
fi

PDF="$OUTDIR/$BASE.pdf"
[ -f "$PDF" ] || { echo "compile_tectonic.sh: compile finished but $PDF missing" >&2; exit 1; }
[ "$QUIET" = "1" ] || echo ">> PDF: $PDF"

# --- Optional PNG previews ---
if [ "$PREVIEW" = "1" ]; then
  if ! command -v pdftoppm >/dev/null 2>&1; then
    echo "compile_tectonic.sh: --preview needs pdftoppm (poppler-utils); skipping." >&2
  else
    PREVIEW_DIR="${PREVIEW_DIR:-$OUTDIR}"
    mkdir -p "$PREVIEW_DIR"
    # -scale-to bounds the longest page side to $SCALE px (matches compile_latex.sh --scale).
    pdftoppm -png -scale-to "$SCALE" "$PDF" "$PREVIEW_DIR/$BASE-page"
    [ "$QUIET" = "1" ] || { echo ">> previews:"; ls "$PREVIEW_DIR/$BASE-page"*.png; }
  fi
fi

# Print the final PDF path on stdout (so callers can capture it).
echo "$PDF"
