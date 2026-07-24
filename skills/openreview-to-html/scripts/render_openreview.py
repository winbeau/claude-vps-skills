#!/usr/bin/env python3
"""Render normalized OpenReview JSON as safe self-contained HTML."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
SUBSECTION_RE = re.compile(r"^\\subsection\{([^{}]+)\}\s*(.*)$")
BULLET_RE = re.compile(r"^\s*[-*•]\s+(.+)$")
NUMBER_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
PRESENTATIONS = {"text", "score", "rating", "confidence", "checklist"}
KINDS = {
    "official-review",
    "meta-review",
    "decision",
    "author-response",
    "comment",
    "withdrawal",
    "revision",
    "other",
}


class RenderError(ValueError):
    """Invalid normalized data or unsafe rendering request."""


def text(value: Any, field: str, *, allow_empty: bool = True) -> str:
    if not isinstance(value, str):
        raise RenderError(f"{field} must be a string")
    if not allow_empty and not value.strip():
        raise RenderError(f"{field} must be non-empty")
    return value


def optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return text(value, field)


def validate_id(value: Any, field: str) -> str:
    result = text(value, field, allow_empty=False)
    if not ID_RE.fullmatch(result):
        raise RenderError(f"{field} contains unsupported characters")
    return result


def parse_forum_url(raw: Any, field: str, *, require_note: bool | None = None) -> tuple[str, str | None, str]:
    value = text(raw, field, allow_empty=False)
    parsed = urlparse(value)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != "openreview.net" or parsed.port is not None:
        raise RenderError(f"{field} must use https://openreview.net")
    if parsed.path.rstrip("/") != "/forum" or parsed.fragment:
        raise RenderError(f"{field} must be an OpenReview /forum URL")
    query = parse_qs(parsed.query, keep_blank_values=True)
    if any(len(values) != 1 for values in query.values()):
        raise RenderError(f"{field} contains duplicate query parameters")
    forum_values = query.get("id", [])
    note_values = query.get("noteId", [])
    if len(forum_values) != 1 or not forum_values[0]:
        raise RenderError(f"{field} must contain one forum id")
    forum_id = validate_id(forum_values[0], f"{field}.id")
    note_id = None
    if note_values:
        note_id = validate_id(note_values[0], f"{field}.noteId")
    if require_note is True and not note_id:
        raise RenderError(f"{field} must contain noteId")
    if require_note is False and note_id:
        raise RenderError(f"{field} must not contain noteId")
    canonical = f"https://openreview.net/forum?id={forum_id}"
    if note_id:
        canonical += f"&noteId={note_id}"
    if value != canonical:
        raise RenderError(f"{field} must use canonical query order: {canonical}")
    return forum_id, note_id, value


def safe_http_url(raw: Any, field: str) -> str:
    value = text(raw, field, allow_empty=False)
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise RenderError(f"{field} must be an absolute HTTP(S) URL without credentials")
    return value


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def safe_text_markup(raw: str) -> str:
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_kind: str | None = None

    def flush_paragraph() -> None:
        if paragraph:
            joined = " ".join(piece.strip() for piece in paragraph if piece.strip())
            if joined:
                blocks.append(f"<p>{escape(joined)}</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if list_items and list_kind:
            items = "".join(f"<li>{escape(item)}</li>" for item in list_items)
            blocks.append(f"<{list_kind}>{items}</{list_kind}>")
        list_items.clear()
        list_kind = None

    for line in lines:
        stripped = line.strip()
        subsection = SUBSECTION_RE.match(stripped)
        bullet = BULLET_RE.match(line)
        numbered = NUMBER_RE.match(line)
        if subsection:
            flush_paragraph()
            flush_list()
            blocks.append(f"<h4>{escape(subsection.group(1).strip())}</h4>")
            if subsection.group(2).strip():
                paragraph.append(subsection.group(2).strip())
        elif bullet:
            flush_paragraph()
            if list_kind not in {None, "ul"}:
                flush_list()
            list_kind = "ul"
            list_items.append(bullet.group(1).strip())
        elif numbered:
            flush_paragraph()
            if list_kind not in {None, "ol"}:
                flush_list()
            list_kind = "ol"
            list_items.append(numbered.group(1).strip())
        elif not stripped:
            flush_paragraph()
            flush_list()
        else:
            if list_kind:
                flush_list()
            paragraph.append(stripped)
    flush_paragraph()
    flush_list()
    return "".join(blocks) if blocks else "<p></p>"


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RenderError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise RenderError(f"{field} must be an array")
    return value


def validate_field(raw: Any, path: str) -> dict[str, str]:
    field = require_object(raw, path)
    label = text(field.get("label"), f"{path}.label", allow_empty=False)
    body = text(field.get("text"), f"{path}.text")
    presentation = field.get("presentation", "text")
    if not isinstance(presentation, str) or presentation not in PRESENTATIONS:
        presentation = "text"
    return {"label": label, "text": body, "presentation": presentation}


def validate_document(raw: Any) -> dict[str, Any]:
    document = require_object(raw, "document")
    if document.get("schema_version") != 1:
        raise RenderError("schema_version must be 1")

    source = require_object(document.get("source"), "source")
    forum_id = validate_id(source.get("forum_id"), "source.forum_id")
    source_forum, requested_note, requested_url = parse_forum_url(source.get("requested_url"), "source.requested_url")
    captured_forum, captured_note, captured_url = parse_forum_url(source.get("captured_url"), "source.captured_url")
    canonical_forum, _, canonical_url = parse_forum_url(
        source.get("canonical_forum_url"), "source.canonical_forum_url", require_note=False
    )
    if {source_forum, captured_forum, canonical_forum} != {forum_id}:
        raise RenderError("source URLs must use source.forum_id")
    selected = optional_text(source.get("selected_note_id"), "source.selected_note_id")
    if selected is not None:
        selected = validate_id(selected, "source.selected_note_id")
    if selected != requested_note:
        raise RenderError("source.selected_note_id must match requested_url noteId")
    if requested_note and captured_note != requested_note:
        raise RenderError("captured_url must retain the requested noteId")
    captured_at = text(source.get("captured_at"), "source.captured_at", allow_empty=False)

    submission = require_object(document.get("submission"), "submission")
    submission_id = validate_id(submission.get("note_id"), "submission.note_id")
    submission_forum, _, submission_url = parse_forum_url(
        submission.get("source_url"), "submission.source_url", require_note=False
    )
    if submission_id != forum_id or submission_forum != forum_id:
        raise RenderError("submission must use the root forum ID")
    title = text(submission.get("title"), "submission.title", allow_empty=False)
    authors = [text(item, f"submission.authors[{index}]", allow_empty=False) for index, item in enumerate(require_list(submission.get("authors", []), "submission.authors"))]
    metadata = [text(item, f"submission.metadata[{index}]", allow_empty=False) for index, item in enumerate(require_list(submission.get("metadata", []), "submission.metadata"))]
    visibility = optional_text(submission.get("visibility"), "submission.visibility")
    fields = [validate_field(item, f"submission.fields[{index}]") for index, item in enumerate(require_list(submission.get("fields", []), "submission.fields"))]
    links: list[dict[str, str]] = []
    for index, item in enumerate(require_list(submission.get("links", []), "submission.links")):
        link = require_object(item, f"submission.links[{index}]")
        links.append(
            {
                "label": text(link.get("label"), f"submission.links[{index}].label", allow_empty=False),
                "url": safe_http_url(link.get("url"), f"submission.links[{index}].url"),
            }
        )
    if not any(link["url"] == canonical_url for link in links):
        links.insert(0, {"label": "Open original forum", "url": canonical_url})

    notes: list[dict[str, Any]] = []
    note_ids: set[str] = set()
    for index, raw_note in enumerate(require_list(document.get("notes", []), "notes")):
        path = f"notes[{index}]"
        note = require_object(raw_note, path)
        note_id = validate_id(note.get("note_id"), f"{path}.note_id")
        if note_id in note_ids:
            raise RenderError(f"duplicate note ID: {note_id}")
        note_ids.add(note_id)
        note_forum, url_note, note_url = parse_forum_url(note.get("source_url"), f"{path}.source_url", require_note=True)
        if note_forum != forum_id or url_note != note_id:
            raise RenderError(f"{path}.source_url does not match its forum/note IDs")
        kind = note.get("kind", "other")
        if not isinstance(kind, str) or kind not in KINDS:
            kind = "other"
        notes.append(
            {
                "note_id": note_id,
                "source_url": note_url,
                "kind": kind,
                "title": text(note.get("title"), f"{path}.title", allow_empty=False),
                "signature": optional_text(note.get("signature"), f"{path}.signature"),
                "created": optional_text(note.get("created"), f"{path}.created"),
                "modified": optional_text(note.get("modified"), f"{path}.modified"),
                "visibility": optional_text(note.get("visibility"), f"{path}.visibility"),
                "fields": [
                    validate_field(item, f"{path}.fields[{field_index}]")
                    for field_index, item in enumerate(require_list(note.get("fields", []), f"{path}.fields"))
                ],
            }
        )
    if selected and selected not in note_ids:
        raise RenderError("selected_note_id is not present in notes")

    return {
        "schema_version": 1,
        "source": {
            "requested_url": requested_url,
            "captured_url": captured_url,
            "canonical_forum_url": canonical_url,
            "forum_id": forum_id,
            "selected_note_id": selected,
            "captured_at": captured_at,
        },
        "submission": {
            "note_id": submission_id,
            "source_url": submission_url,
            "title": title,
            "authors": authors,
            "metadata": metadata,
            "visibility": visibility,
            "links": links,
            "fields": fields,
        },
        "notes": notes,
    }


def render_field(field: dict[str, str]) -> str:
    label = escape(field["label"])
    body = safe_text_markup(field["text"])
    presentation = field["presentation"]
    if presentation in {"rating", "confidence"}:
        return f'<div class="callout-field {presentation}"><span class="field-label">{label}:</span><div class="field-content">{body}</div></div>'
    if presentation == "checklist":
        return f'<div class="check-row"><span class="field-label">{label}:</span><div class="field-content">{body}</div></div>'
    return f'<section class="field"><h3>{label}:</h3><div class="field-content">{body}</div></section>'


def render_fields(fields: list[dict[str, str]]) -> str:
    output: list[str] = []
    index = 0
    while index < len(fields):
        if fields[index]["presentation"] == "score":
            scores: list[str] = []
            while index < len(fields) and fields[index]["presentation"] == "score":
                field = fields[index]
                scores.append(
                    '<div class="score">'
                    f'<div class="score-label">{escape(field["label"])}</div>'
                    f'<div class="score-value">{escape(field["text"])}</div>'
                    "</div>"
                )
                index += 1
            output.append('<div class="score-grid">' + "".join(scores) + "</div>")
            continue
        output.append(render_field(fields[index]))
        index += 1
    return "".join(output)


def anchor_id(note_id: str) -> str:
    return f"note-{note_id}"


def render_submission(submission: dict[str, Any]) -> str:
    author_html = ", ".join(escape(author) for author in submission["authors"])
    metadata_html = "".join(f"<span>{escape(item)}</span>" for item in submission["metadata"])
    visibility_html = (
        f'<div class="visibility">{escape(submission["visibility"])}</div>' if submission["visibility"] else ""
    )
    link_html = []
    for index, link in enumerate(submission["links"]):
        primary = " primary" if index == 0 else ""
        link_html.append(
            f'<a class="source-button{primary}" href="{escape(link["url"])}" rel="noopener noreferrer">{escape(link["label"])}</a>'
        )
    return (
        '<article class="submission" id="submission">'
        f'<div class="submission-id">FORUM · <a href="{escape(submission["source_url"])}" rel="noopener noreferrer">{escape(submission["note_id"])}</a></div>'
        f'<h1><a href="{escape(submission["source_url"])}" rel="noopener noreferrer">{escape(submission["title"])}</a></h1>'
        f'<div class="authors">{author_html}</div>'
        f'<div class="metadata">{metadata_html}</div>'
        f'{visibility_html}<div class="source-links">{"".join(link_html)}</div>'
        f'{render_fields(submission["fields"])}</article>'
    )


def render_note(note: dict[str, Any], selected_id: str | None) -> str:
    selected = note["note_id"] == selected_id
    classes = f'note-card {note["kind"]}' + (" selected-note" if selected else "")
    badge = '<span class="selected-badge">selected source note</span>' if selected else ""
    metadata = []
    if note["signature"]:
        metadata.append(note["signature"])
    if note["created"]:
        metadata.append(note["created"])
    if note["modified"]:
        metadata.append(f'modified {note["modified"]}')
    metadata_html = "".join(f"<span>{escape(item)}</span>" for item in metadata)
    visibility_html = f'<div class="visibility">{escape(note["visibility"])}</div>' if note["visibility"] else ""
    return (
        f'<article class="{classes}" id="{anchor_id(note["note_id"])}" data-note-id="{escape(note["note_id"])}">'
        '<header class="note-head">'
        f'<h2 class="note-title">{escape(note["title"])}{badge}</h2>'
        f'<div class="note-meta">{metadata_html}</div>{visibility_html}'
        f'<a class="note-id" href="{escape(note["source_url"])}" rel="noopener noreferrer">{escape(note["note_id"])}</a>'
        '</header><div class="note-body">'
        f'{render_fields(note["fields"])}</div></article>'
    )


def render_index(document: dict[str, Any]) -> str:
    entries = ['<a href="#submission">Submission overview <span class="index-kind">root</span></a>']
    for note in document["notes"]:
        short_title = note["signature"] or note["title"]
        entries.append(
            f'<a href="#{anchor_id(note["note_id"])}">{escape(short_title)} <span class="index-kind">{escape(note["kind"].replace("-", " "))}</span></a>'
        )
    return "".join(entries)


def render_document(document: dict[str, Any], template: str) -> str:
    submission = document["submission"]
    source = document["source"]
    notes_html = "".join(render_note(note, source["selected_note_id"]) for note in document["notes"])
    replacements = {
        "{{DOCUMENT_TITLE}}": escape(f'{submission["title"]} | OpenReview export'),
        "{{FORUM_URL}}": escape(source["canonical_forum_url"]),
        "{{SUBMISSION_HTML}}": render_submission(submission),
        "{{NOTE_COUNT}}": str(len(document["notes"])),
        "{{NOTE_NOUN}}": "note" if len(document["notes"]) == 1 else "notes",
        "{{NOTES_HTML}}": notes_html,
        "{{CAPTURED_AT}}": escape(source["captured_at"]),
        "{{FORUM_ID}}": escape(source["forum_id"]),
        "{{CAPTURED_URL}}": escape(source["captured_url"]),
        "{{CAPTURED_URL_TEXT}}": escape(source["captured_url"]),
        "{{INDEX_HTML}}": render_index(document),
    }
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    leftovers = PLACEHOLDER_RE.findall(result)
    if leftovers:
        raise RenderError(f"unresolved template placeholders: {', '.join(sorted(set(leftovers)))}")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="normalized JSON file")
    parser.add_argument("--output", required=True, help="new HTML file; existing files are refused")
    parser.add_argument("--template", help="template path; defaults to ../references/template.html")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    template_path = (
        Path(args.template).expanduser().resolve()
        if args.template
        else Path(__file__).resolve().parents[1] / "references" / "template.html"
    )
    if output_path.exists():
        print(f"error: output already exists: {output_path}", file=sys.stderr)
        return 2
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
        document = validate_document(raw)
        template = template_path.read_text(encoding="utf-8")
        rendered = render_document(document, template)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        flags = output_path.open("x", encoding="utf-8")
        try:
            flags.write(rendered)
            flags.write("\n")
        finally:
            flags.close()
    except (OSError, json.JSONDecodeError, RenderError) as exc:
        try:
            if output_path.exists() and output_path.stat().st_size == 0:
                output_path.unlink()
        except OSError:
            pass
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Rendered {len(document['notes'])} notes to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
