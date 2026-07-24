#!/usr/bin/env python3
"""Validate an OpenReview HTML export against normalized source JSON."""

from __future__ import annotations

import argparse
import html.parser
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from render_openreview import RenderError, safe_text_markup, validate_document  # noqa: E402

FORBIDDEN_TAGS = {"iframe", "frame", "object", "embed", "form", "base"}
URL_ATTRS = {"href", "src", "action", "formaction", "poster"}
REMOTE_ASSET_TAGS = {"script", "link", "img", "source", "video", "audio", "track"}
CHROME_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")


class VisibleTextParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)

    @property
    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


class AuditParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.counts: dict[str, int] = {}
        self.note_ids: list[str] = []
        self.hrefs: list[str] = []
        self.has_inline_style = False
        self.csp: str | None = None
        self.selected_note_ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        self.counts[lower] = self.counts.get(lower, 0) + 1
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if lower in FORBIDDEN_TAGS:
            self.errors.append(f"forbidden tag: <{lower}>")
        if lower == "style":
            self.has_inline_style = True
        if lower == "meta" and attr_map.get("http-equiv", "").lower() == "content-security-policy":
            self.csp = attr_map.get("content", "")
        if lower == "article" and "data-note-id" in attr_map:
            self.note_ids.append(attr_map["data-note-id"])
            classes = set(attr_map.get("class", "").split())
            if "selected-note" in classes:
                self.selected_note_ids.append(attr_map["data-note-id"])
        for key, value in attr_map.items():
            if key.startswith("on"):
                self.errors.append(f"inline event handler is forbidden: {key}")
            if key in URL_ATTRS:
                lowered = value.strip().lower()
                if lowered.startswith(("javascript:", "data:text/html", "file:")):
                    self.errors.append(f"unsafe URL in {lower}.{key}: {value}")
        if lower == "a" and "href" in attr_map:
            self.hrefs.append(attr_map["href"])
        if lower in REMOTE_ASSET_TAGS:
            asset = attr_map.get("src") or attr_map.get("href")
            if asset:
                parsed = urlparse(asset)
                if parsed.scheme in {"http", "https"}:
                    self.errors.append(f"external asset is forbidden: <{lower}> {asset}")
                if lower == "img" and not asset.startswith("data:"):
                    self.errors.append(f"non-data image is forbidden: {asset}")


def normalized(value: str) -> str:
    return " ".join(value.split())


def expected_visible(raw: str) -> str:
    parser = VisibleTextParser()
    parser.feed(safe_text_markup(raw))
    parser.close()
    return normalized(parser.text)


def find_chrome() -> str | None:
    for name in CHROME_NAMES:
        path = shutil.which(name)
        if path:
            return path
    return None


def render_screenshot(chrome: str, html_path: Path, screenshot: Path, width: int, height: int) -> str | None:
    if screenshot.exists():
        return f"screenshot already exists: {screenshot}"
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="openreview-html-check-") as profile:
        command = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
            f"--screenshot={screenshot}",
            html_path.as_uri(),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return f"headless Chrome failed: {exc}"
    if result.returncode != 0:
        return f"headless Chrome exited {result.returncode}: {result.stderr.strip()}"
    if not screenshot.is_file() or screenshot.stat().st_size < 1000:
        return "headless Chrome did not produce a non-empty PNG"
    os.chmod(screenshot, 0o600)
    signature = screenshot.read_bytes()[:8]
    if signature != b"\x89PNG\r\n\x1a\n":
        return "screenshot is not a PNG"
    return None


