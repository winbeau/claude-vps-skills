# Rendering components

`render_openreview.py` owns all markup. The normalized source contains plain text only.

## Submission card

Contains:

- Linked title and visible forum ID.
- Authors.
- Compact ordered metadata.
- Visibility when present.
- Validated source links.
- Ordered submission fields.

## Discussion note card

Each note card includes:

- `data-note-id` containing the validated note ID.
- A linked visible note ID.
- Source title, signature, created/modified timestamps, and visibility.
- Every field in source order.
- A visual kind modifier (`official-review`, `meta-review`, `decision`, `author-response`, `comment`, or generic).
- A `selected-note` modifier when it matches `source.selected_note_id`.

## Field rendering

### Generic text

```html
<section class="field">
  <h3>Escaped label</h3>
  <div class="field-content">safe formatted text</div>
</section>
```

### Consecutive scores

Adjacent `presentation: score` fields are grouped into one score grid. The complete original value stays visible.

### Rating and confidence

`rating` and `confidence` use emphasized callouts, with the original label and complete value preserved.

### Checklist

`checklist` uses a compact two-column row on desktop and one column on narrow screens.

## Safe text formatter

Allowed transformations are intentionally small:

- Escape all source text first.
- Convert blank-line blocks into paragraphs.
- Convert unambiguous consecutive bullet lines into `<ul>`.
- Convert unambiguous consecutive numbered lines into `<ol>`.
- Convert `\\subsection{...}` markers into escaped `<h4>` headings.
- Convert remaining single newlines inside a paragraph to spaces.

Do not implement arbitrary Markdown, raw HTML, autolinking, images, embeds, or source-controlled classes.

## Visual system

The template uses an OpenReview-like system without remote resources:

- Deep red navigation and review accent.
- Near-white page background.
- White bordered cards.
- Dark blue-gray headings.
- Muted compact sans-serif metadata.
- A responsive discussion index.
- Distinct restrained accent colors for meta-reviews, decisions, author responses, and comments.
- Desktop/mobile and print styles.

The top bar links to OpenReview. It does not include a fake working search form or controls that imply unsaved interaction.

## Offline security

The template includes a restrictive CSP and must contain no external resources. The only script is template-owned scrollspy behavior. Source strings never enter that script and no `innerHTML` assignment is used.
