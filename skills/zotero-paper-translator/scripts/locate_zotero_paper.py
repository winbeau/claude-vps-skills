#!/usr/bin/env python3
"""Locate a Zotero paper and its PDF by collection path using read-only SQLite."""

from __future__ import annotations

import argparse
import difflib
import glob
import json
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path, PureWindowsPath
from typing import Any


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(value.split())


def compact(value: str) -> str:
    return "".join(char for char in normalized(value) if char.isalnum())


def query_core(value: str) -> str:
    value = normalized(value)
    value = re.sub(r"\s*(?:v(?:ersion)?\s*)?\d+(?:\.\d+)+\s*$", "", value)
    return compact(value)


def query_version(value: str) -> str | None:
    match = re.search(r"(?:v(?:ersion)?\s*)?(\d+(?:\.\d+)+)\s*$", normalized(value))
    return match.group(1) if match else None


def title_versions(value: str) -> list[str]:
    return re.findall(r"(?<!\d)(\d+(?:\.\d+)+)(?!\d)", normalized(value))


def windows_to_posix(value: str) -> Path:
    expanded = os.path.expandvars(value)
    match = re.match(r"^([A-Za-z]):[\\/](.*)$", expanded)
    if match and Path("/mnt").exists():
        drive, rest = match.groups()
        return Path("/mnt") / drive.lower() / Path(*PureWindowsPath(rest).parts)
    return Path(expanded).expanduser()


def read_pref(prefs_file: Path, pref_name: str) -> str | None:
    try:
        text = prefs_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    pattern = rf'user_pref\(\s*"{re.escape(pref_name)}"\s*,\s*("(?:\\.|[^"\\])*")\s*\)'
    match = re.search(pattern, text)
    if not match:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, str) else None


def profile_candidates() -> list[Path]:
    patterns = [
        Path.home() / ".zotero/zotero/*/prefs.js",
        Path.home() / ".config/zotero/*/prefs.js",
        Path.home() / "Library/Application Support/Zotero/Profiles/*/prefs.js",
    ]
    for drive in "cdefghijklmnopqrstuvwxyz":
        patterns.append(Path(f"/mnt/{drive}/Users/*/AppData/Roaming/Zotero/Zotero/Profiles/*/prefs.js"))
    found: list[Path] = []
    for pattern in patterns:
        found.extend(Path(match) for match in glob.glob(str(pattern)))
    return sorted({path.resolve() for path in found if path.is_file()})


def profile_default_data_dir(prefs_file: Path) -> Path | None:
    parts = prefs_file.parts
    try:
        users_index = parts.index("Users")
        return Path(*parts[: users_index + 2]) / "Zotero"
    except ValueError:
        return Path.home() / "Zotero"


def discover_base_attachment_dir() -> Path | None:
    for prefs_file in profile_candidates():
        configured = read_pref(prefs_file, "extensions.zotero.baseAttachmentPath")
        if configured:
            return windows_to_posix(configured).resolve()
    return None


def discover_data_dirs(explicit: str | None) -> list[Path]:
    if explicit:
        return [windows_to_posix(explicit).resolve()]

    env_dir = os.environ.get("ZOTERO_DATA_DIR")
    if env_dir:
        return [windows_to_posix(env_dir).resolve()]

    preferred: list[Path] = []
    defaults: list[Path] = []
    for prefs_file in profile_candidates():
        configured = read_pref(prefs_file, "extensions.zotero.dataDir")
        if configured:
            preferred.append(windows_to_posix(configured))
        else:
            default = profile_default_data_dir(prefs_file)
            if default:
                defaults.append(default)

    for candidates in (preferred, defaults, [Path.home() / "Zotero"]):
        valid = sorted(
            {path.resolve() for path in candidates if (path / "zotero.sqlite").is_file()}
        )
        if valid:
            return valid
    return []


def split_collection_path(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*(?:/|>)\s*", value.strip(" />")) if part.strip()]


def collection_path(row: sqlite3.Row, by_id: dict[int, sqlite3.Row]) -> list[str]:
    names: list[str] = []
    seen: set[int] = set()
    current: sqlite3.Row | None = row
    while current is not None:
        collection_id = int(current["collectionID"])
        if collection_id in seen:
            break
        seen.add(collection_id)
        names.append(str(current["collectionName"]))
        parent_id = current["parentCollectionID"]
        current = by_id.get(int(parent_id)) if parent_id is not None else None
    return list(reversed(names))


def canonical_identifier(value: str) -> str:
    value = normalized(value)
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "https://arxiv.org/abs/", "arxiv:"):
        if value.startswith(prefix):
            value = value.removeprefix(prefix).strip()
    return value


