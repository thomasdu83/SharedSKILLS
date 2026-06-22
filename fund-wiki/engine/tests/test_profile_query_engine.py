from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fund_profile_wiki.index.profile_index import ProductProfileRecord
from fund_profile_wiki.index.relation_index import (
    RelationRecord,
    read_relation_sqlite,
    write_relation_jsonl,
    write_relation_sqlite,
)
from fund_profile_wiki.query.profile_query_engine import execute_profile_query


def test_manager_overview_uses_manager_hard_filter_and_groups(tmp_path: Path) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(index_path, "查询双隆的策略体系", limit=10)

    assert execution.intent.mode == "manager_overview"
    assert execution.intent.recognized_manager == "上海双隆投资有限公司"
    assert execution.results
    assert all(result.manager == "上海双隆投资有限公司" for result in execution.results)
    assert [group.group_name for group in execution.grouped_results] == [
        "多元CTA",
        "标准CTA",
        "趋势CTA",
    ]


def test_manager_query_prefers_dualong_products_for_cta_product_lines(
    tmp_path: Path,
) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(index_path, "双隆有哪些 CTA 产品线？", limit=10)

    assert execution.intent.recognized_manager == "上海双隆投资有限公司"
    assert execution.results
    assert all(result.manager == "上海双隆投资有限公司" for result in execution.results)
    assert execution.results[0].product_name == "双隆-隆元1号"


