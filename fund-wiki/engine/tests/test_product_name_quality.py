from __future__ import annotations

import json
from pathlib import Path

from fund_profile_wiki.index.profile_index import build_profile_index, read_jsonl
from fund_profile_wiki.notes.diligence_note_reader import parse_frontmatter
from fund_profile_wiki.profiles.manager_wiki_compiler import write_manager_wiki_docs
from fund_profile_wiki.profiles.manager_alias_registry import (
    clear_manager_alias_registry_cache,
)
from fund_profile_wiki.profiles.product_name_normalizer import (
    analyze_product_name,
    generate_manager_aliases,
    manager_identity_key,
)
from fund_profile_wiki.profiles.product_profile_compiler import (
    ProductProfile,
    ProductProfileCompiler,
)
from fund_profile_wiki.query.profile_query_engine import execute_profile_query


def test_product_name_normalizer_marks_strategy_product_line_as_generic() -> None:
    analysis = analyze_product_name("中证1000指数增强产品", "平方和")

    assert analysis.is_generic is True
    assert analysis.family == "1000_index_enhancement"
    assert analysis.quality_status == "weak_line"
    assert analysis.reason == "strategy_product_line"
    assert analysis.entity_type == "strategy_line"
    assert analysis.entity_confidence == "low"
    assert "strategy_product_line" in analysis.review_reasons
    assert analysis.canonical_name == "平方和中证1000指数增强"


def test_product_name_normalizer_normalizes_chinese_number_variants() -> None:
    first = analyze_product_name("双隆-隆元1号", "上海双隆投资有限公司")
    second = analyze_product_name("隆元一号", "上海双隆投资有限公司")

    assert first.canonical_key == second.canonical_key
    assert first.is_generic is False
    assert second.is_generic is False


def test_fenced_yaml_source_note_frontmatter_is_parsed() -> None:
    frontmatter, body = parse_frontmatter(
        """```yaml
---
entity_type: "Manager"
primary_entity: "[[海南半鞅私募基金管理合伙企业（有限合伙）]]"
mentioned_products_simple: ["[[半鞅CTA均衡一号]]"]
main_strategies: ["[[CTA]]"]
---
```

### [[半鞅CTA均衡一号]]
- 产品要素：CTA产品。
"""
    )

    assert frontmatter["entity_type"] == "Manager"
    assert frontmatter["primary_entity"] == "[[海南半鞅私募基金管理合伙企业（有限合伙）]]"
    assert body.startswith("### [[半鞅CTA均衡一号]]")


def test_product_name_normalizer_unifies_manager_variants() -> None:
    first = analyze_product_name("双隆-隆成拓展1号", "上海双隆投资有限公司")
    second = analyze_product_name("隆成拓展1号", "双隆投资")
    third = analyze_product_name("隆成拓展1号", "双隆")

    assert first.canonical_key == second.canonical_key
    assert second.canonical_key == third.canonical_key


def test_product_name_normalizer_unifies_city_private_manager_variants() -> None:
    first = manager_identity_key("托特私募")
    second = manager_identity_key("托特（三亚）私募基金管理有限公司")
    third = manager_identity_key("三亚托特私募")

    assert first == second
    assert second == third
    assert "托特" in generate_manager_aliases("托特（三亚）私募基金管理有限公司")
    assert "托特私募" in generate_manager_aliases("托特（三亚）私募基金管理有限公司")


def test_product_name_normalizer_unifies_partnership_manager_variants() -> None:
    first = manager_identity_key("半鞅")
    second = manager_identity_key("海南半鞅私募基金管理合伙企业（有限合伙）")
    third = manager_identity_key("半鞅私募基金")
    fourth = manager_identity_key("海南半鞅私募基金管理合伙企业")

    assert first == second
    assert second == third
    assert third == fourth
    aliases = generate_manager_aliases("海南半鞅私募基金管理合伙企业（有限合伙）")
    assert "半鞅" in aliases
    assert "半鞅私募基金" in aliases
    assert "海南半鞅私募基金管理合伙企业" in aliases


