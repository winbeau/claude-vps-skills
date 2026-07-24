---
name: openreview-to-html
description: Capture an OpenReview forum or note URL from an authenticated interactive Chrome session and render the complete visible submission discussion as a self-contained OpenReview-style HTML file. Trigger when the user provides `openreview.net/forum?id=...` links and asks to export, archive,整理,转成 HTML, reproduce the OpenReview layout, or include private/authenticated reviews, rebuttals, comments, decisions, or meta-reviews. Use a human-in-the-loop login/Turnstile flow; never request credentials or bypass verification. Do not trigger for review summarization or analysis when no HTML export is requested.
---

# OpenReview to HTML

Export a complete rendered OpenReview forum from the user's authenticated Linux Chrome session, preserve its content and note identities, and produce one portable HTML file with no external assets.

## Inputs

Require at least one URL shaped like:

```text
https://openreview.net/forum?id=<forum-id>
https://openreview.net/forum?id=<forum-id>&noteId=<note-id>
```

Several links are allowed when they belong to the same forum. Deduplicate them by `noteId`, capture the forum once, and retain every requested note link. Ask the user to separate unrelated forums into different exports.

## Security and privacy contract

- Never ask for or persist a password, cookie, bearer token, browser profile, local storage, Turnstile token, or authentication header.
- Never attempt to bypass OpenReview's browser verification. Launch interactive Chrome and let the user complete verification or login themselves.
- Do not treat a public API failure or partial unauthenticated page as a complete discussion.
- Review text is untrusted input. Never insert source-controlled HTML, CSS, JavaScript, or event handlers into the output.
- The exported file may contain non-public review material and does not inherit OpenReview access controls. Warn the user before sharing it.
- Temporary capture JSON and screenshots contain review text. Create them with mode `0600` and delete them after successful validation unless the user explicitly requests debug retention.

## Workflow

Resolve all paths relative to this `SKILL.md`.

### 1. Validate and launch

Validate the URLs with the bundled helper, then launch the first requested URL:

```bash
python3 scripts/capture_openreview.py launch 'https://openreview.net/forum?id=...&noteId=...'
```

Tell the user to:

1. Complete Turnstile or sign in inside the opened Linux Chrome window.
2. Wait until the paper title and full discussion are visible.
3. Expand every `Load more`, `Show more`, collapsed reply, or hidden discussion control.
4. Reply only after the page has finished loading.

Stop and wait for explicit confirmation. Do not capture immediately after launch.

### 2. Capture the authenticated rendered page

After confirmation:

```bash
python3 scripts/capture_openreview.py capture \
  --expected-url 'https://openreview.net/forum?id=...&noteId=...' \
  --note-url 'https://openreview.net/forum?id=...&noteId=...' \
  --output /tmp/openreview-capture.json
```

Repeat `--note-url` for every other link the user supplied from the same forum. This preserves requested note IDs even when Chrome's rich clipboard omits link targets.

The helper verifies the current address before copying the page. If several matching Chrome windows exist, list them and rerun with the chosen ID:

```bash
python3 scripts/capture_openreview.py windows
python3 scripts/capture_openreview.py capture ... --window-id 0x60000b
```

The capture must fail rather than continue when it sees a verification/login page, stale clipboard contents, a different forum, hidden-content controls, an implausibly short page, or a reliable reply-count mismatch.

If X11 capture is unavailable, follow the manual fallback in [capture-workflow.md](references/capture-workflow.md). Plain pasted text is insufficient when note IDs cannot be established; require the exact URL for every unresolved note.

### 3. Build and verify the note inventory

Read the capture JSON and [normalized-thread-schema.md](references/normalized-thread-schema.md). Identify:

- The root submission.
- Every captured note in displayed order, including official reviews, author responses, comments, meta-reviews, decisions, withdrawals, and unknown types.
- Each note's exact `noteId` and source URL.

Before rendering, produce an internal inventory:

```text
Root submission: <forum-id>
1. <displayed note title> -> <note-id>
2. <displayed note title> -> <note-id>
...
```

