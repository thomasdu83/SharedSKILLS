#!/usr/bin/env python3
"""Find first-level manager material folders under the due-diligence root."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from _env import load_env_files
from _paths import PathResolutionError, resolve_raw_root


@dataclass(frozen=True)
class ManagerMatch:
    name: str
    path: str
    score: int
    code: str = ""


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).casefold()


def folder_code(folder_name: str) -> str:
    match = re.match(r"^(\d{4,})[_\-\s]", folder_name.strip())
    return match.group(1) if match else ""


def score_folder(folder_name: str, query: str) -> int:
    name = normalize(folder_name)
    needle = normalize(query)
    if not needle:
        return 0
    score = 0
    if name == needle:
        score += 100
    if name.endswith("_" + needle) or name.endswith("-" + needle):
        score += 90
    if needle in name:
        score += 70
    query_chars = [char for char in needle if char.isalnum() or "\u4e00" <= char <= "\u9fff"]
    if query_chars:
        overlap = sum(1 for char in set(query_chars) if char in name)
        score += int(20 * overlap / len(set(query_chars)))
    return score


def find_manager_folders(raw_root: Path, manager: str, *, limit: int = 20) -> list[ManagerMatch]:
    matches: list[ManagerMatch] = []
    try:
        children = list(raw_root.iterdir())
    except OSError as exc:
        raise RuntimeError(f"无法枚举尽调材料根目录: {raw_root} ({exc})") from exc

    for child in children:
        if not child.is_dir():
            continue
        score = score_folder(child.name, manager)
        if score > 0:
            matches.append(ManagerMatch(child.name, str(child), score, folder_code(child.name)))

    matches.sort(key=lambda item: (-item.score, item.name.casefold()))
    return matches[:limit]


def find_same_code_folders(raw_root: Path, selected: ManagerMatch) -> list[ManagerMatch]:
    code = selected.code or folder_code(selected.name)
    if not code:
        return []
    siblings: list[ManagerMatch] = []
    try:
        children = list(raw_root.iterdir())
    except OSError as exc:
        raise RuntimeError(f"无法枚举尽调材料根目录: {raw_root} ({exc})") from exc
    selected_path = Path(selected.path).resolve(strict=False)
    for child in children:
        if not child.is_dir() or folder_code(child.name) != code:
            continue
        if child.resolve(strict=False) == selected_path:
            continue
        siblings.append(ManagerMatch(child.name, str(child), 0, code))
    return sorted(siblings, key=lambda item: item.name.casefold())


def render_matches(matches: list[ManagerMatch]) -> str:
    if not matches:
        return "未找到匹配的管理人文件夹。"
    lines = ["匹配到的管理人文件夹：", "", "| 序号 | 分数 | 文件夹 | 路径 |", "|---:|---:|---|---|"]
    for idx, item in enumerate(matches, start=1):
        lines.append(f"| {idx} | {item.score} | {item.name} | `{item.path}` |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Find manager material folders.")
    parser.add_argument("manager", help="Manager keyword, e.g. 双隆")
    parser.add_argument("--raw-root", help="Explicit raw material root.")
    parser.add_argument("--env-file", help="Explicit .env file to load before resolving paths.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    load_env_files(args.env_file)

    try:
        raw_root = resolve_raw_root(args.raw_root)
        matches = find_manager_folders(raw_root, args.manager, limit=args.limit)
    except (PathResolutionError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(item) for item in matches], ensure_ascii=False, indent=2))
    else:
        print(f"尽调材料根目录: {raw_root}")
        print(render_matches(matches))

    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
