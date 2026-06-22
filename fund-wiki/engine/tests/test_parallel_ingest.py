from __future__ import annotations

from pathlib import Path
from typing import Literal

import fund_profile_wiki.extraction.source_note_builder as builder
from fund_profile_wiki.cache.file_manifest import (
    ManifestRecord,
    append_manifest,
    fingerprint_file,
    load_manifest,
    manifest_path,
    now_iso,
)
from fund_profile_wiki.parsing.document_parser import ParseResult


class _FakeExecutor:
    def __init__(self, max_workers: int, captured: dict[str, int]):
        self.max_workers = max_workers
        self._captured = captured

    def __enter__(self) -> _FakeExecutor:
        self._captured["max_workers"] = self.max_workers
        return self

    def __exit__(self, exc_type, exc, tb) -> Literal[False]:
        return False

    def map(self, func, iterable):
        for item in iterable:
            yield func(item)


class _FakeLLMConfig:
    model = "fake-model"


class _CountingLLMClient:
    calls: list[str] = []

    def __init__(self, provider: str = "deepseek"):
        self.provider = provider

    def complete(self, system_prompt: str, user_text: str, max_tokens: int = 4096) -> str:
        self.calls.append(user_text)
        return """---
doc_date: "2026-06-05"
source_file: "fake.txt"
entity_type: "Manager"
primary_entity: "[[平方和]]"
key_personnel: []
mentioned_products_simple: []
main_strategies: []
sub_strategies: []
strategy_links: []
other_strategies: []
tags: [Source/Diligence]
---

# Fake Source Note
"""


