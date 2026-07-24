# Zotero Paper Translator

`zotero-paper-translator` locates a paper from its Zotero collection path and title, loads the complete PDF text into the active conversation, and translates the requested scope with strict source-to-translation paragraph alignment.

## Typical request

```text
使用 $zotero-paper-translator 翻译 Zotero 中 Notion 文件夹里的 MatrixGame1.0，从摘要到 Introduction，附带原文。
```

Provide three pieces of information:

- Zotero collection path, such as `Notion` or `Research/World Models`.
- Paper title, alias, DOI, arXiv ID, or Zotero item key.
- Section or page range to translate.

The Skill asks for missing information and lists candidates when a collection, paper, or PDF is ambiguous. It does not silently choose among similarly named versions.

## Translation behavior

Before translating, the Skill extracts and ingests the complete PDF in page-labeled chunks. It caches the extraction for later questions about other passages, while still requiring every chunk to enter the active conversation before claiming that the full paper is loaded.

Each natural paragraph is returned in this order:

```text
原文：
<complete source paragraph>

译文：
<complete Chinese translation>
```

Body paragraphs are kept separate. Figure captions, author footnotes, headers, and the next peer-level section are excluded unless explicitly requested.

## Read-only lookup

The normal workflow uses Zotero's local read-only API. If that API is disabled or unavailable from WSL, `scripts/locate_zotero_paper.py` reads `zotero.sqlite` in query-only mode and resolves local PDF attachments without changing the library.

```bash
python3 skills/zotero-paper-translator/scripts/locate_zotero_paper.py \
  --collection-path Notion \
  --title MatrixGame1.0 \
  --json
```

`scripts/prepare_pdf_context.py` creates a page-validated context manifest and bounded text chunks:

```bash
python3 skills/zotero-paper-translator/scripts/prepare_pdf_context.py \
  /absolute/path/to/paper.pdf
```

Zotero writes such as importing, moving, tagging, or deleting records remain outside the default workflow and require an explicit user request.
