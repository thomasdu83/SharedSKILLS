"""Build a lightweight catalog for due-diligence source files."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
import re
from pathlib import Path
from typing import Iterable

from fund_profile_wiki.cache.file_manifest import fingerprint_file, relpath_for
from fund_profile_wiki.config import Settings
from fund_profile_wiki.parsing.document_parser import DocumentParser


@dataclass(frozen=True)
class SourceCatalogEntry:
    manager: str
    source_path: str
    source_relpath: str
    file_name: str
    suffix: str
    priority: int
    category: str
    date_hint: str
    size: int
    mtime: str
    sha256: str
    source_folder_name: str = ""
    source_folder_path: str = ""


PRIORITY_RULES: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    ("diligence_note", 100, ("尽调笔记", "尽调摘要", "尽调反馈", "调研纪要")),
    ("meeting_or_interview", 90, ("会议纪要", "通话记录", "路演纪要", "访谈")),
    ("product_report", 70, ("月报", "产品报告", "业绩归因", "定期报告", "净值")),
    ("presentation", 55, ("路演", "公司介绍", "策略介绍", "标准版", "材料")),
    ("raw_pdf", 45, (".pdf", ".pptx", ".docx")),
    ("audio_or_low_signal", 20, (".mp3", ".m4a", ".wav", ".png", ".jpg", ".jpeg")),
)


def build_source_catalog(
    input_path: Path | Iterable[Path],
    manager: str,
    *,
    source_root: Path | None = None,
    supported_extensions: Iterable[str] = Settings.supported_extensions,
    excluded_paths: Iterable[str | Path] | None = None,
) -> list[SourceCatalogEntry]:
    input_paths = normalize_input_paths(input_path)
    effective_source_root = source_root or common_source_root(input_paths)
    suffixes = {suffix.lower() for suffix in supported_extensions}
    excluded = {
        str(Path(path)).casefold() for path in (excluded_paths or [])
    }
    check_encryption = excluded_paths is None
    entries: list[SourceCatalogEntry] = []
    for root in input_paths:
        paths = [
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix.lower() in suffixes
            and not should_skip_source_file(path)
            and str(path).casefold() not in excluded
            and (not check_encryption or not DocumentParser.is_encrypted_pdf(path))
        ]
        entries.extend(
            catalog_entry(
                path,
                manager,
                effective_source_root,
                source_folder=root,
            )
            for path in paths
        )
    return sorted(
        entries,
        key=lambda item: (-item.priority, item.date_hint or "", item.file_name),
        reverse=False,
    )


def normalize_input_paths(input_path: Path | Iterable[Path]) -> list[Path]:
    if isinstance(input_path, (str, Path)):
        raw_paths = [Path(input_path)]
    else:
        raw_paths = [Path(path) for path in input_path]
    roots = [path.parent if path.is_file() else path for path in raw_paths]
    return [root for root in roots if root.exists()]


def common_source_root(input_paths: Iterable[Path]) -> Path:
    roots = list(input_paths)
    if not roots:
        return Path(".")
    if len(roots) == 1:
        return roots[0]
    try:
        return Path(os.path.commonpath([str(path.resolve(strict=False)) for path in roots]))
    except ValueError:
        return roots[0]


def catalog_entry(
    path: Path,
    manager: str,
    source_root: Path,
    *,
    source_folder: Path | None = None,
) -> SourceCatalogEntry:
    fingerprint = fingerprint_file(path)
    category, priority = classify_file(path)
    return SourceCatalogEntry(
        manager=manager,
        source_path=str(path),
        source_relpath=relpath_for(path, source_root),
        file_name=path.name,
        suffix=path.suffix.lower(),
        priority=priority,
        category=category,
        date_hint=extract_date_hint(path.name),
        size=fingerprint.size,
        mtime=fingerprint.mtime,
        sha256=fingerprint.sha256,
        source_folder_name=source_folder.name if source_folder else "",
        source_folder_path=str(source_folder) if source_folder else "",
    )


def classify_file(path: Path) -> tuple[str, int]:
    name = path.name.lower()
    suffix = path.suffix.lower()
    for category, priority, keywords in PRIORITY_RULES:
        for keyword in keywords:
            if keyword.startswith("."):
                if suffix == keyword:
                    return category, priority
            elif keyword.lower() in name:
                return category, priority
    if suffix in {".md", ".txt"}:
        return "text_note", 60
    return "other", 40


def should_skip_source_file(path: Path) -> bool:
    name = path.stem
    return any(keyword in name for keyword in Settings.skip_filename_keywords)


def extract_date_hint(file_name: str) -> str:
    patterns = [
        r"(20\d{2})[-_年. ]?(\d{1,2})[-_月. ]?(\d{1,2})",
        r"(20\d{2})(\d{2})(\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, file_name)
        if not match:
            continue
        year, month, day = (int(part) for part in match.groups())
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def write_source_catalog(entries: Iterable[SourceCatalogEntry], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    return path
