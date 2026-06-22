"""Normalize raw strategy language into fund-wiki strategy tags."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

import yaml


@dataclass(frozen=True)
class PrimaryTag:
    code: str
    name: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class SecondaryTag:
    code: str
    parent: str
    name: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class StrategyTaxonomy:
    version: str
    primary_tags: tuple[PrimaryTag, ...]
    secondary_tags: tuple[SecondaryTag, ...]
    facet_axes: dict[str, dict[str, tuple[str, ...]]]


@dataclass(frozen=True)
class StrategyTaggingResult:
    primary_strategy_codes: list[str] = field(default_factory=list)
    primary_strategy_tags: list[str] = field(default_factory=list)
    secondary_strategy_codes: list[str] = field(default_factory=list)
    secondary_strategy_tags: list[str] = field(default_factory=list)
    strategy_facets: dict[str, list[str]] = field(default_factory=dict)
    strategy_raw_terms: list[str] = field(default_factory=list)
    candidate_strategy_tags: list[str] = field(default_factory=list)
    strategy_tag_confidence: str = "low"
    strategy_tag_review_status: str = "needs_review"
    strategy_tag_source: str = "taxonomy_rules"


def classify_strategy_text(text: str) -> StrategyTaggingResult:
    """Return normalized strategy labels while preserving raw matched evidence terms."""
    taxonomy = load_taxonomy()
    normalized_text = normalize_for_match(text)
    if not normalized_text:
        return StrategyTaggingResult(
            primary_strategy_codes=["OTHER_REVIEW"],
            primary_strategy_tags=["待确认"],
            strategy_tag_confidence="low",
            strategy_tag_review_status="needs_review",
        )

    raw_terms: list[str] = []
    primary_scores: dict[str, int] = {}
    primary_by_code = {item.code: item for item in taxonomy.primary_tags}
    secondary_hits: list[SecondaryTag] = []

    for tag in taxonomy.secondary_tags:
        matched = matched_aliases(normalized_text, [tag.name, *tag.aliases])
        if not matched:
            continue
        raw_terms.extend(matched)
        secondary_hits.append(tag)
        primary_scores[tag.parent] = primary_scores.get(tag.parent, 0) + 4 + len(matched)

    for tag in taxonomy.primary_tags:
        matched = matched_aliases(normalized_text, [tag.name, *tag.aliases])
        if not matched:
            continue
        raw_terms.extend(matched)
        primary_scores[tag.code] = primary_scores.get(tag.code, 0) + 2 + len(matched)

    if not primary_scores:
        return StrategyTaggingResult(
            primary_strategy_codes=["OTHER_REVIEW"],
            primary_strategy_tags=["待确认"],
            strategy_raw_terms=dedupe(raw_terms),
            candidate_strategy_tags=extract_candidate_terms(text),
            strategy_tag_confidence="low",
            strategy_tag_review_status="needs_review",
        )

    primary_codes = choose_primary_codes(primary_scores, taxonomy)
    primary_tags = [primary_by_code[code].name for code in primary_codes if code in primary_by_code]
    secondary_codes = [
        tag.code for tag in secondary_hits if not primary_codes or tag.parent in primary_codes
    ]
    secondary_tags = [
        tag.name for tag in secondary_hits if not primary_codes or tag.parent in primary_codes
    ]
    facets = infer_facets(normalized_text, taxonomy)
    confidence = infer_confidence(primary_codes, secondary_codes, facets)
    review_status = "confirmed" if confidence in {"high", "medium"} else "needs_review"
    candidate_tags = [
        tag.name for tag in secondary_hits if tag.parent not in set(primary_codes)
    ]

    return StrategyTaggingResult(
        primary_strategy_codes=dedupe(primary_codes),
        primary_strategy_tags=dedupe(primary_tags),
        secondary_strategy_codes=dedupe(secondary_codes),
        secondary_strategy_tags=dedupe(secondary_tags),
        strategy_facets={key: dedupe(value) for key, value in facets.items()},
        strategy_raw_terms=dedupe(raw_terms),
        candidate_strategy_tags=dedupe(candidate_tags + extract_candidate_terms(text)),
        strategy_tag_confidence=confidence,
        strategy_tag_review_status=review_status,
    )


def expand_strategy_query_terms(query: str) -> list[str]:
    """Expand a natural-language query with canonical taxonomy labels and aliases."""
    taxonomy = load_taxonomy()
    normalized_query = normalize_for_match(query)
    terms: list[str] = []
    for tag in taxonomy.primary_tags:
        aliases = [tag.code, tag.name, *tag.aliases]
        if matched_aliases(normalized_query, aliases):
            terms.extend(aliases)
    for tag in taxonomy.secondary_tags:
        aliases = [tag.code, tag.name, *tag.aliases]
        if matched_aliases(normalized_query, aliases):
            terms.extend(aliases)
            parent = next(
                (item for item in taxonomy.primary_tags if item.code == tag.parent),
                None,
            )
            if parent:
                terms.extend([parent.code, parent.name, *parent.aliases])
    return dedupe(terms)


@lru_cache(maxsize=1)
def load_taxonomy() -> StrategyTaxonomy:
    path = Path(__file__).with_name("strategy_taxonomy.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    primary_tags = tuple(
        PrimaryTag(
            code=str(item["code"]),
            name=str(item["name"]),
            aliases=tuple(str(alias) for alias in item.get("aliases", [])),
        )
        for item in data.get("primary_tags", [])
    )
    secondary_tags = tuple(
        SecondaryTag(
            code=str(item["code"]),
            parent=str(item["parent"]),
            name=str(item["name"]),
            aliases=tuple(str(alias) for alias in item.get("aliases", [])),
        )
        for item in data.get("secondary_tags", [])
    )
    facet_axes = {
        str(axis): {
            str(value): tuple(str(alias) for alias in aliases)
            for value, aliases in values.items()
        }
        for axis, values in (data.get("facet_axes", {}) or {}).items()
    }
    return StrategyTaxonomy(
        version=str(data.get("version", "")),
        primary_tags=primary_tags,
        secondary_tags=secondary_tags,
        facet_axes=facet_axes,
    )


def choose_primary_codes(scores: dict[str, int], taxonomy: StrategyTaxonomy) -> list[str]:
    order = {tag.code: idx for idx, tag in enumerate(taxonomy.primary_tags)}
    best_score = max(scores.values())
    best = [
        code
        for code, score in scores.items()
        if score == best_score and code != "OTHER_REVIEW"
    ]
    if not best:
        return ["OTHER_REVIEW"]
    return sorted(best, key=lambda code: order.get(code, 10_000))[:1]


def infer_facets(
    normalized_text: str, taxonomy: StrategyTaxonomy
) -> dict[str, list[str]]:
    facets: dict[str, list[str]] = {}
    for axis, values in taxonomy.facet_axes.items():
        for value, aliases in values.items():
            if matched_aliases(normalized_text, [value, *aliases]):
                facets.setdefault(axis, []).append(value)
    return facets


def infer_confidence(
    primary_codes: list[str],
    secondary_codes: list[str],
    facets: dict[str, list[str]],
) -> str:
    if not primary_codes or "OTHER_REVIEW" in primary_codes:
        return "low"
    if secondary_codes and facets:
        return "high"
    if secondary_codes:
        return "medium"
    return "medium"


def matched_aliases(normalized_text: str, aliases: list[str] | tuple[str, ...]) -> list[str]:
    matches = []
    for alias in aliases:
        normalized_alias = normalize_for_match(alias)
        if normalized_alias and normalized_alias in normalized_text:
            matches.append(str(alias))
    return matches


def extract_candidate_terms(text: str) -> list[str]:
    candidates = []
    for pattern in [
        r"[\u4e00-\u9fffA-Za-z0-9]{0,12}CTA[\u4e00-\u9fffA-Za-z0-9]{0,12}",
        r"[\u4e00-\u9fffA-Za-z0-9]{0,12}套利[\u4e00-\u9fffA-Za-z0-9]{0,12}",
        r"[\u4e00-\u9fffA-Za-z0-9]{0,12}中性[\u4e00-\u9fffA-Za-z0-9]{0,12}",
        r"[\u4e00-\u9fffA-Za-z0-9]{0,12}指增[\u4e00-\u9fffA-Za-z0-9]{0,12}",
    ]:
        candidates.extend(match.group(0) for match in re.finditer(pattern, text))
    return dedupe(candidates)


def normalize_for_match(value: str) -> str:
    return re.sub(r"[\W_]+", "", value or "").lower()


def dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        key = normalize_for_match(text)
        if text and key not in seen:
            result.append(text)
            seen.add(key)
    return result
