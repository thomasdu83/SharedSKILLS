"""Build source notes from parsed raw text."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
import hashlib
import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fund_profile_wiki.cache.file_manifest import (
    FileFingerprint,
    PROMPT_VERSION,
    SCHEMA_VERSION,
    PARSER_VERSION,
    ManifestRecord,
    append_manifest,
    fingerprint_file,
    latest_success_by_hash,
    latest_by_path,
    load_manifest,
    manifest_path,
    now_iso,
    relpath_for,
)
from fund_profile_wiki.config import Settings
from fund_profile_wiki.extraction.llm_client import LLMClient, get_llm_config
from fund_profile_wiki.extraction.source_catalog import (
    SourceCatalogEntry,
    build_source_catalog,
    common_source_root,
    normalize_input_paths,
    should_skip_source_file,
    write_source_catalog,
)
from fund_profile_wiki.logging.progress import ProgressLogger
from fund_profile_wiki.parsing.document_parser import DocumentParser, ParseResult


class SkippedFile(RuntimeError):
    """Raised when a source file is skipped because it is unchanged."""


STRATEGY_RULES = [
    ("中证2000指数增强", ["中证2000指数增强", "中证2000指增", "2000指增", "2000增强"]),
    ("中证1000指数增强", ["中证1000指数增强", "中证1000指增", "1000指增", "1000增强"]),
    ("中证500指数增强", ["中证500指数增强", "中证500指增", "500指增", "500增强"]),
    ("沪深300指数增强", ["沪深300指数增强", "沪深300指增", "300指增", "300增强"]),
    ("指数增强", ["指数增强", "指增"]),
    ("市场中性", ["市场中性", "量化中性"]),
    ("CTA", ["CTA", "管理期货", "商品期货", "商品CTA", "股指CTA", "期权CTA"]),
    ("股票多头", ["股票多头", "量化选股"]),
]

PRODUCT_CANDIDATE_RE = re.compile(
    r"([\u4e00-\u9fffA-Za-z0-9（）()·]{2,48}(?:中证|沪深|国证)?(?:2000|1000|500|300)"
    r"[\u4e00-\u9fffA-Za-z0-9（）()·]{0,24}(?:指数增强|指增|增强)"
    r"[\u4e00-\u9fffA-Za-z0-9（）()·]{0,16})"
)


@dataclass(frozen=True)
class PreparedIngestResult:
    """Parse-stage output used by serial note writing and manifest aggregation."""

    file_path: Path
    state: str
    fingerprint: FileFingerprint | None = None
    parse_result: ParseResult | None = None
    source_note_path: Path = Path("")
    parsed_cache_path: Path = Path("")
    parsed_cache_write_failed: bool = False
    error: str = ""
    skip_reason: str = ""


def ingest_file(
    file_path: Path,
    manager: str,
    output_root: Path = Settings.source_notes_dir,
    snapshot_root: Path = Settings.source_snapshots_dir,
    use_llm: bool = False,
    provider: str = "kimi",
    prompt_path: Path | None = None,
    source_root: Path | None = None,
    snapshot_mode: str = "manifest",
    run_id: str = "",
    manifest_records_by_hash: dict[str, ManifestRecord] | None = None,
    changed_only: bool = False,
    force: bool = False,
    logger: ProgressLogger | None = None,
) -> tuple[Path, str, str, dict[str, float]]:
    """Parse one raw file and write a source note."""
    fingerprint = fingerprint_file(file_path)
    if (
        changed_only
        and not force
        and manifest_records_by_hash
        and fingerprint.sha256 in manifest_records_by_hash
    ):
        previous = manifest_records_by_hash[fingerprint.sha256]
        previous_path = Path(previous.source_note_path)
        if previous_path.exists():
            if logger:
                logger.info("ingest", f"skip unchanged file={file_path.name}")
            raise SkippedFile(str(previous_path))

    if logger:
        logger.info("parse", f"start file={file_path.name} size={fingerprint.size}")
    parse_result = DocumentParser.parse_with_metadata(file_path, progress=logger)
    text = parse_result.text
    if logger:
        logger.info(
            "parse",
            f"done file={file_path.name} status={parse_result.status} method={parse_result.method} chars={len(text)}",
        )
        for warning in parse_result.warnings:
            logger.warning("parse", f"file={file_path.name} warning={warning}")
    manager_dir = output_root / safe_filename(manager)
    manager_dir.mkdir(parents=True, exist_ok=True)
    stats = {"llm_seconds": 0.0}
    snapshot_path = Path("")
    if snapshot_mode == "copy":
        snapshot_path = build_snapshot_path(
            file_path=file_path,
            manager=manager,
            snapshot_root=snapshot_root,
            source_root=source_root,
        )
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, snapshot_path)

    if parse_result.status == "failed":
        content = build_parse_warning_source_note(
            file_path=file_path, manager=manager, parse_result=parse_result
        )
    elif use_llm:
        if logger:
            logger.info(
                "llm_extract", f"start file={file_path.name} provider={provider}"
        )
        prompt = (prompt_path or default_prompt_path()).read_text(encoding="utf-8")
        llm_started = time.perf_counter()
        content = LLMClient(provider=provider).complete(
            system_prompt=prompt,
            user_text=f"管理人提示：{manager}\n原始文件名：{file_path.name}\n\n{text}",
        )
        stats["llm_seconds"] = time.perf_counter() - llm_started
        if logger:
            logger.info(
                "llm_extract",
                f"done file={file_path.name} chars={len(content)} seconds={stats['llm_seconds']:.2f}",
            )
    else:
        content = build_raw_source_note(file_path=file_path, manager=manager, text=text)

    output_path = manager_dir / f"{safe_filename(file_path.stem)}.md"
    output_path.write_text(content.strip() + "\n", encoding="utf-8")
    if logger:
        logger.info("write_note", f"done file={file_path.name} note={output_path}")
    return (
        output_path,
        parse_result.status,
        parse_result.error or "; ".join(parse_result.warnings),
        stats,
    )


def build_manifest_record(
    file_path: Path,
    manager: str,
    source_root: Path | None,
    source_note_path: Path,
    status: str,
    snapshot_mode: str,
    snapshot_path: Path | None,
    provider: str,
    model: str,
    run_id: str,
    error: str = "",
    fingerprint: FileFingerprint | None = None,
) -> ManifestRecord:
    file_fingerprint = fingerprint or fingerprint_file(file_path)
    snapshot_path_text = (
        ""
        if snapshot_path is None or str(snapshot_path) in {"", "."}
        else str(snapshot_path)
    )
    return ManifestRecord(
        run_id=run_id,
        manager=manager,
        source_path=str(file_path),
        source_relpath=relpath_for(file_path, source_root),
        sha256=file_fingerprint.sha256,
        size=file_fingerprint.size,
        mtime=file_fingerprint.mtime,
        parsed_at=now_iso(),
        source_note_path=str(source_note_path),
        status=status,
        snapshot_mode=snapshot_mode,
        snapshot_path=snapshot_path_text,
        provider=provider,
        model=model,
        parser_version=PARSER_VERSION,
        prompt_version=PROMPT_VERSION,
        schema_version=SCHEMA_VERSION,
        error=error,
    )


def model_for(provider: str, use_llm: bool) -> str:
    if not use_llm:
        return ""
    try:
        return get_llm_config(provider).model
    except Exception:
        return ""


def fingerprint_from_catalog(entry: SourceCatalogEntry | None) -> FileFingerprint | None:
    if entry is None:
        return None
    return FileFingerprint(sha256=entry.sha256, size=entry.size, mtime=entry.mtime)


def stat_fingerprint_without_hash(path: Path) -> FileFingerprint:
    stat = path.stat()
    return FileFingerprint(
        sha256="",
        size=stat.st_size,
        mtime=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    )


def source_note_filename(file_path: Path, source_root: Path | None = None) -> str:
    try:
        relative = file_path.relative_to(source_root) if source_root else Path(file_path.name)
    except ValueError:
        relative = Path(file_path.name)
    if source_root and len(relative.parts) > 1:
        stem = "__".join(Path(part).stem if idx == len(relative.parts) - 1 else part for idx, part in enumerate(relative.parts))
    else:
        stem = file_path.stem
    return f"{safe_filename(stem)}.md"


def expected_source_note_path(
    file_path: Path, manager: str, source_root: Path | None = None
) -> Path:
    return (
        Settings.source_notes_dir
        / safe_filename(manager)
        / source_note_filename(file_path, source_root=source_root)
    )


def source_note_mentions_source_file(note_path: Path, file_path: Path) -> bool:
    try:
        head = note_path.read_text(encoding="utf-8", errors="ignore")[:8000]
    except OSError:
        return False
    return file_path.name in head


def can_reuse_existing_source_note(note_path: Path, file_path: Path) -> bool:
    if not note_path.exists() or not source_note_mentions_source_file(note_path, file_path):
        return False
    try:
        return note_path.stat().st_mtime >= file_path.stat().st_mtime
    except OSError:
        return False


def find_encrypted_pdfs(input_path: Path | list[Path]) -> list[Path]:
    input_paths = input_path if isinstance(input_path, list) else [input_path]
    return sorted(
        path
        for root in input_paths
        for path in root.rglob("*.pdf")
        if path.is_file() and DocumentParser.is_encrypted_pdf(path)
    )


def archive_encrypted_parse_warning_notes(
    *,
    input_path: Path,
    manager: str,
    encrypted_paths: list[Path],
    run_id: str,
    logger: ProgressLogger | None,
) -> int:
    if not encrypted_paths:
        return 0
    manager_dir = Settings.source_notes_dir / safe_filename(manager)
    if not manager_dir.exists():
        return 0
    encrypted_names = {path.name for path in encrypted_paths}
    archived = 0
    archive_dir = Settings.run_logs_dir / "archived_source_notes" / safe_filename(manager)
    archive_dir.mkdir(parents=True, exist_ok=True)
    for note_path in sorted(path for path in manager_dir.glob("*.md") if path.is_file()):
        try:
            content = note_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Source/ParseWarning" not in content:
            continue
        if not any(name in content for name in encrypted_names):
            continue
        archive_name = (
            f"{safe_filename(note_path.stem)}_"
            f"{safe_filename(run_id or datetime.now().strftime('%Y%m%d-%H%M%S'))}.md"
        )
        archive_path = archive_dir / archive_name
        try:
            note_path.replace(archive_path)
            archived += 1
            if logger:
                logger.info(
                    "source_note_cleanup",
                    f"archived encrypted parse warning note={note_path} archive={archive_path}",
                )
        except OSError as exc:
            if logger:
                logger.warning(
                    "source_note_cleanup",
                    f"archive failed note={note_path} error={exc}",
                )
    return archived


def write_parsed_cache(
    cache_root: Path | None,
    *,
    run_id: str,
    manager: str,
    file_path: Path,
    source_root: Path | None,
    fingerprint: FileFingerprint,
    parse_result: ParseResult,
    logger: ProgressLogger | None,
) -> Path:
    if cache_root is None:
        return Path("")
    try:
        path = parsed_cache_path_for(
            cache_root,
            run_id=run_id,
            manager=manager,
            file_path=file_path,
            source_root=source_root,
            fingerprint=fingerprint,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            build_parsed_cache_markdown(
                run_id=run_id,
                manager=manager,
                file_path=file_path,
                source_root=source_root,
                fingerprint=fingerprint,
                parse_status=parse_result.status,
                parse_method=parse_result.method,
                parse_quality_reason=parse_result.quality_reason,
                warnings=parse_result.warnings,
                error=parse_result.error,
                text=parse_result.text,
            ),
            encoding="utf-8",
        )
        if logger:
            logger.info("parsed_cache", f"written file={file_path.name} path={path}")
        return path
    except OSError as exc:
        if logger:
            logger.warning(
                "parsed_cache", f"write failed file={file_path.name} error={exc}"
            )
        return Path("")


def write_failed_parsed_cache(
    cache_root: Path | None,
    *,
    run_id: str,
    manager: str,
    file_path: Path,
    source_root: Path | None,
    fingerprint: FileFingerprint | None,
    error: str,
    logger: ProgressLogger | None,
) -> Path:
    if cache_root is None or fingerprint is None:
        return Path("")
    try:
        path = parsed_cache_path_for(
            cache_root,
            run_id=run_id,
            manager=manager,
            file_path=file_path,
            source_root=source_root,
            fingerprint=fingerprint,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            build_parsed_cache_markdown(
                run_id=run_id,
                manager=manager,
                file_path=file_path,
                source_root=source_root,
                fingerprint=fingerprint,
                parse_status="failed",
                parse_method="",
                parse_quality_reason="parse_exception",
                warnings=[],
                error=error,
                text="",
            ),
            encoding="utf-8",
        )
        if logger:
            logger.info("parsed_cache", f"written_failed file={file_path.name} path={path}")
        return path
    except OSError as exc:
        if logger:
            logger.warning(
                "parsed_cache", f"write failed file={file_path.name} error={exc}"
            )
        return Path("")


def parsed_cache_path_for(
    cache_root: Path,
    *,
    run_id: str,
    manager: str,
    file_path: Path,
    source_root: Path | None,
    fingerprint: FileFingerprint,
) -> Path:
    relpath = relpath_for(file_path, source_root)
    suffix = fingerprint.sha256[:10] if fingerprint.sha256 else "nohash"
    filename = f"{safe_filename(Path(relpath).stem)}_{suffix}.md"
    return (
        parsed_cache_manager_dir(cache_root, run_id=run_id, manager=manager)
        / filename
    )


def parsed_cache_run_dir(cache_root: Path, *, run_id: str, manager: str) -> Path:
    return cache_root / ascii_safe_filename(run_id or "manual-run")


def parsed_cache_manager_dir(cache_root: Path, *, run_id: str, manager: str) -> Path:
    return parsed_cache_run_dir(cache_root, run_id=run_id, manager=manager) / safe_filename(manager)


def ascii_safe_filename(name: str) -> str:
    text = safe_filename(name)
    ascii_text = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip(" ._")
    if ascii_text == text and ascii_text:
        return ascii_text
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    prefix = ascii_text[:80].strip(" ._") or "run"
    return f"{prefix}_{digest}"


def build_parsed_cache_markdown(
    *,
    run_id: str,
    manager: str,
    file_path: Path,
    source_root: Path | None,
    fingerprint: FileFingerprint,
    parse_status: str,
    parse_method: str,
    parse_quality_reason: str,
    warnings: list[str],
    error: str,
    text: str,
) -> str:
    metadata = {
        "run_id": run_id,
        "manager": manager,
        "source_file": file_path.name,
        "source_path": str(file_path),
        "source_relpath": relpath_for(file_path, source_root),
        "sha256": fingerprint.sha256,
        "size": fingerprint.size,
        "mtime": fingerprint.mtime,
        "parse_status": parse_status,
        "parse_method": parse_method,
        "parse_quality_reason": parse_quality_reason,
        "warnings": warnings,
        "error": error,
        "chars": len(text),
        "created_at": now_iso(),
    }
    frontmatter = "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in metadata.items()
    )
    return f"""---
{frontmatter}
---

