#!/usr/bin/env python3
"""Refresh source_hash fields in skill-disposition.yaml from local SKILL.md files."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "skill-disposition.yaml"


def main() -> int:
    lines = TABLE.read_text(encoding="utf-8").splitlines(keepends=True)
    current_path: str | None = None
    changed = 0
    out: list[str] = []
    for line in lines:
        path_match = re.match(r"\s+path:\s+(.+?)\s*$", line.rstrip("\r\n"))
        if path_match:
            current_path = path_match.group(1).strip('"\'')
        hash_match = re.match(r"(\s+source_hash:\s+)([0-9a-f]+)(\s*)$", line.rstrip("\r\n"))
        if hash_match and current_path:
            skill_file = ROOT / current_path / "SKILL.md"
            if skill_file.exists():
                digest = hashlib.sha256(skill_file.read_bytes()).hexdigest()[:16]
                newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
                replacement = f"{hash_match.group(1)}{digest}{hash_match.group(3)}{newline}"
                if replacement != line:
                    changed += 1
                line = replacement
        out.append(line)
    TABLE.write_text("".join(out), encoding="utf-8", newline="")
    print(f"updated source_hash fields: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
