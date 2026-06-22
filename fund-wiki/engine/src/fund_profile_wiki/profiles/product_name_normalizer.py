"""Normalize product names and identify product-line pseudo names."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from fund_profile_wiki.profiles.manager_alias_registry import (
    registered_manager_aliases,
    registered_manager_identity_key,
)

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

COMPANY_SUFFIXES = (
    "私募基金管理有限责任公司",
    "基金管理有限责任公司",
    "资产管理有限责任公司",
    "投资管理有限责任公司",
    "投资有限责任公司",
    "资本管理有限责任公司",
    "资本有限责任公司",
    "私募基金管理合伙企业有限合伙",
    "基金管理合伙企业有限合伙",
    "管理合伙企业有限合伙",
    "合伙企业有限合伙",
    "私募基金管理合伙企业（有限合伙）",
    "基金管理合伙企业（有限合伙）",
    "管理合伙企业（有限合伙）",
    "合伙企业（有限合伙）",
    "私募基金管理合伙企业",
    "基金管理合伙企业",
    "管理合伙企业",
    "合伙企业",
    "私募基金管理有限公司",
    "资产管理有限公司",
    "投资管理有限公司",
    "投资有限公司",
    "资本管理有限公司",
    "资本有限公司",
    "基金管理有限公司",
    "有限责任公司",
    "有限公司",
)
CITY_PREFIXES = (
    "上海",
    "北京",
    "深圳市",
    "深圳",
    "广州",
    "杭州",
    "萧山",
    "宁波",
    "南京",
    "苏州",
    "珠海",
    "天津",
    "青岛",
    "厦门",
    "三亚",
    "海南",
    "广东",
    "浙江",
    "江苏",
    "安徽",
    "福建",
    "山东",
    "四川",
    "重庆",
)

FUND_SUFFIXES = (
    "私募证券投资基金",
    "证券投资基金",
    "私募基金",
    "基金",
)

GENERIC_PRODUCT_TAILS = (
    "代表产品",
    "策略产品",
    "系列产品",
    "产品线",
    "产品系列",
    "产品",
)

SPECIFIC_MARKER_RE = re.compile(
    r"(\d+\s*号|[一二三四五六七八九十]+\s*号|\d+\s*期|"
    r"集合资产管理计划|资产管理计划|资管计划|私募证券投资基金|证券投资基金|私募基金|基金)"
)

STRATEGY_FAMILIES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("quant_long", "量化多头", ("量化多头", "量化多头策略", "空气指增")),
    (
        "2000_index_enhancement",
        "中证2000指数增强",
        ("中证2000指数增强", "中证2000指增", "2000指增", "2000增强"),
    ),
    (
        "1000_index_enhancement",
        "中证1000指数增强",
        ("中证1000指数增强", "中证1000指增", "1000指增", "1000增强"),
    ),
    (
        "a500_index_enhancement",
        "中证A500指数增强",
        ("中证A500指数增强", "中证A500指增", "A500指增", "A500增强"),
    ),
    (
        "500_index_enhancement",
        "中证500指数增强",
        ("中证500指数增强", "中证500指增", "500指增", "500增强"),
    ),
    (
        "300_index_enhancement",
        "沪深300指数增强",
        ("沪深300指数增强", "沪深300指增", "300指增", "300增强"),
    ),
    ("index_enhancement", "指数增强", ("指数增强", "量化指增", "指增")),
    ("market_neutral", "市场中性", ("市场中性", "量化中性")),
    ("multi_cta", "多元CTA", ("多元CTA",)),
    ("standard_cta", "标准CTA", ("标准CTA", "通用CTA")),
    ("commodity_cta", "商品CTA", ("商品CTA", "商品趋势", "商品截面", "商品基本面")),
    ("index_futures_cta", "股指CTA", ("股指CTA", "股指期货CTA")),
    ("option_cta", "期权CTA", ("期权CTA", "50ETF期权", "300ETF期权")),
    ("cta", "CTA", ("CTA", "管理期货")),
)


@dataclass(frozen=True)
class ProductNameAnalysis:
    original_name: str
    canonical_name: str
    canonical_key: str
    aliases: list[str]
    family: str
    family_label: str
    is_generic: bool
    quality_status: str
    reason: str
    entity_type: str
    entity_confidence: str
    review_reasons: list[str]


def analyze_product_name(product_name: str, manager: str = "") -> ProductNameAnalysis:
    """Return a deterministic product-name classification."""

    original = extract_wikilink(product_name)
    cleaned = clean_product_name(original)
    manager_aliases = generate_manager_aliases(manager)
    without_manager = strip_manager_prefix(cleaned, manager_aliases)
    family, family_label = detect_strategy_family(cleaned)
    has_specific_marker = has_product_specific_marker(without_manager)
    strategy_like = is_strategy_like_name(without_manager, family_label)
    tail_stripped = strip_generic_product_tail(without_manager)

    is_generic = False
    reason = "product_specific"
    entity_type = "product"
    entity_confidence = "high"
    review_reasons: list[str] = []
    if family and not has_specific_marker and without_manager != tail_stripped:
        is_generic = True
        reason = "strategy_product_line"
    elif without_manager != tail_stripped and not has_specific_marker:
        is_generic = True
        reason = "generic_product_tail"
    elif strategy_like:
        is_generic = True
        reason = "pure_strategy_name"
    elif (
        family
        and not has_specific_marker
        and is_strategy_like_name(tail_stripped, family_label)
    ):
        is_generic = True
        reason = "manager_strategy_line"

    canonical_name = cleaned
    if is_generic:
        canonical_name = generic_canonical_name(manager, family_label, cleaned)
        entity_type = generic_entity_type(without_manager, reason)
        entity_confidence = "low"
        review_reasons.append(reason)
    canonical_key = build_canonical_key(canonical_name, manager, is_generic=is_generic)
    aliases = build_aliases(
        original, cleaned, canonical_name, without_manager, tail_stripped, family_label
    )
    if is_generic:
        quality_status = "weak_line"
    elif is_suspicious_short_name(without_manager, cleaned):
        quality_status = "needs_review"
        reason = "suspicious_short_name"
        entity_confidence = "medium"
        review_reasons.append(reason)
    else:
        quality_status = "confirmed"

    return ProductNameAnalysis(
        original_name=original,
        canonical_name=canonical_name,
        canonical_key=canonical_key,
        aliases=aliases,
        family=family,
        family_label=family_label,
        is_generic=is_generic,
        quality_status=quality_status,
        reason=reason,
        entity_type=entity_type,
        entity_confidence=entity_confidence,
        review_reasons=review_reasons,
    )


def extract_wikilink(value: object) -> str:
    text = str(value or "").strip()
    match = WIKILINK_RE.search(text)
    return match.group(1).strip() if match else text.strip("'\" ")


def clean_product_name(value: str) -> str:
    text = extract_wikilink(value)
    text = re.sub(r"\s+", "", text)
    text = text.strip(" -_，,。；;：:（）()[]【】")
    return text


def normalize_manager_name(value: str) -> str:
    """Normalize manager names for alias generation and identity matching."""
    text = extract_wikilink(value)
    text = re.sub(r"\s+", "", text)
    text = text.strip(" -_，,。；;：:")
    text = re.sub(r"^(\d{4,})[_\-\s]*", "", text)
    text = text.replace("（", "(").replace("）", ")")
    city_pattern = "|".join(
        re.escape(city) for city in sorted(CITY_PREFIXES, key=len, reverse=True)
    )
    text = re.sub(rf"\(({city_pattern})\)", "", text)
    text = re.sub(r"\(([^)]{1,8})\)", r"\1", text)
    for marker in ("私募证券", "私募基金", "私募"):
        if text.endswith(marker):
            text = text[: -len(marker)]
    return clean_product_name(text)


def is_suspicious_short_name(without_manager: str, cleaned: str) -> bool:
    text = strip_generic_product_tail(without_manager or cleaned)
    if has_product_specific_marker(text) or detect_strategy_family(text)[0]:
        return False
    if not re.fullmatch(r"[\u4e00-\u9fff]{2,3}", text):
        return False
    return True


def detect_strategy_family(value: str) -> tuple[str, str]:
    normalized = normalize_for_match(value)
    for family, label, aliases in STRATEGY_FAMILIES:
        if any(normalize_for_match(alias) in normalized for alias in aliases):
            return family, label
    return "", ""


def has_product_specific_marker(value: str) -> bool:
    return bool(SPECIFIC_MARKER_RE.search(value or ""))


def is_strategy_like_name(value: str, family_label: str = "") -> bool:
    normalized = normalize_for_match(strip_generic_product_tail(value))
    if not normalized:
        return False
    labels = {label for _, label, _ in STRATEGY_FAMILIES}
    aliases = {
        alias for _, _, family_aliases in STRATEGY_FAMILIES for alias in family_aliases
    }
    strategy_terms = labels | aliases
    if family_label:
        strategy_terms.add(family_label)
    return normalized in {normalize_for_match(item) for item in strategy_terms}


def strip_generic_product_tail(value: str) -> str:
    result = clean_product_name(value)
    changed = True
    while changed:
        changed = False
        for tail in GENERIC_PRODUCT_TAILS:
            if result.endswith(tail):
                result = result[: -len(tail)].strip()
                changed = True
    return result


def generic_canonical_name(manager: str, family_label: str, fallback: str) -> str:
    manager_short = strip_company_suffix(strip_city_prefix(manager))
    if manager_short and family_label:
        return f"{manager_short}{family_label}"
    return family_label or fallback


def generic_entity_type(product_name: str, reason: str) -> str:
    text = clean_product_name(product_name)
    if text.endswith(("系列", "产品系列", "系列产品")):
        return "product_series"
    if reason in {"pure_strategy_name", "strategy_product_line", "manager_strategy_line"}:
        return "strategy_line"
    return "generic_bucket"


def build_canonical_key(name: str, manager: str, *, is_generic: bool = False) -> str:
    product = normalize_product_synonyms(name)
    for alias in generate_manager_aliases(manager):
        alias_norm = normalize_product_synonyms(alias)
        if alias_norm and product.startswith(alias_norm):
            product = product[len(alias_norm) :]
            break
    prefix = "generic" if is_generic else "product"
    return f"{manager_identity_key(manager)}|{prefix}|{product}"


def normalize_product_synonyms(value: str) -> str:
    text = normalize_for_match(
        replace_chinese_number_suffixes(strip_fund_suffix(value))
    )
    replacements = {
        "中证2000指增": "中证2000指数增强",
        "2000指增": "中证2000指数增强",
        "2000增强": "中证2000指数增强",
        "中证1000指增": "中证1000指数增强",
        "1000指增": "中证1000指数增强",
        "1000增强": "中证1000指数增强",
        "中证500指增": "中证500指数增强",
        "500指增": "中证500指数增强",
        "500增强": "中证500指数增强",
        "沪深300指增": "沪深300指数增强",
        "300指增": "沪深300指数增强",
        "300增强": "沪深300指数增强",
    }
    for old, new in replacements.items():
        text = text.replace(normalize_for_match(old), normalize_for_match(new))
    return text


def replace_chinese_number_suffixes(value: str) -> str:
    result = clean_product_name(value)
    replacements = (
        ("一号", "1号"),
        ("二号", "2号"),
        ("三号", "3号"),
        ("四号", "4号"),
        ("五号", "5号"),
        ("六号", "6号"),
        ("七号", "7号"),
        ("八号", "8号"),
        ("九号", "9号"),
        ("十号", "10号"),
    )
    for chinese, arabic in replacements:
        result = result.replace(chinese, arabic)
    return result


def strip_fund_suffix(value: str) -> str:
    result = clean_product_name(value)
    changed = True
    while changed:
        changed = False
        for suffix in FUND_SUFFIXES:
            if result.endswith(suffix):
                result = result[: -len(suffix)]
                changed = True
    return result


def generate_manager_aliases(manager: str) -> list[str]:
    if not manager:
        return []
    working = normalize_manager_name(manager)
    raw = clean_product_name(manager)
    aliases = {
        raw,
        working,
        strip_city_prefix(working),
        strip_company_suffix(working),
        strip_company_suffix(strip_city_prefix(working)),
    }
    for keyword in (
        "投资",
        "资产",
        "资本",
        "基金管理",
        "私募基金管理",
        "资产管理",
        "投资管理",
    ):
        aliases.add(
            strip_keyword(strip_company_suffix(strip_city_prefix(working)), keyword)
        )
        aliases.add(strip_keyword(strip_company_suffix(working), keyword))
    core = strip_company_suffix(strip_city_prefix(working))
    for keyword in (
        "私募基金管理",
        "基金管理",
        "资产管理",
        "投资管理",
        "投资",
        "资产",
        "资本",
    ):
        stripped = strip_keyword(core, keyword)
        if stripped:
            core = stripped
    for marker in ("私募证券", "私募基金", "私募", "基金"):
        if core.endswith(marker):
            core = core[: -len(marker)]
    if core:
        aliases.add(core)
        aliases.add(f"{core}基金")
        aliases.add(f"{core}私募")
        aliases.add(f"{core}私募基金")
    aliases.update(registered_manager_aliases(manager))
    aliases.update(registered_manager_aliases(working))
    return clean_aliases(aliases)


def manager_identity_key(manager: str) -> str:
    working = normalize_manager_name(manager)
    if not working:
        return ""
    registered_key = registered_manager_identity_key(
        manager
    ) or registered_manager_identity_key(working)
    if registered_key:
        return registered_key
    core = strip_company_suffix(strip_city_prefix(working)) or strip_company_suffix(
        working
    )
    if not core:
        core = working
    for keyword in (
        "私募基金管理",
        "基金管理",
        "资产管理",
        "投资管理",
        "投资",
        "资产",
        "资本",
    ):
        stripped = strip_keyword(core, keyword)
        if stripped:
            core = stripped
    core = strip_city_prefix(core)
    for marker in ("私募证券", "私募基金", "私募", "基金"):
        if core.endswith(marker):
            core = core[: -len(marker)]
    return normalize_for_match(core or working)


def strip_manager_prefix(product_name: str, manager_aliases: list[str]) -> str:
    result = clean_product_name(product_name)
    result_norm = normalize_for_match(result)
    for alias in sorted(
        manager_aliases, key=lambda item: len(normalize_for_match(item)), reverse=True
    ):
        alias_norm = normalize_for_match(alias)
        if alias_norm and result_norm.startswith(alias_norm):
            return result[len(alias) :]
    return result


def strip_company_suffix(value: str) -> str:
    result = clean_product_name(value)
    changed = True
    while changed:
        changed = False
        for suffix in COMPANY_SUFFIXES:
            if result.endswith(suffix):
                result = result[: -len(suffix)]
                changed = True
    return result


def strip_city_prefix(value: str) -> str:
    result = clean_product_name(value)
    changed = True
    while changed:
        changed = False
        for prefix in sorted(CITY_PREFIXES, key=len, reverse=True):
            if result.startswith(prefix):
                result = result[len(prefix) :]
                changed = True
    return result


def strip_keyword(value: str, keyword: str) -> str:
    return clean_product_name(value).replace(keyword, "")


def build_aliases(*values: str) -> list[str]:
    return clean_aliases(value for value in values if value)


def clean_aliases(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = clean_product_name(value)
        key = normalize_for_match(text)
        if len(key) < 2 or key in seen:
            continue
        result.append(text)
        seen.add(key)
    return sorted(result, key=lambda item: (-len(normalize_for_match(item)), item))


def normalize_for_match(value: str) -> str:
    return re.sub(r"[\W_]+", "", value or "").casefold()
