from __future__ import annotations

from pathlib import Path

import fund_profile_wiki.extraction.source_note_builder as builder
import fund_profile_wiki.extraction.source_catalog as source_catalog
from fund_profile_wiki.cache.file_manifest import fingerprint_file
from fund_profile_wiki.extraction.source_catalog import build_source_catalog
from fund_profile_wiki.parsing.document_parser import ParseResult


def test_source_catalog_prioritizes_diligence_notes(tmp_path: Path) -> None:
    root = tmp_path / "raw"
    root.mkdir()
    note = root / "2026-01-08_平方和_尽调笔记.md"
    ppt = root / "平方和公司介绍.pptx"
    pdf = root / "平方和普通附件.pdf"
    for path in (note, ppt, pdf):
        path.write_text("x", encoding="utf-8")

    entries = build_source_catalog(root, "平方和")

    assert entries[0].file_name == note.name
    assert entries[0].priority == 100
    assert {entry.category for entry in entries} >= {
        "diligence_note",
        "presentation",
        "raw_pdf",
    }


def test_source_catalog_skips_encrypted_pdf_before_fingerprint(
    monkeypatch, tmp_path: Path
) -> None:
    root = tmp_path / "raw"
    root.mkdir()
    encrypted = root / "encrypted.pdf"
    encrypted.write_bytes(b"%PDF encrypted placeholder")
    note = root / "note.md"
    note.write_text("note", encoding="utf-8")

    monkeypatch.setattr(
        source_catalog.DocumentParser,
        "is_encrypted_pdf",
        staticmethod(lambda path: Path(path).name == encrypted.name),
    )

    def fake_fingerprint(path: Path):
        if Path(path).name == encrypted.name:
            raise AssertionError("encrypted PDF should be skipped before fingerprint")
        return fingerprint_file(path)

    monkeypatch.setattr(source_catalog, "fingerprint_file", fake_fingerprint)

    entries = source_catalog.build_source_catalog(root, "manager")

    assert [entry.file_name for entry in entries] == [note.name]


def test_source_catalog_skips_investment_committee_before_fingerprint(
    monkeypatch, tmp_path: Path
) -> None:
    root = tmp_path / "raw"
    root.mkdir()
    committee = root / "三亚）私募基金管理有限公司_投决会.md"
    note = root / "三亚私募基金管理有限公司_尽调笔记.md"
    committee.write_text("multi-manager committee memo", encoding="utf-8")
    note.write_text("single manager diligence note", encoding="utf-8")

    monkeypatch.setattr(source_catalog.Settings, "skip_filename_keywords", ("投决会",))

    def fake_fingerprint(path: Path):
        if Path(path).name == committee.name:
            raise AssertionError("investment committee file should be skipped before fingerprint")
        return fingerprint_file(path)

    monkeypatch.setattr(source_catalog, "fingerprint_file", fake_fingerprint)

    entries = source_catalog.build_source_catalog(root, "三亚")

    assert [entry.file_name for entry in entries] == [note.name]


def test_ingest_priority_scope_processes_high_value_files_only(
    monkeypatch, tmp_path: Path
) -> None:
    input_root = tmp_path / "input"
    source_notes_dir = tmp_path / "source_notes"
    run_logs_dir = tmp_path / "run_logs"
    input_root.mkdir()
    high = input_root / "2026_平方和_尽调笔记.md"
    low = input_root / "平方和公司介绍.pptx"
    high.write_text("high", encoding="utf-8")
    low.write_text("low", encoding="utf-8")
    monkeypatch.setattr(builder.Settings, "source_notes_dir", source_notes_dir)
    monkeypatch.setattr(builder.Settings, "run_logs_dir", run_logs_dir)
    monkeypatch.setattr(builder.Settings, "ingest_priority_min_score", 80)
    monkeypatch.setattr(builder.Settings, "parsed_cache_root", tmp_path / "parsed_cache")

    def fake_parse(path: Path, progress=None) -> ParseResult:
        return ParseResult(text=Path(path).name, method="text", chars=10)

    monkeypatch.setattr(
        builder.DocumentParser, "parse_with_metadata", staticmethod(fake_parse)
    )

    written, counts = builder.ingest_folder(
        input_root,
        manager="平方和",
        ingest_scope="priority",
    )

    assert counts["files_total"] == 1
    assert counts["processed"] == 1
    assert [path.stem for path in written] == [high.stem]
    assert (run_logs_dir / "source_catalog" / "平方和.jsonl").exists()
