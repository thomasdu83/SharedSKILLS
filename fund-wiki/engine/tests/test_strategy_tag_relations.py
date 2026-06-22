from __future__ import annotations

from pathlib import Path

from fund_profile_wiki.index.profile_index import ProductProfileRecord
from fund_profile_wiki.index.relation_index import build_relation_records


def test_relation_index_emits_strategy_taxonomy_relations(tmp_path: Path) -> None:
    record = ProductProfileRecord(
        product_name="Gamma稳健1号",
        manager="上海伽马投资有限公司",
        strategy_links=[],
        people_links=[],
        source_notes=[],
        profile_text="",
        evidence_text="",
        search_text="",
        path=str(tmp_path / "gamma.md"),
        updated_at="2026-06-04",
        primary_strategy_tags=["管理期货"],
        secondary_strategy_tags=["商品CTA"],
        strategy_facets={"instrument": ["期货"], "horizon": ["中周期"]},
        strategy_evidence=["材料写明该产品为中周期商品CTA。"],
        strategy_tag_confidence="high",
    )

    relations = build_relation_records([record])
    relation_pairs = {(item.predicate, item.object) for item in relations}

    assert ("has_primary_strategy", "管理期货") in relation_pairs
    assert ("has_secondary_strategy", "商品CTA") in relation_pairs
    assert ("has_strategy_facet", "instrument=期货") in relation_pairs
    assert ("has_strategy_facet", "horizon=中周期") in relation_pairs
