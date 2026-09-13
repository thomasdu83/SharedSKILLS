#!/usr/bin/env python
"""Create or extend the governed version source for every discovered Skill.

Existing version assignments are retained. New Skills receive the explicit
initial baseline version supplied on the command line. This script never edits
SKILL.md files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from build_skill_release import frontmatter
    from skill_doctor import parse_yaml_simple
except ImportError:  # pragma: no cover
    from scripts.build_skill_release import frontmatter
    from scripts.skill_doctor import parse_yaml_simple


def discover(root: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for skill_file in sorted(root.rglob("SKILL.md")):
        if any(part in {".git", "__pycache__", "node_modules", ".venv"} for part in skill_file.parts):
            continue
        skill_id, _ = frontmatter(skill_file)
        items.append({
            "id": skill_id,
            "path": skill_file.parent.relative_to(root).as_posix(),
        })
    return items


def existing_versions(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    data = parse_yaml_simple(path.read_text(encoding="utf-8")) or {}
    versions: dict[tuple[str, str], str] = {}
    for item in data.get("skills", []) if isinstance(data, dict) else []:
        if not isinstance(item, dict):
            continue
        skill_id = str(item.get("id", "")).strip()
        skill_path = str(item.get("path", "")).replace("\\", "/").strip()
        version = str(item.get("version", "")).strip()
        if skill_id and skill_path and version:
            versions[(skill_id, skill_path)] = version
    return versions


def render(skills: list[dict[str, str]]) -> str:
    lines = [
        "# skill-versions.yaml",
        "# SharedSKILLS 的唯一版本来源；由 scripts/build_skill_versions.py 维护。",
        "# 版本改变应同时更新变更说明、行为回归结果和 skill-release.yaml。",
        'schema_version: "1.0"',
        'version_policy: "semantic_versioning"',
        "skills:",
    ]
    for skill in skills:
        lines.extend([
            f"  - id: {json.dumps(skill['id'], ensure_ascii=False)}",
            f"    path: {json.dumps(skill['path'], ensure_ascii=False)}",
            f"    version: {json.dumps(skill['version'], ensure_ascii=False)}",
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="skill-versions.yaml")
    parser.add_argument("--initial-version", default="1.0.0")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    prior = existing_versions(output)
    skills = discover(root)
    for skill in skills:
        key = (skill["id"], skill["path"])
        skill["version"] = prior.get(key, args.initial_version)
    output.write_text(render(skills), encoding="utf-8", newline="\n")
    print(f"generated {output} ({len(skills)} skills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
