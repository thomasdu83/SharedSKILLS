#!/usr/bin/env python
"""Build a deterministic SharedSKILLS release manifest from local Skill files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import date
from pathlib import Path

try:
    from skill_doctor import parse_yaml_simple
except ImportError:  # pragma: no cover - module execution from another cwd
    from scripts.skill_doctor import parse_yaml_simple


def frontmatter(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    name = re.search(r"^name:\s*[\"']?([^\"'\n]+)", text, re.MULTILINE)
    version = re.search(r"^\*\*版本号\*\*：([^\n]+)", text, re.MULTILINE)
    return (name.group(1).strip() if name else path.parent.name,
            version.group(1).strip() if version else "unversioned")


def source_revision(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "working-tree"


def source_state(root: Path) -> str:
    try:
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        ).stdout.strip()
        return "dirty" if dirty else "clean"
    except OSError:
        return "unknown"


def version_map(root: Path) -> dict[tuple[str, str], str]:
    """Load the governed Skill versions without adding metadata to every SKILL.md."""
    path = root / "skill-versions.yaml"
    if not path.exists():
        return {}
    data = parse_yaml_simple(path.read_text(encoding="utf-8")) or {}
    result: dict[tuple[str, str], str] = {}
    for item in data.get("skills", []) if isinstance(data, dict) else []:
        if not isinstance(item, dict):
            continue
        skill_id = str(item.get("id", "")).strip()
        skill_path = str(item.get("path", "")).replace("\\", "/").strip()
        version = str(item.get("version", "")).strip()
        if skill_id and skill_path and version:
            result[(skill_id, skill_path)] = version
    return result


def build(root: Path) -> dict:
    skills = []
    versions = version_map(root)
    for path in sorted(root.rglob("SKILL.md")):
        if any(part in {".git", "__pycache__", "node_modules", ".venv"} for part in path.parts):
            continue
        name, declared = frontmatter(path)
        relative_path = path.parent.relative_to(root).as_posix()
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        skills.append({
            "id": name,
            "path": relative_path,
            "version": versions.get((name, relative_path), declared),
            "sha256": content_hash,
        })
    return {
        "schema_version": "1.0",
        "release_id": f"working-tree-{date.today().strftime('%Y%m%d')}",
        "source_of_truth": "SharedSKILLS",
        "source_revision": source_revision(root),
        "source_state": source_state(root),
        "generated_by": "scripts/build_skill_release.py",
        "skills": skills,
    }


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render(data: dict) -> str:
    lines = [
        "# skill-release.yaml",
        "# SharedSKILLS 发布清单；由 scripts/build_skill_release.py 生成。",
        f"schema_version: {yaml_quote(data['schema_version'])}",
        f"release_id: {yaml_quote(data['release_id'])}",
        f"source_of_truth: {yaml_quote(data['source_of_truth'])}",
        f"source_revision: {yaml_quote(data['source_revision'])}",
        f"source_state: {yaml_quote(data['source_state'])}",
        f"generated_by: {yaml_quote(data['generated_by'])}",
        "skills:",
    ]
    for skill in data["skills"]:
        lines.extend([
            f"  - id: {yaml_quote(skill['id'])}",
            f"    path: {yaml_quote(skill['path'])}",
            f"    version: {yaml_quote(skill['version'])}",
            f"    sha256: {yaml_quote(skill['sha256'])}",
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="skill-release.yaml")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.write_text(render(build(root)), encoding="utf-8", newline="\n")
    print(f"generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
