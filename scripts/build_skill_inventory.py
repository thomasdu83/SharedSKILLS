#!/usr/bin/env python3
"""Generate the complete SharedSKILLS inventory.

The inventory is deliberately separate from ``skill-registry.yaml``:
registry entries are routing entry points, while this file is the full
filesystem/source-of-truth ledger.  The script is deterministic and only
reads SKILL.md frontmatter.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from skill_doctor import parse_yaml_simple
except ImportError:
    from scripts.skill_doctor import parse_yaml_simple


def discover(root: Path) -> list[Path]:
    return sorted(
        p.parent
        for p in root.rglob("SKILL.md")
        if not any(part in {".git", "__pycache__", "node_modules", ".venv"} for part in p.parts)
    )


def frontmatter(path: Path) -> tuple[str, str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        return "", ""
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values.get("name", ""), values.get("description", "")


def registered_paths(root: Path) -> dict[str, dict]:
    """Read each registered role; registration alone does not imply primary."""
    registry = root / "skill-registry.yaml"
    if not registry.exists():
        return {}
    data = parse_yaml_simple(registry.read_text(encoding="utf-8-sig")) or {}
    return {str(s["path"]).replace("\\", "/"): s
            for s in data.get("skills", []) if isinstance(s, dict) and s.get("path")}


META_SKILLS = {
    "skill-creator", "writing-skills", "using-superpowers",
    "zm-skills-manager-local", "workflow-runner", "mcp-builder",
    "writing-plans", "executing-plans", "dispatching-parallel-agents",
    "subagent-driven-development", "systematic-debugging",
    "test-driven-development", "verification-before-completion",
    "using-git-worktrees", "finishing-a-development-branch",
    "requesting-code-review", "receiving-code-review",
}


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build(root: Path) -> str:
    rows: list[tuple[str, str, str, str, str]] = []
    registered = registered_paths(root)
    for directory in discover(root):
        name, description = frontmatter(directory / "SKILL.md")
        rel = directory.relative_to(root).as_posix()
        leaf = directory.name
        if rel in registered:
            entry = registered[rel]
            role = str(entry.get("role", "reference"))
            routable = str(entry.get("routable", False)).lower()
        elif leaf in META_SKILLS:
            role, routable = "meta", "false"
        else:
            role, routable = "reference", "false"
        rows.append((rel, name, description, role, routable))
    lines = [
        "# skill-inventory.yaml",
        "# SharedSKILLS 全量 Skill 资产台账；路由规则见 skill-registry.yaml。",
        "# 本文件由 scripts/build_skill_inventory.py 生成，不负责授权或自动修改 Skill。",
        "schema_version: \"1.0\"",
        "inventory_scope: full",
        f"skill_count: {len(rows)}",
        "skills:",
    ]
    for rel, name, description, role, routable in rows:
        lines.extend([
            f"  - path: {yaml_quote(rel)}",
            f"    id: {yaml_quote(name or rel.split('/')[-1])}",
            "    entry: SKILL.md",
            f"    description: {yaml_quote(description)}",
            "    source_of_truth: SharedSKILLS",
            f"    role: {role}",
            f"    routable: {routable}",
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate skill-inventory.yaml")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="skill-inventory.yaml")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.write_text(build(root), encoding="utf-8", newline="\n")
    print(f"generated {output} ({len(discover(root))} skills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
