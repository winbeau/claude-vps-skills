# Normalized thread schema

The renderer consumes UTF-8 JSON. Source order is significant: preserve `metadata`, `fields`, `links`, and `notes` in the order shown by OpenReview.

## Document

```json
{
  "schema_version": 1,
  "source": {
    "requested_url": "https://openreview.net/forum?id=forum123&noteId=note456",
    "captured_url": "https://openreview.net/forum?id=forum123&noteId=note456",
    "canonical_forum_url": "https://openreview.net/forum?id=forum123",
    "forum_id": "forum123",
    "selected_note_id": "note456",
    "captured_at": "2026-07-24T17:30:00+00:00"
  },
  "submission": {
    "note_id": "forum123",
    "source_url": "https://openreview.net/forum?id=forum123",
    "title": "A Fictional Submission",
    "authors": ["Ada Example", "Lin Sample"],
    "metadata": ["01 MAY 2026", "VENUE SUBMISSION"],
    "visibility": "Conference, Authors, Reviewers",
    "links": [
      {"label": "Open original forum", "url": "https://openreview.net/forum?id=forum123"}
    ],
    "fields": [
      {"label": "TL;DR", "text": "Short source text.", "presentation": "text"},
      {"label": "Abstract", "text": "Full source text.", "presentation": "text"}
    ]
  },
  "notes": [
    {
      "note_id": "note456",
      "source_url": "https://openreview.net/forum?id=forum123&noteId=note456",
      "kind": "official-review",
      "title": "Official Review by Reviewer A1b2",
      "signature": "Reviewer A1b2",
      "created": "26 Jun 2026, 01:00",
      "modified": "23 Jul 2026, 22:21",
      "visibility": "Program Chairs, Area Chairs, Authors, Reviewer A1b2",
      "fields": [
        {"label": "Summary", "text": "Review text.", "presentation": "text"},
        {"label": "Quality", "text": "4: excellent", "presentation": "score"},
        {"label": "Rating", "text": "4: Borderline accept: ...", "presentation": "rating"}
      ]
    }
  ]
}
```

## Required invariants

- `schema_version` is integer `1`.
- `source.forum_id` is non-empty and contains only OpenReview ID characters: letters, digits, `_`, and `-`.
- `source.canonical_forum_url` and `submission.source_url` are the exact canonical HTTPS forum URL.
- `source.selected_note_id` is a string or `null`.
- `submission.note_id` equals `source.forum_id`.
- Every note ID is non-empty and unique.
- Every note source URL is HTTPS, host `openreview.net`, path `/forum`, and contains exactly the document forum ID plus that note's ID.
- Every field has a non-empty `label` and string `text`.
- Unknown kinds, field labels, and presentation hints are permitted. The renderer falls back to generic note/field styling.

## Supported note kinds

Kinds are presentation hints, not a closed content schema:

- `official-review`
- `meta-review`
- `decision`
- `author-response`
- `comment`
- `withdrawal`
- `revision`
- `other`

Unknown strings are rendered as `other`; their content is never discarded.

## Supported field presentations

- `text` — normal paragraphs/lists/subsections.
- `score` — compact score tile. Adjacent score fields are grouped.
- `rating` — emphasized rating callout.
- `confidence` — emphasized confidence callout.
- `checklist` — compact label/value row.

Missing or unknown hints use `text`.

## Text preservation

Store plain source text, not HTML. Keep blank lines between natural paragraphs and list items. The safe renderer recognizes only:

- Blank-line-separated paragraphs.
- Consecutive lines beginning with `- `, `* `, or `• ` as bullets.
- Consecutive lines beginning with `1. `, `2. `, and so on as numbered items.
- `\\subsection{Title}` as an escaped subheading marker.

Everything else remains escaped paragraph text. Do not place source strings in CSS, JavaScript, tag names, or attribute names.

## Mapping discipline

Build a note inventory before creating this file. Each visible note block must map to one and only one `note_id`/`source_url`. Do not map by reviewer initials alone when several candidates exist. Stop and ask for missing note URLs when the capture cannot establish a one-to-one mapping.