def similarity(query: str, title: str, key: str, doi: str | None) -> float:
    if normalized(query) == normalized(key):
        return 1.0
    if doi:
        query_identifier = canonical_identifier(query)
        doi_identifier = canonical_identifier(doi)
        if query_identifier == doi_identifier:
            return 1.0
        if re.fullmatch(r"\d{4}\.\d{4,5}(?:v\d+)?", query_identifier) and query_identifier in doi_identifier.casefold():
            return 1.0
    query_norm, title_norm = normalized(query), normalized(title)
    query_compact, title_compact = compact(query), compact(title)
    core = query_core(query)
    if query_norm == title_norm:
        return 1.0
    if query_compact and query_compact == title_compact:
        return 0.99
    if core and core == title_compact:
        return 0.98
    if core and title_compact.startswith(core):
        score = 0.94
    elif core and core in title_compact:
        score = 0.88
    else:
        score = 0.0
    ratios = [
        difflib.SequenceMatcher(None, query_norm, title_norm).ratio(),
        difflib.SequenceMatcher(None, query_compact, title_compact).ratio(),
    ]
    query_tokens = set(re.findall(r"\w+", query_norm))
    title_tokens = set(re.findall(r"\w+", title_norm))
    if query_tokens:
        ratios.append(len(query_tokens & title_tokens) / len(query_tokens))
    score = max([score, *ratios], default=0.0)

    requested_version = query_version(query)
    versions = title_versions(title)
    if requested_version:
        if requested_version in versions:
            return max(score, 0.99)
        if requested_version.startswith("1.") and not versions and core and title_compact.startswith(core):
            return max(score, 0.98)
        if versions:
            return min(score, 0.69)
    return score


def fetch_authors(connection: sqlite3.Connection, item_id: int) -> list[str]:
    rows = connection.execute(
        """
        SELECT c.firstName, c.lastName
        FROM itemCreators ic
        JOIN creators c ON c.creatorID = ic.creatorID
        WHERE ic.itemID = ?
        ORDER BY ic.orderIndex
        """,
        (item_id,),
    ).fetchall()
    authors = []
    for row in rows:
        name = " ".join(part for part in (row["firstName"], row["lastName"]) if part)
        if name:
            authors.append(name)
    return authors


def item_field(connection: sqlite3.Connection, item_id: int, field_name: str) -> str | None:
    row = connection.execute(
        """
        SELECT v.value
        FROM itemData d
        JOIN fieldsCombined f ON f.fieldID = d.fieldID
        JOIN itemDataValues v ON v.valueID = d.valueID
        WHERE d.itemID = ? AND f.fieldName = ?
        """,
        (item_id, field_name),
    ).fetchone()
    return str(row["value"]) if row and row["value"] is not None else None


def contained_path(root: Path, relative: str) -> Path | None:
    root = root.resolve()
    candidate = (root / relative).resolve()
    if candidate == root or root not in candidate.parents:
        return None
    return candidate


def resolve_attachment_path(
    data_dir: Path,
    key: str,
    stored_path: str | None,
    link_mode: int,
    base_attachment_dir: Path | None,
) -> Path | None:
    if not stored_path:
        return None
    if link_mode == 3:
        return None
    if stored_path.startswith("storage:"):
        if link_mode not in (0, 1, 4):
            return None
        return contained_path(data_dir / "storage" / key, stored_path.removeprefix("storage:"))
    if stored_path.startswith("attachments:"):
        if link_mode != 2 or base_attachment_dir is None:
            return None
        return contained_path(base_attachment_dir, stored_path.removeprefix("attachments:"))
    if link_mode == 2:
        return windows_to_posix(stored_path).resolve()
    return None


def descendants(collection_id: int, rows: list[sqlite3.Row]) -> set[int]:
    result = {collection_id}
    changed = True
    while changed:
        changed = False
        for row in rows:
            parent_id = row["parentCollectionID"]
            current_id = int(row["collectionID"])
            if parent_id is not None and int(parent_id) in result and current_id not in result:
                result.add(current_id)
                changed = True
    return result