# Parsed Text

{text}
"""


def load_parsed_cache_text(path: Path) -> str:
    if not is_real_path(path) or not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    marker = "\n# Parsed Text\n"
    marker_pos = content.find(marker)
    if marker_pos < 0:
        return content
    return content[marker_pos + len(marker) :].lstrip("\n")


def is_real_path(path: Path) -> bool:
    return bool(path) and str(path) not in {"", "."}


def _prepare_file_for_ingest(
    file_path: Path,
    manifest_records_by_hash: dict[str, ManifestRecord] | None,
    changed_only: bool,
    force: bool,
    logger: ProgressLogger | None,
    catalog_entries_by_path: dict[str, SourceCatalogEntry] | None = None,
    parsed_cache_root: Path | None = None,
    run_id: str = "",
    manager: str = "",
    source_root: Path | None = None,
    source_note_root: Path | None = None,
) -> PreparedIngestResult:
    """Compute file fingerprint and parse text without writing any output files."""

    fingerprint: FileFingerprint | None = None
    try:
        catalog_entry = (
            catalog_entries_by_path.get(str(file_path).casefold())
            if catalog_entries_by_path
            else None
        )
        fingerprint = fingerprint_from_catalog(catalog_entry) if catalog_entry else fingerprint_file(file_path)
        if (
            changed_only
            and not force
            and manifest_records_by_hash
            and fingerprint.sha256 in manifest_records_by_hash
        ):
            previous = manifest_records_by_hash[fingerprint.sha256]
            previous_path = Path(previous.source_note_path)
            if previous_path.exists():
                return PreparedIngestResult(
                    file_path=file_path,
                    state="skipped",
                    fingerprint=fingerprint,
                    source_note_path=previous_path,
                    skip_reason="manifest_hash",
                )
        if changed_only and not force:
            existing_note = expected_source_note_path(
                file_path, manager, source_note_root
            )
            if can_reuse_existing_source_note(existing_note, file_path):
                if logger:
                    logger.info(
                        "ingest",
                        f"skip existing source_note file={file_path.name} note={existing_note}",
                    )
                return PreparedIngestResult(
                    file_path=file_path,
                    state="skipped",
                    fingerprint=fingerprint,
                    source_note_path=existing_note,
                    skip_reason="existing_source_note",
                )

        if logger:
            logger.info("parse", f"start file={file_path.name} size={fingerprint.size}")
        parse_result = DocumentParser.parse_with_metadata(file_path, progress=logger)
        parsed_cache_path = write_parsed_cache(
            parsed_cache_root,
            run_id=run_id,
            manager=manager,
            file_path=file_path,
            source_root=source_root,
            fingerprint=fingerprint,
            parse_result=parse_result,
            logger=logger,
        )
        parsed_cache_write_failed = parsed_cache_root is not None and not is_real_path(parsed_cache_path)
        if logger:
            logger.info(
                "parse",
                f"done file={file_path.name} status={parse_result.status} method={parse_result.method} chars={len(parse_result.text)}",
            )
            for warning in parse_result.warnings:
                logger.warning("parse", f"file={file_path.name} warning={warning}")
        return PreparedIngestResult(
            file_path=file_path,
            state="parsed",
            fingerprint=fingerprint,
            parse_result=parse_result,
            parsed_cache_path=parsed_cache_path,
            parsed_cache_write_failed=parsed_cache_write_failed,
        )
    except Exception as exc:  # pylint: disable=broad-except
        parsed_cache_path = write_failed_parsed_cache(
            parsed_cache_root,
            run_id=run_id,
            manager=manager,
            file_path=file_path,
            source_root=source_root,
            fingerprint=fingerprint,
            error=str(exc),
            logger=logger,
        )
        if logger:
            logger.error("parse", f"failed file={file_path.name} error={exc}")
        return PreparedIngestResult(
            file_path=file_path,
            state="failed",
            fingerprint=fingerprint,
            parsed_cache_path=parsed_cache_path,
            parsed_cache_write_failed=parsed_cache_root is not None and not is_real_path(parsed_cache_path),
            error=str(exc),
        )


def _write_prepared_source_note(
    prepared: PreparedIngestResult,
    manager: str,
    use_llm: bool,
    provider: str,
    source_root: Path | None,
    source_note_root: Path | None,
    snapshot_mode: str,
    logger: ProgressLogger | None,
) -> tuple[Path, str, str, dict[str, float]]:
    """Write a source note after parse-stage work has completed."""

    if prepared.parse_result is None:
        raise RuntimeError(f"Prepared parse result missing for {prepared.file_path}")

    file_path = prepared.file_path
    parse_result = prepared.parse_result
    parsed_text = load_parsed_cache_text(prepared.parsed_cache_path) or parse_result.text
    stats = {"llm_seconds": 0.0}
    manager_dir = Settings.source_notes_dir / safe_filename(manager)
    manager_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = Path("")
    if snapshot_mode == "copy":
        snapshot_path = build_snapshot_path(
            file_path=file_path,
            manager=manager,
            snapshot_root=Settings.source_snapshots_dir,
            source_root=source_root,
        )
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, snapshot_path)

    if parse_result.status == "failed":
        content = build_parse_warning_source_note(
            file_path=file_path,
            manager=manager,
            parse_result=parse_result,
        )
    elif use_llm:
        if logger:
            logger.info(
                "llm_extract", f"start file={file_path.name} provider={provider}"
            )
        prompt = default_prompt_path().read_text(encoding="utf-8")
        llm_started = time.perf_counter()
        content = LLMClient(provider=provider).complete(
            system_prompt=prompt,
            user_text=f"管理人提示：{manager}\n原始文件名：{file_path.name}\n\n{parsed_text}",
        )
        stats["llm_seconds"] = time.perf_counter() - llm_started
        if logger:
            logger.info(
                "llm_extract",
                f"done file={file_path.name} chars={len(content)} seconds={stats['llm_seconds']:.2f}",
            )
    else:
        content = build_raw_source_note(
            file_path=file_path,
            manager=manager,
            text=parsed_text,
        )

    output_path = expected_source_note_path(
        file_path, manager, source_note_root
    )
    output_path.write_text(content.strip() + "\n", encoding="utf-8")
    if logger:
        logger.info("write_note", f"done file={file_path.name} note={output_path}")
    return (
        output_path,
        parse_result.status,
        parse_result.error or "; ".join(parse_result.warnings),
        stats,
    )


def ingest_folder(
    input_path: Path | list[Path],
    manager: str,
    use_llm: bool = False,
    provider: str = "kimi",
    snapshot_mode: str = "manifest",
    changed_only: bool = False,
    force: bool = False,
    run_id: str = "",
    log_path: str | None = None,
    parse_workers: int | None = None,
    ingest_scope: str = "all",
    parsed_cache_root: Path | None = None,
) -> tuple[list[Path], dict[str, Any]]:
    """Ingest all supported files under one or more folders."""
    if snapshot_mode == "copy":
        snapshot_mode = "manifest"
    if snapshot_mode not in {"manifest", "copy", "none"}:
        raise ValueError(f"Unsupported snapshot mode: {snapshot_mode}")
    if ingest_scope not in {"all", "priority"}:
        raise ValueError(f"Unsupported ingest scope: {ingest_scope}")
    if parsed_cache_root is None:
        parsed_cache_root = Settings.parsed_cache_root
    input_paths = normalize_input_paths(input_path)
    source_root = common_source_root(input_paths)
    source_note_root = source_root if len(input_paths) > 1 else None
    ingest_started = time.perf_counter()
    logger = ProgressLogger(run_id=run_id, log_path=log_path)
    encrypted_pdf_paths = find_encrypted_pdfs(input_paths)
    archived_parse_warning_notes = archive_encrypted_parse_warning_notes(
        input_path=source_root,
        manager=manager,
        encrypted_paths=encrypted_pdf_paths,
        run_id=run_id,
        logger=logger,
    )
    if encrypted_pdf_paths:
        logger.info(
            "catalog",
            f"encrypted_pdf skipped={len(encrypted_pdf_paths)} archived_notes={archived_parse_warning_notes}",
        )
    catalog_started = time.perf_counter()
    catalog_entries = build_source_catalog(
        input_paths,
        manager,
        source_root=source_root,
        excluded_paths=encrypted_pdf_paths,
    )
    catalog_elapsed = time.perf_counter() - catalog_started
    catalog_category_counts = Counter(entry.category for entry in catalog_entries)
    catalog_source_folder_counts = Counter(
        entry.source_folder_name or "unknown" for entry in catalog_entries
    )
    catalog_entries_by_path = {
        entry.source_path.casefold(): entry for entry in catalog_entries
    }
    catalog_path = Settings.run_logs_dir / "source_catalog" / f"{safe_filename(manager)}.jsonl"
    write_source_catalog(catalog_entries, catalog_path)
    logger.info(
        "catalog",
        f"written entries={len(catalog_entries)} path={catalog_path}",
    )
    allowed_paths = {entry.source_path for entry in catalog_entries}
    if ingest_scope == "priority":
        priority_cutoff = Settings.ingest_priority_min_score
        allowed_paths = {
            entry.source_path
            for entry in catalog_entries
            if entry.priority >= priority_cutoff
        }
        logger.info(
            "catalog",
            f"priority scope enabled cutoff={priority_cutoff} selected={len(allowed_paths)}",
        )
    all_paths = [Path(entry.source_path) for entry in catalog_entries if entry.source_path in allowed_paths]
    paths = [p for p in all_paths if not _should_skip_file(p)]
    if len(paths) < len(all_paths):
        logger.info(
            "ingest",
            f"filter skipped={len(all_paths) - len(paths)} files_total_after_filter={len(paths)}",
        )
    manifest_file = manifest_path(Settings.run_logs_dir)
    previous_records = [
        record for record in load_manifest(manifest_file) if record.manager == manager
    ]
    previous_by_hash = latest_success_by_hash(previous_records)
    previous_by_path = latest_by_path(previous_records)
    current_paths = {str(path).casefold() for path in paths}
    written: list[Path] = []
    counts = {
        "files_total": len(paths),
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "source_missing": 0,
        "encrypted_pdfs_skipped": len(encrypted_pdf_paths),
        "archived_parse_warning_notes": archived_parse_warning_notes,
        "skip_manifest_hash": 0,
        "skip_existing_source_note": 0,
        "skip_duplicate_sha": 0,
        "manifest_records_appended": 0,
        "parse_workers": 0,
        "catalog_seconds": round(catalog_elapsed, 2),
        "parse_seconds": 0.0,
        "finalize_seconds": 0.0,
        "total_seconds": 0.0,
        "llm_files": 0,
        "llm_seconds_total": 0.0,
        "llm_seconds_avg": 0.0,
        "llm_seconds_max": 0.0,
        "ocr_files": 0,
        "parsed_cache_files": 0,
        "parsed_cache_errors": 0,
        "parsed_cache_root": str(parsed_cache_root) if parsed_cache_root else "",
        "parsed_cache_run_dir": str(
            parsed_cache_run_dir(parsed_cache_root, run_id=run_id, manager=manager)
        )
        if parsed_cache_root
        else "",
        "parsed_cache_manager_dir": str(
            parsed_cache_manager_dir(parsed_cache_root, run_id=run_id, manager=manager)
        )
        if parsed_cache_root
        else "",
        "input_roots": [str(path) for path in input_paths],
        "input_root_count": len(input_paths),
        "source_root": str(source_root),
        "source_note_root": str(source_note_root) if source_note_root else "",
        "catalog_entries": len(catalog_entries),
        "catalog_category_counts": dict(catalog_category_counts),
        "catalog_source_folder_counts": dict(catalog_source_folder_counts),
    }
    model_name = model_for(provider, use_llm)

    def record_manifest(record: ManifestRecord) -> None:
        if snapshot_mode == "none":
            return
        append_manifest(manifest_file, [record])
        counts["manifest_records_appended"] += 1

    class ManifestCheckpoint:
        def append(self, record: ManifestRecord) -> None:
            record_manifest(record)

        def __iter__(self):
            return iter(())

        def __len__(self) -> int:
            return int(counts["manifest_records_appended"])

    manifest_records = ManifestCheckpoint()

    for encrypted_path in encrypted_pdf_paths:
        previous = previous_by_path.get(str(encrypted_path).casefold())
        if previous and previous.status == "skipped_encrypted":
            continue
        record_manifest(
            build_manifest_record(
                encrypted_path,
                manager,
                source_root,
                Path(""),
                "skipped_encrypted",
                snapshot_mode,
                Path(""),
                provider if use_llm else "",
                model_name,
                run_id,
                error="encrypted pdf skipped",
                fingerprint=stat_fingerprint_without_hash(encrypted_path),
            )
        )

    sorted_paths = sorted(paths)
    logger.info(
        "ingest",
        f"start manager={manager} files_total={len(paths)} use_llm={use_llm} provider={provider if use_llm else 'n/a'} snapshot={snapshot_mode} changed_only={changed_only} force={force} ingest_scope={ingest_scope}",
    )
    if parsed_cache_root:
        cache_manager_dir = parsed_cache_manager_dir(
            parsed_cache_root, run_id=run_id, manager=manager
        )
        try:
            cache_manager_dir.mkdir(parents=True, exist_ok=True)
            logger.info("parsed_cache", f"prepared path={cache_manager_dir}")
        except OSError as exc:
            logger.warning("parsed_cache", f"prepare failed path={cache_manager_dir} error={exc}")
    requested_workers = (
        parse_workers
        if parse_workers is not None
        else Settings.ingest_parse_max_workers
    )
    max_workers = max(1, min(requested_workers, len(sorted_paths) or 1))
    counts["parse_workers"] = max_workers
    parse_started = time.perf_counter()
    if len(sorted_paths) > 1 and max_workers > 1:
        logger.info("ingest", f"parallel_parse enabled workers={max_workers}")
        prepare = partial(
            _prepare_file_for_ingest,
            manifest_records_by_hash=previous_by_hash,
            changed_only=changed_only,
            force=force,
            logger=logger,
            catalog_entries_by_path=catalog_entries_by_path,
            parsed_cache_root=parsed_cache_root,
            run_id=run_id,
            manager=manager,
            source_root=source_root,
            source_note_root=source_note_root,
        )
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            prepared_results = list(executor.map(prepare, sorted_paths))
    else:
        prepared_results = [
            _prepare_file_for_ingest(
                path,
                manifest_records_by_hash=previous_by_hash,
                changed_only=changed_only,
                force=force,
                logger=logger,
                catalog_entries_by_path=catalog_entries_by_path,
                parsed_cache_root=parsed_cache_root,
                run_id=run_id,
                manager=manager,
                source_root=source_root,
                source_note_root=source_note_root,
            )
            for path in sorted_paths
        ]
    counts["parse_seconds"] = round(time.perf_counter() - parse_started, 2)
    counts["parsed_cache_files"] = sum(
        1 for prepared in prepared_results if is_real_path(prepared.parsed_cache_path)
    )
    counts["parsed_cache_errors"] = sum(
        1
        for prepared in prepared_results
        if prepared.state == "failed" and is_real_path(prepared.parsed_cache_path)
    )
    counts["parsed_cache_write_failures"] = sum(
        1 for prepared in prepared_results if prepared.parsed_cache_write_failed
    )
    counts["ocr_files"] = sum(
        1
        for prepared in prepared_results
        if prepared.parse_result is not None and prepared.parse_result.method == "ocr"
    )

    finalize_started = time.perf_counter()
    source_note_by_run_hash: dict[str, Path] = {}
    for idx, prepared in enumerate(prepared_results, start=1):
        path = prepared.file_path
        logger.info(
            "ingest",
            f"file {idx}/{len(sorted_paths)} finalize name={path.name} state={prepared.state}",
        )
        try:
            if prepared.state == "skipped":
                counts["skipped"] += 1
                if prepared.skip_reason == "existing_source_note":
                    counts["skip_existing_source_note"] += 1
                else:
                    counts["skip_manifest_hash"] += 1
                logger.info(
                    "ingest",
                    f"file {idx}/{len(sorted_paths)} skipped name={path.name} reason={prepared.skip_reason or 'manifest_hash'}",
                )
                if snapshot_mode != "none":
                    manifest_records.append(
                        build_manifest_record(
                            path,
                            manager,
                            source_root,
                            prepared.source_note_path,
                            "skipped",
                            snapshot_mode,
                            Path(""),
                            provider if use_llm else "",
                            model_name,
                            run_id,
                            fingerprint=prepared.fingerprint,
                        )
                    )
                continue

            if prepared.state == "failed":
                counts["failed"] += 1
                logger.error(
                    "ingest",
                    f"file {idx}/{len(sorted_paths)} failed name={path.name} error={prepared.error}",
                )
                if snapshot_mode != "none":
                    manifest_records.append(
                        build_manifest_record(
                            path,
                            manager,
                            source_root,
                            Path(""),
                            "failed",
                            snapshot_mode,
                            Path(""),
                            provider if use_llm else "",
                            model_name,
                            run_id,
                            error=prepared.error,
                            fingerprint=prepared.fingerprint,
                        )
                    )
                continue

            fingerprint_hash = prepared.fingerprint.sha256 if prepared.fingerprint else ""
            if (
                use_llm
                and fingerprint_hash
                and fingerprint_hash in source_note_by_run_hash
            ):
                duplicate_note_path = source_note_by_run_hash[fingerprint_hash]
                counts["skipped"] += 1
                counts["skip_duplicate_sha"] += 1
                logger.info(
                    "ingest",
                    (
                        f"file {idx}/{len(sorted_paths)} skipped name={path.name} "
                        f"reason=duplicate_sha note={duplicate_note_path}"
                    ),
                )
                if snapshot_mode != "none":
                    manifest_records.append(
                        build_manifest_record(
                            path,
                            manager,
                            source_root,
                            duplicate_note_path,
                            "skipped_duplicate_sha",
                            snapshot_mode,
                            Path(""),
                            provider if use_llm else "",
                            model_name,
                            run_id,
                            error="duplicate sha in same run; reused source note",
                            fingerprint=prepared.fingerprint,
                        )
                    )
                continue

            output_path, parse_status, parse_error, write_stats = _write_prepared_source_note(
                prepared,
                manager=manager,
                use_llm=use_llm,
                provider=provider,
                source_root=source_root,
                source_note_root=source_note_root,
                snapshot_mode=snapshot_mode,
                logger=logger,
            )
            llm_seconds = float(write_stats.get("llm_seconds", 0.0) or 0.0)
            if llm_seconds > 0:
                counts["llm_files"] += 1
                counts["llm_seconds_total"] += llm_seconds
                counts["llm_seconds_max"] = max(
                    float(counts["llm_seconds_max"]), llm_seconds
                )
            written.append(output_path)
            if (
                use_llm
                and prepared.fingerprint
                and prepared.fingerprint.sha256
                and parse_status != "failed"
            ):
                source_note_by_run_hash.setdefault(prepared.fingerprint.sha256, output_path)
            if parse_status == "failed":
                counts["failed"] += 1
                logger.warning(
                    "ingest",
                    f"file {idx}/{len(paths)} failed name={path.name} error={parse_error}",
                )
            else:
                counts["processed"] += 1
                logger.info(
                    "ingest", f"file {idx}/{len(paths)} processed name={path.name}"
                )
            snapshot_path = (
                build_snapshot_path(
                    path, manager, Settings.source_snapshots_dir, source_root
                )
                if snapshot_mode == "copy"
                else Path("")
            )
            if snapshot_mode != "none":
                manifest_records.append(
                    build_manifest_record(
                        path,
                        manager,
                        source_root,
                        output_path,
                        parse_status,
                        snapshot_mode,
                        snapshot_path,
                        provider if use_llm else "",
                        model_name,
                        run_id,
                        error=parse_error,
                        fingerprint=prepared.fingerprint,
                    )
                )
        except Exception as exc:
            counts["failed"] += 1
            logger.error(
                "ingest", f"file {idx}/{len(paths)} failed name={path.name} error={exc}"
            )
            if snapshot_mode != "none":
                manifest_records.append(
                    build_manifest_record(
                        path,
                        manager,
                        source_root,
                        Path(""),
                        "failed",
                        snapshot_mode,
                        Path(""),
                        provider if use_llm else "",
                        model_name,
                        run_id,
                        error=str(exc),
                        fingerprint=prepared.fingerprint,
                    )
                )
    for source_key, previous in previous_by_path.items():
        if source_key in current_paths:
            continue
        if previous.status == "source_missing":
            continue
        source_path = Path(previous.source_path)
        if source_path.exists():
            continue
        counts["source_missing"] += 1
        logger.warning("manifest", f"source_missing path={previous.source_path}")
        if snapshot_mode != "none":
            manifest_records.append(
                ManifestRecord(
                    run_id=run_id,
                    manager=manager,
                    source_path=previous.source_path,
                    source_relpath=previous.source_relpath,
                    sha256=previous.sha256,
                    size=previous.size,
                    mtime=previous.mtime,
                    parsed_at=now_iso(),
                    source_note_path=previous.source_note_path,
                    status="source_missing",
                    snapshot_mode=snapshot_mode,
                    snapshot_path="",
                    provider=previous.provider,
                    model=previous.model,
                    parser_version=PARSER_VERSION,
                    prompt_version=PROMPT_VERSION,
                    schema_version=SCHEMA_VERSION,
                    error="source file no longer exists",
                )
            )
    if snapshot_mode != "none":
        append_manifest(manifest_file, manifest_records)
        logger.info(
            "manifest", f"appended records={len(manifest_records)} path={manifest_file}"
        )
    counts["finalize_seconds"] = round(time.perf_counter() - finalize_started, 2)
    counts["llm_seconds_total"] = round(float(counts["llm_seconds_total"]), 2)
    if counts["llm_files"]:
        counts["llm_seconds_avg"] = round(
            float(counts["llm_seconds_total"]) / int(counts["llm_files"]), 2
        )
        counts["llm_seconds_max"] = round(float(counts["llm_seconds_max"]), 2)
    counts["total_seconds"] = round(time.perf_counter() - ingest_started, 2)
    logger.info(
        "ingest",
        f"done processed={counts['processed']} skipped={counts['skipped']} failed={counts['failed']} source_missing={counts['source_missing']} total_seconds={counts['total_seconds']} llm_seconds={counts['llm_seconds_total']}",
    )
    return written, counts


def build_raw_source_note(file_path: Path, manager: str, text: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    extracted = infer_entities_from_raw_text(
        file_path=file_path, manager=manager, text=text
    )
    product_links = [ensure_wikilink(item["name"]) for item in extracted["products"]]
    strategy_links = [ensure_wikilink(item) for item in extracted["strategies"]]
    products_json = (
        build_products_json_block(extracted["products"])
        if extracted["products"]
        else ""
    )
    return f"""---
