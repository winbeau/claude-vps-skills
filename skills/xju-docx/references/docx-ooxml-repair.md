# DOCX OOXML Repair Playbook

Use this when Word opens a generated/edited `.docx` with a repair warning such as "发现无法读取的内容", or when images/captions fail after programmatic edits.

## Diagnosis

- Treat WSL path conversion as a separate concern: `/mnt/c/...` and `C:\...` point to the same file, but Word repair popups usually mean package/OOXML structure risk, not merely a path issue.
- Preserve the broken file for comparison; do not keep patching it in place.
- Run package preflight on the clean base, broken output, and candidate fix:

```bash
python3 scripts/check_docx_package.py clean.docx broken.docx candidate.docx
```

The script checks zip integrity, XML parseability, missing relationship targets, external links, temp clipboard paths, and obvious metadata damage. Passing this check is necessary but not sufficient; Word open without repair is the final check.

## Safe Rebuild Pattern

1. Start from the earliest Word-openable `.docx` backup or the user original.
2. Write a small manifest of intended logical changes: captions, headings, TOC rows, figure mapping, image replacements.
3. Patch the smallest necessary OOXML part. For caption/heading/TOC text edits, prefer touching only `word/document.xml`.
4. Copy every unchanged zip entry byte-for-byte from the clean base. Preserve relationship files, media, `[Content_Types].xml`, and `docProps/*` unless a specific change requires them.
5. Avoid whole-document XML serializer round trips when Word fields, bookmarks, TOC hyperlinks, or drawing markup must be preserved. Use targeted paragraph/string replacement that keeps existing XML scaffolding.
6. Never run broad text replacements across the package. A replacement like `Temp -> ""` can corrupt `<Template>` into `<late>` and make Word repair the document.
7. If a picture paragraph also contains a caption, keep the run containing `<w:drawing>` or `<w:pict>`, remove caption text runs from that paragraph, and insert a separate caption paragraph cloned from a known-good caption style.
8. When inserting TOC/body headings, clone a nearby same-style paragraph, update visible text, and retarget bookmarks/anchors to unique IDs/names.

## Verification Loop

Run these checks before handing the file to the user:

```bash
python3 scripts/check_docx_package.py candidate.docx
```

Then inspect the candidate logically:

- Figure captions count and order match the manifest.
- Chapter/section numbers are unique and do not over-shift later chapters.
- `word/_rels/document.xml.rels` has no unexpected external image links.
- Referenced media files exist under `word/media/`.
- `docProps/app.xml` still has `<Template>Normal.dotm</Template>` when present.

Finally, open the file in Word/WPS. If Word still reports unreadable content, reduce the patch scope and bisect from the clean base. Use Word's Open and Repair only as a last-resort salvage step, then save under a new filename and re-run package preflight.