def test_air_index_query_does_not_normalize_to_index_enhancement(
    tmp_path: Path,
) -> None:
    records = [
        ProductProfileRecord(
            product_name="远和可旺1号",
            manager="杭州远和私募基金有限公司",
            strategy_links=["[[量化多头]]", "[[空气指增]]"],
            people_links=[],
            source_notes=[],
            profile_text="远和可旺1号是杭州远和私募基金有限公司旗下产品，策略标签为量化多头, 空气指增。",
            evidence_text="策略定位: 空气指增，属于量化多头策略。",
            search_text="远和可旺1号 杭州远和私募基金有限公司 量化多头 空气指增",
            path=str(tmp_path / "air-index.md"),
            updated_at="2026-06-09",
            primary_strategy_tags=["股票多头"],
            mentioned_strategy_tags=["量化多头", "空气指增"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
        )
    ]
    index_path = build_index(tmp_path, records)

    execution = execute_profile_query(index_path, "空气指增 产品", limit=5)

    assert execution.results
    assert execution.results[0].product_name == "远和可旺1号"
    assert "指数增强" not in execution.intent.normalized_conditions
    assert "股票多头" in execution.intent.normalized_conditions


def test_manager_alias_query_resolves_to_same_manager(tmp_path: Path) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(index_path, "查询双隆投资的策略体系", limit=10)

    assert execution.intent.mode == "manager_overview"
    assert execution.intent.recognized_manager == "上海双隆投资有限公司"
    assert execution.results
    assert all(result.manager == "上海双隆投资有限公司" for result in execution.results)


def test_plain_manager_query_defaults_to_manager_overview(tmp_path: Path) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(index_path, "双隆", limit=10)

    assert execution.intent.mode == "manager_overview"
    assert execution.intent.recognized_manager == "上海双隆投资有限公司"
    assert execution.results
    assert all(result.manager == "上海双隆投资有限公司" for result in execution.results)


def test_manager_product_query_keeps_product_filter_for_smoke_query(
    tmp_path: Path,
) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(index_path, "双隆 产品", limit=10)

    assert execution.intent.mode == "product_filter"
    assert execution.intent.recognized_manager == "上海双隆投资有限公司"
    assert execution.results
    assert all(result.manager == "上海双隆投资有限公司" for result in execution.results)


def test_manager_product_query_demotes_weak_generic_product_names(
    tmp_path: Path,
) -> None:
    records = [
        ProductProfileRecord(
            product_name="半鞅对冲产品",
            manager="海南半鞅私募基金",
            strategy_links=["[[CTA]]"],
            people_links=[],
            source_notes=[],
            profile_text="半鞅对冲产品是产品线描述。",
            evidence_text="策略配置: 管理期货。",
            search_text="半鞅对冲产品 海南半鞅私募基金 产品 管理期货",
            path=str(tmp_path / "generic.md"),
            updated_at="2026-06-07",
            primary_strategy_tags=["管理期货"],
            secondary_strategy_tags=["商品CTA"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
            profile_quality_status="needs_review",
            product_name_reason="generic_product_tail",
        ),
        ProductProfileRecord(
            product_name="半鞅CTA进取1号私募证券投资基金",
            manager="海南半鞅私募基金管理合伙企业（有限合伙）",
            strategy_links=["[[CTA]]"],
            people_links=[],
            source_notes=[],
            profile_text="半鞅CTA进取1号私募证券投资基金是半鞅旗下CTA产品。",
            evidence_text="策略配置: 管理期货。",
            search_text="半鞅CTA进取1号私募证券投资基金 海南半鞅私募基金管理合伙企业（有限合伙） 管理期货",
            path=str(tmp_path / "real.md"),
            updated_at="2026-06-07",
            primary_strategy_tags=["管理期货"],
            secondary_strategy_tags=["商品CTA"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
            profile_quality_status="confirmed",
            product_name_reason="product_specific",
        ),
    ]
    index_path = build_index(tmp_path, records)

    execution = execute_profile_query(index_path, "半鞅 产品", limit=5)

    assert execution.results
    assert execution.results[0].product_name == "半鞅CTA进取1号私募证券投资基金"


def test_manager_alias_query_canonicalizes_mixed_manager_names(tmp_path: Path) -> None:
    index_path = build_index(
        tmp_path,
        [
            ProductProfileRecord(
                product_name="双隆-隆元1号",
                manager="双隆投资",
                strategy_links=["[[CTA]]"],
                people_links=[],
                source_notes=[],
                profile_text="双隆-隆元1号是双隆投资旗下产品。",
                evidence_text="",
                search_text="双隆-隆元1号 双隆投资 CTA",
                path=str(tmp_path / "a.md"),
                updated_at="2026-06-03",
            ),
            ProductProfileRecord(
                product_name="双隆-隆富2号",
                manager="上海双隆投资有限公司",
                strategy_links=["[[CTA]]"],
                people_links=[],
                source_notes=[],
                profile_text="双隆-隆富2号是上海双隆投资有限公司旗下产品。",
                evidence_text="",
                search_text="双隆-隆富2号 上海双隆投资有限公司 CTA",
                path=str(tmp_path / "b.md"),
                updated_at="2026-06-03",
            ),
        ],
    )

    execution = execute_profile_query(index_path, "查询双隆投资的策略体系", limit=10)

    assert execution.intent.recognized_manager == "上海双隆投资有限公司"
    assert execution.intent.hard_filters[0].label == "manager=上海双隆投资有限公司"


def test_manager_hard_filter_uses_identity_for_same_brand_legal_entities(
    tmp_path: Path,
) -> None:
    records = [
        ProductProfileRecord(
            product_name="图灵A500指数增强1号私募证券投资基金",
            manager="图灵私募基金管理（海南）有限公司",
            strategy_links=["[[指数增强]]"],
            people_links=[],
            source_notes=[],
            profile_text="图灵A500指数增强1号私募证券投资基金是海南图灵旗下产品。",
            evidence_text="团队曾任职于深圳市图灵投资管理有限公司。",
            search_text="图灵A500指数增强1号 图灵私募基金管理（海南）有限公司 海南图灵 深圳市图灵投资管理有限公司",
            path=str(tmp_path / "hainan.md"),
            updated_at="2026-06-08",
            primary_strategy_tags=["指数增强"],
            secondary_strategy_tags=["A500指增"],
            profile_quality_status="confirmed",
        ),
        ProductProfileRecord(
            product_name="股指高频做市商策略",
            manager="深圳市图灵投资管理有限公司",
            strategy_links=["[[高频交易]]"],
            people_links=[],
            source_notes=[],
            profile_text="股指高频做市商策略是深圳市图灵投资管理有限公司旗下产品。",
            evidence_text="深圳图灵历史策略材料。",
            search_text="股指高频做市商策略 深圳市图灵投资管理有限公司 深圳图灵 图灵",
            path=str(tmp_path / "shenzhen.md"),
            updated_at="2026-06-08",
            primary_strategy_tags=["相对价值"],
            profile_quality_status="confirmed",
        ),
    ]
    index_path = build_index(tmp_path, records)

    shenzhen = execute_profile_query(index_path, "深圳图灵 产品", limit=10)
    hainan = execute_profile_query(index_path, "海南图灵 产品", limit=10)

    assert shenzhen.intent.recognized_manager == "深圳市图灵投资管理有限公司"
    assert [result.manager for result in shenzhen.results] == [
        "深圳市图灵投资管理有限公司"
    ]
    assert hainan.intent.recognized_manager == "图灵私募基金管理（海南）有限公司"
    assert [result.manager for result in hainan.results] == [
        "图灵私募基金管理（海南）有限公司"
    ]


def test_compound_filter_marks_all_hard_conditions_satisfied(tmp_path: Path) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(
        index_path,
        "找 1000 指增，行业暴露 3% 以内，投资经理有 WorldQuant 背景的基金",
        limit=10,
    )

    assert execution.intent.mode == "compound_filter"
    assert execution.results[0].product_name == "Alpha中证1000指数增强1号"
    assert execution.results[0].hard_filter_satisfied is True
    assert execution.results[0].hard_filter_status == "satisfied"
    assert execution.results[0].missing_terms == []


def test_query_300_index_increase_returns_matching_manager_and_product(
    tmp_path: Path,
) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(index_path, "查询具有 300 指增的公司", limit=10)

    assert execution.intent.mode == "manager_filter"
    assert execution.manager_results
    assert execution.manager_results[0].manager == "北京贝塔投资有限公司"
    assert execution.results[0].manager == "北京贝塔投资有限公司"
    assert execution.results[0].product_name == "Beta沪深300指数增强1号"
    assert execution.results[0].hard_filter_satisfied is True
    assert execution.results[0].hard_filter_status == "satisfied"


def test_manager_filter_returns_managers_without_product_topk_truncation(
    tmp_path: Path,
) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(
        index_path, "fund-wiki 哪些管理人有期货策略？", limit=2
    )

    assert execution.intent.mode == "manager_filter"
    assert "管理期货" in execution.intent.normalized_conditions
    assert [item.manager for item in execution.manager_results] == [
        "上海双隆投资有限公司",
        "广州伽马投资有限公司",
    ]
    assert execution.manager_results[0].matched_products == 3
    assert execution.manager_results[1].matched_products == 1
    assert len(execution.results) == 2


def test_manager_filter_prefers_real_products_over_generic_lines(
    tmp_path: Path,
) -> None:
    records = sample_records() + [
        ProductProfileRecord(
            product_name="工具化CTA",
            manager="上海双隆投资有限公司",
            strategy_links=["[[工具化CTA]]"],
            people_links=[],
            source_notes=[],
            profile_text="工具化CTA是产品线描述。",
            evidence_text="策略逻辑: 工具化CTA。",
            search_text="工具化CTA 上海双隆投资有限公司 CTA 管理期货",
            path=str(tmp_path / "generic.md"),
            updated_at="2026-06-06",
            primary_strategy_tags=["管理期货"],
            secondary_strategy_tags=["商品CTA"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
        )
    ]
    index_path = build_index(tmp_path, records)

    execution = execute_profile_query(index_path, "哪些管理人有期货策略？", limit=5)

    first_manager = execution.manager_results[0]
    assert first_manager.manager == "上海双隆投资有限公司"
    assert first_manager.representative_products[0] == "双隆-隆元1号"
    assert "工具化CTA" not in first_manager.representative_products[:3]
    assert "generic_product_name" in first_manager.review_flags


def test_manager_filter_flags_mixed_cta_and_index_tags(tmp_path: Path) -> None:
    record = ProductProfileRecord(
        product_name="托特CTA1号私募证券投资基金",
        manager="托特（三亚）私募基金管理有限公司",
        strategy_links=["[[CTA]]", "[[300指增]]"],
        people_links=[],
        source_notes=[],
        profile_text="托特CTA1号同时出现CTA和指增表述。",
        evidence_text="策略配置: CTA（中周期趋势）。",
        search_text="托特CTA1号 管理期货 CTA 300指增 500指增 1000指增",
        path=str(tmp_path / "tot.md"),
        updated_at="2026-06-06",
        primary_strategy_tags=["管理期货", "指数增强"],
        secondary_strategy_tags=["趋势CTA", "300指增", "500指增", "1000指增"],
        strategy_tag_confidence="high",
        strategy_tag_review_status="confirmed",
    )
    index_path = build_index(tmp_path, [record])

    execution = execute_profile_query(index_path, "哪些管理人有期货策略？", limit=5)

    assert execution.manager_results
    result = execution.manager_results[0]
    assert result.manager == "托特（三亚）私募基金管理有限公司"
    assert result.confidence == "review_needed"
    assert "mixed_strategy_tags" in result.review_flags
    assert "tag_conflict_review_needed" in result.review_flags


def test_manager_filter_merges_alias_manager_names(tmp_path: Path) -> None:
    records = [
        ProductProfileRecord(
            product_name="托特CTA1号",
            manager="托特（三亚）私募基金管理有限公司",
            strategy_links=["[[CTA]]"],
            people_links=[],
            source_notes=[],
            profile_text="托特CTA1号是CTA产品。",
            evidence_text="策略配置: CTA。",
            search_text="托特CTA1号 托特（三亚）私募基金管理有限公司 CTA 管理期货",
            path=str(tmp_path / "tot_full.md"),
            updated_at="2026-06-06",
            primary_strategy_tags=["管理期货"],
            secondary_strategy_tags=["趋势CTA"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
        ),
        ProductProfileRecord(
            product_name="托特量化选股优选一号",
            manager="托特",
            strategy_links=["[[CTA]]"],
            people_links=[],
            source_notes=[],
            profile_text="托特量化选股优选一号提到股指期货对冲。",
            evidence_text="策略逻辑: 通过股指期货对冲市场风险。",
            search_text="托特量化选股优选一号 托特 股指期货 管理期货",
            path=str(tmp_path / "tot_short.md"),
            updated_at="2026-06-06",
            primary_strategy_tags=["管理期货"],
            secondary_strategy_tags=["股指CTA"],
            strategy_tag_confidence="medium",
            strategy_tag_review_status="confirmed",
        ),
    ]
    index_path = build_index(tmp_path, records)

    execution = execute_profile_query(index_path, "哪些管理人有期货策略？", limit=10)

    assert len(execution.manager_results) == 1
    result = execution.manager_results[0]
    assert result.manager == "托特（三亚）私募基金管理有限公司"
    assert result.matched_products == 2


def test_single_product_query_recognizes_product_name(tmp_path: Path) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(index_path, "双隆隆元1号是什么策略？", limit=10)

    assert execution.intent.mode == "single_product"
    assert execution.intent.recognized_manager == "上海双隆投资有限公司"
    assert execution.intent.recognized_product == "双隆-隆元1号"
    assert execution.results[0].product_name == "双隆-隆元1号"
    assert execution.results[0].hard_filter_satisfied is True
    assert execution.results[0].hard_filter_status == "satisfied"


def test_cli_json_contract_exposes_compatibility_fields(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    index_dir = docs_root / "indexes"
    index_dir.mkdir(parents=True)
    index_path = build_index(index_dir, sample_records())
    assert index_path.exists()

    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root.parent / "scripts" / "query_fund_wiki.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "查询双隆的策略体系",
            "--json",
            "--limit",
            "5",
            "--docs-root",
            str(docs_root),
            "--project-root",
            str(project_root),
            "--python",
            sys.executable,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["intent_mode"] == "manager_overview"
    assert payload["recognized_manager"] == "上海双隆投资有限公司"
    assert payload["recognized_product"] is None
    assert payload["hard_filters"] == ["manager=上海双隆投资有限公司"]
    assert payload["grouped_results"]
    assert payload["results"]
    first = payload["results"][0]
    assert isinstance(first["hard_filter_satisfied"], bool)
    assert first["hard_filter_satisfied"] is True
    assert first["hard_filter_status"] in {"satisfied", "unsatisfied", "not_applicable"}
    assert payload["context_budget_chars"] > 0
    assert payload["used_context_chars"] >= 0
    assert "relations_jsonl" in payload
    assert "relation_matches" in first
    assert "ranking_reasons" in first
    assert "packed_profile_text" in first
    assert "packed_evidence" in first
    assert "primary_strategy_tags" in first
    assert "secondary_strategy_tags" in first
    assert "strategy_facets" in first
    assert "strategy_tag_confidence" in first
    assert "strategy_tag_review_status" in first


def test_relation_index_participates_in_compound_query_matching(tmp_path: Path) -> None:
    index_dir = tmp_path / "indexes"
    index_dir.mkdir()
    record = ProductProfileRecord(
        product_name="Alpha中证1000指数增强1号",
        manager="上海阿尔法投资有限公司",
        strategy_links=["[[中证1000指数增强]]"],
        people_links=[],
        source_notes=[],
        profile_text="Alpha中证1000指数增强1号是指数增强产品。",
        evidence_text="",
        search_text="Alpha中证1000指数增强1号 上海阿尔法投资有限公司 中证1000指数增强",
        path=str(tmp_path / "alpha.md"),
        updated_at="2026-06-03",
    )
    index_path = build_index(index_dir, [record])
    write_relation_jsonl(
        [
            RelationRecord(
                subject=record.product_name,
                predicate="has_people_background",
                object="WorldQuant背景",
                manager=record.manager,
                product_name=record.product_name,
                evidence=["投资经理曾任 WorldQuant。"],
                path=record.path,
            ),
            RelationRecord(
                subject=record.product_name,
                predicate="has_exposure_constraint",
                object="行业暴露3%以内",
                manager=record.manager,
                product_name=record.product_name,
                evidence=["组合行业暴露控制在3%以内。"],
                path=record.path,
            ),
        ],
        index_path.with_name("relations.jsonl"),
    )

    execution = execute_profile_query(
        index_path,
        "找1000指增，行业暴露3%以内，投资经理有WorldQuant背景的基金",
        limit=5,
    )

    assert execution.results
    first = execution.results[0]
    assert first.product_name == record.product_name
    assert first.hard_filter_status == "satisfied"
    assert first.relation_matches
    assert any(reason.startswith("relation") for reason in first.ranking_reasons)


def test_query_uses_relation_sqlite_when_jsonl_is_absent(tmp_path: Path) -> None:
    index_dir = tmp_path / "indexes"
    index_dir.mkdir()
    record = ProductProfileRecord(
        product_name="Alpha中证1000指数增强1号",
        manager="上海阿尔法投资有限公司",
        strategy_links=["[[中证1000指数增强]]"],
        people_links=[],
        source_notes=[],
        profile_text="Alpha中证1000指数增强1号是指数增强产品。",
        evidence_text="",
        search_text="Alpha中证1000指数增强1号 上海阿尔法投资有限公司 中证1000指数增强",
        path=str(tmp_path / "alpha.md"),
        updated_at="2026-06-03",
    )
    index_path = build_index(index_dir, [record])
    write_relation_sqlite(
        [
            RelationRecord(
                subject=record.product_name,
                predicate="has_people_background",
                object="WorldQuant背景",
                manager=record.manager,
                product_name=record.product_name,
                evidence=["投资经理曾任 WorldQuant。"],
                path=record.path,
            ),
            RelationRecord(
                subject=record.product_name,
                predicate="has_exposure_constraint",
                object="行业暴露3%以内",
                manager=record.manager,
                product_name=record.product_name,
                evidence=["组合行业暴露控制在3%以内。"],
                path=record.path,
            ),
        ],
        index_path.with_name("relations.sqlite"),
    )

    execution = execute_profile_query(
        index_path,
        "找1000指增，行业暴露3%以内，投资经理有WorldQuant背景的基金",
        limit=5,
    )

    assert execution.results
    first = execution.results[0]
    assert first.product_name == record.product_name
    assert first.hard_filter_status == "satisfied"
    assert first.relation_matches
    assert any(reason.startswith("relation") for reason in first.ranking_reasons)


def test_read_relation_sqlite_filters_predicates(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "relations.sqlite"
    write_relation_sqlite(
        [
            RelationRecord(
                subject="Alpha产品",
                predicate="has_source_note",
                object="source_notes/alpha.md",
                product_name="Alpha产品",
            ),
            RelationRecord(
                subject="Alpha产品",
                predicate="has_exposure_constraint",
                object="行业暴露3%以内",
                product_name="Alpha产品",
            ),
        ],
        sqlite_path,
    )

    rows = read_relation_sqlite(
        sqlite_path, predicates=["has_exposure_constraint"]
    )

    assert [(item.predicate, item.object) for item in rows] == [
        ("has_exposure_constraint", "行业暴露3%以内")
    ]


def test_query_context_budget_packs_result_text(tmp_path: Path) -> None:
    record = ProductProfileRecord(
        product_name="Long中证1000指数增强1号",
        manager="上海长文本投资有限公司",
        strategy_links=["[[中证1000指数增强]]"],
        people_links=[],
        source_notes=[],
        profile_text="中证1000指数增强。" + "A" * 5000,
        evidence_text="",
        search_text="Long中证1000指数增强1号 中证1000指数增强",
        path=str(tmp_path / "long.md"),
        updated_at="2026-06-03",
        evidence_summary=["中证1000指数增强产品。"],
    )
    index_path = build_index(tmp_path, [record])

    execution = execute_profile_query(
        index_path,
        "找1000指增产品",
        limit=5,
        context_budget_chars=500,
        per_result_chars=360,
    )

    assert execution.results
    assert execution.used_context_chars <= execution.context_budget_chars
    assert len(execution.results[0].packed_profile_text) < len(record.profile_text)
    assert execution.results[0].context_chars <= execution.context_budget_chars


def test_query_synonym_expands_qian_index_increase(tmp_path: Path) -> None:
    index_path = build_index(tmp_path, sample_records())

    execution = execute_profile_query(index_path, "找千指增产品", limit=5)

    assert execution.results
    assert execution.results[0].product_name == "Alpha中证1000指数增强1号"


def test_query_matches_normalized_strategy_tags_without_old_strategy_text(
    tmp_path: Path,
) -> None:
    record = ProductProfileRecord(
        product_name="Gamma稳健1号",
        manager="上海伽马投资有限公司",
        strategy_links=[],
        people_links=[],
        source_notes=[],
        profile_text="产品画像仅保留简要描述。",
        evidence_text="",
        search_text="Gamma稳健1号 上海伽马投资有限公司",
        path=str(tmp_path / "gamma.md"),
        updated_at="2026-06-04",
        primary_strategy_codes=["CTA"],
        primary_strategy_tags=["管理期货"],
        secondary_strategy_codes=["CTA_COMMODITY"],
        secondary_strategy_tags=["商品CTA"],
        strategy_facets={"instrument": ["期货"]},
        strategy_tag_confidence="high",
        strategy_tag_review_status="confirmed",
    )
    index_path = build_index(tmp_path, [record])

    execution = execute_profile_query(index_path, "查询管理期货产品", limit=5)

    assert execution.results
    first = execution.results[0]
    assert first.product_name == "Gamma稳健1号"
    assert first.primary_strategy_tags == ["管理期货"]
    assert first.secondary_strategy_tags == ["商品CTA"]
    assert first.strategy_facets == {"instrument": ["期货"]}


def test_query_preserves_external_evidence_fields_after_packing(
    tmp_path: Path,
) -> None:
    record = ProductProfileRecord(
        product_name="Alpha WorldQuant Fund",
        manager="Alpha Manager",
        strategy_links=["[[WorldQuant]]"],
        people_links=[],
        source_notes=[],
        profile_text="The investment manager has WorldQuant background.",
        evidence_text="WorldQuant background is mentioned in the source note.",
        search_text="WorldQuant Alpha Manager",
        path=str(tmp_path / "alpha.md"),
        updated_at="2026-06-07",
        evidence_source_type="official_public",
        external_evidence_status="supported",
        evidence_conflict_status="none",
        source_priority=30,
        external_evidence=[
            {
                "url": "https://example.com/alpha",
                "title": "Alpha official page",
                "source_tier": "official_public",
                "claim": "WorldQuant background",
            }
        ],
    )
    index_path = build_index(tmp_path, [record])

    execution = execute_profile_query(index_path, "WorldQuant", limit=1)

    assert execution.results
    result = execution.results[0]
    assert result.evidence_source_type == "official_public"
    assert result.external_evidence_status == "supported"
    assert result.evidence_conflict_status == "none"
    assert result.source_priority == 30
    assert result.external_evidence[0]["url"] == "https://example.com/alpha"


def test_query_does_not_match_only_on_zm_rejected_candidates(tmp_path: Path) -> None:
    record = ProductProfileRecord(
        product_name="磐松红利指数增强1号",
        manager="上海磐松私募基金管理有限公司",
        strategy_links=["[[指数增强]]"],
        people_links=[],
        source_notes=[],
        profile_text="磐松红利指数增强1号是磐松旗下红利指增产品。",
        evidence_text="",
        search_text="磐松红利指数增强1号 上海磐松私募基金管理有限公司 红利指数增强",
        path=str(tmp_path / "pansong.md"),
        updated_at="2026-06-08",
        primary_strategy_tags=["指数增强"],
        secondary_strategy_tags=["红利指增"],
        strategy_tag_confidence="high",
        strategy_tag_review_status="confirmed",
        zm_rejected_candidates=[
            "fundID=1543858 | fundCode=SSG992 | fundName=图灵进取中证1000指数增强私募证券投资基金"
        ],
    )
    index_path = build_index(tmp_path, [record])

    execution = execute_profile_query(index_path, "图灵", limit=5)

    assert execution.results == []
    assert execution.manager_results == []


def test_query_without_retrieval_signal_returns_no_results(tmp_path: Path) -> None:
    record = ProductProfileRecord(
        product_name="磐松红利指数增强1号",
        manager="上海磐松私募基金管理有限公司",
        strategy_links=["[[指数增强]]"],
        people_links=[],
        source_notes=[],
        profile_text="磐松红利指数增强1号是磐松旗下红利指增产品。",
        evidence_text="",
        search_text="磐松红利指数增强1号 上海磐松私募基金管理有限公司 红利指数增强",
        path=str(tmp_path / "pansong.md"),
        updated_at="2026-06-08",
        evidence_summary=["这是一个有完整证据摘要的产品。"],
        primary_strategy_tags=["指数增强"],
        secondary_strategy_tags=["红利指增"],
        strategy_tag_confidence="high",
        strategy_tag_review_status="confirmed",
    )
    index_path = build_index(tmp_path, [record])

    execution = execute_profile_query(index_path, "图灵", limit=5)

    assert execution.results == []
    assert execution.manager_results == []


def build_index(tmp_path: Path, records: list[ProductProfileRecord]) -> Path:
    path = tmp_path / "product_profiles.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.__dict__, ensure_ascii=False) + "\n")
    return path


def sample_records() -> list[ProductProfileRecord]:
    return [
        ProductProfileRecord(
            product_name="双隆-隆元1号",
            manager="上海双隆投资有限公司",
            strategy_links=["[[多元CTA]]", "[[商品CTA]]", "[[股指CTA]]", "[[期权CTA]]"],
            people_links=["[[张津鹏]]"],
            source_notes=[
                "Y:\\投顾管理人研究\\fund_profile_wiki_docs\\source_notes\\双隆\\双隆投资2025标准版_20260108.md"
            ],
            profile_text="双隆-隆元1号是上海双隆投资有限公司旗下产品，策略标签为多元CTA, 商品CTA, 股指CTA, 期权CTA。",
            evidence_text="策略逻辑: 多元CTA，通过商品CTA、股指CTA与期权CTA进行组合配置。\n来源: `Y:\\...\\双隆投资2025标准版_20260108.md`",
            search_text="双隆-隆元1号 上海双隆投资有限公司 多元CTA 商品CTA 股指CTA 期权CTA",
            path="Y:\\投顾管理人研究\\fund_profile_wiki_docs\\product_profiles\\双隆-隆元1号.md",
            updated_at="2026-01-08",
            primary_strategy_tags=["管理期货"],
            secondary_strategy_tags=["多元CTA", "商品CTA", "股指CTA", "期权CTA"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
        ),
        ProductProfileRecord(
            product_name="双隆-隆富2号",
            manager="上海双隆投资有限公司",
            strategy_links=["[[标准CTA]]", "[[商品CTA]]", "[[股指CTA]]"],
            people_links=["[[张津鹏]]"],
            source_notes=[
                "Y:\\投顾管理人研究\\fund_profile_wiki_docs\\source_notes\\双隆\\双隆投资2025标准版_20260108.md"
            ],
            profile_text="双隆-隆富2号是上海双隆投资有限公司旗下产品，策略标签为标准CTA, 商品CTA, 股指CTA。",
            evidence_text="策略逻辑: 标准CTA，商品CTA 70%，股指CTA 30%。\n来源: `Y:\\...\\双隆投资2025标准版_20260108.md`",
            search_text="双隆-隆富2号 上海双隆投资有限公司 标准CTA 商品CTA 股指CTA",
            path="Y:\\投顾管理人研究\\fund_profile_wiki_docs\\product_profiles\\双隆-隆富2号.md",
            updated_at="2026-01-08",
            primary_strategy_tags=["管理期货"],
            secondary_strategy_tags=["标准CTA", "商品CTA", "股指CTA"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
        ),
        ProductProfileRecord(
            product_name="双隆-隆成拓展1号",
            manager="上海双隆投资有限公司",
            strategy_links=["[[趋势CTA]]", "[[工具化CTA]]"],
            people_links=["[[张津鹏]]"],
            source_notes=[
                "Y:\\投顾管理人研究\\fund_profile_wiki_docs\\source_notes\\双隆\\双隆投资2025标准版_20260108.md"
            ],
            profile_text="双隆-隆成拓展1号是上海双隆投资有限公司旗下产品，策略标签为趋势CTA, 工具化CTA。",
            evidence_text="策略逻辑: 趋势CTA，聚焦中短周期趋势信号。\n来源: `Y:\\...\\双隆投资2025标准版_20260108.md`",
            search_text="双隆-隆成拓展1号 上海双隆投资有限公司 趋势CTA 工具化CTA",
            path="Y:\\投顾管理人研究\\fund_profile_wiki_docs\\product_profiles\\双隆-隆成拓展1号.md",
            updated_at="2026-01-08",
            primary_strategy_tags=["管理期货"],
            secondary_strategy_tags=["趋势CTA"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
        ),
        ProductProfileRecord(
            product_name="Gamma CTA 1号",
            manager="广州伽马投资有限公司",
            strategy_links=["[[CTA]]"],
            people_links=[],
            source_notes=[
                "Y:\\投顾管理人研究\\fund_profile_wiki_docs\\source_notes\\伽马\\gamma.md"
            ],
            profile_text="Gamma CTA 1号是广州伽马投资有限公司旗下产品，策略标签为CTA。",
            evidence_text="策略逻辑: CTA。",
            search_text="Gamma CTA 1号 广州伽马投资有限公司 CTA",
            path="Y:\\投顾管理人研究\\fund_profile_wiki_docs\\product_profiles\\Gamma CTA 1号.md",
            updated_at="2026-01-08",
            primary_strategy_tags=["管理期货"],
            secondary_strategy_tags=["趋势CTA"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
        ),
        ProductProfileRecord(
            product_name="Alpha中证1000指数增强1号",
            manager="上海阿尔法投资有限公司",
            strategy_links=["[[中证1000指数增强]]", "[[指数增强]]"],
            people_links=["[[Alice]]"],
            source_notes=[
                "Y:\\投顾管理人研究\\fund_profile_wiki_docs\\source_notes\\阿尔法\\alpha.md"
            ],
            profile_text="Alpha中证1000指数增强1号是上海阿尔法投资有限公司旗下产品，策略标签为中证1000指数增强, 指数增强。关键人员曾任 WorldQuant，行业偏离≤±3%。",
            evidence_text="策略逻辑: 中证1000指数增强。\n风险与组合约束证据：行业偏离≤±3%。\n关键人员/团队背景证据：曾任 WorldQuant。",
            search_text="Alpha中证1000指数增强1号 上海阿尔法投资有限公司 中证1000 指数增强 WorldQuant 行业偏离≤±3%",
            path="Y:\\投顾管理人研究\\fund_profile_wiki_docs\\product_profiles\\Alpha中证1000指数增强1号.md",
            updated_at="2026-01-08",
            primary_strategy_tags=["指数增强"],
            secondary_strategy_tags=["1000指增"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
        ),
        ProductProfileRecord(
            product_name="Beta沪深300指数增强1号",
            manager="北京贝塔投资有限公司",
            strategy_links=["[[沪深300指数增强]]", "[[指数增强]]"],
            people_links=[],
            source_notes=[
                "Y:\\投顾管理人研究\\fund_profile_wiki_docs\\source_notes\\贝塔\\beta.md"
            ],
            profile_text="Beta沪深300指数增强1号是北京贝塔投资有限公司旗下产品，策略标签为沪深300指数增强, 指数增强。",
            evidence_text="策略逻辑: 沪深300指数增强。",
            search_text="Beta沪深300指数增强1号 北京贝塔投资有限公司 沪深300 300指增 指数增强",
            path="Y:\\投顾管理人研究\\fund_profile_wiki_docs\\product_profiles\\Beta沪深300指数增强1号.md",
            updated_at="2026-01-08",
            primary_strategy_tags=["指数增强"],
            secondary_strategy_tags=["300指增"],
            strategy_tag_confidence="high",
            strategy_tag_review_status="confirmed",
        ),
    ]
