"""Structured retrieval over product profile indexes."""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from fund_profile_wiki.index.profile_index import ProductProfileRecord, read_jsonl
from fund_profile_wiki.index.relation_index import (
    RelationRecord,
    read_relation_jsonl,
    read_relation_sqlite,
    relation_jsonl_path_for,
    relation_sqlite_path_for,
)
from fund_profile_wiki.profiles.product_name_normalizer import (
    generate_manager_aliases as generate_shared_manager_aliases,
    manager_identity_key,
)
from fund_profile_wiki.taxonomy.strategy_taxonomy import expand_strategy_query_terms

HardFilterStatus = Literal["satisfied", "unsatisfied", "not_applicable"]

KNOWN_TERMS = [
    "中证2000",
    "2000指增",
    "2000增强",
    "中证1000",
    "1000指增",
    "1000增强",
    "中证500",
    "500指增",
    "500增强",
    "沪深300",
    "300指增",
    "300增强",
    "红利",
    "指增",
    "指数增强",
    "量化指增",
    "行业暴露",
    "行业偏离",
    "风格暴露",
    "WorldQuant",
    "worldquant",
    "世坤",
    "Barra",
    "BARRA",
    "市场中性",
    "多元CTA",
    "标准CTA",
    "商品CTA",
    "期权CTA",
    "金融CTA",
    "趋势CTA",
    "基本面CTA",
    "CTA",
]

OVERVIEW_KEYWORDS = [
    "策略体系",
    "产品线",
    "有哪些策略",
    "哪些策略",
    "有哪些产品线",
    "概览",
    "概况",
]

PRODUCT_QUERY_KEYWORDS = [
    "是什么策略",
    "什么策略",
    "啥策略",
    "做什么策略",
    "是什么产品",
]
PRODUCT_LIST_KEYWORDS = [
    "产品",
    "基金",
    "产品列表",
    "有哪些产品",
    "哪些产品",
]
MANAGER_FILTER_KEYWORDS = [
    "哪些管理人",
    "有哪些管理人",
    "哪些公司",
    "有哪些公司",
    "哪些私募",
    "有哪些私募",
    "哪些基金公司",
    "有哪些基金公司",
    "哪些投顾",
    "有哪些投顾",
    "哪几家",
]
DEFAULT_CONTEXT_BUDGET_CHARS = 8000
DEFAULT_RESULT_TEXT_BUDGET_CHARS = 900
QUERY_SYNONYMS: dict[str, list[str]] = {
    "1000指增": ["中证1000", "中证1000指数增强", "1000增强", "千指增"],
    "500指增": ["中证500", "中证500指数增强", "500增强"],
    "300指增": ["沪深300", "沪深300指数增强", "300增强"],
    "2000指增": ["中证2000", "中证2000指数增强", "2000增强"],
    "指增": ["指数增强", "量化指增"],
    "行业暴露": ["行业偏离", "行业敞口", "行业约束"],
    "WorldQuant": ["worldquant", "世坤"],
    "Barra": ["BARRA", "风险模型", "风控模型"],
    "期货策略": ["管理期货", "CTA", "商品期货", "商品CTA", "股指期货", "股指CTA"],
    "商品期货": ["商品CTA", "商品期货CTA", "管理期货", "CTA"],
    "股指期货": ["股指CTA", "股指期货CTA", "管理期货", "CTA"],
    "期权策略": ["期权", "期权CTA", "期权波动率", "期权套利"],
    "CTA": ["管理期货", "商品期货", "商品CTA", "股指CTA"],
    "市场中性": ["量化中性", "股票市场中性"],
}
COMPANY_SUFFIXES = [
    "私募基金管理有限公司",
    "资产管理有限公司",
    "投资管理有限公司",
    "投资有限公司",
    "资本管理有限公司",
    "资本有限公司",
    "基金管理有限公司",
    "有限公司",
]
CITY_PREFIXES = [
    "上海",
    "北京",
    "深圳",
    "广州",
    "杭州",
    "宁波",
    "南京",
    "苏州",
    "珠海",
    "天津",
    "青岛",
    "厦门",
]


@dataclass(frozen=True)
class HardFilter:
    kind: str
    label: str
    aliases: list[str]


@dataclass(frozen=True)
class QueryIntent:
    mode: str
    raw_query: str
    query_terms: list[str]
    hard_filters: list[HardFilter]
    recognized_manager: str | None = None
    recognized_product: str | None = None
    normalized_conditions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileSearchResult:
    product_name: str
    manager: str
    score: float
    matched_terms: list[str]
    missing_terms: list[str]
    hard_filter_satisfied: bool
    hard_filter_status: HardFilterStatus
    profile_text: str
    evidence_snippet: str
    path: str
    entity_type: str = "product"
    entity_confidence: str = "high"
    canonical_product_name: str = ""
    profile_quality_status: str = ""
    review_reasons: list[str] = field(default_factory=list)
    evidence_source_type: str = "internal_due_diligence"
    external_evidence_status: str = "not_checked"
    evidence_conflict_status: str = "none"
    source_priority: int = 10
    external_evidence: list[dict] = field(default_factory=list)
    primary_strategy_tags: list[str] = field(default_factory=list)
    secondary_strategy_tags: list[str] = field(default_factory=list)
    direct_strategy_tags: list[str] = field(default_factory=list)
    mentioned_strategy_tags: list[str] = field(default_factory=list)
    rejected_strategy_tags: list[str] = field(default_factory=list)
    strategy_facets: dict[str, list[str]] = field(default_factory=dict)
    strategy_tag_confidence: str = ""
    strategy_tag_review_status: str = ""
    relation_matches: list[str] = field(default_factory=list)
    ranking_reasons: list[str] = field(default_factory=list)
    packed_profile_text: str = ""
    packed_evidence: str = ""
    context_chars: int = 0


