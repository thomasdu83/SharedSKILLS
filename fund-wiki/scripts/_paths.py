#!/usr/bin/env python3
"""Path resolution helpers for the fund-wiki Trae skill."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable


PROJECT_ROOT_ENVS = ("FPW_PROJECT_ROOT", "FUND_PROFILE_WIKI_PROJECT_ROOT")
RAW_ROOT_ENVS = ("FPW_RAW_ROOT", "FPW_DD_ROOT")
DOCS_ROOT_ENVS = ("FPW_DOCS_ROOT", "FUND_PROFILE_WIKI_DOCS_ROOT")
DEV_PROJECT_ROOT_ENVS = ("FPW_DEV_PROJECT_ROOT",)
LOCAL_DOCS_ROOT_ENVS = ("FPW_LOCAL_DOCS_ROOT",)

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT_ROOT = SKILL_ROOT / "engine"

RAW_ROOT_CANDIDATES = (
    Path(r"W:\投顾信息（PPT、尽调反馈表等）"),
    Path(r"Z:\投顾信息（PPT、尽调反馈表等）"),
    Path(r"\\10.168.20.10\投顾信息（PPT、尽调反馈表等）"),
)

DOCS_ROOT_CANDIDATES = (
    Path(r"Y:\投顾管理人研究\fund_profile_wiki_docs"),
    Path(r"\\10.168.20.10\资产-投资研究\投顾管理人研究\fund_profile_wiki_docs"),
)


class PathResolutionError(RuntimeError):
    """Raised when a required path cannot be resolved."""


def _env_paths(names: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for name in names:
        value = os.environ.get(name)
        if value:
            paths.append(Path(value))
    return paths


def _dedupe(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).casefold()
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def _is_dir(path: Path) -> bool:
    try:
        return path.exists() and path.is_dir()
    except OSError:
        return False


def _format_candidates(paths: Iterable[Path]) -> str:
    return "\n".join(f"- {path}" for path in paths)


def _default_local_docs_root() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return (
            Path(local_appdata) / "QuantSystem" / "fund-wiki" / "fund_profile_wiki_docs"
        )
    return SKILL_ROOT / ".local" / "fund_profile_wiki_docs"


def project_root_candidates(explicit: str | None = None) -> list[Path]:
    paths: list[Path] = []
    if explicit:
        paths.append(Path(explicit))
    paths.extend(_env_paths(PROJECT_ROOT_ENVS))
    paths.append(DEFAULT_PROJECT_ROOT)
    if os.environ.get("FPW_ALLOW_DEV_PROJECT_FALLBACK") == "1":
        paths.extend(_env_paths(DEV_PROJECT_ROOT_ENVS))
    return _dedupe(paths)


def raw_root_candidates(explicit: str | None = None) -> list[Path]:
    paths: list[Path] = []
    if explicit:
        paths.append(Path(explicit))
    paths.extend(_env_paths(RAW_ROOT_ENVS))
    paths.extend(RAW_ROOT_CANDIDATES)
    return _dedupe(paths)


def docs_root_candidates(
    explicit: str | None = None, allow_local_fallback: bool = False
) -> list[Path]:
    paths: list[Path] = []
    if explicit:
        paths.append(Path(explicit))
    paths.extend(_env_paths(DOCS_ROOT_ENVS))
    paths.extend(DOCS_ROOT_CANDIDATES)
    if allow_local_fallback or os.environ.get("FPW_ALLOW_LOCAL_DOCS_FALLBACK") == "1":
        local_docs = _env_paths(LOCAL_DOCS_ROOT_ENVS)
        paths.extend(local_docs or [_default_local_docs_root()])
    return _dedupe(paths)


def resolve_project_root(explicit: str | None = None) -> Path:
    candidates = project_root_candidates(explicit)
    for root in candidates:
        if _is_dir(root) and (root / "scripts" / "ingest_raw_docs.py").exists():
            return root
    raise PathResolutionError(
        "未找到 fund_profile_wiki 项目根目录。候选路径：\n"
        + _format_candidates(candidates)
    )


def resolve_raw_root(explicit: str | None = None) -> Path:
    candidates = raw_root_candidates(explicit)
    for root in candidates:
        if _is_dir(root):
            return root
    raise PathResolutionError(
        "未找到尽调材料根目录。请确认 W:/Z: 网盘或 UNC 路径可达。候选路径：\n"
        + _format_candidates(candidates)
    )


def resolve_docs_root(
    explicit: str | None = None,
    *,
    allow_local_fallback: bool = False,
    create: bool = True,
    accept_creatable: bool = False,
) -> Path:
    candidates = docs_root_candidates(
        explicit, allow_local_fallback=allow_local_fallback
    )
    for root in candidates:
        if _is_dir(root):
            return root
        try:
            parent = root.parent
            if parent.exists() and parent.is_dir():
                if accept_creatable and not create:
                    return root
                if create:
                    root.mkdir(parents=False, exist_ok=True)
                    return root
        except OSError:
            continue
    raise PathResolutionError(
        "未找到 fund_profile_wiki_docs 输出根目录。请确认 Y: 共享目录可达，或显式传入 --docs-root。候选路径：\n"
        + _format_candidates(candidates)
    )


def default_python() -> str:
    explicit = os.environ.get("FPW_PYTHON")
    if explicit:
        return explicit
    current = sys.executable
    if current:
        return current
    return "python"
