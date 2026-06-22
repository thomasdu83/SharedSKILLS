#!/usr/bin/env python3
"""Find saved fund track-tag audit reports in the shared report store."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import sys

from _report_store import ReportStoreError, ensure_under_root, report_dir, require_report_root


TIMESTAMP_RE = re.compile(r"^(?P<stamp>\d{8}-\d{6})_(?P<title>.+?)\.md$", re.I)
INVALID_QUERY_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
SPACES = re.compile(r"\s+")


@dataclass
class ReportMatch:
    path: Path
    timestamp: str
    audit_time: str
    title: str
    score: int
    mtime: str


def default_output_dirs(root: Path, include_batch: bool) -> list[Path]:
    dirs = [report_dir("fund", root), report_dir("root", root)]
    if include_batch:
        dirs.append(report_dir("batch", root))
    return dirs


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = INVALID_QUERY_CHARS.sub("", str(value)).lower()
    text = SPACES.sub("", text)
    for suffix in ("私募证券投资基金", "私募投资基金", "证券投资基金", "投资基金"):
        text = text.replace(suffix, "")
    for token in ("策略标签审核", "赛道标签审核", "标签审核", "审核报告"):
        text = text.replace(token, "")
    return text


def parse_timestamp(filename: str, mtime: float) -> tuple[str, str, str]:
    match = TIMESTAMP_RE.match(filename)
    if match:
        stamp = match.group("stamp")
        title = match.group("title")
        try:
            audit_time = datetime.strptime(stamp, "%Y%m%d-%H%M%S").strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except ValueError:
            audit_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        return stamp, audit_time, title
    audit_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    return datetime.fromtimestamp(mtime).strftime("%Y%m%d-%H%M%S"), audit_time, filename


def score_report(query: str, title: str, filename: str) -> int:
    q = normalize_text(query)
    title_norm = normalize_text(title)
    file_norm = normalize_text(filename)
    if not q:
        return 0
    score = 0
    if q == title_norm:
        score += 1000
    if q in title_norm:
        score += 700
    if q in file_norm:
        score += 500
    query_parts = [part for part in re.split(r"[-_（）()]+", normalize_text(query)) if part]
    for part in query_parts:
        if len(part) >= 2 and part in file_norm:
            score += 80
    return score


def find_reports(query: str, output_dirs: list[Path]) -> list[ReportMatch]:
    matches: list[ReportMatch] = []
    seen: set[str] = set()
    for output_dir in output_dirs:
        if not output_dir.exists():
            continue
        for path in output_dir.glob("*.md"):
            path_key = str(path.resolve())
            if path_key in seen:
                continue
            seen.add(path_key)
            stat = path.stat()
            stamp, audit_time, title = parse_timestamp(path.name, stat.st_mtime)
            score = score_report(query, title, path.name)
            if score <= 0:
                continue
            matches.append(
                ReportMatch(
                    path=path.resolve(),
                    timestamp=stamp,
                    audit_time=audit_time,
                    title=title,
                    score=score,
                    mtime=datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )
            )
    matches.sort(key=lambda item: (item.score, item.timestamp), reverse=True)
    return matches


def emit_text(matches: list[ReportMatch], show_all: bool) -> None:
    if not matches:
        print("NO_MATCH")
        return
    selected = matches if show_all else matches[:1]
    print(f"MATCHES {len(matches)}")
    for item in selected:
        print(f"audit_time: {item.audit_time}")
        print(f"title: {item.title}")
        print(f"score: {item.score}")
        print(f"path: {item.path}")
        print("")


def emit_json(matches: list[ReportMatch], show_all: bool) -> None:
    selected = matches if show_all else matches[:1]
    payload = {
        "matches": len(matches),
        "reports": [
            {
                "path": str(item.path),
                "timestamp": item.timestamp,
                "audit_time": item.audit_time,
                "title": item.title,
                "score": item.score,
                "mtime": item.mtime,
            }
            for item in selected
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Find saved fund track-tag audit reports.")
    parser.add_argument("query", help="Fund name or query term")
    parser.add_argument(
        "--shared-root",
        help="Shared report root. Defaults to Y:\\投顾管理人研究\\fund-track-tag-audit or env FUND_TRACK_TAG_AUDIT_ROOT.",
    )
    parser.add_argument(
        "--output-dir",
        action="append",
        help="Explicit directory to search. Can be repeated. Defaults are disabled when supplied.",
    )
    parser.add_argument("--all", action="store_true", help="Show all matching reports")
    parser.add_argument(
        "--include-batch",
        action="store_true",
        help="Also search shared batch summaries. Disabled by default so batch summaries are not reused as single-fund reports.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    try:
        root = require_report_root(args.shared_root)
        if args.output_dir:
            output_dirs = [ensure_under_root(Path(item), root, "搜索目录") for item in args.output_dir]
        else:
            output_dirs = default_output_dirs(root, args.include_batch)
    except ReportStoreError as exc:
        if args.json:
            print(
                json.dumps(
                    {"matches": 0, "reports": [], "error": str(exc)},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(str(exc))
        return 2
    matches = find_reports(args.query, output_dirs)
    if args.json:
        emit_json(matches, args.all)
    else:
        emit_text(matches, args.all)
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