@dataclass(frozen=True)
class GroupedQueryResult:
    group_name: str
    representative_products: list[str]
    evidence_snippets: list[str]
    paths: list[str]


@dataclass(frozen=True)
class ManagerSearchResult:
    manager: str
    score: float
    matched_products: int
    representative_products: list[str]
    matched_strategy_tags: list[str]
    evidence_snippets: list[str]
    paths: list[str]
    confidence: str
    review_flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class QueryExecutionResult:
    query: str
    intent: QueryIntent
    results: list[ProfileSearchResult]
    grouped_results: list[GroupedQueryResult] = field(default_factory=list)
    manager_results: list[ManagerSearchResult] = field(default_factory=list)
    context_budget_chars: int = DEFAULT_CONTEXT_BUDGET_CHARS
    used_context_chars: int = 0
    truncated_result_count: int = 0


def query_product_profiles(
    index_jsonl: Path, query: str, limit: int = 10
) -> list[ProfileSearchResult]:
    return execute_profile_query(index_jsonl, query, limit=limit).results


def execute_profile_query(
    index_jsonl: Path,
    query: str,
    limit: int = 10,
    *,
    context_budget_chars: int = DEFAULT_CONTEXT_BUDGET_CHARS,
    per_result_chars: int = DEFAULT_RESULT_TEXT_BUDGET_CHARS,
) -> QueryExecutionResult:
    records = read_jsonl(index_jsonl)
    intent = infer_query_intent(records, query)
    relations_by_product = load_relations_by_product(index_jsonl, records, intent)
    results: list[ProfileSearchResult] = []
    for record in records:
        relations = relations_by_product.get(record.product_name, [])
        score, matched, missing, status, relation_matches, reasons = score_record(
            record, intent, relations
        )
        if score <= 0:
            continue
        results.append(
            ProfileSearchResult(
                product_name=record.product_name,
                manager=record.manager,
                score=score,
                matched_terms=matched,
                missing_terms=missing,
                hard_filter_satisfied=status != "unsatisfied",
                hard_filter_status=status,
                profile_text=record.profile_text,
                evidence_snippet=pick_snippet(record, matched),
                path=record.path,
                entity_type=record.entity_type,
                entity_confidence=record.entity_confidence,
                canonical_product_name=record.canonical_product_name,
                profile_quality_status=record.profile_quality_status,
                review_reasons=record.review_reasons,
                evidence_source_type=record.evidence_source_type,
                external_evidence_status=record.external_evidence_status,
                evidence_conflict_status=record.evidence_conflict_status,
                source_priority=record.source_priority,
                external_evidence=record.external_evidence,
                primary_strategy_tags=record.primary_strategy_tags,
                secondary_strategy_tags=record.secondary_strategy_tags,
                direct_strategy_tags=record.direct_strategy_tags,
                mentioned_strategy_tags=record.mentioned_strategy_tags,
                rejected_strategy_tags=record.rejected_strategy_tags,
                strategy_facets=record.strategy_facets,
                strategy_tag_confidence=record.strategy_tag_confidence,
                strategy_tag_review_status=record.strategy_tag_review_status,
                relation_matches=relation_matches,
                ranking_reasons=reasons,
            )
        )
    results.sort(key=result_sort_key)
    manager_results = (
        build_manager_results(results, limit=limit)
        if intent.mode == "manager_filter"
        else []
    )
    limited, used_chars, truncated_count = pack_results(
        results[:limit],
        context_budget_chars=context_budget_chars,
        per_result_chars=per_result_chars,
    )
    grouped = (
        build_grouped_results(limited) if intent.mode == "manager_overview" else []
    )
    return QueryExecutionResult(
        query=query,
        intent=intent,
        results=limited,
        grouped_results=grouped,
        manager_results=manager_results,
        context_budget_chars=context_budget_chars,
        used_context_chars=used_chars,
        truncated_result_count=truncated_count,
    )


def infer_query_intent(records: list[ProductProfileRecord], query: str) -> QueryIntent:
    recognized_manager = recognize_manager(records, query)
    recognized_product = recognize_product(records, query)
    query_terms = extract_query_terms(query)
    hard_filters: list[HardFilter] = []
    if recognized_manager:
        hard_filters.append(
            HardFilter(
                kind="manager",
                label=f"manager={recognized_manager}",
                aliases=generate_manager_aliases(recognized_manager),
            )
        )
    if recognized_product:
        hard_filters.append(
            HardFilter(
                kind="product",
                label=f"product={recognized_product}",
                aliases=generate_product_aliases(
                    recognized_product, recognized_manager
                ),
            )
        )
    hard_filters.extend(extract_condition_hard_filters(query))

    condition_count = len([item for item in hard_filters if item.kind == "condition"])
    product_list_requested = any(keyword in query for keyword in PRODUCT_LIST_KEYWORDS)
    manager_filter_requested = is_manager_filter_query(
        query,
        recognized_manager=recognized_manager,
        recognized_product=recognized_product,
    )
    if recognized_product or any(
        keyword in query for keyword in PRODUCT_QUERY_KEYWORDS
    ):
        mode = "single_product" if recognized_product else "product_filter"
    elif manager_filter_requested:
        mode = "manager_filter"
    elif recognized_manager and any(keyword in query for keyword in OVERVIEW_KEYWORDS):
        mode = "manager_overview"
    elif condition_count >= 2:
        mode = "compound_filter"
    elif recognized_manager and not condition_count:
        mode = "product_filter" if product_list_requested else "manager_overview"
    else:
        mode = "product_filter"

    return QueryIntent(
        mode=mode,
        raw_query=query,
        query_terms=query_terms,
        hard_filters=hard_filters,
        recognized_manager=recognized_manager,
        recognized_product=recognized_product,
        normalized_conditions=extract_normalized_conditions(
            query, query_terms, hard_filters
        ),
    )