doc_date: "{today}"
source_file: "{file_path.name}"
entity_type: "Manager"
primary_entity: "[[{manager}]]"
key_personnel: []
mentioned_products_simple: {json.dumps(product_links, ensure_ascii=False)}
main_strategies: {json.dumps(strategy_links, ensure_ascii=False)}
sub_strategies: []
strategy_links: []
other_strategies: []
tags: [Source/RawDiligence, Source/HeuristicExtract]
---

# Raw Source Note

{products_json}

## Manager
[[{manager}]]

## Raw Text
{text}
"""


def infer_entities_from_raw_text(
    file_path: Path, manager: str, text: str
) -> dict[str, list]:
    """Lightweight fallback extraction for non-LLM source notes."""
    haystack = "\n".join([file_path.stem, text[:30000]])
    strategies = infer_strategy_links(haystack)
    products = infer_product_entries(haystack, manager=manager, strategies=strategies)
    if not products and strategies:
        products = [
            {
                "name": f"{manager}{strategies[0]}",
                "main_strategies": [strategies[0]],
                "sub_strategies": [],
            }
        ]
    return {"products": products, "strategies": strategies}


def infer_strategy_links(text: str) -> list[str]:
    matched = []
    lower = text.lower()
    for strategy, aliases in STRATEGY_RULES:
        if any(alias.lower() in lower for alias in aliases):
            matched.append(strategy)
    return dedupe(matched)


def infer_product_entries(
    text: str, manager: str, strategies: list[str]
) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    for raw in PRODUCT_CANDIDATE_RE.findall(text):
        product = clean_product_candidate(raw, manager=manager)
        if not product or is_generic_strategy_name(product):
            continue
        products.append(
            {
                "name": product,
                "main_strategies": strategies[:3],
                "sub_strategies": [],
            }
        )
        if len(products) >= 12:
            break
    return dedupe_product_entries(products)


def clean_product_candidate(value: str, manager: str) -> str:
    text = value.strip()
    text = re.sub(r"^.*?[【\[][^】\]]*[】\]]", "", text)
    text = re.sub(r"(20\d{2}[-年.]?\d{1,2}[-月.]?\d{0,2}日?)$", "", text)
    text = re.sub(r"20\d{6}$", "", text)
    text = re.sub(r"(一页通|路演|材料|介绍|尽调|投决会|产品)$", "", text)
    text = text.strip(" -_（）()·：:，,。；;")
    if not text:
        return ""
    manager_short = strip_company_words(manager)
    if len(text) <= 12 and manager_short and manager_short not in text:
        text = f"{manager_short}{text}"
    return text


def is_generic_strategy_name(value: str) -> bool:
    normalized = re.sub(r"\s+", "", value)
    generic = {
        "中证2000指数增强",
        "中证1000指数增强",
        "中证500指数增强",
        "沪深300指数增强",
        "指数增强",
        "2000指增",
        "1000指增",
        "500指增",
        "300指增",
    }
    return normalized in generic


def build_products_json_block(products: list[dict[str, Any]]) -> str:
    payload = [
        {
            "name": ensure_wikilink(str(product["name"])),
            "main_strategies": [
                ensure_wikilink(item) for item in product.get("main_strategies", [])
            ],
            "sub_strategies": [
                ensure_wikilink(item) for item in product.get("sub_strategies", [])
            ],
        }
        for product in products
    ]
    return (
        "<!-- system: mentioned_products_json (generated by heuristic fallback) -->\n"
        "```json\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n"
        "```\n"
    )


def ensure_wikilink(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if text.startswith("[[") and text.endswith("]]"):
        return text
    return f"[[{text}]]"


def strip_company_words(value: str) -> str:
    text = value.strip()
    for token in [
        "私募基金管理有限公司",
        "资产管理有限公司",
        "投资管理有限公司",
        "投资有限公司",
        "有限公司",
        "合伙企业",
        "有限合伙",
    ]:
        text = text.replace(token, "")
    for prefix in ["上海", "北京", "深圳", "广州", "杭州", "宁波"]:
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip("（）()· ")


def dedupe(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        key = value.casefold()
        if value and key not in seen:
            result.append(value)
            seen.add(key)
    return result


def dedupe_product_entries(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen = set()
    for product in products:
        name = str(product.get("name", "")).strip()
        key = re.sub(r"\W+", "", name).casefold()
        if not name or key in seen:
            continue
        result.append(product)
        seen.add(key)
    return result


def build_parse_warning_source_note(
    file_path: Path, manager: str, parse_result: ParseResult
) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    warnings = "\n".join(f"- {warning}" for warning in parse_result.warnings) or "- n/a"
    extracted_text = parse_result.text.strip() or "[No usable text extracted.]"
    extracted = infer_entities_from_raw_text(
        file_path=file_path, manager=manager, text=extracted_text
    )
    product_links = [ensure_wikilink(item["name"]) for item in extracted["products"]]
    strategy_links = [ensure_wikilink(item) for item in extracted["strategies"]]
    products_json = (
        build_products_json_block(extracted["products"])
        if extracted["products"]
        else ""
    )
    return f"""---