def _configure_paths(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    source_notes_dir = tmp_path / "source_notes"
    run_logs_dir = tmp_path / "run_logs"
    monkeypatch.setattr(builder.Settings, "source_notes_dir", source_notes_dir)
    monkeypatch.setattr(builder.Settings, "run_logs_dir", run_logs_dir)
    monkeypatch.setattr(
        builder.Settings, "source_snapshots_dir", tmp_path / "source_snapshots"
    )
    monkeypatch.setattr(builder.Settings, "parsed_cache_root", tmp_path / "parsed_cache")
    return source_notes_dir, run_logs_dir


def test_ingest_folder_parallelizes_parse_stage_and_writes_manifest_serially(
    monkeypatch, tmp_path: Path
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    for name in ("alpha.md", "beta.txt", "gamma.md"):
        (input_root / name).write_text(f"raw-{name}", encoding="utf-8")

    source_notes_dir, run_logs_dir = _configure_paths(monkeypatch, tmp_path)
    captured: dict[str, int] = {}
    monkeypatch.setattr(
        builder,
        "ThreadPoolExecutor",
        lambda max_workers: _FakeExecutor(max_workers, captured),
    )

    def fake_parse(path: Path, progress=None) -> ParseResult:
        return ParseResult(text=f"parsed::{Path(path).name}", method="text", chars=16)

    monkeypatch.setattr(
        builder.DocumentParser, "parse_with_metadata", staticmethod(fake_parse)
    )

    written, counts = builder.ingest_folder(
        input_root,
        manager="平方和",
        parse_workers=3,
    )

    assert captured["max_workers"] == 3
    expected_counts = {
        "files_total": 3,
        "processed": 3,
        "skipped": 0,
        "failed": 0,
        "source_missing": 0,
        "parsed_cache_files": 3,
        "parsed_cache_errors": 0,
        "parsed_cache_root": str(tmp_path / "parsed_cache"),
        "parsed_cache_run_dir": str(tmp_path / "parsed_cache" / "manual-run"),
        "parsed_cache_manager_dir": str(
            tmp_path / "parsed_cache" / "manual-run" / "平方和"
        ),
    }
    for key, value in expected_counts.items():
        assert counts[key] == value
    assert [path.name for path in written] == ["alpha.md", "beta.md", "gamma.md"]
    assert all(path.exists() for path in written)

    records = load_manifest(manifest_path(run_logs_dir))
    assert len(records) == 3
    assert {record.status for record in records} == {"success"}
    assert all(
        record.source_note_path.startswith(str(source_notes_dir)) for record in records
    )
    assert len(list((tmp_path / "parsed_cache").rglob("*.md"))) == 3


def test_ingest_folder_accepts_multiple_roots_without_note_name_collision(
    monkeypatch, tmp_path: Path
) -> None:
    raw_root = tmp_path / "raw"
    folder_a = raw_root / "353725_ManagerA"
    folder_b = raw_root / "353725_ManagerAlias"
    folder_a.mkdir(parents=True)
    folder_b.mkdir(parents=True)
    (folder_a / "note.md").write_text("content-a", encoding="utf-8")
    (folder_b / "note.md").write_text("content-b", encoding="utf-8")

    source_notes_dir, run_logs_dir = _configure_paths(monkeypatch, tmp_path)

    def fake_parse(path: Path, progress=None) -> ParseResult:
        return ParseResult(text=f"parsed::{Path(path).parent.name}", method="text", chars=16)

    monkeypatch.setattr(
        builder.DocumentParser, "parse_with_metadata", staticmethod(fake_parse)
    )

    written, counts = builder.ingest_folder(
        [folder_a, folder_b],
        manager="ManagerA",
        parse_workers=2,
    )

    assert counts["input_root_count"] == 2
    assert counts["source_root"] == str(raw_root)
    assert counts["catalog_source_folder_counts"] == {
        "353725_ManagerA": 1,
        "353725_ManagerAlias": 1,
    }
    assert sorted(path.name for path in written) == [
        "353725_ManagerA__note.md",
        "353725_ManagerAlias__note.md",
    ]
    assert all(path.exists() for path in written)

    records = load_manifest(manifest_path(run_logs_dir))
    assert len(records) == 2
    assert {Path(record.source_relpath).parts[0] for record in records} == {
        "353725_ManagerA",
        "353725_ManagerAlias",
    }
    assert all(
        record.source_note_path.startswith(str(source_notes_dir)) for record in records
    )


def test_ingest_folder_skips_unchanged_files_before_parse(
    monkeypatch, tmp_path: Path
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    source_file = input_root / "same.md"
    source_file.write_text("unchanged", encoding="utf-8")

    source_notes_dir, run_logs_dir = _configure_paths(monkeypatch, tmp_path)
    existing_note = source_notes_dir / "平方和" / "same.md"
    existing_note.parent.mkdir(parents=True, exist_ok=True)
    existing_note.write_text("existing note", encoding="utf-8")

    fingerprint = fingerprint_file(source_file)
    append_manifest(
        manifest_path(run_logs_dir),
        [
            ManifestRecord(
                run_id="old-run",
                manager="平方和",
                source_path=str(source_file),
                source_relpath=source_file.name,
                sha256=fingerprint.sha256,
                size=fingerprint.size,
                mtime=fingerprint.mtime,
                parsed_at=now_iso(),
                source_note_path=str(existing_note),
                status="success",
                snapshot_mode="manifest",
                snapshot_path="",
                provider="",
                model="",
                parser_version="test",
                prompt_version="test",
                schema_version="test",
            )
        ],
    )

    def fail_if_called(path: Path, progress=None) -> ParseResult:
        raise AssertionError(f"parse should not be called for unchanged file: {path}")

    monkeypatch.setattr(
        builder.DocumentParser, "parse_with_metadata", staticmethod(fail_if_called)
    )

    written, counts = builder.ingest_folder(
        input_root,
        manager="平方和",
        changed_only=True,
        parse_workers=4,
    )

    assert written == []
    expected_counts = {
        "files_total": 1,
        "processed": 0,
        "skipped": 1,
        "failed": 0,
        "source_missing": 0,
        "parsed_cache_files": 0,
        "parsed_cache_errors": 0,
        "parsed_cache_root": str(tmp_path / "parsed_cache"),
        "parsed_cache_run_dir": str(tmp_path / "parsed_cache" / "manual-run"),
        "parsed_cache_manager_dir": str(
            tmp_path / "parsed_cache" / "manual-run" / "平方和"
        ),
    }
    for key, value in expected_counts.items():
        assert counts[key] == value

    records = load_manifest(manifest_path(run_logs_dir))
    assert len(records) == 2
    assert records[-1].status == "skipped"
    assert records[-1].source_note_path == str(existing_note)


def test_ingest_folder_reuses_same_run_duplicate_sha_before_llm(
    monkeypatch, tmp_path: Path
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    (input_root / "alpha.txt").write_text("same raw content", encoding="utf-8")
    (input_root / "beta.txt").write_text("same raw content", encoding="utf-8")

    source_notes_dir, run_logs_dir = _configure_paths(monkeypatch, tmp_path)
    _CountingLLMClient.calls = []
    monkeypatch.setattr(builder, "get_llm_config", lambda provider: _FakeLLMConfig())
    monkeypatch.setattr(builder, "LLMClient", _CountingLLMClient)
    monkeypatch.setattr(
        builder.DocumentParser,
        "parse_with_metadata",
        staticmethod(
            lambda path, progress=None: ParseResult(
                text=f"parsed::{Path(path).name}",
                method="text",
                chars=16,
            )
        ),
    )

    written, counts = builder.ingest_folder(
        input_root,
        manager="平方和",
        use_llm=True,
        provider="deepseek",
        parse_workers=2,
    )

    assert len(_CountingLLMClient.calls) == 1
    assert [path.name for path in written] == ["alpha.md"]
    assert counts["processed"] == 1
    assert counts["skipped"] == 1
    assert counts["skip_duplicate_sha"] == 1
    assert counts["llm_files"] == 1

    records = load_manifest(manifest_path(run_logs_dir))
    assert [record.status for record in records] == [
        "success",
        "skipped_duplicate_sha",
    ]
    assert records[1].source_note_path == records[0].source_note_path
    assert records[0].source_note_path.startswith(str(source_notes_dir))