def is_manager_filter_query(
    query: str,
    *,
    recognized_manager: str | None,
    recognized_product: str | None,
) -> bool:
    if recognized_manager or recognized_product:
        return False
    if any(keyword in query for keyword in MANAGER_FILTER_KEYWORDS):
        return True
    manager_entity_terms = ["管理人", "公司", "私募", "基金公司", "投顾"]
    discovery_terms = ["具有", "具备", "有", "做", "覆盖", "筛选", "找"]
    return any(term in query for term in manager_entity_terms) and any(
        term in query for term in discovery_terms
    )


def extract_normalized_conditions(
    query: str, query_terms: list[str], hard_filters: list[HardFilter]
) -> list[str]:
    conditions = [item.label for item in hard_filters if item.kind == "condition"]
    normalized_query = normalize_for_match(query)
    candidate_labels = [
        "管理期货",
        "股票多头",
        "CTA",
        "商品CTA",
        "股指CTA",
        "期权CTA",
        "期权波动率",
        "指数增强",
        "300指增",
        "500指增",
        "1000指增",
        "2000指增",
        "市场中性",
        "WorldQuant背景",
        "行业暴露",
        "行业暴露3%以内",
    ]
    for label in candidate_labels:
        normalized_label = normalize_for_match(label)
        if (
            label == "指数增强"
            and query_mentions_air_index_strategy(query)
            and not query_has_explicit_index_enhancement(query)
        ):
            continue
        if normalized_label and (
            normalized_label in normalized_query
            or any(
                normalized_label == normalize_for_match(term) for term in query_terms
            )
        ):
            conditions.append(label)
    if "期货策略" in query or "管理期货" in query:
        conditions.extend(["管理期货", "商品CTA", "股指CTA"])
    if "商品期货" in query:
        conditions.extend(["商品CTA"])
    if "股指期货" in query:
        conditions.extend(["股指CTA"])
    if "期权策略" in query:
        conditions.extend(["期权CTA", "期权波动率"])
    return dedupe_terms(conditions)


def recognize_manager(records: list[ProductProfileRecord], query: str) -> str | None:
    normalized_query = normalize_for_match(query)
    best_manager: str | None = None
    best_alias_len = -1
    best_manager_len = -1
    for manager in sorted({record.manager for record in records if record.manager}):
        for alias in generate_manager_aliases(manager):
            normalized_alias = normalize_for_match(alias)
            if normalized_alias and normalized_alias in normalized_query:
                alias_len = len(normalized_alias)
                manager_len = len(normalize_for_match(manager))
                if alias_len > best_alias_len or (
                    alias_len == best_alias_len and manager_len > best_manager_len
                ):
                    best_manager = manager
                    best_alias_len = alias_len
                    best_manager_len = manager_len
    return canonicalize_manager_name(records, best_manager)


def canonicalize_manager_name(
    records: list[ProductProfileRecord], manager: str | None
) -> str | None:
    if not manager:
        return None
    identity = manager_identity_key(manager)
    if not identity:
        return manager
    candidates = {
        record.manager.strip()
        for record in records
        if record.manager and manager_identity_key(record.manager) == identity
    }
    candidates.add(manager.strip())
    return max(candidates, key=manager_name_score)


def manager_name_score(value: str) -> tuple[int, int, str]:
    text = str(value).strip()
    suffix_keywords = (
        "私募基金管理有限公司",
        "资产管理有限公司",
        "投资管理有限公司",
        "投资有限公司",
        "资本管理有限公司",
        "基金管理有限公司",
        "有限公司",
    )
    has_company_suffix = int(any(text.endswith(keyword) for keyword in suffix_keywords))
    return (has_company_suffix, len(text), text)


def recognize_product(records: list[ProductProfileRecord], query: str) -> str | None:
    normalized_query = normalize_for_match(query)
    best_product: str | None = None
    best_alias_len = -1
    best_product_len = 10**9
    for product_name in sorted(
        {record.product_name for record in records if record.product_name}
    ):
        manager = next(
            (
                record.manager
                for record in records
                if record.product_name == product_name and record.manager
            ),
            None,
        )
        for alias in generate_product_aliases(product_name, manager):
            normalized_alias = normalize_for_match(alias)
            if normalized_alias and normalized_alias in normalized_query:
                alias_len = len(normalized_alias)
                product_len = len(normalize_for_match(product_name))
                if alias_len > best_alias_len or (
                    alias_len == best_alias_len and product_len < best_product_len
                ):
                    best_product = product_name
                    best_alias_len = alias_len
                    best_product_len = product_len
    return best_product


def extract_query_terms(query: str) -> list[str]:
    lower_query = query.lower()
    terms = []
    for term in KNOWN_TERMS:
        if (
            term == "指增"
            and query_mentions_air_index_strategy(query)
            and not query_has_explicit_index_enhancement(query)
        ):
            continue
        if term.lower() in lower_query:
            terms.append(term)
    terms.extend(expand_strategy_query_terms(query))
    terms.extend(re.findall(r"[A-Za-z][A-Za-z0-9_&.\-]+", query))
    normalized_query = normalize_for_match(query)
    for key, aliases in QUERY_SYNONYMS.items():
        if (
            key == "指增"
            and query_mentions_air_index_strategy(query)
            and not query_has_explicit_index_enhancement(query)
        ):
            continue
        candidates = [key, *aliases]
        if any(
            normalize_for_match(candidate) in normalized_query
            for candidate in candidates
        ):
            terms.append(key)
            terms.extend(aliases)
    if "3%" in query or "3％" in query or "以内" in query:
        terms.extend(["行业偏离≤±3%", "行业暴露3%以内"])
    terms.extend(cjk_bigrams(query))
    return expand_terms(dedupe_terms(terms))


