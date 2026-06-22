"""Append-only source file manifest and hash helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


MANIFEST_FILENAME = "source_manifest.jsonl"
PARSER_VERSION = "fund-wiki-parser-v1"
PROMPT_VERSION = "fund-wiki-extract-md-v1"
SCHEMA_VERSION = "markdown-v1"


@dataclass(frozen=True)
class FileFingerprint:
    sha256: str
    size: int
    mtime: str


@dataclass(frozen=True)
class ManifestRecord:
    run_id: str
    manager: str
    source_path: str
    source_relpath: str
    sha256: str
    size: int
    mtime: str
    parsed_at: str
    source_note_path: str
    status: str
    snapshot_mode: str
    snapshot_path: str
    provider: str
    model: str
    parser_version: str
    prompt_version: str
    schema_version: str
    error: str = ""


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def fingerprint_file(path: Path) -> FileFingerprint:
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return FileFingerprint(
        sha256=digest.hexdigest(),
        size=stat.st_size,
        mtime=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    )


def manifest_path(run_logs_dir: Path) -> Path:
    return run_logs_dir / MANIFEST_FILENAME


def load_manifest(path: Path) -> list[ManifestRecord]:
    if not path.exists():
        return []
    records: list[ManifestRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                records.append(ManifestRecord(**payload))
            except (TypeError, json.JSONDecodeError):
                continue
    return records


def append_manifest(path: Path, records: Iterable[ManifestRecord]) -> None:
    rows = list(records)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in rows:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def latest_success_by_hash(records: Iterable[ManifestRecord]) -> dict[str, ManifestRecord]:
    result: dict[str, ManifestRecord] = {}
    for record in records:
        if record.status in {"success", "partial_success"}:
            result[record.sha256] = record
    return result


def latest_by_path(records: Iterable[ManifestRecord]) -> dict[str, ManifestRecord]:
    result: dict[str, ManifestRecord] = {}
    for record in records:
        result[record.source_path.casefold()] = record
    return result


def relpath_for(file_path: Path, source_root: Path | None) -> str:
    try:
        return str(file_path.relative_to(source_root)) if source_root else file_path.name
    except ValueError:
        return file_path.name
