#!/usr/bin/env python3
"""Environment-file loading helpers for fund-wiki skill scripts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from _paths import SKILL_ROOT


ENV_FILE_ENVS = ("FPW_ENV_FILE", "FUND_WIKI_ENV_FILE")
QUANT_SYSTEM_ROOT = SKILL_ROOT.parents[2] if len(SKILL_ROOT.parents) >= 3 else SKILL_ROOT
MACRO_SCORE_ENV_FILE = QUANT_SYSTEM_ROOT / "domains" / "macro" / "external-report-macro-score" / "src" / ".env"


def _dedupe(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).casefold()
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def env_file_candidates(explicit: str | None = None) -> list[Path]:
    paths: list[Path] = []
    if explicit:
        paths.append(Path(explicit))
    for env_var in ENV_FILE_ENVS:
        value = os.environ.get(env_var)
        if value:
            paths.append(Path(value))
    paths.extend(
        [
            SKILL_ROOT / ".env",
            QUANT_SYSTEM_ROOT / ".env",
            MACRO_SCORE_ENV_FILE,
            Path.cwd() / ".env",
        ]
    )
    return _dedupe(paths)


def load_env_files(explicit: str | None = None) -> list[Path]:
    """Load existing .env files without overriding already-set environment variables."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return []

    loaded: list[Path] = []
    for path in env_file_candidates(explicit):
        try:
            if path.exists() and path.is_file():
                load_dotenv(path, override=False)
                loaded.append(path)
        except OSError:
            continue
    return loaded

