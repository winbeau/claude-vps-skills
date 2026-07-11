#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import posixpath
import sys
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
REQUIRED_PARTS = {
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml",
    "word/_rels/document.xml.rels",
}
SUSPICIOUS_TEXT = [
    "codex-clipboard",
    "AppData/Local/Temp",
    "AppData\\Local\\Temp",
    "<late>",
    "</late>",
]


def relationship_base(rels_name: str) -> str:
    rels_path = PurePosixPath(rels_name)
    if rels_path.parent.name == "_rels":
        base = rels_path.parent.parent
    else:
        base = rels_path.parent
    return "" if str(base) == "." else str(base)


def resolve_relationship_target(rels_name: str, target: str) -> str:
    target = target.replace("\\", "/")
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(relationship_base(rels_name), target))


def inspect_docx(path: Path, allow_external: bool = False) -> dict:
    report: dict = {
        "file": str(path),
        "ok": False,
        "issues": [],
        "warnings": [],
        "counts": {},
    }
    if not path.exists():
        report["issues"].append(f"file not found: {path}")
        return report
    if not zipfile.is_zipfile(path):
        report["issues"].append("not a zip/docx package")
        return report

    try:
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
            bad_member = zf.testzip()
            if bad_member:
                report["issues"].append(f"zip CRC/read failure: {bad_member}")

            missing_required = sorted(REQUIRED_PARTS - names)
            for name in missing_required:
                report["issues"].append(f"missing required part: {name}")

            xml_entries = sorted(n for n in names if n.endswith(".xml") or n.endswith(".rels"))
            media_entries = sorted(n for n in names if n.startswith("word/media/"))
            report["counts"]["xml_entries"] = len(xml_entries)
            report["counts"]["media_entries"] = len(media_entries)

            for name in xml_entries:
                data = zf.read(name)
                try:
                    ET.fromstring(data)
                except Exception as exc:
                    report["issues"].append(f"XML parse error in {name}: {exc}")
                    continue

                text = data.decode("utf-8", "replace")
                for needle in SUSPICIOUS_TEXT:
                    if needle in text:
                        report["issues"].append(f"suspicious text `{needle}` found in {name}")

            rel_targets = 0
            missing_targets = []
            external_targets = []
            for name in sorted(n for n in names if n.endswith(".rels")):
                root = ET.fromstring(zf.read(name))
                for rel in root.findall(f"{REL_NS}Relationship"):
                    target = rel.attrib.get("Target", "")
                    mode = rel.attrib.get("TargetMode", "")
                    if not target or target.startswith("#"):
                        continue
                    if mode == "External":
                        external_targets.append(f"{name} -> {target}")
                        continue
                    if "://" in target:
                        report["issues"].append(f"absolute URI without TargetMode=External: {name} -> {target}")
                        continue
                    resolved = resolve_relationship_target(name, target)
                    rel_targets += 1
                    if resolved not in names:
                        missing_targets.append(f"{name} -> {target} (resolved {resolved})")

            report["counts"]["internal_relationship_targets"] = rel_targets
            if external_targets and not allow_external:
                report["issues"].extend(f"external relationship: {item}" for item in external_targets)
            elif external_targets:
                report["warnings"].extend(f"external relationship allowed: {item}" for item in external_targets)
            report["issues"].extend(f"missing relationship target: {item}" for item in missing_targets)

            app_xml = "docProps/app.xml"
            if app_xml in names:
                app_text = zf.read(app_xml).decode("utf-8", "replace")
                if "<Template>" not in app_text or "</Template>" not in app_text:
                    report["warnings"].append("docProps/app.xml has no Template element; inspect if Word repairs the file")
    except Exception as exc:
        report["issues"].append(f"cannot inspect package: {exc}")

    report["ok"] = not report["issues"]
    return report


def print_report(report: dict, quiet: bool = False) -> None:
    if quiet and report["ok"]:
        return
    status = "OK" if report["ok"] else "FAIL"
    print(f"{status}: {report['file']}")
    counts = report.get("counts") or {}
    if counts:
        print(
            "  counts: "
            + ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        )
    for issue in report.get("issues", []):
        print(f"  ISSUE: {issue}")
    for warning in report.get("warnings", []):
        print(f"  WARN: {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect DOCX package health before Word visual QA.")
    parser.add_argument("docx", nargs="+", type=Path)
    parser.add_argument("--allow-external", action="store_true", help="Do not fail on external relationships.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    parser.add_argument("--quiet", action="store_true", help="Suppress OK reports.")
    args = parser.parse_args(argv)

    reports = [inspect_docx(path, allow_external=args.allow_external) for path in args.docx]
    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print_report(report, quiet=args.quiet)
    return 1 if any(not report["ok"] for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
