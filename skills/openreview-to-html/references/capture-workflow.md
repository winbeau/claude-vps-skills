# Authenticated capture workflow

OpenReview may put both the website and API behind a Turnstile challenge. This Skill does not bypass it. It opens an ordinary interactive Linux Chrome window, waits for the user to complete verification or login, then copies the rendered page through X11 keyboard automation.

## Prerequisites

- Linux or WSLg desktop with `$DISPLAY` available.
- Linux `google-chrome`, `google-chrome-stable`, `chromium`, or `chromium-browser`.
- `xclip`.
- X11 and XTest shared libraries (`libX11.so.6`, `libXtst.so.6`).
- Python 3 standard library.

The helper deliberately does not use a custom browser profile, remote-debugging port, Selenium, Playwright, cookies, or browser database files.

## Normal flow

```bash
python3 scripts/capture_openreview.py launch "$URL"
```

After the user says the page is fully loaded:

```bash
python3 scripts/capture_openreview.py capture \
  --expected-url "$URL" \
  --note-url "$OTHER_NOTE_URL" \
  --output /tmp/openreview-capture.json
```

Repeat `--note-url` for the other OpenReview links supplied by the user. This is especially important when the browser's rich clipboard does not expose anchor targets.

The capture sequence is keyboard-only:

1. Enumerate visible X11 Chrome windows whose title indicates OpenReview.
2. Activate the unambiguous target window.
3. Send `Ctrl+L`, then `Ctrl+C` and validate the clipboard URL.
4. Send `Escape` to return to the document.
5. Send `Ctrl+A`, then `Ctrl+C`.
6. Read `text/plain` and, when available, `text/html` clipboard targets.
7. Keep the plain page text and a sanitized inventory of `https://openreview.net/forum` links. Discard the rich clipboard HTML.

Use `--focus-delay`, `--copy-delay`, or `--window-id` when WSLg timing or multiple windows require it.

## Completeness checks

Capture is rejected when:

- The page says `Verifying your browser`, asks to complete the check, or shows a login form instead of the forum.
- The active URL is not the expected forum.
- The copied value is only an email address, URL, or stale short clipboard string.
- The requested `noteId` is absent from both the page text and captured note links.
- The page still displays `Load more`, `Show more replies`, `View more replies`, or `Expand replies`.
- A reliable `N / N replies shown` marker does not match the number of recognizable top-level discussion headings.
- The copied page lacks an OpenReview marker, a paper title region, or enough content to be plausible.

OpenReview forms and wording change, so the model still verifies the normalized note inventory after capture. Script checks are a guardrail, not permission to guess.

## Multiple-window recovery

```bash
python3 scripts/capture_openreview.py windows
```

Example:

```text
0x60000b  Example Submission ... | OpenReview - Google Chrome
0xa00012  Another Paper ... | OpenReview - Google Chrome
```

Rerun capture with the exact window ID. Never choose one arbitrarily.

## Manual fallback

Use this only when X11 capture is unavailable.

1. Ask the user to copy the complete visible forum text after expanding all discussion controls.
2. Require the exact root forum URL.
3. Require the exact URL for every discussion note if note IDs are not otherwise available.
4. Create a capture bundle manually with:

```bash
python3 scripts/capture_openreview.py manual \
  --source-url "$URL" \
  --text-file /absolute/complete-forum.txt \
  --note-url 'https://openreview.net/forum?id=...&noteId=...' \
  --note-url 'https://openreview.net/forum?id=...&noteId=...' \
  --output /tmp/openreview-capture.json
```

Pasted text alone is insufficient when it cannot prove which note ID belongs to each block. Ask for unresolved URLs instead of fabricating IDs.

## Privacy

The capture JSON contains the visible discussion and may be private. It is written with mode `0600`. It never contains cookies, tokens, profile paths, storage state, headers, or raw live HTML. Delete it after the final HTML has been validated unless the user explicitly requests debug retention.
