# OpenReview to HTML

`openreview-to-html` exports an OpenReview submission and its complete visible discussion from an authenticated interactive Chrome session into one portable HTML file that resembles the OpenReview forum layout.

## Typical request

```text
使用 $openreview-to-html 把这些 OpenReview review 链接整理成一个和 OpenReview 样式一致的 HTML。
```

Supported URLs:

```text
https://openreview.net/forum?id=<forum-id>
https://openreview.net/forum?id=<forum-id>&noteId=<note-id>
```

Multiple links from one forum are accepted. The Skill captures the complete forum once and retains all requested note IDs and links.

## Authentication flow

OpenReview may require Turnstile verification or login before it shows reviews. The Skill does not bypass this check and never requests credentials.

1. The Skill opens the requested URL in interactive Linux Chrome.
2. You complete verification or login in the browser.
3. Expand any hidden or collapsed replies and wait for the complete discussion.
4. Tell the Skill that the page is ready.
5. The Skill verifies the active URL, copies the rendered page through X11, normalizes every visible note, and renders the export.

The export includes the root submission and visible official reviews, comments, author responses, meta-reviews, decisions, and unknown note types. It preserves note IDs, source links, field order, pseudonyms, timestamps, visibility text, ratings, confidence, and checklist fields without rewriting the prose.

## Prerequisites

The automatic capture path is intended for Linux or WSLg:

- Python 3
- Linux Chrome (`google-chrome`, `google-chrome-stable`, `chromium`, or `chromium-browser`)
- An X11 display in `$DISPLAY`
- `xclip`
- `libX11.so.6`
- `libXtst.so.6`

The Skill does not read browser cookie databases, clone profiles, enable remote debugging, or save storage state.

## Multiple Chrome windows

If several OpenReview windows match, the Skill stops rather than guessing:

```bash
python3 skills/openreview-to-html/scripts/capture_openreview.py windows
```

Then it captures the chosen window by ID:

```bash
python3 skills/openreview-to-html/scripts/capture_openreview.py capture \
  --expected-url 'https://openreview.net/forum?id=...' \
  --window-id 0x60000b \
  --output /tmp/openreview-capture.json
```

## Manual fallback

When X11/WSLg automation is unavailable, copy the complete visible forum text into a file and provide the root and note URLs:

```bash
python3 skills/openreview-to-html/scripts/capture_openreview.py manual \
  --source-url 'https://openreview.net/forum?id=...' \
  --text-file /absolute/complete-forum.txt \
  --note-url 'https://openreview.net/forum?id=...&noteId=...' \
  --output /tmp/openreview-capture.json
```

A text copy without note URLs may be insufficient because the Skill must never invent note IDs. It asks only for mappings that remain unresolved.

## Output

The output is one `.html` file with inline CSS and a small inline navigation script. It uses no CDNs, remote fonts, images, analytics, or network requests. The renderer escapes source text and includes a restrictive offline Content Security Policy.

When no path is requested, the Skill derives an English title slug ending in `-openreview.html`. Existing files are not overwritten; `-v2`, `-v3`, and later suffixes are used.

## Validation

Before reporting success, the Skill checks the HTML against normalized source JSON and renders desktop and mobile screenshots in headless Chrome. It verifies that every expected field, ID, and source URL is present and that no source content became executable markup.

## Privacy

An exported file may contain reviews that were visible only because you were logged in. The local HTML has no OpenReview access control. Treat it like any other private document and review recipients before sharing it.

Temporary capture files and screenshots also contain review text. The Skill creates them with restrictive permissions and removes them after successful validation unless you explicitly request debug retention.
