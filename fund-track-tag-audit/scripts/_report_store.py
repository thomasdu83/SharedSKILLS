#!/usr/bin/env python3
"""Shared report-store paths for fund track-tag audit reports."""

from __future__ import annotations

from pathlib import Path
import os


ENV_VARS = ("FUND_TRACK_TAG_AUDIT_ROOT", "FUND_TRACK_TAG_AUDIT_SHARED_ROOT")
DEFAULT_SHARED_ROOT = Path(r"Y:\投顾管理人研究\fund-track-tag-audit")
UNC_SHARED_ROOT = Path(
    r"\\10.168.20.10\资产-投资研究\投顾管理人研究\fund-track-tag-audit"
)


class ReportStoreError(RuntimeError):
    """Raised when the shared report store is unavailable."""


def candidate_roots(explicit_root: str | None = None) -> list[Path]:
    roots: list[Path] = []
    if explicit_root:
        roots.append(Path(explicit_root))
    for env_var in ENV_VARS:
        value = os.environ.get(env_var)
        if value:
            roots.append(Path(value))
    roots.extend([DEFAULT_SHARED_ROOT, UNC_SHARED_ROOT])

    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(root)
    return deduped


def find_existing_root(explicit_root: str | None = None) -> Path | None:
    for root in candidate_roots(explicit_root):
        try:
            if root.exists() and root.is_dir():
                return root
        except OSError:
            continue
    return None


def format_candidate_roots(explicit_root: str | None = None) -> str:
    return "\n".join(f"- {root}" for root in candidate_roots(explicit_root))


def require_report_root(explicit_root: str | None = None) -> Path:
    root = find_existing_root(explicit_root)
    if root is not None:
        return root
    raise ReportStoreError(
        "未找到共享报告库。请确认网盘已挂载并已加入 Trae workspace。\n"
        "候选路径：\n"
        f"{format_candidate_roots(explicit_root)}"
    )


def report_dir(kind: str, root: Path) -> Path:
    if kind == "fund":
        return root / "funds"
    if kind == "batch":
        return root / "batch"
    if kind == "root":
        return root
    raise ValueError(f"unknown report kind: {kind}")


def ensure_under_root(path: Path, root: Path, label: str = "路径") -> Path:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if resolved_path == resolved_root or resolved_root in resolved_path.parents:
        return resolved_path
    raise ReportStoreError(f"{label}必须位于共享报告库内：{resolved_path}")