def test_product_name_normalizer_unifies_limited_liability_manager_variants() -> None:
    first = manager_identity_key("添益")
    second = manager_identity_key("上海添益私募基金管理有限责任公司")

    assert first == second
    aliases = generate_manager_aliases("上海添益私募基金管理有限责任公司")
    assert "添益" in aliases
    assert "添益私募" in aliases


def test_product_name_normalizer_unifies_district_manager_variants() -> None:
    first = manager_identity_key("山信资本")
    second = manager_identity_key("杭州萧山山信私募基金管理有限公司")
    third = manager_identity_key("萧山山信")

    assert first == second
    assert second == third
    aliases = generate_manager_aliases("杭州萧山山信私募基金管理有限公司")
    assert "山信资本" in aliases
    assert "杭州萧山山信私募基金管理有限公司" in aliases


def test_product_name_normalizer_keeps_turing_legal_entities_distinct() -> None:
    shenzhen = manager_identity_key("深圳市图灵投资管理有限公司")
    hainan = manager_identity_key("图灵私募基金管理（海南）有限公司")

    assert shenzhen == manager_identity_key("深圳图灵")
    assert hainan == manager_identity_key("海南图灵")
    assert shenzhen != hainan
    assert manager_identity_key("图灵") not in {shenzhen, hainan}


def test_product_name_normalizer_unifies_province_manager_variants() -> None:
    first = manager_identity_key("宏锡")
    second = manager_identity_key("宏锡基金")
    third = manager_identity_key("广东宏锡基金管理有限公司")

    assert first == second
    assert second == third
    aliases = generate_manager_aliases("广东宏锡基金管理有限公司")
    assert "宏锡" in aliases
    assert "宏锡基金" in aliases


def test_manager_alias_registry_overrides_heuristic_identity(
    tmp_path: Path, monkeypatch
) -> None:
    alias_file = tmp_path / "manager-aliases.yaml"
    alias_file.write_text(
        """
managers:
  - canonical: 蓝海
    identity_key: 蓝海
    aliases:
      - 蔚蓝海岸投资管理有限公司
      - 蓝海量化
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("FPW_MANAGER_ALIAS_FILE", str(alias_file))
    clear_manager_alias_registry_cache()

    try:
        assert manager_identity_key("蓝海") == manager_identity_key(
            "蔚蓝海岸投资管理有限公司"
        )
        aliases = generate_manager_aliases("蓝海")
        assert "蔚蓝海岸投资管理有限公司" in aliases
        assert "蓝海量化" in aliases
    finally:
        clear_manager_alias_registry_cache()


def test_product_name_normalizer_marks_suspicious_short_names_for_review() -> None:
    analysis = analyze_product_name("信弘", "托特（三亚）私募基金管理有限公司")

    assert analysis.quality_status == "needs_review"
    assert analysis.reason == "suspicious_short_name"
    assert analysis.entity_type == "product"
    assert analysis.entity_confidence == "medium"


def test_product_name_normalizer_marks_generic_tail_products_as_weak() -> None:
    analysis = analyze_product_name("半鞅对冲产品", "海南半鞅私募基金")

    assert analysis.is_generic is True
    assert analysis.quality_status == "weak_line"
    assert analysis.reason == "generic_product_tail"
    assert analysis.entity_type == "generic_bucket"


def test_product_name_normalizer_treats_manager_private_fund_prefix_as_prefix() -> None:
    analysis = analyze_product_name("半鞅私募基金中证500指数增强", "海南半鞅私募基金")

    assert analysis.is_generic is True
    assert analysis.reason in {
        "pure_strategy_name",
        "manager_strategy_line",
        "strategy_product_line",
    }


def test_enrich_profile_filters_cross_benchmark_index_tags() -> None:
    profile = ProductProfile(
        product_name="托特1000指增",
        manager="托特私募",
        strategy_links=["[[300指增]]", "[[1000指增]]", "[[指数增强]]"],
    )

    ProductProfileCompiler().enrich_profile(profile, include_external=False)

    assert "1000指增" in profile.secondary_strategy_tags
    assert "300指增" not in profile.secondary_strategy_tags
    assert "中证1000指增" in profile.product_line
    assert "沪深300指增" not in profile.product_line


def test_compiler_merges_generic_product_line_into_real_product(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes" / "平方和"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir(parents=True)
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[平方和]]"
mentioned_products_simple:
  - "[[中证1000指数增强产品]]"
  - "[[平方和鼎盛中证1000指数增强15号]]"
main_strategies: ["[[中证1000指数增强]]"]
---

### [[中证1000指数增强产品]]
- 策略定位：中证1000指数增强，行业暴露控制在 3% 以内。

### [[平方和鼎盛中证1000指数增强15号]]
- 产品要素：该产品为中证1000指数增强代表产品。
- 当前持仓/风险暴露：行业暴露控制在 3% 以内。
""",
        encoding="utf-8",
    )

    written = ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)
    report = json.loads(
        (tmp_path / "reports" / "profile_quality.json").read_text(encoding="utf-8")
    )

    assert count == 1
    assert len(written) == 1
    assert records[0].product_name == "平方和鼎盛中证1000指数增强15号"
    assert "中证1000指数增强产品" in records[0].product_aliases
    assert records[0].profile_quality_status == "confirmed"
    assert records[0].entity_type == "product"
    assert records[0].entity_confidence == "high"
    assert "中证1000指数增强" in records[0].mentioned_strategy_tags
    assert report["profile_count"] == 1
    assert report["generic_profile_count"] == 0

    execution = execute_profile_query(jsonl_path, "查询平方和1000指增产品", limit=5)
    assert execution.results
    assert execution.results[0].product_name == "平方和鼎盛中证1000指数增强15号"