def locate(args: argparse.Namespace) -> dict[str, Any]:
    data_dirs = discover_data_dirs(args.data_dir)
    if not data_dirs:
        return {
            "status": "data_dir_not_found",
            "message": "No Zotero data directory was found; pass --data-dir.",
        }
    if len(data_dirs) > 1:
        return {
            "status": "ambiguous_data_dirs",
            "message": "Multiple Zotero data directories were found; pass --data-dir.",
            "candidates": [str(path) for path in data_dirs],
        }

    data_dir = data_dirs[0]
    database = data_dir / "zotero.sqlite"
    uri = f"{database.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        tables = {
            str(row["name"])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        required_tables = {
            "collections",
            "collectionItems",
            "items",
            "itemTypes",
            "itemData",
            "itemDataValues",
            "fieldsCombined",
            "itemAttachments",
            "deletedItems",
        }
        missing_tables = sorted(required_tables - tables)
        if missing_tables:
            return {
                "status": "unsupported_schema",
                "message": f"Zotero database is missing required tables: {', '.join(missing_tables)}",
                "database": str(database),
            }
        if "deletedCollections" in tables:
            collection_rows = connection.execute(
                """
                SELECT c.collectionID, c.collectionName, c.parentCollectionID, c.libraryID, c.key
                FROM collections c
                LEFT JOIN deletedCollections d ON d.collectionID = c.collectionID
                WHERE d.collectionID IS NULL
                ORDER BY c.collectionID
                """
            ).fetchall()
        else:
            collection_rows = connection.execute(
                """
                SELECT collectionID, collectionName, parentCollectionID, libraryID, key
                FROM collections
                ORDER BY collectionID
                """
            ).fetchall()
        by_id = {int(row["collectionID"]): row for row in collection_rows}
        requested_parts = [normalized(part) for part in split_collection_path(args.collection_path)]
        collection_matches = []
        all_collections = []
        for row in collection_rows:
            path_parts = collection_path(row, by_id)
            entry = {
                "collection_id": int(row["collectionID"]),
                "collection_key": str(row["key"]),
                "library_id": int(row["libraryID"]),
                "path": "/".join(path_parts),
            }
            all_collections.append(entry)
            if [normalized(part) for part in path_parts] == requested_parts:
                if args.library_id is None or int(row["libraryID"]) == args.library_id:
                    collection_matches.append((row, entry))

        base = {
            "data_dir": str(data_dir),
            "database": str(database),
            "requested_collection_path": args.collection_path,
            "requested_title": args.title,
        }
        if not collection_matches:
            target = normalized("/".join(split_collection_path(args.collection_path)))
            closest = sorted(
                all_collections,
                key=lambda entry: difflib.SequenceMatcher(None, target, normalized(entry["path"])).ratio(),
                reverse=True,
            )[: args.limit]
            return {
                **base,
                "status": "collection_not_found",
                "message": "The exact Zotero collection path was not found.",
                "candidates": closest,
            }
        if len(collection_matches) > 1:
            return {
                **base,
                "status": "ambiguous_collection",
                "message": "The collection path exists in multiple libraries; pass --library-id.",
                "candidates": [entry for _, entry in collection_matches],
            }

        selected_collection, collection_entry = collection_matches[0]
        collection_ids = (
            descendants(int(selected_collection["collectionID"]), collection_rows)
            if args.recursive
            else {int(selected_collection["collectionID"])}
        )
        placeholders = ",".join("?" for _ in collection_ids)
        item_rows = connection.execute(
            f"""
            SELECT DISTINCT i.itemID, i.key, t.typeName
            FROM collectionItems ci
            JOIN items i ON i.itemID = ci.itemID
            JOIN itemTypes t ON t.itemTypeID = i.itemTypeID
            LEFT JOIN deletedItems d ON d.itemID = i.itemID
            WHERE ci.collectionID IN ({placeholders}) AND d.itemID IS NULL
            ORDER BY i.itemID
            """,
            tuple(sorted(collection_ids)),
        ).fetchall()

        candidates = []
        for row in item_rows:
            item_id = int(row["itemID"])
            title = item_field(connection, item_id, "title") or ""
            doi = item_field(connection, item_id, "DOI")
            entry = {
                "item_id": item_id,
                "item_key": str(row["key"]),
                "item_type": str(row["typeName"]),
                "title": title,
                "authors": fetch_authors(connection, item_id),
                "date": item_field(connection, item_id, "date"),
                "doi": doi,
                "score": round(similarity(args.title, title, str(row["key"]), doi), 4),
            }
            candidates.append(entry)
        candidates.sort(key=lambda entry: (-entry["score"], entry["title"]))
        visible_candidates = candidates[: args.limit]
        if not candidates:
            return {
                **base,
                "status": "item_not_found",
                "collection": collection_entry,
                "message": "The collection contains no live top-level items.",
                "candidates": [],
            }

        best = candidates[0]
        runner_up = candidates[1]["score"] if len(candidates) > 1 else 0.0
        confident = best["score"] >= 0.72 and (best["score"] >= 0.98 or best["score"] - runner_up >= 0.08)
        if not confident:
            return {
                **base,
                "status": "ambiguous_item" if best["score"] >= 0.45 else "item_not_found",
                "collection": collection_entry,
                "message": "No unique high-confidence item match was found.",
                "candidates": visible_candidates,
            }

        attachment_rows = connection.execute(
            """
            SELECT i.itemID, i.key, a.linkMode, a.contentType, a.path
            FROM itemAttachments a
            JOIN items i ON i.itemID = a.itemID
            LEFT JOIN deletedItems d ON d.itemID = i.itemID
            WHERE (a.parentItemID = ? OR a.itemID = ?) AND d.itemID IS NULL
            ORDER BY i.itemID
            """,
            (best["item_id"], best["item_id"]),
        ).fetchall()
        attachments = []
        base_attachment_dir = discover_base_attachment_dir()
        for row in attachment_rows:
            stored_path = str(row["path"]) if row["path"] is not None else None
            content_type = str(row["contentType"] or "")
            if content_type.casefold() != "application/pdf" and not (stored_path or "").casefold().endswith(".pdf"):
                continue
            path = resolve_attachment_path(
                data_dir,
                str(row["key"]),
                stored_path,
                int(row["linkMode"]),
                base_attachment_dir,
            )
            attachments.append(
                {
                    "attachment_id": int(row["itemID"]),
                    "attachment_key": str(row["key"]),
                    "link_mode": int(row["linkMode"]),
                    "content_type": content_type,
                    "stored_path": stored_path,
                    "path": str(path) if path else None,
                    "exists": bool(path and path.is_file()),
                }
            )

        existing = [attachment for attachment in attachments if attachment["exists"]]
        result = {
            **base,
            "collection": collection_entry,
            "item": best,
            "attachments": attachments,
        }
        if len(existing) == 1:
            return {**result, "status": "ok", "pdf_path": existing[0]["path"]}
        if len(existing) > 1:
            return {
                **result,
                "status": "ambiguous_pdf",
                "message": "Multiple local PDF attachments were found; ask the user to choose.",
            }
        return {
            **result,
            "status": "pdf_not_found",
            "message": "The item was found, but no resolvable local PDF attachment exists.",
        }
    finally:
        connection.close()


