#!/usr/bin/env python3
"""Validate cross-stage artifacts for an idea-discovery run.

The validator intentionally parses only the small, stable YAML envelope and
Markdown fields defined by the suite. It has no third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SCHEMA = "idea-research/v1"
SUITE_VERSION = "1.0.0"


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([a-zA-Z_][\w-]*):\s*(.*?)\s*$", line)
        if match:
            result[match.group(1)] = match.group(2).strip('"\'')
    return result


def markdown_value(text: str, field: str) -> str | None:
    pattern = rf"(?mi)^-\s*\*\*{re.escape(field)}:\*\*\s*(.+?)\s*$"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def candidate_revisions(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    headings = list(re.finditer(r"(?m)^###\s+(IDEA-\d+):", text))
    result: dict[str, int] = {}
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[start:end]
        revision = markdown_value(section, "idea_revision")
        result[heading.group(1)] = int(revision) if revision and revision.isdigit() else 1
    return result


def validate_envelope(
    path: Path,
    expected_run_id: str | None,
    expected_stage: str,
    errors: list[str],
) -> dict[str, str]:
    envelope = parse_frontmatter(path)
    label = str(path)
    if not envelope:
        errors.append(f"{label}: missing or invalid YAML frontmatter")
        return {}
    if envelope.get("schema") != SCHEMA:
        errors.append(f"{label}: schema must be {SCHEMA}")
    if envelope.get("suite_version") != SUITE_VERSION:
        errors.append(f"{label}: suite_version must be {SUITE_VERSION}")
    if envelope.get("stage") != expected_stage:
        errors.append(f"{label}: stage must be {expected_stage}")
    if expected_run_id and envelope.get("run_id") != expected_run_id:
        errors.append(f"{label}: run_id does not match {expected_run_id}")
    return envelope


def validate_candidate_artifact(
    path: Path,
    run_id: str,
    stage: str,
    candidate_id: str,
    revision: int,
    errors: list[str],
) -> dict[str, str]:
    envelope = validate_envelope(path, run_id, stage, errors)
    if not envelope:
        return {}
    if envelope.get("candidate_id") != candidate_id:
        errors.append(f"{path}: candidate_id must be {candidate_id}")
    if envelope.get("idea_revision") != str(revision):
        errors.append(f"{path}: idea_revision must be {revision}")
    return envelope


def validate_run(run_dir: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    routes: list[dict[str, str]] = []

    required = {
        "00-brief.md": "brief",
        "10-scan.md": "scan",
        "20-candidates.md": "generate",
    }
    envelopes: dict[str, dict[str, str]] = {}
    run_id: str | None = None

    for filename, stage in required.items():
        path = run_dir / filename
        if not path.exists():
            errors.append(f"missing {filename}")
            owner = "idea-synthesize" if stage == "brief" else f"idea-{stage}"
            routes.append({"artifact": filename, "skill": owner})
            continue
        envelope = validate_envelope(path, run_id, stage, errors)
        envelopes[filename] = envelope
        if run_id is None and envelope.get("run_id"):
            run_id = envelope["run_id"]

    if run_id is None:
        run_id = run_dir.name
        warnings.append("run_id inferred from directory name")

    revisions = candidate_revisions(run_dir / "20-candidates.md")
    if (run_dir / "20-candidates.md").exists() and not revisions:
        warnings.append("no candidate headings matching '### IDEA-NNN:' were found")

    for candidate_id, revision in revisions.items():
        novelty_path = run_dir / "30-novelty" / f"{candidate_id}.md"
        if not novelty_path.exists():
            routes.append({"artifact": str(novelty_path.relative_to(run_dir)), "skill": "idea-check-novelty"})
            continue
        validate_candidate_artifact(
            novelty_path, run_id, "novelty", candidate_id, revision, errors
        )
        novelty_text = novelty_path.read_text(encoding="utf-8")
        novelty_verdict = markdown_value(novelty_text, "verdict")
        if novelty_verdict in {"known", "unresolved"}:
            continue

        review_path = run_dir / "40-review" / f"{candidate_id}.md"
        if not review_path.exists():
            routes.append({"artifact": str(review_path.relative_to(run_dir)), "skill": "idea-review"})
            continue
        validate_candidate_artifact(
            review_path, run_id, "review", candidate_id, revision, errors
        )
        review_text = review_path.read_text(encoding="utf-8")
        review_verdict = markdown_value(review_text, "review_verdict")
        if review_verdict != "advance":
            continue

        experiment_path = run_dir / "50-experiments" / f"{candidate_id}.md"
        if not experiment_path.exists():
            routes.append(
                {"artifact": str(experiment_path.relative_to(run_dir)), "skill": "idea-design-experiment"}
            )
            continue
        validate_candidate_artifact(
            experiment_path, run_id, "experiment", candidate_id, revision, errors
        )

    return {
        "valid": not errors and not routes,
        "run_id": run_id,
        "candidate_count": len(revisions),
        "errors": errors,
        "warnings": warnings,
        "missing_routes": routes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    if not args.run_dir.is_dir():
        print(f"Run directory does not exist: {args.run_dir}", file=sys.stderr)
        return 2

    report = validate_run(args.run_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"valid: {str(report['valid']).lower()}")
        print(f"run_id: {report['run_id']}")
        print(f"candidate_count: {report['candidate_count']}")
        for key in ("errors", "warnings", "missing_routes"):
            print(f"{key}: {json.dumps(report[key], ensure_ascii=False)}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