def test_compiler_merges_number_variants_into_single_profile(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes" / "双隆"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir(parents=True)
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[上海双隆投资有限公司]]"
mentioned_products_simple:
  - "[[双隆-隆元1号]]"
  - "[[隆元一号]]"
main_strategies: ["[[CTA]]"]
---

### [[双隆-隆元1号]]
- 产品要素：双隆-隆元1号私募证券投资基金，策略为 CTA。

### [[隆元一号]]
- 风险点：隆元一号在行情切换阶段可能存在回撤。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    assert len(records) == 1
    assert "双隆-隆元1号" in records[0].product_aliases
    assert "隆元一号" in records[0].product_aliases


def test_compiler_merges_short_and_full_private_fund_names(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes" / "半鞅"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir(parents=True)
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[海南半鞅私募基金管理合伙企业（有限合伙）]]"
mentioned_products_simple:
  - "[[半鞅CTA进取一号]]"
  - "[[半鞅CTA进取1号私募证券投资基金]]"
main_strategies: ["[[CTA]]"]
---

### [[半鞅CTA进取一号]]
- 产品要素：半鞅CTA进取一号为CTA产品。

### [[半鞅CTA进取1号私募证券投资基金]]
- 产品要素：半鞅CTA进取1号私募证券投资基金为同一产品全称。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    assert len(records) == 1
    assert records[0].manager == "海南半鞅私募基金管理合伙企业（有限合伙）"
    assert "半鞅CTA进取一号" in records[0].product_aliases
    assert "半鞅CTA进取1号私募证券投资基金" in records[0].product_aliases


