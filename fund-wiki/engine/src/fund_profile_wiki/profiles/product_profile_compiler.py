"""Compile product-level LLM profiles from source notes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

from fund_profile_wiki.config import Settings
from fund_profile_wiki.index.profile_index import load_profile_records
from fund_profile_wiki.notes.diligence_note_reader import (
    MarkdownNote,
    ensure_wikilink,
    extract_heading_section,
    extract_lines_containing,
    extract_products,
    extract_wikilink,
    normalize_link_list,
    read_markdown_note,
)
from fund_profile_wiki.profiles.product_name_normalizer import (
    ProductNameAnalysis,
    analyze_product_name,
    generate_manager_aliases as shared_generate_manager_aliases,
    manager_identity_key as shared_manager_identity_key,
)
from fund_profile_wiki.profiles.profile_quality import write_profile_quality_report
from fund_profile_wiki.profiles.manager_wiki_compiler import write_manager_wiki_docs
from fund_profile_wiki.profiles.zmdata_identity import enrich_profile_with_zmdata
from fund_profile_wiki.taxonomy.strategy_taxonomy import classify_strategy_text

INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\n\r\t]+')

COMPANY_SUFFIXES = [
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
]
CITY_PREFIXES = [
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
]
PRODUCT_SUFFIXES = ["私募证券投资基金", "证券投资基金", "私募基金", "基金"]
PRODUCT_LINE_RULES = [
    ("多元CTA", ["多元CTA"]),
    ("标准CTA", ["标准CTA", "通用CTA"]),
    ("商品CTA", ["商品CTA", "商品趋势", "商品截面", "商品期限结构", "商品基本面"]),
    ("股指CTA", ["股指CTA", "股指期货CTA"]),
    ("金融CTA", ["金融CTA"]),
    ("期权CTA", ["期权CTA", "50ETF", "300ETF", "期权"]),
    ("趋势CTA", ["趋势CTA", "趋势"]),
    ("基本面CTA", ["基本面CTA", "基本面"]),
    ("工具化CTA", ["工具化CTA", "隆成拓展"]),
    ("中证2000指增", ["中证2000", "2000指增", "2000增强"]),
    ("中证1000指增", ["中证1000", "1000指增", "1000增强"]),
    ("中证A500指增", ["中证A500", "A500指增", "A500指数增强", "A500增强"]),
    ("中证500指增", ["中证500", "500指增", "500增强"]),
    ("沪深300指增", ["沪深300", "300指增", "300增强"]),
    ("指数增强", ["指数增强", "量化指增", "指增"]),
    ("市场中性", ["市场中性"]),
]
BENCHMARK_LINE_LABELS = {
    "2000": {"中证2000指增"},
    "1000": {"中证1000指增"},
    "A500": {"中证A500指增"},
    "500": {"中证500指增"},
    "300": {"沪深300指增"},
}
BENCHMARK_SECONDARY_CODES = {
    "2000": {"IE_2000"},
    "1000": {"IE_1000"},
    "A500": {"IE_A500"},
    "500": {"IE_500"},
    "300": {"IE_300"},
}
BENCHMARK_SECONDARY_TAGS = {
    "2000": {"2000指增"},
    "1000": {"1000指增"},
    "A500": {"A500指增"},
    "500": {"500指增"},
    "300": {"300指增"},
}
BENCHMARK_FACET_VALUES = {
    "2000": "中证2000",
    "1000": "中证1000",
    "A500": "中证A500",
    "500": "中证500",
    "300": "沪深300",
}


@dataclass(frozen=True)
class EvidenceItem:
    text: str
    source_path: str


@dataclass
class ProductProfile:
    product_name: str
    manager: str = ""
    entity_type: str = "product"
    entity_confidence: str = "high"
    strategy_links: list[str] = field(default_factory=list)
    people_links: list[str] = field(default_factory=list)
    source_notes: list[str] = field(default_factory=list)
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    llm_profile: str = ""
    manager_aliases: list[str] = field(default_factory=list)
    product_aliases: list[str] = field(default_factory=list)
    strategy_positioning: str = ""
    product_line: list[str] = field(default_factory=list)
    risk_points: list[str] = field(default_factory=list)
    key_people_summary: str = ""
    evidence_summary: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    evidence_source_type: str = "internal_due_diligence"
    external_evidence_status: str = "not_checked"
    evidence_conflict_status: str = "none"
    source_priority: int = 10
    external_evidence: list[dict] = field(default_factory=list)
    strategy_raw_terms: list[str] = field(default_factory=list)
    strategy_evidence: list[str] = field(default_factory=list)
    primary_strategy_codes: list[str] = field(default_factory=list)
    primary_strategy_tags: list[str] = field(default_factory=list)
    secondary_strategy_codes: list[str] = field(default_factory=list)
    secondary_strategy_tags: list[str] = field(default_factory=list)
    direct_strategy_tags: list[str] = field(default_factory=list)
    mentioned_strategy_tags: list[str] = field(default_factory=list)
    rejected_strategy_tags: list[str] = field(default_factory=list)
    strategy_facets: dict[str, list[str]] = field(default_factory=dict)
    candidate_strategy_tags: list[str] = field(default_factory=list)
    strategy_tag_confidence: str = ""
    strategy_tag_source: str = ""
    strategy_tag_review_status: str = ""
    canonical_product_name: str = ""
    profile_quality_status: str = "confirmed"
    product_name_reason: str = "product_specific"
    review_reasons: list[str] = field(default_factory=list)
    zm_match_status: str = "off"
    zm_fund_ids: list[str] = field(default_factory=list)
    zm_fund_codes: list[str] = field(default_factory=list)
    zm_candidate_matches: list[str] = field(default_factory=list)
    zm_rejected_candidates: list[str] = field(default_factory=list)


class ProductProfileCompiler:
    RISK_KEYWORDS = [
        "风险",
        "暴露",
        "行业",
        "偏离",
        "敞口",
        "持仓",
        "Barra",
        "BARRA",
        "换手",
        "容量",
    ]
    PEOPLE_BACKGROUND_KEYWORDS = [
        "WorldQuant",
        "worldquant",
        "世坤",
        "Pine River",
        "GSA",
        "Fore Research",
        "曾任",
        "曾就职",
        "任职",
    ]

    def __init__(self, template_path: Path | None = None):
        self.template_path = (
            template_path
            or Path(__file__).resolve().parents[3]
            / "templates"
            / "product_profile_auto.md"
        )

    def compile_from_roots(
        self,
        source_roots: Iterable[Path],
        output_root: Path = Settings.product_profiles_dir,
    ) -> list[Path]:
        source_roots = list(source_roots)
        profiles = self.collect_profiles(source_roots)
        apply_canonical_manager_names(profiles)
        for profile in profiles:
            self.enrich_profile(profile, include_external=True)
        profiles = merge_profiles_by_external_identity(
            profiles,
            max_evidence_items=Settings.product_profile_max_evidence_items,
        )
        apply_canonical_manager_names(profiles)
        output_root.mkdir(parents=True, exist_ok=True)
        removed_existing_by_source = remove_existing_source_note_profiles(
            output_root, source_roots
        )
        removed_existing = remove_existing_manager_profiles(
            output_root, {profile.manager for profile in profiles if profile.manager}
        )
        removed_existing += removed_existing_by_source
        written = []
        used_output_paths: set[Path] = set()
        for profile in profiles:
            self.enrich_profile(profile, include_external=False)
            profile.llm_profile = self.build_llm_profile(profile)
            path = output_path_for_profile(profile, output_root, used_output_paths)
            path.write_text(self.render_profile(profile), encoding="utf-8")
            used_output_paths.add(path)
            written.append(path)
        final_records = load_profile_records(output_root)
        write_profile_quality_report(
            final_records,
            report_path_for_output_root(output_root),
            removed_existing_profiles=removed_existing,
        )
        write_manager_wiki_docs(final_records, docs_root_for_output_root(output_root))
        return written

    def collect_profiles(self, source_roots: Iterable[Path]) -> list[ProductProfile]:
        fragments: list[ProductProfile] = []
        for root in source_roots:
            if not root.exists():
                continue
            for note_path in root.rglob("*.md"):
                note = read_markdown_note(note_path)
                fragments.extend(self._fragments_from_note(note))
        return self._merge_fragments(fragments)

    def _merge_fragments(self, fragments: list[ProductProfile]) -> list[ProductProfile]:
        by_product: dict[str, ProductProfile] = {}
        generic_fragments: list[tuple[ProductProfile, ProductNameAnalysis]] = []
        for fragment in fragments:
            analysis = analyze_product_name(fragment.product_name, fragment.manager)
            apply_product_name_analysis(fragment, analysis)
            if analysis.is_generic:
                generic_fragments.append((fragment, analysis))
                continue
            current = by_product.setdefault(
                analysis.canonical_key,
                ProductProfile(
                    product_name=analysis.canonical_name,
                    manager=fragment.manager,
                    entity_type=fragment.entity_type,
                    entity_confidence=fragment.entity_confidence,
                    canonical_product_name=analysis.canonical_name,
                    profile_quality_status=analysis.quality_status,
                    product_name_reason=analysis.reason,
                    product_aliases=list(analysis.aliases),
                    review_reasons=list(fragment.review_reasons),
                ),
            )
            merge_profile(
                current,
                fragment,
                max_evidence_items=Settings.product_profile_max_evidence_items,
            )

        for fragment, analysis in generic_fragments:
            targets = [
                profile
                for profile in by_product.values()
                if profiles_share_manager(profile, fragment)
                and profile_matches_family(profile, analysis.family)
            ]
            if targets:
                for target in targets:
                    target.product_aliases = dedupe(
                        target.product_aliases + analysis.aliases
                    )
                    merge_profile(
                        target,
                        fragment,
                        max_evidence_items=Settings.product_profile_max_evidence_items,
                    )
                continue
            if analysis.is_generic:
                continue
            current = by_product.setdefault(
                analysis.canonical_key,
                ProductProfile(
                    product_name=analysis.canonical_name,
                    manager=fragment.manager,
                    entity_type=fragment.entity_type,
                    entity_confidence=fragment.entity_confidence,
                    canonical_product_name=analysis.canonical_name,
                    profile_quality_status=analysis.quality_status,
                    product_name_reason=analysis.reason,
                    product_aliases=list(analysis.aliases),
                    review_reasons=list(fragment.review_reasons),
                ),
            )
            merge_profile(
                current,
                fragment,
                max_evidence_items=Settings.product_profile_max_evidence_items,
            )
        return sorted(by_product.values(), key=lambda item: item.product_name)

    def _fragments_from_note(self, note: MarkdownNote) -> list[ProductProfile]:
        products = extract_products(note)
        if not products:
            return []
        manager = self._infer_manager(note)
        people_links = normalize_link_list(note.frontmatter.get("key_personnel", []))
        fragments = []
        for product in products:
            product_name = extract_wikilink(product.get("name"))
            strategies = normalize_link_list(
                product.get("main_strategies", [])
            ) + normalize_link_list(product.get("sub_strategies", []))
            if not strategies:
                strategies = normalize_link_list(
                    note.frontmatter.get("main_strategies", [])
                ) + normalize_link_list(note.frontmatter.get("sub_strategies", []))
            strategies = filter_strategy_links_for_product(
                product_name, dedupe(strategies)
            )
            entity_type = normalize_entity_type(str(product.get("entity_type", "")))
            if not entity_type and bool(product.get("is_series", False)):
                entity_type = "product_series"
            entity_confidence = normalize_entity_confidence(
                str(product.get("confidence", ""))
            )
            product_manager = extract_wikilink(product.get("manager_name")) or manager
            evidence = self._collect_evidence(
                note, product_name, strategies, people_links
            )
            evidence_quote = str(product.get("evidence_quote", "") or "").strip()
            if evidence_quote:
                evidence.insert(0, evidence_quote)
            fragments.append(
                ProductProfile(
                    product_name=product_name,
                    manager=product_manager,
                    entity_type=entity_type or "product",
                    entity_confidence=entity_confidence or "high",
                    strategy_links=strategies,
                    people_links=people_links,
                    source_notes=[str(note.path)],
                    evidence_items=[
                        EvidenceItem(text=item, source_path=str(note.path))
                        for item in evidence
                    ],
                )
            )
        return fragments

    def _infer_manager(self, note: MarkdownNote) -> str:
        fm = note.frontmatter
        if fm.get("manager"):
            return extract_wikilink(fm["manager"])
        if str(fm.get("entity_type", "")).strip() == "Manager" and fm.get(
            "primary_entity"
        ):
            return extract_wikilink(fm["primary_entity"])
        return ""

    def _collect_evidence(
        self,
        note: MarkdownNote,
        product_name: str,
        strategy_links: list[str],
        people_links: list[str],
    ) -> list[str]:
        evidence: list[str] = []
        for people_link in people_links:
            section = extract_heading_section(note.body, extract_wikilink(people_link))
            evidence.extend(
                extract_lines_containing(
                    section, self.PEOPLE_BACKGROUND_KEYWORDS, limit=4
                )
            )
        evidence.extend(
            extract_lines_containing(note.body, self.RISK_KEYWORDS, limit=8)
        )
        evidence.extend(
            clean_evidence_lines(
                extract_heading_section(note.body, product_name).splitlines()
            )
        )
        for strategy_link in strategy_links:
            section = extract_heading_section(
                note.body, extract_wikilink(strategy_link)
            )
            evidence.extend(clean_evidence_lines(section.splitlines(), limit=3))
        return dedupe([line for line in evidence if line])[
            : Settings.product_profile_max_evidence_items
        ]

    def build_llm_profile(self, profile: ProductProfile) -> str:
        strategies = ", ".join(
            extract_wikilink(item)
            for item in profile.strategy_links
            if extract_wikilink(item)
        )
        sentence = f"{profile.product_name}是{profile.manager + '旗下' if profile.manager else ''}产品，策略标签为{strategies or '材料未提及'}。"
        background = first_matching(
            profile.evidence_items, self.PEOPLE_BACKGROUND_KEYWORDS
        )
        risk = first_matching(profile.evidence_items, self.RISK_KEYWORDS)
        if background:
            sentence += (
                f"关键人员/团队背景证据：{strip_markdown_bullet(background.text)}。"
            )
        if risk:
            sentence += f"风险与组合约束证据：{strip_markdown_bullet(risk.text)}。"
        return truncate_text(sentence, Settings.product_profile_max_chars)

    def enrich_profile(
        self, profile: ProductProfile, *, include_external: bool = True
    ) -> None:
        """Derive stable structured fields from existing profile evidence."""
        profile.manager_aliases = generate_manager_aliases(profile.manager)
        profile.product_aliases = clean_aliases(
            profile.product_aliases
            + generate_product_aliases(profile.product_name, profile.manager)
            + (
                [profile.canonical_product_name]
                if profile.canonical_product_name
                else []
            )
        )
        if include_external:
            external = enrich_profile_with_zmdata(
                product_name=profile.product_name,
                manager=profile.manager,
                product_aliases=profile.product_aliases,
                manager_aliases=profile.manager_aliases,
                mode=Settings.zmdata_mode,
                page_size=Settings.zmdata_search_page_size,
            )
            profile.zm_match_status = external.status
            profile.zm_fund_ids = dedupe(profile.zm_fund_ids + external.fund_ids)
            profile.zm_fund_codes = dedupe(profile.zm_fund_codes + external.fund_codes)
            profile.zm_candidate_matches = dedupe(
                profile.zm_candidate_matches + external.candidate_matches
            )
            profile.zm_rejected_candidates = dedupe(
                profile.zm_rejected_candidates
                + getattr(external, "rejected_candidates", [])
            )
            if external.aliases:
                profile.product_aliases = clean_aliases(
                    profile.product_aliases + external.aliases
                )
        profile.product_line = infer_product_lines(profile)
        benchmark = benchmark_from_product(profile)
        profile.product_line = filter_product_lines_for_benchmark(
            profile.product_line, benchmark
        )
        profile.risk_points = collect_matching_evidence(
            profile.evidence_items, self.RISK_KEYWORDS, limit=5
        )
        profile.key_people_summary = join_summary(
            collect_matching_evidence(
                profile.evidence_items, self.PEOPLE_BACKGROUND_KEYWORDS, limit=3
            )
        )
        profile.evidence_summary = build_evidence_summary(profile)
        profile.source_files = dedupe(
            [Path(path).name for path in profile.source_notes if path]
        )
        tagging = classify_strategy_text(strategy_classification_text(profile))
        profile.strategy_raw_terms = dedupe(
            profile.strategy_raw_terms + tagging.strategy_raw_terms
        )
        profile.strategy_evidence = dedupe(
            profile.strategy_evidence
            + [strip_markdown_bullet(item.text) for item in profile.evidence_items[:5]]
        )[: Settings.product_profile_max_evidence_items]
        profile.primary_strategy_codes = dedupe(
            profile.primary_strategy_codes + tagging.primary_strategy_codes
        )
        profile.primary_strategy_tags = dedupe(
            profile.primary_strategy_tags + tagging.primary_strategy_tags
        )
        profile.secondary_strategy_codes = dedupe(
            profile.secondary_strategy_codes + tagging.secondary_strategy_codes
        )
        profile.secondary_strategy_tags = dedupe(
            profile.secondary_strategy_tags + tagging.secondary_strategy_tags
        )
        profile.strategy_facets = merge_facet_dicts(
            profile.strategy_facets, tagging.strategy_facets
        )
        tags_before_guardrails = dedupe(
            profile.product_line
            + profile.primary_strategy_tags
            + profile.secondary_strategy_tags
        )
        filter_strategy_tags_for_benchmark(profile, benchmark)
        apply_product_scope_strategy_guardrails(profile, benchmark)
        apply_air_index_strategy_override(profile, benchmark)
        profile.candidate_strategy_tags = dedupe(
            profile.candidate_strategy_tags + tagging.candidate_strategy_tags
        )
        refresh_strategy_scope_fields(profile, tags_before_guardrails)
        profile.strategy_tag_confidence = tagging.strategy_tag_confidence
        profile.strategy_tag_source = tagging.strategy_tag_source
        profile.strategy_tag_review_status = tagging.strategy_tag_review_status
        profile.strategy_positioning = build_strategy_positioning(profile)

    def render_profile(self, profile: ProductProfile) -> str:
        template = self.template_path.read_text(encoding="utf-8")
        source_notes = dedupe(profile.source_notes)
        evidence_section = (
            "\n".join(
                f"- {strip_markdown_bullet(item.text)}  \n  来源: `{item.source_path}`"
                for item in profile.evidence_items
            )
            or "- 材料未提及可用证据"
        )
        replacements = {
            "{{PRODUCT_NAME}}": ensure_wikilink(profile.product_name),
            "{{PRODUCT_TITLE}}": profile.product_name,
            "{{MANAGER_NAME}}": ensure_wikilink(profile.manager)
            if profile.manager
            else "",
            "{{ENTITY_TYPE}}": json.dumps(profile.entity_type, ensure_ascii=False),
            "{{ENTITY_CONFIDENCE}}": json.dumps(
                profile.entity_confidence, ensure_ascii=False
            ),
            "{{STRATEGY_LINKS}}": json.dumps(
                dedupe(profile.strategy_links), ensure_ascii=False
            ),
            "{{PEOPLE_LINKS}}": json.dumps(
                dedupe(profile.people_links), ensure_ascii=False
            ),
            "{{SOURCE_NOTES}}": json.dumps(source_notes, ensure_ascii=False),
            "{{MANAGER_ALIASES}}": json.dumps(
                profile.manager_aliases, ensure_ascii=False
            ),
            "{{PRODUCT_ALIASES}}": json.dumps(
                profile.product_aliases, ensure_ascii=False
            ),
            "{{STRATEGY_POSITIONING}}": json.dumps(
                profile.strategy_positioning, ensure_ascii=False
            ),
            "{{PRODUCT_LINE}}": json.dumps(profile.product_line, ensure_ascii=False),
            "{{RISK_POINTS}}": json.dumps(profile.risk_points, ensure_ascii=False),
            "{{KEY_PEOPLE_SUMMARY}}": json.dumps(
                profile.key_people_summary, ensure_ascii=False
            ),
            "{{EVIDENCE_SUMMARY}}": json.dumps(
                profile.evidence_summary, ensure_ascii=False
            ),
            "{{SOURCE_FILES}}": json.dumps(profile.source_files, ensure_ascii=False),
            "{{EVIDENCE_SOURCE_TYPE}}": json.dumps(
                profile.evidence_source_type, ensure_ascii=False
            ),
            "{{EXTERNAL_EVIDENCE_STATUS}}": json.dumps(
                profile.external_evidence_status, ensure_ascii=False
            ),
            "{{EVIDENCE_CONFLICT_STATUS}}": json.dumps(
                profile.evidence_conflict_status, ensure_ascii=False
            ),
            "{{SOURCE_PRIORITY}}": json.dumps(profile.source_priority, ensure_ascii=False),
            "{{EXTERNAL_EVIDENCE}}": json.dumps(
                profile.external_evidence, ensure_ascii=False
            ),
            "{{STRATEGY_RAW_TERMS}}": json.dumps(
                profile.strategy_raw_terms, ensure_ascii=False
            ),
            "{{STRATEGY_EVIDENCE}}": json.dumps(
                profile.strategy_evidence, ensure_ascii=False
            ),
            "{{PRIMARY_STRATEGY_CODES}}": json.dumps(
                profile.primary_strategy_codes, ensure_ascii=False
            ),
            "{{PRIMARY_STRATEGY_TAGS}}": json.dumps(
                profile.primary_strategy_tags, ensure_ascii=False
            ),
            "{{SECONDARY_STRATEGY_CODES}}": json.dumps(
                profile.secondary_strategy_codes, ensure_ascii=False
            ),
            "{{SECONDARY_STRATEGY_TAGS}}": json.dumps(
                profile.secondary_strategy_tags, ensure_ascii=False
            ),
            "{{DIRECT_STRATEGY_TAGS}}": json.dumps(
                profile.direct_strategy_tags, ensure_ascii=False
            ),
            "{{MENTIONED_STRATEGY_TAGS}}": json.dumps(
                profile.mentioned_strategy_tags, ensure_ascii=False
            ),
            "{{REJECTED_STRATEGY_TAGS}}": json.dumps(
                profile.rejected_strategy_tags, ensure_ascii=False
            ),
            "{{STRATEGY_FACETS}}": json.dumps(
                profile.strategy_facets, ensure_ascii=False
            ),
            "{{CANDIDATE_STRATEGY_TAGS}}": json.dumps(
                profile.candidate_strategy_tags, ensure_ascii=False
            ),
            "{{STRATEGY_TAG_CONFIDENCE}}": json.dumps(
                profile.strategy_tag_confidence, ensure_ascii=False
            ),
            "{{STRATEGY_TAG_SOURCE}}": json.dumps(
                profile.strategy_tag_source, ensure_ascii=False
            ),
            "{{STRATEGY_TAG_REVIEW_STATUS}}": json.dumps(
                profile.strategy_tag_review_status, ensure_ascii=False
            ),
            "{{CANONICAL_PRODUCT_NAME}}": json.dumps(
                profile.canonical_product_name or profile.product_name,
                ensure_ascii=False,
            ),
            "{{PROFILE_QUALITY_STATUS}}": json.dumps(
                profile.profile_quality_status, ensure_ascii=False
            ),
            "{{PRODUCT_NAME_REASON}}": json.dumps(
                profile.product_name_reason, ensure_ascii=False
            ),
            "{{REVIEW_REASONS}}": json.dumps(
                profile.review_reasons, ensure_ascii=False
            ),
            "{{ZM_MATCH_STATUS}}": json.dumps(
                profile.zm_match_status, ensure_ascii=False
            ),
            "{{ZM_FUND_IDS}}": json.dumps(profile.zm_fund_ids, ensure_ascii=False),
            "{{ZM_FUND_CODES}}": json.dumps(profile.zm_fund_codes, ensure_ascii=False),
            "{{ZM_CANDIDATE_MATCHES}}": json.dumps(
                profile.zm_candidate_matches, ensure_ascii=False
            ),
            "{{ZM_REJECTED_CANDIDATES}}": json.dumps(
                profile.zm_rejected_candidates, ensure_ascii=False
            ),
            "{{UPDATED_AT}}": datetime.now().strftime("%Y-%m-%d"),
            "{{LLM_PROFILE}}": profile.llm_profile,
            "{{EVIDENCE_SECTION}}": evidence_section,
            "{{SOURCE_NOTES_SECTION}}": "\n".join(f"- `{p}`" for p in source_notes)
            or "- 无",
        }
        rendered = template
        for key, value in replacements.items():
            rendered = rendered.replace(key, value)
        return rendered


def merge_profile(
    target: ProductProfile, incoming: ProductProfile, max_evidence_items: int
) -> None:
    if not target.manager and incoming.manager:
        target.manager = incoming.manager
    preferred_product_name = choose_preferred_product_name(
        target.product_name, incoming.product_name
    )
    if preferred_product_name != target.product_name:
        target.product_name = preferred_product_name
        if incoming.canonical_product_name:
            target.canonical_product_name = incoming.canonical_product_name
    if target.entity_type != "product" and incoming.entity_type == "product":
        target.entity_type = incoming.entity_type
        target.entity_confidence = incoming.entity_confidence
    elif target.entity_type == "product" and incoming.entity_type != "product":
        target.review_reasons = dedupe(
            target.review_reasons + incoming.review_reasons + [incoming.entity_type]
        )
    elif incoming.entity_type and not target.entity_type:
        target.entity_type = incoming.entity_type
        target.entity_confidence = incoming.entity_confidence
    else:
        target.entity_confidence = lower_confidence(
            target.entity_confidence, incoming.entity_confidence
        )
    target.strategy_links = dedupe(target.strategy_links + incoming.strategy_links)
    target.people_links = dedupe(target.people_links + incoming.people_links)
    target.source_notes = dedupe(target.source_notes + incoming.source_notes)
    target.manager_aliases = dedupe(target.manager_aliases + incoming.manager_aliases)
    target.product_aliases = dedupe(target.product_aliases + incoming.product_aliases)
    target.product_line = dedupe(target.product_line + incoming.product_line)
    target.risk_points = dedupe(target.risk_points + incoming.risk_points)
    target.evidence_summary = dedupe(
        target.evidence_summary + incoming.evidence_summary
    )
    target.source_files = dedupe(target.source_files + incoming.source_files)
    target.evidence_source_type = choose_evidence_source_type(
        target.evidence_source_type, incoming.evidence_source_type
    )
    target.external_evidence_status = choose_external_evidence_status(
        target.external_evidence_status, incoming.external_evidence_status
    )
    target.evidence_conflict_status = choose_evidence_conflict_status(
        target.evidence_conflict_status, incoming.evidence_conflict_status
    )
    target.source_priority = min(target.source_priority, incoming.source_priority)
    target.external_evidence = merge_external_evidence(
        target.external_evidence, incoming.external_evidence
    )
    target.strategy_raw_terms = dedupe(
        target.strategy_raw_terms + incoming.strategy_raw_terms
    )
    target.strategy_evidence = dedupe(
        target.strategy_evidence + incoming.strategy_evidence
    )
    target.primary_strategy_codes = dedupe(
        target.primary_strategy_codes + incoming.primary_strategy_codes
    )
    target.primary_strategy_tags = dedupe(
        target.primary_strategy_tags + incoming.primary_strategy_tags
    )
    target.secondary_strategy_codes = dedupe(
        target.secondary_strategy_codes + incoming.secondary_strategy_codes
    )
    target.secondary_strategy_tags = dedupe(
        target.secondary_strategy_tags + incoming.secondary_strategy_tags
    )
    target.direct_strategy_tags = dedupe(
        target.direct_strategy_tags + incoming.direct_strategy_tags
    )
    target.mentioned_strategy_tags = dedupe(
        target.mentioned_strategy_tags + incoming.mentioned_strategy_tags
    )
    target.rejected_strategy_tags = dedupe(
        target.rejected_strategy_tags + incoming.rejected_strategy_tags
    )
    target.strategy_facets = merge_facet_dicts(
        target.strategy_facets, incoming.strategy_facets
    )
    target.candidate_strategy_tags = dedupe(
        target.candidate_strategy_tags + incoming.candidate_strategy_tags
    )
    if not target.strategy_tag_confidence and incoming.strategy_tag_confidence:
        target.strategy_tag_confidence = incoming.strategy_tag_confidence
    if not target.strategy_tag_source and incoming.strategy_tag_source:
        target.strategy_tag_source = incoming.strategy_tag_source
    if not target.strategy_tag_review_status and incoming.strategy_tag_review_status:
        target.strategy_tag_review_status = incoming.strategy_tag_review_status
    target.zm_fund_ids = dedupe(target.zm_fund_ids + incoming.zm_fund_ids)
    target.zm_fund_codes = dedupe(target.zm_fund_codes + incoming.zm_fund_codes)
    target.zm_candidate_matches = dedupe(
        target.zm_candidate_matches + incoming.zm_candidate_matches
    )
    target.zm_rejected_candidates = dedupe(
        target.zm_rejected_candidates + incoming.zm_rejected_candidates
    )
    if not target.canonical_product_name and incoming.canonical_product_name:
        target.canonical_product_name = incoming.canonical_product_name
    if target.zm_match_status in {
        "off",
        "not_found",
        "unavailable",
        "error",
    } and incoming.zm_match_status not in {"off", ""}:
        target.zm_match_status = incoming.zm_match_status
    if (
        target.profile_quality_status == "confirmed"
        and incoming.profile_quality_status != "confirmed"
    ):
        target.product_name_reason = dedupe(
            [target.product_name_reason, incoming.product_name_reason]
        )[0]
    target.review_reasons = dedupe(target.review_reasons + incoming.review_reasons)
    seen = {(item.text, item.source_path) for item in target.evidence_items}
    for item in incoming.evidence_items:
        if (item.text, item.source_path) not in seen:
            target.evidence_items.append(item)
            seen.add((item.text, item.source_path))
        if len(target.evidence_items) >= max_evidence_items:
            break


def apply_canonical_manager_names(profiles: list[ProductProfile]) -> None:
    """Normalize manager display names across profiles from the same manager."""

    by_identity: dict[str, list[ProductProfile]] = {}
    for profile in profiles:
        key = manager_identity_key(profile.manager)
        if not key:
            continue
        by_identity.setdefault(key, []).append(profile)
    for group in by_identity.values():
        canonical = choose_canonical_manager_name(
            [profile.manager for profile in group if profile.manager]
        )
        if not canonical:
            continue
        aliases = dedupe(
            [canonical]
            + [profile.manager for profile in group if profile.manager]
            + [
                alias
                for profile in group
                for alias in profile.manager_aliases
                if alias
            ]
        )
        for profile in group:
            profile.manager = canonical
            profile.manager_aliases = dedupe(profile.manager_aliases + aliases)


def choose_canonical_manager_name(names: list[str]) -> str:
    candidates = dedupe([name for name in names if name])
    if not candidates:
        return ""
    return max(candidates, key=manager_name_preference_key)


def manager_name_preference_key(name: str) -> tuple[int, int, str]:
    normalized = re.sub(r"\s+", "", name)
    legal_score = 0
    for suffix in COMPANY_SUFFIXES:
        if suffix in normalized:
            legal_score = max(legal_score, len(suffix))
    return (legal_score, len(normalized), normalized)


def apply_product_name_analysis(
    profile: ProductProfile, analysis: ProductNameAnalysis
) -> None:
    profile.canonical_product_name = analysis.canonical_name
    profile.profile_quality_status = analysis.quality_status
    profile.product_name_reason = analysis.reason
    if profile.entity_type in {"", "product"} or analysis.entity_type != "product":
        profile.entity_type = analysis.entity_type
    profile.entity_confidence = lower_confidence(
        profile.entity_confidence, analysis.entity_confidence
    )
    profile.review_reasons = dedupe(
        profile.review_reasons + analysis.review_reasons
    )
    profile.product_aliases = dedupe(profile.product_aliases + analysis.aliases)


def merge_profiles_by_external_identity(
    profiles: list[ProductProfile], max_evidence_items: int
) -> list[ProductProfile]:
    if not profiles:
        return []
    merged: list[ProductProfile] = []
    matched_by_key: dict[str, ProductProfile] = {}
    for profile in profiles:
        identity_keys = external_identity_keys(profile)
        target = next(
            (matched_by_key[key] for key in identity_keys if key in matched_by_key),
            None,
        )
        if target is None:
            merged.append(profile)
            target = profile
        else:
            merge_profile(target, profile, max_evidence_items=max_evidence_items)
        for key in identity_keys:
            matched_by_key[key] = target
    unique_profiles = []
    seen_ids = set()
    for profile in merged:
        identifier = id(profile)
        if identifier in seen_ids:
            continue
        unique_profiles.append(profile)
        seen_ids.add(identifier)
    return sorted(unique_profiles, key=lambda item: item.product_name)


def external_identity_keys(profile: ProductProfile) -> list[str]:
    if profile.zm_match_status != "matched":
        return []
    keys = [f"fund_id:{value}" for value in profile.zm_fund_ids if value]
    if keys:
        return keys
    return [f"fund_code:{value}" for value in profile.zm_fund_codes if value]


def choose_preferred_product_name(current: str, incoming: str) -> str:
    if not current:
        return incoming
    if not incoming:
        return current
    current_quality = product_display_name_quality(current)
    incoming_quality = product_display_name_quality(incoming)
    if incoming_quality > current_quality:
        return incoming
    if incoming_quality < current_quality:
        return current
    current_norm = normalize_for_match(current)
    incoming_norm = normalize_for_match(incoming)
    if len(incoming_norm) > len(current_norm):
        return incoming
    if len(incoming_norm) == len(current_norm) and incoming < current:
        return incoming
    return current


def product_display_name_quality(name: str) -> tuple[int, int]:
    normalized = normalize_for_match(name)
    has_specific = int(bool(re.search(r"(\d+\s*号|[一二三四五六七八九十]+\s*号|\d+\s*期)", name)))
    has_fund_suffix = int(any(suffix in name for suffix in PRODUCT_SUFFIXES))
    has_generic_tail = int(name.endswith(("产品", "产品线", "系列产品", "产品系列")))
    return (has_specific + has_fund_suffix - has_generic_tail, len(normalized))


def profiles_share_manager(left: ProductProfile, right: ProductProfile) -> bool:
    if not left.manager or not right.manager:
        return False
    return manager_identity_key(left.manager) == manager_identity_key(right.manager)


def profile_matches_family(profile: ProductProfile, family: str) -> bool:
    if not family:
        return False
    fields = [
        profile.product_name,
        profile.canonical_product_name,
        " ".join(extract_wikilink(item) for item in profile.strategy_links),
        " ".join(profile.product_aliases),
    ]
    analysis = analyze_product_name("\n".join(fields), profile.manager)
    return analysis.family == family


def remove_existing_manager_profiles(output_root: Path, managers: set[str]) -> int:
    if not managers or not output_root.exists():
        return 0
    normalized_managers = {
        manager_identity_key(manager)
        for manager in managers
        if manager_identity_key(manager)
    }
    removed = 0
    for path in output_root.rglob("*.md"):
        try:
            note = read_markdown_note(path)
        except OSError:
            continue
        manager = extract_wikilink(note.frontmatter.get("manager", ""))
        if manager_identity_key(manager) not in normalized_managers:
            continue
        try:
            path.unlink()
            removed += 1
        except OSError:
            continue
    return removed


def remove_existing_source_note_profiles(
    output_root: Path, source_roots: Iterable[Path]
) -> int:
    """Remove stale generated profiles tied to source notes being rebuilt."""

    if not output_root.exists():
        return 0
    normalized_roots = [
        normalize_path_for_scope(root)
        for root in source_roots
        if str(root).strip()
    ]
    normalized_roots = [root for root in normalized_roots if root]
    if not normalized_roots:
        return 0
    removed = 0
    for path in output_root.rglob("*.md"):
        try:
            note = read_markdown_note(path)
        except OSError:
            continue
        source_notes = note.frontmatter.get("source_notes", [])
        if not isinstance(source_notes, list):
            source_notes = [source_notes]
        if not any(
            path_is_under_any_source_root(str(source_note), normalized_roots)
            for source_note in source_notes
            if source_note
        ):
            continue
        try:
            path.unlink()
            removed += 1
        except OSError:
            continue
    return removed


def output_path_for_profile(
    profile: ProductProfile, output_root: Path, used_paths: set[Path]
) -> Path:
    base_name = safe_filename(profile.product_name)
    base_path = output_root / f"{base_name}.md"
    if output_path_available_for_profile(base_path, profile, used_paths):
        return base_path

    manager_label = safe_filename(manager_filename_label(profile.manager))
    if manager_label:
        candidate = output_root / f"{manager_label}__{base_name}.md"
        if output_path_available_for_profile(candidate, profile, used_paths):
            return candidate

    suffix = manager_identity_key(profile.manager) or "unknown_manager"
    counter = 2
    while True:
        candidate = output_root / f"{safe_filename(suffix)}__{base_name}_{counter}.md"
        if output_path_available_for_profile(candidate, profile, used_paths):
            return candidate
        counter += 1


def output_path_available_for_profile(
    path: Path, profile: ProductProfile, used_paths: set[Path]
) -> bool:
    if path in used_paths:
        return False
    if not path.exists():
        return True
    try:
        note = read_markdown_note(path)
    except OSError:
        return False
    existing_manager = extract_wikilink(note.frontmatter.get("manager", ""))
    if not existing_manager:
        return True
    return manager_identity_key(existing_manager) == manager_identity_key(profile.manager)


def manager_filename_label(manager: str) -> str:
    if not manager:
        return ""
    return (
        strip_company_suffix(strip_city_prefix(manager))
        or strip_company_suffix(manager)
        or manager_identity_key(manager)
        or manager
    )


def normalize_path_for_scope(value: object) -> str:
    text = str(value or "").strip().strip("'\"")
    text = text.replace("\\", "/")
    text = re.sub(r"/+", "/", text)
    return text.casefold().rstrip("/")


def path_is_under_any_source_root(path: str, normalized_roots: list[str]) -> bool:
    normalized = normalize_path_for_scope(path)
    if not normalized:
        return False
    return any(
        normalized == root or normalized.startswith(f"{root}/")
        for root in normalized_roots
    )


def report_path_for_output_root(output_root: Path) -> Path:
    if output_root == Settings.product_profiles_dir:
        return Settings.reports_dir / "profile_quality.json"
    return output_root.parent / "reports" / "profile_quality.json"


def docs_root_for_output_root(output_root: Path) -> Path:
    if output_root == Settings.product_profiles_dir:
        return Settings.docs_root
    return output_root.parent


def build_strategy_positioning(profile: ProductProfile) -> str:
    strategies = [
        extract_wikilink(item)
        for item in profile.strategy_links
        if extract_wikilink(item)
    ]
    product_lines = profile.product_line or infer_product_lines(profile)
    evidence = profile.evidence_summary or build_evidence_summary(profile)
    parts = []
    if profile.primary_strategy_tags:
        parts.append("一级策略：" + "、".join(profile.primary_strategy_tags))
    if profile.secondary_strategy_tags:
        parts.append("二级策略：" + "、".join(profile.secondary_strategy_tags[:6]))
    if product_lines:
        parts.append("产品线：" + "、".join(product_lines))
    if strategies:
        parts.append("策略标签：" + "、".join(strategies[:8]))
    if evidence:
        parts.append("代表证据：" + strip_markdown_bullet(evidence[0]))
    return "；".join(parts) or "材料未提及明确策略定位"


def strategy_classification_text(profile: ProductProfile) -> str:
    scoped_evidence = product_scoped_evidence(profile)
    return "\n".join(
        [
            profile.product_name,
            profile.canonical_product_name,
            profile.manager,
            " ".join(profile.product_aliases),
            " ".join(extract_wikilink(item) for item in profile.strategy_links),
            " ".join(profile.product_line),
            " ".join(scoped_evidence),
        ]
    )


def product_scoped_evidence(profile: ProductProfile, limit: int = 6) -> list[str]:
    aliases = [
        profile.product_name,
        profile.canonical_product_name,
        *profile.product_aliases[:6],
    ]
    alias_keys = {
        normalize_for_match(alias)
        for alias in aliases
        if len(normalize_for_match(alias)) >= 3
    }
    lines: list[str] = []
    for item in profile.evidence_items:
        text = strip_markdown_bullet(item.text)
        normalized = normalize_for_match(text)
        if alias_keys and any(alias in normalized for alias in alias_keys):
            lines.append(text)
        if len(lines) >= limit:
            break
    return dedupe(lines)


def benchmark_from_product(profile: ProductProfile) -> str:
    text = normalize_for_match(
        "\n".join(
            [
                profile.product_name,
                profile.canonical_product_name,
                " ".join(profile.product_aliases),
            ]
        )
    )
    if "2000" in text or "中证2000" in text:
        return "2000"
    if "1000" in text or "中证1000" in text or "千指" in text:
        return "1000"
    if "a500" in text or "中证a500" in text:
        return "A500"
    if "500" in text or "中证500" in text:
        return "500"
    if "300" in text or "沪深300" in text:
        return "300"
    return ""


def filter_product_lines_for_benchmark(lines: list[str], benchmark: str) -> list[str]:
    benchmark_labels = set().union(*BENCHMARK_LINE_LABELS.values())
    if not benchmark:
        return dedupe(
            line for line in lines if line not in benchmark_labels
        )
    allowed = BENCHMARK_LINE_LABELS[benchmark] | {"指数增强"}
    return dedupe(
        line for line in lines if line not in benchmark_labels or line in allowed
    )


def filter_strategy_tags_for_benchmark(
    profile: ProductProfile, benchmark: str
) -> None:
    all_index_codes = set().union(*BENCHMARK_SECONDARY_CODES.values())
    all_index_tags = set().union(*BENCHMARK_SECONDARY_TAGS.values())
    if not benchmark:
        profile.secondary_strategy_codes = [
            code for code in profile.secondary_strategy_codes if code not in all_index_codes
        ]
        profile.secondary_strategy_tags = [
            tag for tag in profile.secondary_strategy_tags if tag not in all_index_tags
        ]
        facets = dict(profile.strategy_facets)
        benchmark_values = {"沪深300", "中证500", "中证A500", "中证1000", "中证2000"}
        if "benchmark" in facets:
            facets["benchmark"] = [
                value for value in facets["benchmark"] if value not in benchmark_values
            ]
            if not facets["benchmark"]:
                facets.pop("benchmark")
        profile.strategy_facets = facets
        return
    allowed_codes = BENCHMARK_SECONDARY_CODES[benchmark]
    allowed_tags = BENCHMARK_SECONDARY_TAGS[benchmark]
    profile.secondary_strategy_codes = [
        code
        for code in profile.secondary_strategy_codes
        if code not in all_index_codes or code in allowed_codes
    ]
    profile.secondary_strategy_tags = [
        tag
        for tag in profile.secondary_strategy_tags
        if tag not in all_index_tags or tag in allowed_tags
    ]


def apply_product_scope_strategy_guardrails(
    profile: ProductProfile, benchmark: str
) -> None:
    """Keep product-level strategy labels anchored to the product itself."""

    if benchmark:
        benchmark_value = BENCHMARK_FACET_VALUES.get(benchmark)
        if benchmark_value:
            facets = dict(profile.strategy_facets)
            facets["benchmark"] = [benchmark_value]
            profile.strategy_facets = facets
        if not product_name_has_cta_signal(profile.product_name):
            cta_product_lines = {
                line for line, _aliases in PRODUCT_LINE_RULES if "CTA" in line
            }
            profile.product_line = [
                line for line in profile.product_line if line not in cta_product_lines
            ]
            profile.primary_strategy_codes = [
                code
                for code in profile.primary_strategy_codes
                if code not in {"CTA", "VOL"}
            ]
            profile.primary_strategy_tags = [
                tag
                for tag in profile.primary_strategy_tags
                if tag not in {"管理期货", "期权波动率"}
            ]
            profile.secondary_strategy_codes = [
                code
                for code in profile.secondary_strategy_codes
                if not code.startswith(("CTA_", "VOL_"))
            ]
            profile.secondary_strategy_tags = [
                tag for tag in profile.secondary_strategy_tags if "CTA" not in tag
            ]
        if "EQ_INDEX_ENH" not in profile.primary_strategy_codes:
            profile.primary_strategy_codes = dedupe(
                ["EQ_INDEX_ENH"] + profile.primary_strategy_codes
            )
        if "指数增强" not in profile.primary_strategy_tags:
            profile.primary_strategy_tags = dedupe(
                ["指数增强"] + profile.primary_strategy_tags
            )
        return

    index_primary_codes = {"EQ_INDEX_ENH"}
    index_primary_tags = {"指数增强"}
    profile.primary_strategy_codes = [
        code for code in profile.primary_strategy_codes if code not in index_primary_codes
    ]
    profile.primary_strategy_tags = [
        tag for tag in profile.primary_strategy_tags if tag not in index_primary_tags
    ]
    if not profile.primary_strategy_codes and "管理期货" in profile.primary_strategy_tags:
        profile.primary_strategy_codes = ["CTA"]
    if not profile.primary_strategy_tags and any(
        normalize_for_match(term) in normalize_for_match(profile.product_name)
        for term in ["CTA", "管理期货"]
    ):
        profile.primary_strategy_codes = ["CTA"]
        profile.primary_strategy_tags = ["管理期货"]


def apply_air_index_strategy_override(profile: ProductProfile, benchmark: str) -> None:
    """Map '空气指增' style labels to quant-long unless a benchmarked index enhancement is explicit."""
    if benchmark or not profile_has_air_index_signal(profile):
        return
    profile.primary_strategy_codes = dedupe(
        ["EQ_LONG"]
        + [code for code in profile.primary_strategy_codes if code != "EQ_INDEX_ENH"]
    )
    profile.primary_strategy_tags = dedupe(
        ["股票多头"]
        + [tag for tag in profile.primary_strategy_tags if tag != "指数增强"]
    )
    profile.product_line = [line for line in profile.product_line if line != "指数增强"]


def profile_has_air_index_signal(profile: ProductProfile) -> bool:
    text = "\n".join(
        [
            profile.product_name,
            profile.canonical_product_name,
            " ".join(profile.product_aliases),
            " ".join(extract_wikilink(item) for item in profile.strategy_links),
            " ".join(profile.strategy_raw_terms),
            " ".join(profile.strategy_evidence),
            profile.llm_profile,
        ]
    )
    normalized = normalize_for_match(text)
    return any(
        normalize_for_match(term) in normalized for term in ("空气指增", "量化多头")
    )


def product_name_has_cta_signal(product_name: str) -> bool:
    normalized = normalize_for_match(product_name)
    return "cta" in normalized or "管理期货" in product_name


def refresh_strategy_scope_fields(
    profile: ProductProfile, tags_before_guardrails: list[str]
) -> None:
    direct = dedupe(
        profile.primary_strategy_tags
        + profile.secondary_strategy_tags
        + profile.product_line
    )
    mentioned = dedupe(
        [
            extract_wikilink(item)
            for item in profile.strategy_links
            if extract_wikilink(item)
        ]
        + profile.candidate_strategy_tags
    )
    profile.direct_strategy_tags = direct
    profile.mentioned_strategy_tags = [
        item for item in mentioned if normalize_for_match(item) not in {
            normalize_for_match(tag) for tag in direct
        }
    ]
    profile.rejected_strategy_tags = dedupe(
        profile.rejected_strategy_tags
        + [
            item
            for item in tags_before_guardrails
            if normalize_for_match(item)
            not in {normalize_for_match(tag) for tag in direct}
        ]
    )


def filter_strategy_links_for_product(
    product_name: str, strategies: list[str]
) -> list[str]:
    benchmark = benchmark_from_text(product_name)
    if not benchmark:
        return strategies
    all_benchmark_labels = set().union(*BENCHMARK_SECONDARY_TAGS.values())
    allowed = BENCHMARK_SECONDARY_TAGS[benchmark] | BENCHMARK_LINE_LABELS[benchmark]
    filtered = []
    for strategy in strategies:
        text = extract_wikilink(strategy)
        if text in all_benchmark_labels and text not in allowed:
            continue
        if text in set().union(*BENCHMARK_LINE_LABELS.values()) and text not in allowed:
            continue
        filtered.append(strategy)
    return dedupe(filtered)


def benchmark_from_text(value: str) -> str:
    text = normalize_for_match(value)
    if "2000" in text:
        return "2000"
    if "1000" in text or "千指" in text:
        return "1000"
    if "a500" in text:
        return "A500"
    if "500" in text:
        return "500"
    if "300" in text:
        return "300"
    return ""


def merge_facet_dicts(
    left: dict[str, list[str]], right: dict[str, list[str]]
) -> dict[str, list[str]]:
    merged = {key: list(values) for key, values in left.items()}
    for key, values in right.items():
        merged[key] = dedupe(merged.get(key, []) + list(values))
    return merged


def build_evidence_summary(profile: ProductProfile) -> list[str]:
    strategy_names = [
        extract_wikilink(item)
        for item in profile.strategy_links
        if extract_wikilink(item)
    ]
    keywords = dedupe(
        strategy_names
        + [label for label, _ in PRODUCT_LINE_RULES]
        + ["策略", "收益", "回撤", "风险", "行业", "WorldQuant"]
    )
    preferred = collect_matching_evidence(profile.evidence_items, keywords, limit=5)
    fallback = [strip_markdown_bullet(item.text) for item in profile.evidence_items[:5]]
    return dedupe([line for line in preferred + fallback if line])[:5]


def infer_product_lines(profile: ProductProfile) -> list[str]:
    haystack = "\n".join(
        [
            profile.product_name,
            profile.manager,
            " ".join(extract_wikilink(item) for item in profile.strategy_links),
            " ".join(item.text for item in profile.evidence_items),
            profile.llm_profile,
        ]
    ).lower()
    lines = []
    for label, aliases in PRODUCT_LINE_RULES:
        if any(product_line_alias_matches(alias, haystack) for alias in aliases):
            lines.append(label)
    return filter_product_lines_for_benchmark(dedupe(lines), benchmark_from_product(profile))


def product_line_alias_matches(alias: str, haystack: str) -> bool:
    normalized_haystack = normalize_for_match(haystack)
    normalized_alias = normalize_for_match(alias)
    if not normalized_haystack or not normalized_alias:
        return False
    if normalized_alias == normalize_for_match("指增"):
        trimmed = normalized_haystack.replace(normalize_for_match("空气指增"), "")
        return normalized_alias in trimmed
    return normalized_alias in normalized_haystack


def collect_matching_evidence(
    items: Iterable[EvidenceItem], keywords: list[str], limit: int
) -> list[str]:
    out = []
    for item in items:
        text = strip_markdown_bullet(item.text)
        if not text:
            continue
        lower = text.lower()
        if any(keyword.lower() in lower for keyword in keywords):
            out.append(text)
            if len(out) >= limit:
                break
    return dedupe(out)


def join_summary(lines: list[str], max_chars: int = 260) -> str:
    return truncate_text("；".join(lines), max_chars) if lines else ""


def normalize_entity_type(value: str) -> str:
    normalized = normalize_for_match(value)
    mapping = {
        "product": "product",
        "fund": "product",
        "realproduct": "product",
        "series": "product_series",
        "productseries": "product_series",
        "strategyline": "strategy_line",
        "strategy": "strategy_line",
        "generic": "generic_bucket",
        "genericbucket": "generic_bucket",
        "unknown": "unknown",
    }
    return mapping.get(normalized, "")


def normalize_entity_confidence(value: str) -> str:
    normalized = normalize_for_match(value)
    if normalized in {"high", "medium", "low"}:
        return normalized
    if normalized in {"confirmed", "strong"}:
        return "high"
    if normalized in {"review", "needsreview", "uncertain"}:
        return "medium"
    return ""


def lower_confidence(left: str, right: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    left_norm = normalize_entity_confidence(left) or "high"
    right_norm = normalize_entity_confidence(right) or "high"
    return left_norm if order[left_norm] <= order[right_norm] else right_norm


EVIDENCE_SOURCE_PRIORITY = {
    "internal_due_diligence": 10,
    "regulatory_public": 20,
    "official_public": 30,
    "manager_website": 40,
    "third_party_public": 70,
    "search_discovery_only": 90,
}

EXTERNAL_EVIDENCE_STATUS_RANK = {
    "conflict": 0,
    "external_only": 1,
    "supported": 2,
    "not_found": 3,
    "not_checked": 4,
}

EVIDENCE_CONFLICT_STATUS_RANK = {
    "conflict": 0,
    "partial_conflict": 1,
    "none": 2,
    "unknown": 3,
}


def choose_evidence_source_type(left: str, right: str) -> str:
    left_norm = normalize_evidence_source_type(left)
    right_norm = normalize_evidence_source_type(right)
    left_rank = EVIDENCE_SOURCE_PRIORITY.get(left_norm, 100)
    right_rank = EVIDENCE_SOURCE_PRIORITY.get(right_norm, 100)
    return left_norm if left_rank <= right_rank else right_norm


def choose_external_evidence_status(left: str, right: str) -> str:
    left_norm = normalize_external_evidence_status(left)
    right_norm = normalize_external_evidence_status(right)
    left_rank = EXTERNAL_EVIDENCE_STATUS_RANK.get(left_norm, 99)
    right_rank = EXTERNAL_EVIDENCE_STATUS_RANK.get(right_norm, 99)
    return left_norm if left_rank <= right_rank else right_norm


def choose_evidence_conflict_status(left: str, right: str) -> str:
    left_norm = normalize_evidence_conflict_status(left)
    right_norm = normalize_evidence_conflict_status(right)
    left_rank = EVIDENCE_CONFLICT_STATUS_RANK.get(left_norm, 99)
    right_rank = EVIDENCE_CONFLICT_STATUS_RANK.get(right_norm, 99)
    return left_norm if left_rank <= right_rank else right_norm


def normalize_evidence_source_type(value: str) -> str:
    normalized = normalize_for_match(value)
    mapping = {
        "internalduediligence": "internal_due_diligence",
        "internal": "internal_due_diligence",
        "regulatorypublic": "regulatory_public",
        "regulatory": "regulatory_public",
        "officialpublic": "official_public",
        "official": "official_public",
        "managerwebsite": "manager_website",
        "website": "manager_website",
        "thirdpartypublic": "third_party_public",
        "thirdparty": "third_party_public",
        "searchdiscoveryonly": "search_discovery_only",
        "searchonly": "search_discovery_only",
    }
    return mapping.get(normalized, "internal_due_diligence")


def normalize_external_evidence_status(value: str) -> str:
    normalized = normalize_for_match(value)
    mapping = {
        "notchecked": "not_checked",
        "unchecked": "not_checked",
        "supported": "supported",
        "verified": "supported",
        "externalonly": "external_only",
        "searchonly": "external_only",
        "notfound": "not_found",
        "missing": "not_found",
        "conflict": "conflict",
        "conflicted": "conflict",
    }
    return mapping.get(normalized, "not_checked")


def normalize_evidence_conflict_status(value: str) -> str:
    normalized = normalize_for_match(value)
    mapping = {
        "none": "none",
        "noconflict": "none",
        "unknown": "unknown",
        "partialconflict": "partial_conflict",
        "conflict": "conflict",
        "conflicted": "conflict",
    }
    return mapping.get(normalized, "none")


def merge_external_evidence(left: list[dict], right: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    for item in [*(left or []), *(right or [])]:
        if not isinstance(item, dict):
            continue
        normalized = {str(key): item[key] for key in item if str(key).strip()}
        key = "|".join(
            str(normalized.get(field, "") or "").strip()
            for field in ("url", "title", "claim", "publisher")
        )
        if not key or key in seen:
            continue
        merged.append(normalized)
        seen.add(key)
    return merged


def generate_manager_aliases(manager: str) -> list[str]:
    return shared_generate_manager_aliases(manager)


def manager_identity_key(manager: str) -> str:
    return shared_manager_identity_key(manager)


def generate_product_aliases(product_name: str, manager: str = "") -> list[str]:
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
    for manager_alias in generate_manager_aliases(manager):
        manager_norm = normalize_for_match(manager_alias)
        product_norm = normalize_for_match(normalized)
        if manager_norm and product_norm.startswith(manager_norm):
            remainder = product_norm[len(manager_norm) :]
            if remainder:
                aliases.add(remainder)
    return clean_aliases(aliases)


def strip_company_suffix(value: str) -> str:
    result = value.strip()
    changed = True
    while changed:
        changed = False
        for suffix in COMPANY_SUFFIXES:
            if result.endswith(suffix):
                result = result[: -len(suffix)].strip()
                changed = True
    return result


def strip_city_prefix(value: str) -> str:
    result = value.strip()
    changed = True
    while changed:
        changed = False
        for prefix in sorted(CITY_PREFIXES, key=len, reverse=True):
            if result.startswith(prefix):
                result = result[len(prefix) :].strip()
                changed = True
    return result


def strip_product_suffix(value: str) -> str:
    result = value.strip()
    for suffix in PRODUCT_SUFFIXES:
        if result.endswith(suffix):
            result = result[: -len(suffix)].strip()
    return result


def strip_keyword(value: str, keyword: str) -> str:
    return value.replace(keyword, "").strip()


def normalize_for_match(value: str) -> str:
    return re.sub(r"[\W_]+", "", value or "").lower()


def clean_aliases(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        normalized = normalize_for_match(text)
        if len(normalized) < 2:
            continue
        if normalized not in seen:
            result.append(text)
            seen.add(normalized)
    return sorted(result, key=lambda item: (-len(normalize_for_match(item)), item))


def clean_evidence_lines(lines: Iterable[str], limit: int = 6) -> list[str]:
    out = []
    for raw in lines:
        line = raw.strip()
        if (
            not line
            or line.startswith("###")
            or line.startswith("```")
            or line.startswith("---")
            or line.startswith("<!--")
        ):
            continue
        if is_non_evidence_line(line):
            continue
        out.append(line)
        if len(out) >= limit:
            break
    return out


def safe_filename(name: str) -> str:
    return INVALID_FILENAME_CHARS.sub("_", name).strip(" .") or "未命名产品"


def strip_markdown_bullet(text: str) -> str:
    text = re.sub(r"^\s*[-*]\s*", "", text.strip())
    text = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def is_non_evidence_line(line: str) -> bool:
    normalized = strip_markdown_bullet(line)
    return "(未提及)" in normalized or bool(
        re.fullmatch(r"[\u4e00-\u9fa5A-Za-z /]+[:：]", normalized)
    )


def dedupe(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def first_matching(
    items: Iterable[EvidenceItem], keywords: list[str]
) -> EvidenceItem | None:
    item_list = list(items)
    for keyword in keywords:
        lower_keyword = keyword.lower()
        for item in item_list:
            if lower_keyword in item.text.lower():
                return item
    return None


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip("，。；;,. ") + "…"