def validate_html(html_path: Path, document: dict, raw_html: str) -> list[str]:
    errors: list[str] = []
    if not re.match(r"(?is)^\s*<!doctype\s+html>", raw_html):
        errors.append("missing HTML doctype")
    parser = AuditParser()
    try:
        parser.feed(raw_html)
        parser.close()
    except html.parser.HTMLParseError as exc:
        errors.append(f"HTML parse error: {exc}")
    errors.extend(parser.errors)
    for tag in ("html", "head", "body", "title", "main"):
        if parser.counts.get(tag, 0) != 1:
            errors.append(f"expected exactly one <{tag}>, found {parser.counts.get(tag, 0)}")
    if not parser.has_inline_style:
        errors.append("missing inline style block")
    if not parser.csp:
        errors.append("missing Content Security Policy meta tag")
    else:
        required = ("default-src 'none'", "connect-src 'none'", "object-src 'none'", "form-action 'none'")
        for directive in required:
            if directive not in parser.csp:
                errors.append(f"CSP missing directive: {directive}")

    visible_parser = VisibleTextParser()
    visible_parser.feed(raw_html)
    visible_parser.close()
    visible = normalized(visible_parser.text)

    source = document["source"]
    submission = document["submission"]
    expected_ids = [note["note_id"] for note in document["notes"]]
    if parser.note_ids != expected_ids:
        errors.append(f"rendered note IDs/order {parser.note_ids!r} do not match source {expected_ids!r}")
    if len(set(parser.note_ids)) != len(parser.note_ids):
        errors.append("duplicate rendered data-note-id")
    if source["selected_note_id"]:
        if parser.selected_note_ids != [source["selected_note_id"]]:
            errors.append("selected note highlighting is missing or applied to the wrong card")
    elif parser.selected_note_ids:
        errors.append("selected note highlighting exists without selected_note_id")

    required_hrefs = [source["canonical_forum_url"], submission["source_url"]]
    required_hrefs.extend(note["source_url"] for note in document["notes"])
    for href in required_hrefs:
        if href not in parser.hrefs:
            errors.append(f"missing source link: {href}")

    expected_strings = [
        source["forum_id"],
        submission["note_id"],
        submission["title"],
        *submission["authors"],
        *submission["metadata"],
    ]
    if submission["visibility"]:
        expected_strings.append(submission["visibility"])
    for link in submission["links"]:
        expected_strings.append(link["label"])
    for field in submission["fields"]:
        expected_strings.extend([field["label"], expected_visible(field["text"])])
    for note in document["notes"]:
        expected_strings.extend([note["note_id"], note["title"]])
        for key in ("signature", "created", "modified", "visibility"):
            if note[key]:
                expected_strings.append(note[key])
        for field in note["fields"]:
            expected_strings.extend([field["label"], expected_visible(field["text"])])

    for value in expected_strings:
        value = normalized(value)
        if value and value not in visible:
            errors.append(f"source text is missing from visible HTML: {value[:100]}")

    if re.search(r"\{\{[A-Z][A-Z0-9_]*\}\}", raw_html):
        errors.append("raw template placeholder remains in HTML")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="rendered HTML")
    parser.add_argument("--source", required=True, help="normalized JSON used by the renderer")
    parser.add_argument("--screenshot", help="new desktop PNG path")
    parser.add_argument("--mobile-screenshot", help="new mobile PNG path")
    parser.add_argument("--skip-browser", action="store_true", help="run structural checks only")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    html_path = Path(args.input).expanduser().resolve()
    source_path = Path(args.source).expanduser().resolve()
    try:
        raw_source = json.loads(source_path.read_text(encoding="utf-8"))
        document = validate_document(raw_source)
        raw_html = html_path.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError, RenderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    errors = validate_html(html_path, document, raw_html)
    rendered: list[Path] = []
    if not args.skip_browser:
        chrome = find_chrome()
        if not chrome:
            errors.append("Linux Chrome/Chromium was not found for browser validation")
        else:
            if args.screenshot:
                screenshot = Path(args.screenshot).expanduser().resolve()
                error = render_screenshot(chrome, html_path, screenshot, 1440, 1200)
                if error:
                    errors.append(error)
                else:
                    rendered.append(screenshot)
            if args.mobile_screenshot:
                screenshot = Path(args.mobile_screenshot).expanduser().resolve()
                # Chrome clamps headless desktop windows to roughly 500 CSS px. This
                # still exercises the narrow/mobile media queries without adding a
                # browser-driver dependency.
                error = render_screenshot(chrome, html_path, screenshot, 500, 844)
                if error:
                    errors.append(error)
                else:
                    rendered.append(screenshot)

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(document['notes'])} notes in {html_path}")
    for screenshot in rendered:
        print(f"Screenshot: {screenshot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