def test_compiler_reads_fenced_yaml_manager_and_merges_variants(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source_notes" / "半鞅"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir(parents=True)
    (source_root / "roadshow.md").write_text(
        """```yaml
---
entity_type: "Manager"
primary_entity: "[[海南半鞅私募基金管理合伙企业（有限合伙）]]"
mentioned_products_simple:
  - "[[半鞅CTA均衡一号]]"
main_strategies: ["[[CTA]]"]
---
```

<!-- system: mentioned_products_json (do not edit manually) -->
```json
[
  {"name":"[[半鞅CTA均衡一号]]","main_strategies":["[[CTA]]"],"sub_strategies":[]}
]
```

### [[半鞅CTA均衡一号]]
- 产品要素：半鞅CTA均衡一号为CTA产品。
""",
        encoding="utf-8",
    )
    (source_root / "deck.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[海南半鞅私募基金管理合伙企业（有限合伙）]]"
mentioned_products_simple:
  - "[[半鞅CTA均衡1号]]"
main_strategies: ["[[CTA]]"]
---

### [[半鞅CTA均衡1号]]
- 产品要素：半鞅CTA均衡1号为同一产品。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    assert len(records) == 1
    assert records[0].manager == "海南半鞅私募基金管理合伙企业（有限合伙）"
    assert "半鞅CTA均衡一号" in records[0].product_aliases
    assert "半鞅CTA均衡1号" in records[0].product_aliases


def test_compiler_does_not_create_orphan_generic_product_profiles(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes" / "半鞅"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir(parents=True)
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[海南半鞅私募基金]]"
mentioned_products_simple:
  - "[[半鞅对冲产品]]"
  - "[[半鞅私募基金中证500指数增强]]"
main_strategies: ["[[市场中性]]", "[[中证500指数增强]]"]
---

### [[半鞅对冲产品]]
- 策略定位：半鞅对冲产品为管理人产品线描述。

### [[半鞅私募基金中证500指数增强]]
- 策略定位：中证500指数增强产品线。
""",
        encoding="utf-8",
    )

    written = ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)

    assert written == []
    assert count == 0
    assert read_jsonl(jsonl_path) == []


def test_index_enhancement_product_rejects_same_note_cta_tags(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes" / "半鞅"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir(parents=True)
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[海南半鞅私募基金管理合伙企业（有限合伙）]]"
mentioned_products_simple:
  - "[[半鞅1000指数增强]]"
main_strategies: ["[[中证1000指数增强]]", "[[基本面CTA]]"]
---

### [[半鞅1000指数增强]]
- 产品要素：对标中证1000指数，行业暴露控制在 3% 以内。
- 策略特征：阿尔法策略和CTA策略均为高频换手，但本产品为指数增强产品。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    record = records[0]
    assert record.entity_type == "product"
    assert "指数增强" in record.primary_strategy_tags
    assert "基本面CTA" not in record.product_line
    assert "基本面CTA" in record.rejected_strategy_tags


def test_compiler_merges_manager_variants_into_single_profile(
    tmp_path: Path, monkeypatch
) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    (source_root / "a").mkdir(parents=True)
    (source_root / "b").mkdir(parents=True)
    (source_root / "a" / "first.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[上海双隆投资有限公司]]"
mentioned_products_simple:
  - "[[双隆-隆成拓展1号]]"
main_strategies: ["[[CTA]]"]
---

### [[双隆-隆成拓展1号]]
- 产品要素：双隆-隆成拓展1号，策略为 CTA。
""",
        encoding="utf-8",
    )
    (source_root / "b" / "second.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[双隆]]"
mentioned_products_simple:
  - "[[隆成拓展1号]]"
main_strategies: ["[[CTA]]"]
---

### [[隆成拓展1号]]
- 风险点：隆成拓展1号在极端行情下可能回撤。
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "fund_profile_wiki.profiles.product_profile_compiler.enrich_profile_with_zmdata",
        lambda **_: __import__(
            "fund_profile_wiki.profiles.zmdata_identity",
            fromlist=["ZMDataEnrichment"],
        ).ZMDataEnrichment(status="unavailable"),
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)
    report = json.loads(
        (tmp_path / "reports" / "profile_quality.json").read_text(encoding="utf-8")
    )

    assert count == 1
    assert len(records) == 1
    assert records[0].canonical_product_name in {"双隆-隆成拓展1号", "隆成拓展1号"}
    assert "双隆-隆成拓展1号" in records[0].product_aliases
    assert "隆成拓展1号" in records[0].product_aliases
    assert records[0].zm_match_status == "unavailable"
    assert report["duplicate_group_count"] == 0


def test_compiler_does_not_overwrite_same_product_name_across_managers(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    (source_root / "a").mkdir(parents=True)
    (source_root / "b").mkdir(parents=True)
    (source_root / "a" / "first.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[上海甲方投资管理有限公司]]"
mentioned_products_simple: ["[[量化CTA1号]]"]
main_strategies: ["[[CTA]]"]
---

### [[量化CTA1号]]
- 产品要素：甲方量化CTA1号。
""",
        encoding="utf-8",
    )
    (source_root / "b" / "second.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[北京乙方资产管理有限公司]]"
mentioned_products_simple: ["[[量化CTA1号]]"]
main_strategies: ["[[CTA]]"]
---

### [[量化CTA1号]]
- 产品要素：乙方量化CTA1号。
""",
        encoding="utf-8",
    )

    written = ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 2
    assert len(records) == 2
    assert len(written) == 2
    assert len(list(profile_root.glob("*.md"))) == 2
    assert {record.manager for record in records} == {
        "上海甲方投资管理有限公司",
        "北京乙方资产管理有限公司",
    }


def test_compiler_removes_existing_manager_profiles_before_rebuild(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source_notes" / "平方和"
    profile_root = tmp_path / "product_profiles"
    source_root.mkdir(parents=True)
    profile_root.mkdir(parents=True)
    stale = profile_root / "中证1000指数增强产品.md"
    stale.write_text(
        """---
profile_type: ProductProfile
product_name: "[[中证1000指数增强产品]]"
manager: "[[平方和]]"
---
""",
        encoding="utf-8",
    )
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[平方和]]"
mentioned_products_simple: ["[[平方和鼎盛中证1000指数增强15号]]"]
main_strategies: ["[[中证1000指数增强]]"]
---

### [[平方和鼎盛中证1000指数增强15号]]
- 产品要素：中证1000指数增强。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)

    assert not stale.exists()
    assert (profile_root / "平方和鼎盛中证1000指数增强15号.md").exists()


def test_compiler_removes_stale_orphan_profiles_by_source_note_scope(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source_notes" / "半鞅"
    profile_root = tmp_path / "product_profiles"
    source_root.mkdir(parents=True)
    profile_root.mkdir(parents=True)
    source_note = source_root / "roadshow.md"
    stale = profile_root / "半鞅CTA均衡一号.md"
    stale.write_text(
        f"""---
profile_type: ProductProfile
product_name: "[[半鞅CTA均衡一号]]"
manager: ""
source_notes: ["{source_note}"]
---
""",
        encoding="utf-8",
    )
    source_note.write_text(
        """```yaml
---
entity_type: "Manager"
primary_entity: "[[海南半鞅私募基金管理合伙企业（有限合伙）]]"
mentioned_products_simple: ["[[半鞅CTA均衡一号]]"]
main_strategies: ["[[CTA]]"]
---
```

### [[半鞅CTA均衡一号]]
- 产品要素：CTA产品。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)

    frontmatter, _body = parse_frontmatter(stale.read_text(encoding="utf-8"))
    assert frontmatter["manager"] == "[[海南半鞅私募基金管理合伙企业（有限合伙）]]"
    assert len(list(profile_root.glob("*.md"))) == 1


def test_compiler_removes_existing_manager_profiles_for_manager_aliases(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source_notes" / "双隆"
    profile_root = tmp_path / "product_profiles"
    source_root.mkdir(parents=True)
    profile_root.mkdir(parents=True)
    stale = profile_root / "旧别名产品.md"
    stale.write_text(
        """---
profile_type: ProductProfile
product_name: "[[旧别名产品]]"
manager: "[[双隆投资]]"
---
""",
        encoding="utf-8",
    )
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[上海双隆投资有限公司]]"
mentioned_products_simple: ["[[双隆-隆元1号]]"]
main_strategies: ["[[CTA]]"]
---

### [[双隆-隆元1号]]
- 产品要素：CTA。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)

    assert not stale.exists()
    assert (profile_root / "双隆-隆元1号.md").exists()


def test_manager_wiki_docs_group_and_cleanup_alias_variants(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    for folder in ("manager_profiles", "product_maps", "risk_flags", "timelines"):
        target = docs_root / folder
        target.mkdir(parents=True)
        (target / "双隆.md").write_text("stale", encoding="utf-8")
        (target / "双隆投资.md").write_text("stale", encoding="utf-8")
        (target / "上海双隆投资有限公司.md").write_text("stale", encoding="utf-8")

    profile_a = type(
        "ProfileA",
        (),
        {
            "product_name": "双隆-隆元1号",
            "manager": "双隆",
            "strategy_positioning": "",
            "product_line": ["CTA"],
            "risk_points": [],
            "key_people_summary": "",
            "evidence_summary": [],
            "source_files": ["a.md"],
            "profile_quality_status": "confirmed",
        },
    )()
    profile_b = type(
        "ProfileB",
        (),
        {
            "product_name": "隆成拓展1号",
            "manager": "上海双隆投资有限公司",
            "strategy_positioning": "",
            "product_line": ["CTA"],
            "risk_points": [],
            "key_people_summary": "",
            "evidence_summary": [],
            "source_files": ["b.md"],
            "profile_quality_status": "confirmed",
        },
    )()

    written = write_manager_wiki_docs([profile_a, profile_b], docs_root)

    assert len(written) == 4
    for folder in ("manager_profiles", "product_maps", "risk_flags", "timelines"):
        names = sorted(path.name for path in (docs_root / folder).glob("*.md"))
        assert names == ["上海双隆投资有限公司.md"]


def test_manager_wiki_docs_group_recent_full_and_short_name_variants(
    tmp_path: Path,
) -> None:
    docs_root = tmp_path / "docs"
    stale_names = [
        "添益.md",
        "上海添益私募基金管理有限责任公司.md",
        "山信资本.md",
        "杭州萧山山信私募基金管理有限公司.md",
    ]
    for folder in ("manager_profiles", "product_maps", "risk_flags", "timelines"):
        target = docs_root / folder
        target.mkdir(parents=True)
        for name in stale_names:
            (target / name).write_text("stale", encoding="utf-8")

    def profile(product_name: str, manager: str) -> object:
        return type(
            "Profile",
            (),
            {
                "product_name": product_name,
                "manager": manager,
                "strategy_positioning": "",
                "product_line": ["指数增强"],
                "primary_strategy_tags": [],
                "secondary_strategy_tags": [],
                "risk_points": [],
                "key_people_summary": "",
                "evidence_summary": [],
                "source_files": [f"{product_name}.md"],
                "profile_quality_status": "confirmed",
            },
        )()

    written = write_manager_wiki_docs(
        [
            profile("添益一号", "添益"),
            profile("添益二号", "上海添益私募基金管理有限责任公司"),
            profile("山信一号", "山信资本"),
            profile("山信二号", "杭州萧山山信私募基金管理有限公司"),
        ],
        docs_root,
    )

    assert len(written) == 8
    for folder in ("manager_profiles", "product_maps", "risk_flags", "timelines"):
        names = sorted(path.name for path in (docs_root / folder).glob("*.md"))
        assert names == [
            "上海添益私募基金管理有限责任公司.md",
            "杭州萧山山信私募基金管理有限公司.md",
        ]