def extract_condition_hard_filters(query: str) -> list[HardFilter]:
    filters: list[HardFilter] = []
    lower_query = query.lower()
    if "期货策略" in query or "管理期货" in query:
        filters.append(
            HardFilter(
                "condition",
                "管理期货",
                [
                    "管理期货",
                    "期货策略",
                    "商品期货",
                    "商品CTA",
                    "股指期货",
                    "股指CTA",
                    "量化CTA",
                ],
            )
        )
    if "商品期货" in query:
        filters.append(
            HardFilter(
                "condition",
                "商品CTA",
                ["商品期货", "商品CTA", "商品期货CTA"],
            )
        )
    if "股指期货" in query:
        filters.append(
            HardFilter(
                "condition",
                "股指CTA",
                ["股指期货", "股指CTA", "股指期货CTA", "金融CTA"],
            )
        )
    if "期权策略" in query:
        filters.append(
            HardFilter(
                "condition",
                "期权策略",
                ["期权策略", "期权CTA", "期权波动率", "期权套利"],
            )
        )
    if "2000" in query and ("指增" in query or "增强" in query):
        filters.append(
            HardFilter("condition", "2000指增", ["中证2000", "2000指增", "2000增强"])
        )
    if "1000" in query and ("指增" in query or "增强" in query):
        filters.append(
            HardFilter("condition", "1000指增", ["中证1000", "1000指增", "1000增强"])
        )
    if "500" in query and ("指增" in query or "增强" in query):
        filters.append(
            HardFilter("condition", "500指增", ["中证500", "500指增", "500增强"])
        )
    if "300" in query and ("指增" in query or "增强" in query):
        filters.append(
            HardFilter("condition", "300指增", ["沪深300", "300指增", "300增强"])
        )
    if "行业" in query and ("暴露" in query or "偏离" in query):
        filters.append(
            HardFilter(
                "condition",
                "行业暴露",
                [
                    "行业暴露",
                    "行业偏离",
                    "行业偏离≤±3%",
                    "行业偏离<=±3%",
                    "行业暴露3%以内",
                ],
            )
        )
    if "3%" in query or "3％" in query:
        filters.append(
            HardFilter(
                "condition",
                "行业暴露3%以内",
                [
                    "行业偏离≤±3%",
                    "行业偏离<=±3%",
                    "行业偏离≤3%",
                    "行业暴露3%以内",
                    "行业暴露 3% 以内",
                ],
            )
        )
    if "worldquant" in lower_query or "世坤" in query:
        filters.append(
            HardFilter(
                "condition", "WorldQuant背景", ["worldquant", "WorldQuant", "世坤"]
            )
        )
    return filters