def render_human(result: dict[str, Any]) -> str:
    lines = [f"Status: {result['status']}"]
    if result.get("message"):
        lines.append(str(result["message"]))
    if result.get("collection"):
        lines.append(f"Collection: {result['collection']['path']}")
    if result.get("item"):
        item = result["item"]
        lines.append(f"Item: {item['title']} [{item['item_key']}]")
    if result.get("pdf_path"):
        lines.append(f"PDF: {result['pdf_path']}")
    for candidate in result.get("candidates", []):
        title = candidate.get("title") or candidate.get("path") or str(candidate)
        key = candidate.get("item_key") or candidate.get("collection_key") or ""
        score = f" score={candidate['score']:.4f}" if "score" in candidate else ""
        lines.append(f"Candidate: {title} [{key}]{score}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Locate a Zotero paper PDF by exact collection path and fuzzy title (read-only)."
    )
    parser.add_argument("--collection-path", required=True, help="Collection path, e.g. Notion or Research/World Models")
    parser.add_argument("--title", required=True, help="Paper title, alias, DOI, arXiv ID, or Zotero item key")
    parser.add_argument("--data-dir", help="Zotero data directory; auto-discovered when omitted")
    parser.add_argument("--library-id", type=int, help="Disambiguate identical paths in multiple libraries")
    parser.add_argument("--recursive", action="store_true", help="Include descendant collections")
    parser.add_argument("--limit", type=int, default=8, help="Maximum candidates to return")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = locate(args)
    except (OSError, sqlite3.Error) as error:
        result = {"status": "error", "message": str(error)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_human(result))
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
