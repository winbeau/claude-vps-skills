#!/usr/bin/env python3
"""Extract and cache a PDF as bounded, page-labeled context chunks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

CACHE_FORMAT_VERSION = 1


def tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required PDF tool is unavailable: {name}")
    return path


def page_count(pdf: Path) -> int:
    result = subprocess.run(
        [tool("pdfinfo"), str(pdf)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("pdfinfo did not report a page count")
    return int(match.group(1))


def source_key(pdf: Path) -> str:
    return hashlib.sha256(str(pdf).encode("utf-8")).hexdigest()[:16]


def safe_stem(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return value[:60] or "paper"


def split_large_page(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    remaining = text
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit + 1)
        if split_at < limit // 2:
            split_at = limit
        parts.append(remaining[:split_at])
        remaining = remaining[split_at:]
        if remaining.startswith("\n"):
            remaining = remaining[1:]
    parts.append(remaining)
    return parts


def build_units(pages: list[str], max_chars: int) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for page_number, page_text in enumerate(pages, start=1):
        parts = split_large_page(page_text, max_chars)
        for part_number, part_text in enumerate(parts, start=1):
            label = f"=== PDF PAGE {page_number} ==="
            if len(parts) > 1:
                label = f"=== PDF PAGE {page_number} (part {part_number}/{len(parts)}) ==="
            units.append(
                {
                    "page_start": page_number,
                    "page_end": page_number,
                    "text": f"{label}\n{part_text.rstrip()}\n",
                }
            )
    return units


def group_units(units: list[dict[str, Any]], max_chars: int) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_size = 0
    for unit in units:
        unit_size = len(unit["text"])
        if current and current_size + unit_size > max_chars:
            chunks.append(
                {
                    "page_start": current[0]["page_start"],
                    "page_end": current[-1]["page_end"],
                    "body": "\n".join(entry["text"] for entry in current),
                }
            )
            current = []
            current_size = 0
        current.append(unit)
        current_size += unit_size
    if current:
        chunks.append(
            {
                "page_start": current[0]["page_start"],
                "page_end": current[-1]["page_end"],
                "body": "\n".join(entry["text"] for entry in current),
            }
        )
    return chunks


def cached_manifest(
    manifest_path: Path,
    pdf: Path,
    stat: Any,
    max_chars: int,
) -> dict[str, Any] | None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    matches = (
        manifest.get("cache_format_version") == CACHE_FORMAT_VERSION
        and manifest.get("source_path") == str(pdf)
        and manifest.get("source_size") == stat.st_size
        and manifest.get("source_mtime_ns") == stat.st_mtime_ns
        and manifest.get("max_chars") == max_chars
        and manifest.get("complete") is True
    )
    if not matches:
        return None
    if not all(Path(chunk["path"]).is_file() for chunk in manifest.get("chunks", [])):
        return None
    manifest["cached"] = True
    return manifest


def prepare(pdf: Path, cache_root: Path, max_chars: int) -> dict[str, Any]:
    pdf = pdf.expanduser().resolve()
    if not pdf.is_file():
        raise RuntimeError(f"PDF does not exist: {pdf}")
    if max_chars < 4000:
        raise RuntimeError("--max-chars must be at least 4000")

    stat = pdf.stat()
    work_dir = cache_root.expanduser().resolve() / f"{safe_stem(pdf.stem)}-{source_key(pdf)}"
    work_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = work_dir / "manifest.json"
    cached = cached_manifest(manifest_path, pdf, stat, max_chars)
    if cached:
        return cached

    total_pages = page_count(pdf)
    full_text_path = work_dir / "full-text.txt"
    subprocess.run(
        [tool("pdftotext"), "-layout", "-enc", "UTF-8", str(pdf), str(full_text_path)],
        check=True,
        capture_output=True,
    )
    raw_text = full_text_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    pages = raw_text.split("\f")
    if len(pages) == total_pages + 1 and not pages[-1].strip():
        pages.pop()
    if len(pages) != total_pages:
        raise RuntimeError(
            f"Text extraction page mismatch: pdfinfo={total_pages}, extracted={len(pages)}"
        )

    # Reserve room for the per-chunk audit header so every emitted file stays bounded.
    content_limit = max_chars - 256
    chunks = group_units(build_units(pages, content_limit), content_limit)
    for old_chunk in work_dir.glob("chunk-*.txt"):
        old_chunk.unlink()

    chunk_entries = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_path = work_dir / f"chunk-{index:04d}.txt"
        header = (
            f"=== COMPLETE PDF CONTEXT CHUNK {index}/{len(chunks)} | "
            f"PAGES {chunk['page_start']}-{chunk['page_end']} OF {total_pages} ===\n\n"
        )
        chunk_text = header + chunk["body"]
        if len(chunk_text) > max_chars:
            raise RuntimeError(
                f"Context chunk {index} exceeds --max-chars: {len(chunk_text)} > {max_chars}"
            )
        chunk_path.write_text(chunk_text, encoding="utf-8")
        chunk_entries.append(
            {
                "index": index,
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "characters": len(chunk_text),
                "path": str(chunk_path),
            }
        )

    manifest = {
        "status": "ok",
        "cache_format_version": CACHE_FORMAT_VERSION,
        "complete": True,
        "cached": False,
        "source_path": str(pdf),
        "source_size": stat.st_size,
        "source_mtime_ns": stat.st_mtime_ns,
        "page_count": total_pages,
        "extracted_page_count": len(pages),
        "max_chars": max_chars,
        "full_text_path": str(full_text_path),
        "chunk_count": len(chunk_entries),
        "chunks": chunk_entries,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a PDF for complete conversation-context ingestion."
    )
    parser.add_argument("pdf", help="Absolute or relative path to a local PDF")
    parser.add_argument(
        "--cache-dir",
        default="/tmp/zotero-paper-translator",
        help="Cache root (default: /tmp/zotero-paper-translator)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=24000,
        help="Maximum characters per context chunk (default: 24000)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = prepare(Path(args.pdf), Path(args.cache_dir), args.max_chars)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"status": "error", "message": str(error)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