doc_date: "{today}"
source_file: "{file_path.name}"
entity_type: "Manager"
primary_entity: "[[{manager}]]"
key_personnel: []
mentioned_products_simple: {json.dumps(product_links, ensure_ascii=False)}
main_strategies: {json.dumps(strategy_links, ensure_ascii=False)}
sub_strategies: []
strategy_links: []
other_strategies: []
tags: [Source/RawDiligence, Source/ParseWarning, Source/HeuristicExtract]
parse_status: "{parse_result.status}"
parse_method: "{parse_result.method}"
parse_quality_reason: "{parse_result.quality_reason}"
---

# Parse Warning Source Note

{products_json}

## Manager
[[{manager}]]

## What Happened

This file likely needs OCR, but fund-wiki could not obtain reliable OCR text. The deposit workflow continued and recorded this warning note.

## Warnings
{warnings}

## Error
{parse_result.error or "n/a"}

## Extracted Text
{extracted_text}
"""


def default_prompt_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "templates"
        / "prompt_diligence_extract.md"
    )


def build_snapshot_path(
    file_path: Path,
    manager: str,
    snapshot_root: Path,
    source_root: Path | None = None,
) -> Path:
    try:
        relative = (
            file_path.relative_to(source_root) if source_root else Path(file_path.name)
        )
    except ValueError:
        relative = Path(file_path.name)
    safe_parts = [safe_filename(part) for part in relative.parts]
    return snapshot_root / safe_filename(manager) / Path(*safe_parts)


def safe_filename(name: str) -> str:
    for ch in '<>:"/\\|?*\n\r\t':
        name = name.replace(ch, "_")
    return name.strip(" .") or "untitled"


def _should_skip_file(path: Path) -> bool:
    return should_skip_source_file(path)
