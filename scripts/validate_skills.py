#!/usr/bin/env python3
"""Validate the repository's portable Agent Skill layout."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_ROOT_DIRS = {"agents", "assets", "references", "scripts"}
LEGAL_ROOT_FILES = {"LICENSE", "ATTRIBUTION.md", "VERSIONS.md"}
RUNTIME_NAMES = {"__pycache__", ".DS_Store", ".pytest_cache", ".mypy_cache"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def frontmatter_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening YAML delimiter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("missing closing YAML delimiter")
    return text[4:end]


def top_level_keys(yaml_text: str) -> list[str]:
    return re.findall(r"(?m)^([A-Za-z_][A-Za-z0-9_-]*):(?:\s|$)", yaml_text)


def scalar_value(yaml_text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", yaml_text)
    if not match:
        return None
    value = match.group(1).strip()
    if value in {">", "|", ">-", "|-"}:
        lines = yaml_text[match.end() :].splitlines()
        folded: list[str] = []
        for line in lines:
            if line and not line[0].isspace():
                break
            if line.strip():
                folded.append(line.strip())
        return " ".join(folded)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value


def interface_values(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not re.search(r"(?m)^interface:\s*$", text):
        return {}
    values: dict[str, str] = {}
    for key in ("display_name", "short_description", "default_prompt"):
        match = re.search(rf"(?m)^  {key}:\s*(.*?)\s*$", text)
        if match:
            value = match.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            values[key] = value
    return values


def broken_links(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for match in LINK_RE.finditer(text):
        raw = match.group(1).strip().split()[0].strip("<>")
        if not raw or raw.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = (path.parent / raw.split("#", 1)[0]).resolve()
        if not target.exists():
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{path.relative_to(ROOT)}:{line}: broken link: {raw}")
    return errors


def validate_skill(skill: Path) -> list[str]:
    errors: list[str] = []
    name = skill.name
    if not NAME_RE.fullmatch(name):
        errors.append("directory name must be lowercase kebab-case")

    skill_md = skill / "SKILL.md"
    if not skill_md.is_file():
        return errors + ["missing SKILL.md"]

    try:
        frontmatter = frontmatter_text(skill_md)
    except Exception as exc:
        return errors + [f"invalid SKILL.md frontmatter: {exc}"]

    if set(top_level_keys(frontmatter)) != {"name", "description"}:
        errors.append("SKILL.md frontmatter must contain only name and description")
    if scalar_value(frontmatter, "name") != name:
        errors.append(f"frontmatter name must match directory ({name})")
    description = scalar_value(frontmatter, "description")
    if not description:
        errors.append("description must be a non-empty string")
    elif len(description) > 1024:
        errors.append("description exceeds 1024 characters")

    agent_file = skill / "agents" / "openai.yaml"
    if not agent_file.is_file():
        errors.append("missing agents/openai.yaml")
    else:
        interface = interface_values(agent_file)
        for key in ("display_name", "short_description", "default_prompt"):
            if not interface.get(key):
                errors.append(f"agents/openai.yaml missing interface.{key}")
        prompt = interface.get("default_prompt", "")
        if f"${name}" not in prompt:
            errors.append(f"default_prompt must mention ${name}")
        short = interface.get("short_description", "")
        if short and not 25 <= len(short) <= 64:
            errors.append("short_description must be 25-64 characters")

    for child in skill.iterdir():
        if child.name in RUNTIME_NAMES or child.suffix in {".pyc", ".pyo"}:
            errors.append(f"runtime artifact is not allowed: {child.name}")
        if child.is_dir() and child.name not in ALLOWED_ROOT_DIRS:
            errors.append(f"unexpected root directory: {child.name}")
        if child.is_file() and child.name != "SKILL.md" and child.name not in LEGAL_ROOT_FILES:
            errors.append(f"unexpected root file: {child.name}")

    for path in skill.rglob("*"):
        if path.name in RUNTIME_NAMES or path.suffix in {".pyc", ".pyo"}:
            errors.append(f"runtime artifact is not allowed: {path.relative_to(skill)}")

    errors.extend(broken_links(skill_md))

    return errors


def main() -> int:
    if not SKILLS.is_dir():
        print(f"Missing skills directory: {SKILLS}", file=sys.stderr)
        return 1

    skills = sorted(path for path in SKILLS.iterdir() if path.is_dir())
    failures = 0
    for skill in skills:
        errors = validate_skill(skill)
        if errors:
            failures += 1
            print(f"FAIL {skill.name}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK   {skill.name}")

    documentation_errors: list[str] = []
    for pattern in ("README.md", "CLAUDE.md", "docs/skills/*.md"):
        for path in ROOT.glob(pattern):
            documentation_errors.extend(broken_links(path))
    if documentation_errors:
        failures += 1
        print("FAIL documentation")
        for error in documentation_errors:
            print(f"  - {error}")

    if failures:
        print(f"\n{failures}/{len(skills)} skills failed validation.", file=sys.stderr)
        return 1
    print(f"\nValidated {len(skills)} skills: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