def score_record(
    record: ProductProfileRecord,
    intent: QueryIntent,
    relations: list[RelationRecord] | None = None,
) -> tuple[float, list[str], list[str], HardFilterStatus, list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []
    relation_matches: list[str] = []
    ranking_reasons: list[str] = []
    score = 0.0
    haystack = build_search_haystack(record)
    haystack_lower = haystack.lower()
    strategy_tag_text = build_strategy_tag_text(record)
    strategy_tag_lower = strategy_tag_text.lower()
    relation_text = build_relation_text(relations or [])
    relation_lower = relation_text.lower()

    manager_filter = next(
        (item for item in intent.hard_filters if item.kind == "manager"), None
    )
    if manager_filter:
        if manager_filter_matches(manager_filter, record.manager):
            matched.append(manager_filter.label)
            score += 20.0
            ranking_reasons.append("manager_hard_filter")
        else:
            return (
                0.0,
                [],
                [manager_filter.label],
                "unsatisfied",
                [],
                ["manager_hard_filter_missing"],
            )

    product_filter = next(
        (item for item in intent.hard_filters if item.kind == "product"), None
    )
    if product_filter:
        if aliases_match(product_filter.aliases, record.product_name):
            matched.append(product_filter.label)
            score += 15.0
            ranking_reasons.append("product_hard_filter")
        else:
            return (
                0.0,
                [],
                [product_filter.label],
                "unsatisfied",
                [],
                ["product_hard_filter_missing"],
            )

    normalized_product = normalize_for_match(record.product_name)
    normalized_manager = normalize_for_match(record.manager)
    for term in intent.query_terms:
        normalized_term = normalize_for_match(term)
        if not normalized_term:
            continue
        if normalized_term in normalized_product:
            matched.append(term)
            score += term_weight(term, field="product")
            ranking_reasons.append(f"product_term:{term}")
        elif normalized_term in normalized_manager:
            matched.append(term)
            score += term_weight(term, field="manager")
            ranking_reasons.append(f"manager_term:{term}")
        elif term.lower() in strategy_tag_lower:
            matched.append(term)
            score += term_weight(term, field="strategy_tag")
            ranking_reasons.append(f"strategy_tag_term:{term}")
        elif term.lower() in haystack_lower:
            matched.append(term)
            score += term_weight(term, field="text")
            ranking_reasons.append(f"text_term:{term}")
        elif term.lower() in relation_lower:
            matched.append(term)
            relation_matches.append(relation_match_label(term, relations or []))
            score += term_weight(term, field="relation")
            ranking_reasons.append(f"relation_term:{term}")

    for condition in [item for item in intent.hard_filters if item.kind == "condition"]:
        relation_hit = aliases_match(condition.aliases, relation_text)
        strategy_tag_hit = aliases_match(condition.aliases, strategy_tag_text)
        if (
            strategy_tag_hit
            or aliases_match(condition.aliases, haystack)
            or relation_hit
        ):
            matched.append(condition.label)
            score += 5.5 if relation_hit or strategy_tag_hit else 4.0
            ranking_reasons.append(
                f"{'relation' if relation_hit else 'strategy_tag' if strategy_tag_hit else 'text'}_hard_filter:{condition.label}"
            )
            if relation_hit:
                relation_matches.append(
                    relation_match_label(condition.label, relations or [])
                )
        else:
            missing.append(condition.label)
            score -= 2.5

    status: HardFilterStatus = "not_applicable"
    if intent.hard_filters:
        status = "satisfied" if not missing else "unsatisfied"

    condition_filters = [
        item for item in intent.hard_filters if item.kind == "condition"
    ]
    matched_condition_labels = {
        item for item in matched if item in {flt.label for flt in condition_filters}
    }
    if (
        condition_filters
        and not matched_condition_labels
        and not manager_filter
        and not product_filter
    ):
        return (
            0.0,
            [],
            dedupe_terms(missing),
            "unsatisfied",
            [],
            ["condition_hard_filter_missing"],
        )

    if not matched and not relation_matches:
        return (
            0.0,
            [],
            dedupe_terms(missing),
            status,
            [],
            ["no_retrieval_signal"],
        )

    if intent.mode == "manager_overview" and manager_filter:
        score += 3.0
        ranking_reasons.append("manager_overview_boost")
    if intent.mode == "single_product" and product_filter:
        score += 3.0
        ranking_reasons.append("single_product_boost")
    if record.evidence_summary:
        score += min(len(record.evidence_summary), 3) * 0.25
        ranking_reasons.append("evidence_quality")
    quality_penalty = profile_quality_penalty(record)
    if quality_penalty:
        score -= quality_penalty
        ranking_reasons.append(f"profile_quality:{record.profile_quality_status}")

    return (
        score,
        dedupe_terms(matched),
        dedupe_terms(missing),
        status,
        dedupe_terms(relation_matches),
        dedupe_terms(ranking_reasons),
    )


def result_sort_key(result: ProfileSearchResult) -> tuple[float, int, int, int, str]:
    quality_rank = 0 if result.profile_quality_status == "confirmed" else 1
    entity_rank = 0 if result.entity_type == "product" else 1
    generic_rank = 1 if is_generic_product_name(result.product_name) else 0
    return (-result.score, quality_rank, entity_rank, generic_rank, result.product_name)


def profile_quality_penalty(record: ProductProfileRecord) -> float:
    status = record.profile_quality_status or "confirmed"
    reason = record.product_name_reason or ""
    penalty = 0.0
    if status == "weak_line":
        penalty += 6.0
    elif status == "needs_review":
        penalty += 4.0
    elif status and status != "confirmed":
        penalty += 3.0
    if record.entity_type and record.entity_type != "product":
        penalty += 5.0
    if record.entity_confidence == "medium":
        penalty += 1.5
    elif record.entity_confidence == "low":
        penalty += 3.0
    if reason in {
        "pure_strategy_name",
        "strategy_product_line",
        "manager_strategy_line",
        "generic_product_tail",
    }:
        penalty += 2.0
    if is_generic_product_name(record.product_name):
        penalty += 2.0
    return penalty


def build_grouped_results(
    results: list[ProfileSearchResult],
) -> list[GroupedQueryResult]:
    grouped: dict[str, list[ProfileSearchResult]] = {}
    for result in results:
        group_name = infer_group_name(result)
        grouped.setdefault(group_name, []).append(result)
    ordered_groups = []
    for group_name, items in sorted(
        grouped.items(), key=lambda item: group_sort_key(item[0])
    ):
        ordered_groups.append(
            GroupedQueryResult(
                group_name=group_name,
                representative_products=[item.product_name for item in items[:3]],
                evidence_snippets=dedupe_terms(
                    [
                        item.evidence_snippet
                        for item in items[:2]
                        if item.evidence_snippet
                    ]
                ),
                paths=dedupe_terms([item.path for item in items[:3]]),
            )
        )
    return ordered_groups


def build_manager_results(
    results: list[ProfileSearchResult], *, limit: int
) -> list[ManagerSearchResult]:
    grouped: dict[str, list[ProfileSearchResult]] = {}
    for result in results:
        if not result.manager:
            continue
        grouped.setdefault(manager_result_group_key(result.manager), []).append(result)

    manager_results: list[ManagerSearchResult] = []
    for _manager_key, items in grouped.items():
        manager = canonical_manager_for_results(items)
        sorted_items = sorted(items, key=representative_product_sort_key)
        review_flags = dedupe_terms(
            [flag for item in items for flag in review_flags_for_result(item)]
        )
        matched_strategy_tags = dedupe_terms(
            [
                tag
                for item in sorted_items
                for tag in item.primary_strategy_tags + item.secondary_strategy_tags
                if tag
            ]
        )
        evidence_snippets = dedupe_terms(
            [item.evidence_snippet for item in sorted_items if item.evidence_snippet]
        )[:3]
        paths = dedupe_terms([item.path for item in sorted_items if item.path])[:3]
        manager_results.append(
            ManagerSearchResult(
                manager=manager,
                score=manager_result_score(items, review_flags),
                matched_products=len(items),
                representative_products=[
                    item.product_name for item in sorted_items[:3]
                ],
                matched_strategy_tags=matched_strategy_tags[:8],
                evidence_snippets=evidence_snippets,
                paths=paths,
                confidence=manager_confidence(items, review_flags),
                review_flags=review_flags,
            )
        )

    manager_results.sort(
        key=lambda item: (-item.score, -item.matched_products, item.manager)
    )
    return manager_results[:limit]


def manager_result_group_key(manager: str) -> str:
    return manager_identity_key(manager) or normalize_for_match(manager) or manager


def canonical_manager_for_results(items: list[ProfileSearchResult]) -> str:
    managers = {item.manager.strip() for item in items if item.manager.strip()}
    if not managers:
        return ""
    return max(managers, key=manager_name_score)


def representative_product_sort_key(result: ProfileSearchResult) -> tuple:
    generic_penalty = 1 if is_generic_product_name(result.product_name) else 0
    quality_bonus = 0 if result.profile_quality_status == "confirmed" else 1
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    confidence_rank = confidence_order.get(result.strategy_tag_confidence, 3)
    return (
        generic_penalty,
        quality_bonus,
        confidence_rank,
        -result.score,
        len(normalize_for_match(result.product_name)),
        result.product_name,
    )


def manager_result_score(
    items: list[ProfileSearchResult], review_flags: list[str]
) -> float:
    if not items:
        return 0.0
    score = max(item.score for item in items)
    score += min(len(items), 6) * 1.5
    score += sum(
        0.5
        for item in items
        if item.strategy_tag_confidence == "high"
        or item.strategy_tag_review_status == "confirmed"
    )
    if "tag_conflict_review_needed" in review_flags:
        score -= 2.0
    if "weak_text_match" in review_flags and len(items) == 1:
        score -= 1.0
    return score


def manager_confidence(
    items: list[ProfileSearchResult], review_flags: list[str]
) -> str:
    if not items:
        return "low"
    if "tag_conflict_review_needed" in review_flags:
        return "review_needed"
    if len(items) >= 2:
        return "high"
    item = items[0]
    if (
        item.strategy_tag_confidence == "high"
        or item.strategy_tag_review_status == "confirmed"
    ):
        return "high"
    if "weak_text_match" in review_flags:
        return "medium"
    return "medium"


def review_flags_for_result(result: ProfileSearchResult) -> list[str]:
    flags: list[str] = []
    if is_generic_product_name(result.product_name):
        flags.append("generic_product_name")
    if result.profile_quality_status and result.profile_quality_status != "confirmed":
        flags.append("profile_quality_review_needed")
    if not has_structured_strategy_match(result):
        flags.append("weak_text_match")
    if has_mixed_cta_index_tags(result):
        flags.extend(["mixed_strategy_tags", "tag_conflict_review_needed"])
    return dedupe_terms(flags)


def is_generic_product_name(product_name: str) -> bool:
    name = product_name.strip()
    if not name:
        return True
    if any(keyword in name for keyword in ["系列", "产品线", "工具化", "策略体系"]):
        return True
    if name.endswith(("产品", "策略产品", "代表产品")) and "号" not in name:
        return True
    normalized = normalize_for_match(name)
    if normalized.endswith("cta") and "号" not in name:
        return True
    return False


def has_structured_strategy_match(result: ProfileSearchResult) -> bool:
    return any(
        reason.startswith("strategy_tag_term:")
        or reason.startswith("strategy_tag_hard_filter:")
        for reason in result.ranking_reasons
    )


def has_mixed_cta_index_tags(result: ProfileSearchResult) -> bool:
    tags = result.primary_strategy_tags + result.secondary_strategy_tags
    normalized_tags = [normalize_for_match(tag) for tag in tags]
    has_cta = any(
        token in normalized_tags
        for token in [
            normalize_for_match("管理期货"),
            normalize_for_match("商品CTA"),
            normalize_for_match("股指CTA"),
            normalize_for_match("趋势CTA"),
            normalize_for_match("基本面CTA"),
        ]
    )
    has_index_enh = any(
        token in normalized_tags
        for token in [
            normalize_for_match("指数增强"),
            normalize_for_match("300指增"),
            normalize_for_match("500指增"),
            normalize_for_match("1000指增"),
            normalize_for_match("2000指增"),
        ]
    )
    return has_cta and has_index_enh


def infer_group_name(result: ProfileSearchResult) -> str:
    for tag in result.secondary_strategy_tags:
        if tag:
            return tag
    for tag in result.primary_strategy_tags:
        if tag:
            return tag
    text = "\n".join([result.profile_text, result.evidence_snippet]).lower()
    if "多元cta" in text:
        return "多元CTA"
    if "标准cta" in text:
        return "标准CTA"
    if "商品cta" in text:
        return "商品CTA"
    if "期权cta" in text:
        return "期权CTA"
    if "趋势cta" in text:
        return "趋势CTA"
    if "基本面cta" in text:
        return "基本面CTA"
    if "金融cta" in text:
        return "金融CTA"
    if "工具化cta" in text:
        return "工具化CTA"
    if "cta" in text:
        return "CTA其他"
    if "市场中性" in text:
        return "市场中性"
    if "空气指增" in text or "量化多头" in text:
        return "股票多头"
    if "指数增强" in text or "指增" in text:
        return "指数增强"
    return "其他策略"


def group_sort_key(name: str) -> tuple[int, str]:
    order = {
        "多元CTA": 0,
        "标准CTA": 1,
        "商品CTA": 2,
        "期权CTA": 3,
        "趋势CTA": 4,
        "基本面CTA": 5,
        "金融CTA": 6,
        "工具化CTA": 7,
        "CTA其他": 8,
        "市场中性": 9,
        "股票多头": 10,
        "指数增强": 11,
        "其他策略": 99,
    }
    return order.get(name, 98), name


def query_mentions_air_index_strategy(query: str) -> bool:
    return normalize_for_match("空气指增") in normalize_for_match(query)


def query_has_explicit_index_enhancement(query: str) -> bool:
    normalized = normalize_for_match(query)
    return any(
        normalize_for_match(term) in normalized for term in ("指数增强", "量化指增")
    )


def build_search_haystack(record: ProductProfileRecord) -> str:
    return "\n".join(
        [
            record.product_name,
            record.manager,
            record.entity_type,
            record.entity_confidence,
            " ".join(record.strategy_links),
            " ".join(record.people_links),
            " ".join(record.manager_aliases),
            " ".join(record.product_aliases),
            record.strategy_positioning,
            " ".join(record.product_line),
            " ".join(record.risk_points),
            record.key_people_summary,
            " ".join(record.evidence_summary),
            " ".join(record.source_files),
            record.evidence_source_type,
            record.external_evidence_status,
            record.evidence_conflict_status,
            str(record.source_priority),
            json.dumps(record.external_evidence, ensure_ascii=False),
            " ".join(record.strategy_raw_terms),
            " ".join(record.strategy_evidence),
            " ".join(record.primary_strategy_codes),
            " ".join(record.primary_strategy_tags),
            " ".join(record.secondary_strategy_codes),
            " ".join(record.secondary_strategy_tags),
            " ".join(record.direct_strategy_tags),
            " ".join(record.mentioned_strategy_tags),
            " ".join(record.rejected_strategy_tags),
            json.dumps(record.strategy_facets, ensure_ascii=False),
            " ".join(record.candidate_strategy_tags),
            record.strategy_tag_confidence,
            record.strategy_tag_source,
            record.strategy_tag_review_status,
            record.canonical_product_name,
            record.profile_quality_status,
            record.product_name_reason,
            " ".join(record.review_reasons),
            record.zm_match_status,
            record.profile_text,
            record.evidence_text,
            record.search_text,
        ]
    )


def build_strategy_tag_text(record: ProductProfileRecord) -> str:
    return "\n".join(
        [
            " ".join(record.primary_strategy_codes),
            " ".join(record.primary_strategy_tags),
            " ".join(record.secondary_strategy_codes),
            " ".join(record.secondary_strategy_tags),
            " ".join(record.direct_strategy_tags),
            json.dumps(record.strategy_facets, ensure_ascii=False),
            record.strategy_tag_confidence,
            record.strategy_tag_review_status,
        ]
    )


def load_relations_by_product(
    index_jsonl: Path,
    records: list[ProductProfileRecord],
    intent: QueryIntent,
) -> dict[str, list[RelationRecord]]:
    if not query_needs_relation_index(intent):
        return {}
    product_names = [record.product_name for record in records if record.product_name]
    relations = read_relation_sqlite(
        relation_sqlite_path_for(index_jsonl),
        product_names=product_names,
        predicates=relation_predicates_for_query(intent),
    )
    if not relations:
        relations = read_relation_jsonl(relation_jsonl_path_for(index_jsonl))
    grouped: dict[str, list[RelationRecord]] = {}
    for relation in relations:
        if not relation.product_name:
            continue
        grouped.setdefault(relation.product_name, []).append(relation)
    return grouped


def query_needs_relation_index(intent: QueryIntent) -> bool:
    relation_conditions = {"WorldQuant背景", "行业暴露", "行业暴露3%以内"}
    if any(
        item.kind == "condition" and item.label in relation_conditions
        for item in intent.hard_filters
    ):
        return True
    return any(item in relation_conditions for item in intent.normalized_conditions)


def relation_predicates_for_query(intent: QueryIntent) -> list[str]:
    predicates: list[str] = []
    condition_labels = {
        item.label
        for item in intent.hard_filters
        if item.kind == "condition"
    } | set(intent.normalized_conditions)
    if "WorldQuant背景" in condition_labels:
        predicates.append("has_people_background")
    if "行业暴露" in condition_labels or "行业暴露3%以内" in condition_labels:
        predicates.append("has_exposure_constraint")
    return dedupe_terms(
        predicates
        + [
            "has_primary_strategy",
            "has_secondary_strategy",
            "has_direct_strategy_tag",
            "has_candidate_strategy",
            "has_strategy",
            "has_strategy_facet",
            "has_product_line",
        ]
    )


def build_relation_text(relations: list[RelationRecord]) -> str:
    return "\n".join(
        [
            " ".join(
                [
                    relation.subject,
                    relation.predicate,
                    relation.object,
                    " ".join(relation.evidence),
                ]
            )
            for relation in relations
        ]
    )


def relation_match_label(term: str, relations: list[RelationRecord]) -> str:
    term_norm = normalize_for_match(term)
    for relation in relations:
        text = " ".join([relation.subject, relation.predicate, relation.object])
        if term_norm and term_norm in normalize_for_match(text):
            return f"{relation.predicate}={relation.object}"
    return f"relation={term}"


def pack_results(
    results: list[ProfileSearchResult],
    *,
    context_budget_chars: int,
    per_result_chars: int,
) -> tuple[list[ProfileSearchResult], int, int]:
    packed: list[ProfileSearchResult] = []
    used = 0
    truncated_count = 0
    for result in results:
        packed_profile = truncate_text(result.profile_text, per_result_chars // 2)
        packed_evidence = truncate_text(
            "\n".join(
                part
                for part in [
                    result.evidence_snippet,
                    "；".join(result.relation_matches[:4]),
                ]
                if part
            ),
            per_result_chars // 2,
        )
        context_chars = len(packed_profile) + len(packed_evidence)
        if packed and used + context_chars > context_budget_chars:
            truncated_count += 1
            continue
        if not packed and context_chars > context_budget_chars:
            packed_profile = truncate_text(
                packed_profile, max(context_budget_chars // 2, 120)
            )
            packed_evidence = truncate_text(
                packed_evidence, max(context_budget_chars // 2, 120)
            )
            context_chars = len(packed_profile) + len(packed_evidence)
            truncated_count += 1
        used += context_chars
        packed.append(
            ProfileSearchResult(
                product_name=result.product_name,
                manager=result.manager,
                score=result.score,
                matched_terms=result.matched_terms,
                missing_terms=result.missing_terms,
                hard_filter_satisfied=result.hard_filter_satisfied,
                hard_filter_status=result.hard_filter_status,
                profile_text=result.profile_text,
                evidence_snippet=result.evidence_snippet,
                path=result.path,
                entity_type=result.entity_type,
                entity_confidence=result.entity_confidence,
                canonical_product_name=result.canonical_product_name,
                profile_quality_status=result.profile_quality_status,
                review_reasons=result.review_reasons,
                evidence_source_type=result.evidence_source_type,
                external_evidence_status=result.external_evidence_status,
                evidence_conflict_status=result.evidence_conflict_status,
                source_priority=result.source_priority,
                external_evidence=result.external_evidence,
                primary_strategy_tags=result.primary_strategy_tags,
                secondary_strategy_tags=result.secondary_strategy_tags,
                direct_strategy_tags=result.direct_strategy_tags,
                mentioned_strategy_tags=result.mentioned_strategy_tags,
                rejected_strategy_tags=result.rejected_strategy_tags,
                strategy_facets=result.strategy_facets,
                strategy_tag_confidence=result.strategy_tag_confidence,
                strategy_tag_review_status=result.strategy_tag_review_status,
                relation_matches=result.relation_matches,
                ranking_reasons=result.ranking_reasons,
                packed_profile_text=packed_profile,
                packed_evidence=packed_evidence,
                context_chars=context_chars,
            )
        )
    return packed, used, truncated_count


def expand_terms(terms: list[str]) -> list[str]:
    expanded = list(terms)
    for term in terms:
        for key, aliases in QUERY_SYNONYMS.items():
            if normalize_for_match(term) == normalize_for_match(
                key
            ) or normalize_for_match(term) in {
                normalize_for_match(alias) for alias in aliases
            }:
                expanded.append(key)
                expanded.extend(aliases)
    return dedupe_terms(expanded)


def cjk_bigrams(text: str) -> list[str]:
    chars = [ch for ch in text if "\u4e00" <= ch <= "\u9fff"]
    return [chars[idx] + chars[idx + 1] for idx in range(len(chars) - 1)]


def generate_manager_aliases(manager: str | None) -> list[str]:
    return generate_shared_manager_aliases(manager or "")


def manager_filter_matches(manager_filter: HardFilter, manager: str | None) -> bool:
    if not manager:
        return False
    filter_manager = manager_filter.label.partition("=")[2] or manager_filter.label
    filter_identity = manager_identity_key(filter_manager)
    manager_identity = manager_identity_key(manager)
    if filter_identity and manager_identity:
        return filter_identity == manager_identity
    return aliases_match(manager_filter.aliases, manager)


def generate_product_aliases(
    product_name: str | None, manager: str | None = None
) -> list[str]:
    if not product_name:
        return []
    aliases = {
        product_name.strip(),
        product_name.replace("-", ""),
        product_name.replace("-", " "),
    }
    normalized = strip_product_suffix(product_name)
    aliases.add(normalized)
    aliases.add(normalized.replace("-", ""))
    parts = [part.strip() for part in re.split(r"[-_\s]+", normalized) if part.strip()]
    if len(parts) >= 2:
        aliases.add("".join(parts[1:]))
        aliases.add(" ".join(parts[1:]))
    manager_aliases = generate_manager_aliases(manager)
    for manager_alias in manager_aliases:
        manager_norm = normalize_for_match(manager_alias)
        product_norm = normalize_for_match(normalized)
        if manager_norm and product_norm.startswith(manager_norm):
            remainder = product_norm[len(manager_norm) :]
            if remainder:
                aliases.add(remainder)
    return clean_aliases(aliases)


def aliases_match(aliases: list[str], value: str) -> bool:
    normalized_value = normalize_for_match(value)
    for alias in aliases:
        normalized_alias = normalize_for_match(alias)
        if normalized_alias and normalized_alias in normalized_value:
            return True
    return False


def strip_product_suffix(value: str) -> str:
    result = value.strip()
    for suffix in ["私募证券投资基金", "私募基金", "证券投资基金"]:
        if result.endswith(suffix):
            result = result[: -len(suffix)].strip()
    return result


def normalize_for_match(value: str) -> str:
    return re.sub(r"[\W_]+", "", value or "").lower()


def term_weight(term: str, field: str) -> float:
    lower = term.lower()
    if field == "manager":
        return 6.0
    if field == "product":
        return 8.0
    if field == "strategy_tag":
        return 4.5
    if field == "relation":
        return 4.5
    if lower in ("worldquant", "世坤"):
        return 5.0
    if "cta" in lower:
        return 3.0
    if (
        "2000" in lower
        or "1000" in lower
        or "500" in lower
        or "300" in lower
        or "指增" in term
        or "指数增强" in term
    ):
        return 3.0
    if "行业" in term or "暴露" in term or "偏离" in term:
        return 2.5
    return 1.5


def pick_snippet(record: ProductProfileRecord, matched_terms: list[str]) -> str:
    lines = [
        line.strip("- ").strip() for line in record.evidence_summary if line.strip()
    ]
    lines.extend(
        line.strip("- ").strip() for line in record.risk_points if line.strip()
    )
    lines.extend(
        line.strip("- ").strip() for line in record.strategy_evidence if line.strip()
    )
    if record.primary_strategy_tags or record.secondary_strategy_tags:
        lines.append(
            "Strategy tags: "
            + " / ".join(record.primary_strategy_tags + record.secondary_strategy_tags)
        )
    if record.strategy_positioning:
        lines.append(record.strategy_positioning)
    lines.extend(
        line.strip("- ").strip()
        for line in record.evidence_text.splitlines()
        if line.strip()
    )
    for term in matched_terms:
        for line in lines:
            if term.lower() in line.lower():
                return line
    return lines[0] if lines else record.profile_text


def clean_aliases(values: set[str]) -> list[str]:
    cleaned = []
    seen = set()
    for value in values:
        text = str(value).strip()
        normalized = normalize_for_match(text)
        if len(normalized) < 2:
            continue
        if normalized not in seen:
            cleaned.append(text)
            seen.add(normalized)
    return sorted(cleaned, key=lambda item: (-len(normalize_for_match(item)), item))


def dedupe_terms(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        key = value.lower()
        if value and key not in seen:
            result.append(value)
            seen.add(key)
    return result


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip("，。；;,. ") + "…"
