---
name: zotero-paper-translator
description: Locate papers in a local Zotero library from a collection/folder path plus a paper title or alias, load the complete PDF text into the active conversation context, then read and translate requested sections with strict paragraph-by-paragraph source/Chinese alignment. Use when the user refers to a paper by phrases such as "Notion 文件夹中的 MatrixGame", asks to find/open/read/translate a paper in a named or nested Zotero collection, requests 摘要/Introduction/章节的中英对照翻译, or follows up about another passage in the same Zotero paper. Require the collection path, paper identifier, and requested scope for a new translation task; ask when any is missing or ambiguous.
---

# Zotero Paper Translator

Resolve the intended Zotero item before reading it. For translation, preserve the PDF's natural paragraphs and always pair each complete source paragraph with its complete Chinese translation.

## Required Inputs

Identify three inputs from the request:

1. **Collection path**: a top-level or nested Zotero collection, for example `Notion` or `Research/World Models`.
2. **Paper identifier**: title, recognizable title fragment, alias, DOI, arXiv ID, or Zotero item key.
3. **Reading scope**: section names, page range, or another precise boundary. Treat "摘要到 Introduction" as the Abstract plus the entire Introduction, ending before the next numbered section.

Ask a concise question before searching if the collection path or paper identifier is absent. Ask for the desired section/page range before translating if the reading scope is absent. Do not infer a collection from an unrelated working-directory name.

## Locate the Item

1. Read and follow the available `Zotero:Zotero` skill for Zotero access. Read and follow the available PDF skill before extracting a PDF whose layout affects paragraph order.
2. Start with the Zotero helper's read-only `status --json`. Use its collection, search, children, full-text, and file-URL routes when the local API is enabled.
3. Resolve every segment of a nested collection path. Search inside that collection, not merely across the whole library. An alias such as `MatrixGame1.0` may fuzzy-match an official title such as `Matrix-Game: Interactive World Foundation Model`, but never conceal the resolved title from the user.
4. If the local API is disabled, inaccessible from WSL, or insufficient for nested paths, run the bundled read-only fallback:

   ```bash
   python3 scripts/locate_zotero_paper.py \
     --collection-path 'Notion' \
     --title 'MatrixGame1.0' \
     --json
   ```

   Resolve `scripts/` relative to this `SKILL.md`. Add `--data-dir /path/to/Zotero` only when auto-discovery reports multiple or no data directories. Add `--recursive` only when the user means a collection and all its descendants.
5. If the requested item is not in the stated collection, report that fact. A global-library match is diagnostic, not permission to silently use an item from another collection.
6. For multiple collection, item, or PDF matches, list concise candidates with collection path, full title, authors/year, item key, and attachment filename as available; ask the user to choose. Do not select by guesswork.
7. Prefer the main article PDF. Do not substitute an HTML snapshot, supplementary file, earlier version, or similarly named paper without confirmation.

All ordinary lookup and reading actions are read-only. Do not import, move, edit, tag, delete, or sync Zotero records unless the user explicitly requests that write; then follow the Zotero skill's confirmation rules.

## Load the Complete PDF into Context

When the user requests translation, load the complete PDF text into the active conversation context **before translating the requested scope**. This is mandatory even when the user initially asks for only one section, because later questions may refer to any other passage.

1. Prepare a stable, page-aware context cache with the bundled helper. It runs `pdfinfo`, extracts every page with layout preserved, checks the extracted page count, and writes bounded chunks plus a JSON manifest:

   ```bash
   python3 scripts/prepare_pdf_context.py '/absolute/paper.pdf'
   ```

   Resolve `scripts/` relative to this `SKILL.md`. Reuse a manifest with `cached: true`; it represents the same source path, size, modification time, and chunk size.
2. Read every `chunks[].path` from the manifest into the conversation in index order, from the first page through EOF. Multiple bounded chunks may be read in ordered parallel batches for speed. Keep each batch below the tool output limit and verify that no call reports truncation.
3. Compare the ingested chunk indices with `chunk_count`, and confirm that the last chunk's `page_end` equals `page_count`. Continue until every chunk has actually been returned to the model; creating the cache or reading only its manifest does not count as loading the PDF into context.
4. Retain the chunk manifest and page labels so later quotations can be checked against the correct page. Keep the cache for fast recovery after context compaction, but treat it only as a cache, not as a substitute for ingestion.
5. Do not paste the whole PDF into the visible response. Briefly report the loaded page and chunk counts, then give the requested aligned translation.
6. If extraction is incomplete because the PDF is scanned, perform OCR using the PDF skill, build equivalent page-labeled chunks, and load them in the same first-page-to-EOF sequence. Mark uncertain OCR passages.
7. If the complete text cannot fit because of a hard context limit, do not claim that it was fully loaded. State the exact limitation and ask whether to proceed with a complete local text index plus on-demand chunk loading.

On follow-up requests about the same paper, use the already loaded full text and page map. Re-open the cached chunk only if the relevant source text is no longer present after context compaction, and verify it visually when layout affects interpretation.

## Establish Section Boundaries

1. Inspect PDF metadata and extracted text, then render the relevant pages for visual verification. Do not trust extraction order alone for multi-column pages, figures, footnotes, or page-spanning paragraphs.
2. Determine the exact first and last headings before translating. Stop before the next peer-level section when the user names a section rather than pages.
3. Preserve natural paragraph boundaries. Join only line wraps, page breaks within one paragraph, and typographic line-end hyphenation such as `mod-` + `els` -> `models`.
4. Exclude author footnotes, headers, footers, figure/table captions, and marginal text unless the user includes them in scope. Say briefly what was excluded when it could otherwise be mistaken for body text.
5. Preserve citations, equations, URLs, figure/table references, symbols, and proper names. Never silently paraphrase or summarize the source paragraph.

## Translate in Strict Alignment

Translate every requested natural paragraph in order using exactly this pattern:

```markdown
**摘要（Abstract）**

原文：

> Complete source paragraph, with PDF line wraps repaired.

译文：

完整、忠实、自然的中文段落。

**Introduction：第 1 段**

原文：

> Complete source paragraph.

译文：

完整中文译文。
```

The alignment contract is mandatory:

- Put the original first and the translation immediately after it.
- Use one source paragraph and one translated paragraph per unit. Do not merge separate source paragraphs or split one source paragraph merely for style.
- Include the full source paragraph, not only its first sentence or an excerpt.
- Translate faithfully rather than adding explanations, claims, or a summary. Put requested commentary after the aligned translation and label it separately.
- Keep citation markers attached to the claims they support.
- Use consistent technical terminology across the requested scope. Prefer established Chinese research usage, for example `world model` -> `世界模型`, `temporal coherence` -> `时序连贯性`, and `action controllability` -> `动作可控性`; adjust when the paper defines a specialized term.
- Retain model, dataset, benchmark, and product names in their official form unless an established translation exists.

For a long scope, continue in section-sized blocks without replacing untranslated material with a summary. Clearly state the completed boundary if a response must be split.

## Present the Result

Start with one sentence confirming the resolved collection path, official paper title, and a clickable absolute link to the local PDF when available. Then provide the aligned translation directly. Mention extraction ambiguities or repaired OCR only when material; do not burden a clean result with tool logs.
