from __future__ import annotations

from pathlib import Path

import fund_profile_wiki.extraction.source_note_builder as builder
from fund_profile_wiki.parsing.document_parser import ParseResult


def configure_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(builder.Settings, "source_notes_dir", tmp_path / "source_notes")
    monkeypatch.setattr(builder.Settings, "run_logs_dir", tmp_path / "run_logs")
    monkeypatch.setattr(
        builder.Settings, "source_snapshots_dir", tmp_path / "source_snapshots"
    )
    monkeypatch.setattr(builder.Settings, "parsed_cache_root", tmp_path / "parsed_cache")


def test_ingest_reuses_catalog_fingerprint_for_prepare_stage(
    monkeypatch, tmp_path: Path
) -> None:
    configure_paths(monkeypatch, tmp_path)
    input_root = tmp_path / "input"
    input_root.mkdir()
    source_file = input_root / "alpha.md"
    source_file.write_text("raw alpha", encoding="utf-8")

    def fake_parse(path: Path, progress=None) -> ParseResult:
        return ParseResult(text=f"parsed::{Path(path).name}", method="text", chars=16)

    monkeypatch.setattr(
        builder.DocumentParser, "parse_with_metadata", staticmethod(fake_parse)
    )
    monkeypatch.setattr(
        builder,
        "fingerprint_file",
        lambda path: (_ for _ in ()).throw(
            AssertionError("prepare stage should reuse source_catalog fingerprint")
        ),
    )

    written, counts = builder.ingest_folder(input_root, manager="平方和")

    assert len(written) == 1
    assert counts["processed"] == 1
    assert counts["parsed_cache_files"] == 1
    assert list((tmp_path / "parsed_cache").rglob("*.md"))


def test_llm_input_prefers_local_parsed_cache(monkeypatch, tmp_path: Path) -> None:
    configure_paths(monkeypatch, tmp_path)
    input_root = tmp_path / "input"
    input_root.mkdir()
    source_file = input_root / "alpha.md"
    source_file.write_text("raw alpha", encoding="utf-8")
    captured: dict[str, str] = {}

    def fake_parse(path: Path, progress=None) -> ParseResult:
        return ParseResult(text="from parse", method="text", chars=10)

    def fake_write_cache(*args, **kwargs) -> Path:
        cache_root = tmp_path / "parsed_cache"
        cache_path = cache_root / "manual-run" / "平方和" / "alpha_cache.md"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            "---\nsource_file: alpha.md\n---\n\n# Parsed Text\n\nfrom cache",
            encoding="utf-8",
        )
        return cache_path

    class FakeLLMClient:
        def __init__(self, provider: str):
            self.provider = provider

        def complete(self, *, system_prompt: str, user_text: str) -> str:
            captured["user_text"] = user_text
            return """---
doc_date: "2026-06-03"
source_file: "alpha.md"
entity_type: "Manager"
primary_entity: "[[平方和]]"
mentioned_products_simple: []
main_strategies: []
tags: [Source/LLMExtract]
---

# LLM Note
"""

    monkeypatch.setattr(
        builder.DocumentParser, "parse_with_metadata", staticmethod(fake_parse)
    )
    monkeypatch.setattr(builder, "write_parsed_cache", fake_write_cache)
    monkeypatch.setattr(builder, "LLMClient", FakeLLMClient)

    written, counts = builder.ingest_folder(
        input_root,
        manager="平方和",
        use_llm=True,
        provider="deepseek",
    )

    assert len(written) == 1
    assert counts["processed"] == 1
    assert "from cache" in captured["user_text"]
    assert "from parse" not in captured["user_text"]
