from __future__ import annotations

from fund_profile_wiki.taxonomy.strategy_taxonomy import (
    classify_strategy_text,
    expand_strategy_query_terms,
)


def test_classify_index_enhancement_strategy_text() -> None:
    result = classify_strategy_text(
        "产品定位为中证1000指数增强，行业暴露控制在3%以内，使用 Barra 风险模型。"
    )

    assert result.primary_strategy_codes == ["EQ_INDEX_ENH"]
    assert "指数增强" in result.primary_strategy_tags
    assert "1000指增" in result.secondary_strategy_tags
    assert result.strategy_facets["benchmark"] == ["中证1000"]
    assert result.strategy_tag_confidence in {"medium", "high"}
    assert result.strategy_tag_review_status == "confirmed"


def test_classify_cta_strategy_text() -> None:
    result = classify_strategy_text(
        "策略为中周期商品趋势CTA，覆盖商品期货和股指期货，收益来源包含时序动量。"
    )

    assert result.primary_strategy_codes == ["CTA"]
    assert "管理期货" in result.primary_strategy_tags
    assert "商品CTA" in result.secondary_strategy_tags
    assert "趋势CTA" in result.secondary_strategy_tags
    assert "商品期货" in result.strategy_facets["instrument"]


def test_expand_strategy_query_terms_links_aliases_to_taxonomy() -> None:
    terms = expand_strategy_query_terms("查询管理期货产品")

    assert "CTA" in terms
    assert "管理期货" in terms
    assert "量化CTA" in terms


def test_air_index_enhancement_maps_to_quant_long() -> None:
    result = classify_strategy_text("产品定位为空气指增策略，采用量化选股。")

    assert result.primary_strategy_codes == ["EQ_LONG"]
    assert "股票多头" in result.primary_strategy_tags

    terms = expand_strategy_query_terms("查询空气指增策略")
    assert "股票多头" in terms
    assert "量化多头" in terms
    assert "空气指增" in terms
