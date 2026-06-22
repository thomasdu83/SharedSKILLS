#!/usr/bin/env python3
"""Save a fund track-tag audit report to the shared report store."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import os
from pathlib import Path
import re
import subprocess
import sys

from _report_store import (
    ReportStoreError,
    ensure_under_root,
    report_dir,
    require_report_root,
)


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WHITESPACE = re.compile(r"\s+")

VALIDATE_SCRIPT = Path(__file__).resolve().parent / "validate_audit_report.py"


def sanitize_filename_part(value: str, max_chars: int = 80) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("_", value)
    cleaned = WHITESPACE.sub("", cleaned).strip(" ._")
    if not cleaned:
        return "策略标签审核"
    return cleaned[:max_chars].strip(" ._") or "策略标签审核"


def _read_temp_file(path: str) -> str:
    p = Path(path).resolve()
    tmp_root = Path(os.environ.get("TEMP", os.environ.get("TMP", ""))).resolve()
    if tmp_root != Path("."):
        try:
            p.relative_to(tmp_root)
        except ValueError:
            raise SystemExit(
                f"--temp-file 必须位于 %%TEMP%% 目录下: {p}\n当前 %%TEMP%% = {tmp_root}"
            )
    return p.read_text(encoding="utf-8")


def _cleanup_temp_file(path: str) -> None:
    p = Path(path).resolve()
    p.unlink(missing_ok=True)


def read_report_content(args: argparse.Namespace) -> str:
    if args.content_base64 is not None:
        return base64.b64decode(args.content_base64).decode("utf-8")
    if args.temp_file is not None:
        return _read_temp_file(args.temp_file)
    if args.content is not None:
        return args.content
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit(
        "未提供报告内容。请使用 --content-base64 / --temp-file / --content 或通过 stdin 传入 Markdown。"
    )


def build_output_path(args: argparse.Namespace) -> Path:
    root = require_report_root(args.shared_root)
    output_dir = (
        ensure_under_root(Path(args.output_dir), root, "输出目录")
        if args.output_dir
        else report_dir(args.kind, root)
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.filename:
        filename = sanitize_filename_part(args.filename)
        if not filename.lower().endswith(".md"):
            filename += ".md"
    else:
        title = sanitize_filename_part(args.title or "策略标签审核")
        timestamp = args.timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}_{title}.md" if not args.no_timestamp else f"{title}.md"

    path = ensure_under_root(output_dir / filename, root, "输出路径")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Save a fund track-tag audit report to the shared report store as Markdown."
    )
    parser.add_argument("--title", help="Report title used in the generated filename")
    parser.add_argument(
        "--filename", help="Exact filename to use; .md is appended if absent"
    )
    parser.add_argument("--timestamp", help="Timestamp prefix, e.g. 20260528-092631")
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Do not prefix filename with timestamp",
    )
    parser.add_argument(
        "--shared-root",
        help="Shared report root. Defaults to Y:\\投顾管理人研究\\fund-track-tag-audit or env FUND_TRACK_TAG_AUDIT_ROOT.",
    )
    parser.add_argument(
        "--output-dir", help="Explicit directory for saved Markdown reports"
    )
    parser.add_argument(
        "--kind",
        choices=["fund", "batch"],
        default="fund",
        help="Default output subdirectory under shared root: fund -> funds, batch -> batch",
    )
    parser.add_argument(
        "--content",
        help="Markdown content to save (short/simple text only; prefer --content-base64)",
    )
    parser.add_argument(
        "--content-base64",
        help="Base64-encoded Markdown content. Preferred method: safe for all content, single-step, no shell escaping issues.",
    )
    parser.add_argument(
        "--temp-file",
        help="Read report content from a temp file (auto-deleted after read). Must be under %%TEMP%%.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_false",
        dest="validate",
        help="Skip report validation before saving. Not recommended for shared reports.",
    )
    parser.set_defaults(validate=True)
    args = parser.parse_args()

    content = read_report_content(args).strip()
    if not content:
        raise SystemExit("报告内容为空，未保存。")

    if args.validate and VALIDATE_SCRIPT.exists():
        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), "--strict", "--content", content],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.returncode != 0:
            raise SystemExit(
                "报告格式校验未通过（错误或警告），已拒绝保存。请修正后重试。\n"
                "提示：使用 --temp-file 时，校验失败不会删除临时文件，"
                "可直接修改后重试。"
            )

    try:
        path = build_output_path(args)
    except ReportStoreError as exc:
        raise SystemExit(str(exc)) from exc
    path.write_text(content + "\n", encoding="utf-8")
    if args.temp_file:
        _cleanup_temp_file(args.temp_file)
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
