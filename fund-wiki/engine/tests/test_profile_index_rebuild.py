from __future__ import annotations

import sqlite3
from pathlib import Path

from fund_profile_wiki.index.profile_index import ProductProfileRecord, write_sqlite


def test_write_sqlite_replaces_existing_broken_index(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "product_profiles.sqlite"
    sqlite_path.write_text("not a sqlite database", encoding="utf-8")

    write_sqlite(
        [
            ProductProfileRecord(
                product_name="平方和中证1000指数增强",
                manager="平方和",
                strategy_links=["[[中证1000指数增强]]"],
                people_links=[],
                source_notes=[],
                profile_text="平方和中证1000指数增强是平方和旗下产品。",
                evidence_text="策略定位: 中证1000指数增强。",
                search_text="平方和 中证1000 指数增强",
                path="Y:\\投顾管理人研究\\fund_profile_wiki_docs\\product_profiles\\平方和中证1000指数增强.md",
                updated_at="2026-06-03",
            )
        ],
        sqlite_path,
    )

    with sqlite3.connect(sqlite_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
        fts_count = conn.execute("SELECT COUNT(*) FROM profile_fts").fetchone()[0]

    assert count == 1
    assert fts_count == 1