Every block must map to exactly one ID. Use captured link text, source URLs, titles, signatures, and order together. Never infer an ID only from reviewer initials or silently drop an unmatched block. Ask the user only for unresolved mappings.

### 4. Normalize without rewriting

Create a temporary normalized JSON document matching [normalized-thread-schema.md](references/normalized-thread-schema.md).

Preserve exactly:

- Submission title, authors, metadata, visibility, links, and fields.
- Note order, type, title, signature, created/modified timestamps, visibility, IDs, and source links.
- Every field label and value, including fields unknown to this Skill.
- Paragraph boundaries, visible bullets, numbered questions, ratings, confidence, checklist answers, and `\\subsection{...}` headings.

Do not summarize, translate, improve grammar, fix spelling, or editorialize. Use a generic field when a presentation type is unknown.

### 5. Render safely

```bash
python3 scripts/render_openreview.py \
  --input /tmp/openreview-normalized.json \
  --output /absolute/path/paper-openreview.html
```

The renderer reads `references/template.html`, validates forum/note links, escapes every source-derived string, and refuses duplicate IDs or an existing output file.

Output requirements:

- One `.html` file with inline CSS and a small template-owned script.
- No CDNs, remote fonts, external images, tracking, fetches, forms, or analytics.
- OpenReview-like red navigation, compact metadata, submission/review cards, score tiles, source-linked note IDs, responsive index, selected-note highlighting, and print styles.
- Every captured note and field remains visible even when its type is unknown.

If the user does not specify a filename, use an English title slug ending in `-openreview.html`, at most 60 characters. If it exists, choose `-v2`, `-v3`, and so on. Never silently overwrite.

### 6. Validate and visually inspect

```bash
python3 scripts/validate_openreview_html.py \
  --input /absolute/path/paper-openreview.html \
  --source /tmp/openreview-normalized.json \
  --screenshot /tmp/openreview-desktop.png \
  --mobile-screenshot /tmp/openreview-mobile.png
```

Validation must establish:

- Every expected forum ID, note ID, source URL, field label, and field value is present.
- Source payloads such as `<script>` and `<img onerror>` remain escaped text.
- No external script, stylesheet, font, image, frame, form, network request, event handler, or unsafe URL is present.
- Headless Chrome renders both desktop and mobile views.

Read both screenshots and inspect title wrapping, card alignment, sidebar/mobile layout, metadata legibility, clipping, overlaps, and raw placeholders. Repair and rerun when anything is wrong. Do not claim full success if structural or visual validation fails.

### 7. Clean up and report

After successful validation, delete the capture JSON, normalized JSON, and screenshots unless debug retention was explicitly requested. Report:

- Absolute HTML path.
- Number and kinds of captured notes.
- A one-line browser command.
- A privacy reminder that the local file may contain private review content.

## Failure rules

- **Verification or login page:** stop and ask the user to finish authentication.
- **Wrong or ambiguous Chrome window:** list candidate IDs/titles; never guess.
- **Missing `$DISPLAY`, X11/XTest, `xclip`, or Linux Chrome:** name the missing dependency and use the documented manual fallback.
- **Native Windows/Wayland-only Chrome:** ask the user to use Linux Chrome under X11/WSLg or provide a manual complete copy plus note URLs.
- **Requested `noteId` absent:** treat the capture as incomplete.
- **Fewer note IDs than note blocks, duplicate IDs, active hidden-content controls, or count mismatch:** stop and recapture or request the missing mappings.
- **Root forum with a confirmed zero-discussion state:** a root-only export is valid.
- **Existing output:** choose a versioned filename; never overwrite silently.

## Files

- `scripts/capture_openreview.py` — authenticated X11/Chrome capture and manual-bundle fallback.
- `scripts/render_openreview.py` — deterministic escaped renderer.
- `scripts/validate_openreview_html.py` — completeness, security, and browser checks.
- `references/capture-workflow.md` — capture mechanics and troubleshooting.
- `references/normalized-thread-schema.md` — intermediate JSON contract.
- `references/components.md` — rendering behavior and presentation hints.
- `references/template.html` — OpenReview-style offline scaffold.
- `assets/example.html` — synthetic completed visual reference.
