from __future__ import annotations

from pathlib import Path

from fund_profile_wiki.extraction.source_note_builder import (
    build_parse_warning_source_note,
    build_raw_source_note,
)
from fund_profile_wiki.index.profile_index import build_profile_index, read_jsonl
from fund_profile_wiki.parsing.document_parser import ParseResult
from fund_profile_wiki.profiles.product_profile_compiler import ProductProfileCompiler
from fund_profile_wiki.profiles.zmdata_identity import ZMDataEnrichment
from fund_profile_wiki.profiles.zmdata_identity import enrich_profile_with_zmdata
from fund_profile_wiki.query.profile_query_engine import execute_profile_query


def test_compiler_and_index_preserve_structured_profile_fields(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir()
    note_path = source_root / "alpha.md"
    note_path.write_text(
        """---
entity_type: "Manager"
primary_entity: "[[上海阿尔法投资有限公司]]"
key_personnel: ["[[张三]]"]
mentioned_products_simple: ["[[Alpha中证1000指数增强1号]]"]
main_strategies: ["[[中证1000指数增强]]"]
---

### [[张三]]
- 投资经理曾任 WorldQuant，负责量化选股模型研发。

### [[Alpha中证1000指数增强1号]]
- 策略定位: 中证1000指数增强，行业偏离≤±3%，组合使用 Barra 风险模型。
- 风险点: 行业暴露控制在 3% 以内。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    record = records[0]
    assert "阿尔法" in record.manager_aliases
    assert "1000指增" in record.product_line or "中证1000指增" in record.product_line
    assert any("行业偏离" in item for item in record.risk_points)
    assert "WorldQuant" in record.key_people_summary
    assert note_path.name in record.source_files
    assert record.primary_strategy_tags == ["指数增强"]
    assert "1000指增" in record.secondary_strategy_tags
    assert record.strategy_facets.get("benchmark") == ["中证1000"]

    execution = execute_profile_query(
        jsonl_path,
        "找1000指增，行业暴露3%以内，投资经理有WorldQuant背景的基金",
        limit=5,
    )
    assert execution.results
    assert execution.results[0].product_name == "Alpha中证1000指数增强1号"
    assert execution.results[0].hard_filter_satisfied is True
    assert execution.results[0].hard_filter_status == "satisfied"


def test_compiler_and_query_support_2000_index_increase(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir()
    note_path = source_root / "alpha_2000.md"
    note_path.write_text(
        """---
entity_type: "Manager"
primary_entity: "[[上海阿尔法投资有限公司]]"
mentioned_products_simple: ["[[Alpha中证2000指数增强1号]]"]
main_strategies: ["[[中证2000指数增强]]"]
---

### [[Alpha中证2000指数增强1号]]
- 策略定位: 中证2000指数增强，面向小微盘指数增强配置。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    assert "中证2000指增" in records[0].product_line

    execution = execute_profile_query(jsonl_path, "找2000指增的基金", limit=5)
    assert execution.results
    assert execution.results[0].product_name == "Alpha中证2000指数增强1号"
    assert execution.results[0].hard_filter_satisfied is True
    assert execution.results[0].hard_filter_status == "satisfied"


def test_air_index_strategy_is_not_promoted_to_index_enhancement(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir()
    (source_root / "air_index.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[杭州远和私募基金有限公司]]"
mentioned_products_simple: ["[[远和可旺1号]]"]
main_strategies: ["[[空气指增]]", "[[量化多头]]"]
---

### [[远和可旺1号]]
- 策略定位: 空气指增，属于量化多头策略。
- 策略逻辑: 通过量化选股获取股票多头收益，不以指数增强作为主策略标签。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    record = records[0]
    assert record.product_name == "远和可旺1号"
    assert "股票多头" in record.primary_strategy_tags
    assert "指数增强" not in record.product_line
    assert "指数增强" not in record.direct_strategy_tags
    assert "空气指增" in record.mentioned_strategy_tags


def test_raw_source_note_heuristic_fields_allow_profile_build(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir()
    note_path = source_root / "raw.md"
    note_path.write_text(
        build_raw_source_note(
            Path("【500指增】一页通-平方和鼎盛中证500指数增强18号20250411.pdf"),
            "平方和",
            "产品名称：平方和鼎盛中证500指数增强18号。策略为中证500指数增强，行业偏离控制在3%以内。",
        ),
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count >= 1
    assert any(
        "平方和鼎盛中证500指数增强18号" in record.product_name for record in records
    )
    record = next(
        record
        for record in records
        if "平方和鼎盛中证500指数增强18号" in record.product_name
    )
    assert "中证500指增" in record.product_line

    execution = execute_profile_query(jsonl_path, "找平方和500指增产品", limit=5)
    assert execution.results
    assert execution.results[0].hard_filter_satisfied is True


def test_parse_warning_note_keeps_filename_product_clues(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    source_root.mkdir()
    note_path = source_root / "warning.md"
    note_path.write_text(
        build_parse_warning_source_note(
            file_path=Path("平方和鼎盛中证1000指数增强15号-加密文件.pdf"),
            manager="平方和",
            parse_result=ParseResult(
                text="",
                status="failed",
                method="pdf",
                error="document closed or encrypted",
            ),
        ),
        encoding="utf-8",
    )

    written = ProductProfileCompiler().compile_from_roots([source_root], profile_root)

    assert written
    assert any("平方和鼎盛中证1000指数增强15号" in path.stem for path in written)


def test_compiler_writes_manager_wiki_docs(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    source_root.mkdir()
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[上海阿尔法投资有限公司]]"
key_personnel: ["[[张三]]"]
mentioned_products_simple: ["[[Alpha中证1000指数增强1号]]"]
main_strategies: ["[[中证1000指数增强]]"]
---

### [[张三]]
- 投资经理曾任 WorldQuant，负责量化选股模型研发。
### [[Alpha中证1000指数增强1号]]
- 策略定位：中证1000指数增强，行业偏离≤3%，组合使用 Barra 风险模型。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)

    assert (tmp_path / "manager_profiles" / "上海阿尔法投资有限公司.md").exists()
    assert (tmp_path / "product_maps" / "上海阿尔法投资有限公司.md").exists()
    assert (tmp_path / "risk_flags" / "上海阿尔法投资有限公司.md").exists()
    assert (tmp_path / "timelines" / "上海阿尔法投资有限公司.md").exists()


def test_compiler_preserves_flow_when_zmdata_is_unavailable(
    tmp_path: Path, monkeypatch
) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir()
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[上海阿尔法投资有限公司]]"
mentioned_products_simple: ["[[Alpha中证1000指数增强1号]]"]
main_strategies: ["[[中证1000指数增强]]"]
---

### [[Alpha中证1000指数增强1号]]
- 策略定位：中证1000指数增强，行业偏离≤3%。
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "fund_profile_wiki.profiles.product_profile_compiler.enrich_profile_with_zmdata",
        lambda **_: ZMDataEnrichment(status="unavailable"),
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    assert records[0].product_name == "Alpha中证1000指数增强1号"
    assert records[0].zm_match_status == "unavailable"
    assert records[0].zm_fund_ids == []


def test_compiler_records_zmdata_identity_when_unique_match_found(
    tmp_path: Path, monkeypatch
) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir()
    (source_root / "alpha.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[上海双隆投资有限公司]]"
mentioned_products_simple: ["[[双隆-隆元1号]]"]
main_strategies: ["[[CTA]]"]
---

### [[双隆-隆元1号]]
- 产品要素：双隆-隆元1号私募证券投资基金，策略为 CTA。
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "fund_profile_wiki.profiles.product_profile_compiler.enrich_profile_with_zmdata",
        lambda **_: ZMDataEnrichment(
            status="matched",
            fund_ids=["1613015"],
            fund_codes=["S28439"],
            aliases=[
                "双隆-隆元1号私募证券投资基金",
                "双隆隆元一号",
            ],
            candidate_matches=[
                "fundID=1613015 | fundCode=S28439 | fundName=双隆-隆元1号私募证券投资基金"
            ],
        ),
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    assert records[0].zm_match_status == "matched"
    assert records[0].zm_fund_ids == ["1613015"]
    assert records[0].zm_fund_codes == ["S28439"]
    assert "双隆-隆元1号私募证券投资基金" in records[0].product_aliases


def test_zmdata_cross_manager_candidates_are_rejected(monkeypatch) -> None:
    class FakeZMData:
        def fund_search_quick(self, term, pageSize=10):  # noqa: N802
            return [
                {
                    "fundID": "1718694",
                    "fundCode": "SBGV68",
                    "fundName": "半鞅1000指数增强私募证券投资基金",
                    "fundNameUse": "半鞅1000指数增强",
                    "fundManageCompany": "宁波数法私募基金管理有限公司",
                }
            ]

    monkeypatch.setattr(
        "fund_profile_wiki.profiles.zmdata_identity.load_zmdata_client",
        lambda: FakeZMData(),
    )

    enrichment = enrich_profile_with_zmdata(
        product_name="半鞅1000指数增强",
        manager="海南半鞅私募基金管理合伙企业（有限合伙）",
        product_aliases=["半鞅1000指数增强"],
        manager_aliases=["半鞅"],
    )

    assert enrichment.status == "cross_manager_candidates_only"
    assert enrichment.candidate_matches == []
    assert enrichment.rejected_candidates


def test_compiler_canonicalizes_same_manager_aliases(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir()
    (source_root / "short.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[托特]]"
mentioned_products_simple: ["[[托特A500指数增强1号]]"]
main_strategies: ["[[中证A500指数增强]]"]
---

### [[托特A500指数增强1号]]
- 策略定位：中证A500指数增强。
""",
        encoding="utf-8",
    )
    (source_root / "legal.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[托特（三亚）私募基金管理有限公司]]"
mentioned_products_simple: ["[[托特中证1000指数增强1号]]"]
main_strategies: ["[[中证1000指数增强]]"]
---

### [[托特中证1000指数增强1号]]
- 策略定位：中证1000指数增强。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 2
    assert {record.manager for record in records} == {"托特（三亚）私募基金管理有限公司"}
    assert all("托特" in record.manager_aliases for record in records)


def test_cta_product_does_not_inherit_index_enhancement_tags(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir()
    (source_root / "mixed.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[托特（三亚）私募基金管理有限公司]]"
mentioned_products_simple: ["[[托特CTA1号]]"]
main_strategies: ["[[CTA]]", "[[中证1000指数增强]]", "[[中证2000指数增强]]"]
---

### [[托特CTA1号]]
- 产品策略：趋势CTA，使用股指期货和商品期货。
- 管理人同时还有300、500、1000、2000指增产品线。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    record = records[0]
    assert record.product_name == "托特CTA1号"
    assert "管理期货" in record.primary_strategy_tags
    assert "1000指增" not in record.secondary_strategy_tags
    assert "2000指增" not in record.secondary_strategy_tags
    assert "benchmark" not in record.strategy_facets


def test_a500_is_not_classified_as_500_index_enhancement(tmp_path: Path) -> None:
    source_root = tmp_path / "source_notes"
    profile_root = tmp_path / "product_profiles"
    index_dir = tmp_path / "indexes"
    source_root.mkdir()
    (source_root / "a500.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[托特（三亚）私募基金管理有限公司]]"
mentioned_products_simple: ["[[托特A500指数增强1号]]"]
main_strategies: ["[[中证A500指数增强]]"]
---

### [[托特A500指数增强1号]]
- 策略定位：中证A500指数增强。
""",
        encoding="utf-8",
    )

    ProductProfileCompiler().compile_from_roots([source_root], profile_root)
    jsonl_path, _, count = build_profile_index(profile_root, index_dir)
    records = read_jsonl(jsonl_path)

    assert count == 1
    record = records[0]
    assert "A500指增" in record.secondary_strategy_tags
    assert "500指增" not in record.secondary_strategy_tags
    assert record.strategy_facets.get("benchmark") == ["中证A500"]
