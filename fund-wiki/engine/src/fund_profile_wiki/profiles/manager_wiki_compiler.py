"""Write manager-level wiki docs from compiled product profiles."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Protocol

from fund_profile_wiki.profiles.product_name_normalizer import manager_identity_key


class ProductProfileLike(Protocol):
    product_name: str
    manager: str
    strategy_positioning: str
    product_line: list[str]
    primary_strategy_tags: list[str]
    secondary_strategy_tags: list[str]
    risk_points: list[str]
    key_people_summary: str
    evidence_summary: list[str]
    source_files: list[str]
    profile_quality_status: str


def write_manager_wiki_docs(
    profiles: Iterable[ProductProfileLike], docs_root: Path
) -> list[Path]:
    rows = [profile for profile in profiles if profile.manager]
    by_manager: dict[str, list[ProductProfileLike]] = defaultdict(list)
    display_names: dict[str, str] = {}
    for profile in rows:
        identity = manager_identity_key(profile.manager)
        if not identity:
            continue
        by_manager[identity].append(profile)
        display_names[identity] = choose_preferred_manager_name(
            display_names.get(identity, ""),
            profile.manager,
        )
    remove_existing_manager_docs(docs_root, set(by_manager))
    written: list[Path] = []
    for identity, items in by_manager.items():
        written.extend(
            write_docs_for_manager(
                display_names.get(identity, items[0].manager), items, docs_root
            )
        )
    return written


def write_docs_for_manager(
    manager: str, profiles: list[ProductProfileLike], docs_root: Path
) -> list[Path]:
    paths = [
        docs_root / "manager_profiles" / f"{safe_filename(manager)}.md",
        docs_root / "product_maps" / f"{safe_filename(manager)}.md",
        docs_root / "risk_flags" / f"{safe_filename(manager)}.md",
        docs_root / "timelines" / f"{safe_filename(manager)}.md",
    ]
    contents = [
        render_manager_profile(manager, profiles),
        render_product_map(manager, profiles),
        render_risk_flags(manager, profiles),
        render_timeline(manager, profiles),
    ]
    written = []
    for path, content in zip(paths, contents, strict=True):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def remove_existing_manager_docs(docs_root: Path, manager_keys: set[str]) -> int:
    if not manager_keys:
        return 0
    removed = 0
    for folder_name in ("manager_profiles", "product_maps", "risk_flags", "timelines"):
        folder = docs_root / folder_name
        if not folder.exists():
            continue
        for path in folder.glob("*.md"):
            if manager_identity_key(path.stem) not in manager_keys:
                continue
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
    return removed


def render_manager_profile(manager: str, profiles: list[ProductProfileLike]) -> str:
    product_lines = dedupe(
        line for profile in profiles for line in profile.product_line if line
    )
    primary_tags = dedupe(
        tag
        for profile in profiles
        for tag in list_attr(profile, "primary_strategy_tags")
        if tag
    )
    secondary_tags = dedupe(
        tag
        for profile in profiles
        for tag in list_attr(profile, "secondary_strategy_tags")
        if tag
    )
    people = dedupe(
        profile.key_people_summary for profile in profiles if profile.key_people_summary
    )
    products = sorted(profile.product_name for profile in profiles)
    return "\n".join(
        [
            "---",
            "profile_type: ManagerProfile",
            f'manager: "[[{manager}]]"',
            f'updated_at: "{today()}"',
            "tags: [Profile/Manager]",
            "---",
            "",
            f"# {manager}",
            "",
            "## Primary Strategy Tags",
            bullet_lines(primary_tags) or "- 材料未提及",
            "",
            "## Secondary Strategy Tags",
            bullet_lines(secondary_tags) or "- 材料未提及",
            "",
            "## Strategy Lines",
            bullet_lines(product_lines) or "- 材料未提及",
            "",
            "## Products",
            bullet_lines(products) or "- 材料未提及",
            "",
            "## Key People Summary",
            bullet_lines(people) or "- 材料未提及",
            "",
        ]
    )


def render_product_map(manager: str, profiles: list[ProductProfileLike]) -> str:
    lines = [
        "---",
        "profile_type: ProductMap",
        f'manager: "[[{manager}]]"',
        f'updated_at: "{today()}"',
        "tags: [Profile/ProductMap]",
        "---",
        "",
        f"# {manager} Product Map",
        "",
        "| Product | Primary tags | Product line | Quality | Evidence |",
        "|---|---|---|---|---|",
    ]
    for profile in sorted(profiles, key=lambda item: item.product_name):
        evidence = first_non_empty(profile.evidence_summary)
        lines.append(
            "| "
            + " | ".join(
                [
                    escape_cell(profile.product_name),
                    escape_cell(
                        "、".join(list_attr(profile, "primary_strategy_tags"))
                        or "材料未提及"
                    ),
                    escape_cell("、".join(profile.product_line) or "材料未提及"),
                    escape_cell(profile.profile_quality_status or "unknown"),
                    escape_cell(evidence or "材料未提及"),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_risk_flags(manager: str, profiles: list[ProductProfileLike]) -> str:
    lines = [
        "---",
        "profile_type: RiskFlags",
        f'manager: "[[{manager}]]"',
        f'updated_at: "{today()}"',
        "tags: [Profile/RiskFlags]",
        "---",
        "",
        f"# {manager} Risk Flags",
        "",
    ]
    for profile in sorted(profiles, key=lambda item: item.product_name):
        if not profile.risk_points:
            continue
        lines.extend(
            [f"## {profile.product_name}", bullet_lines(profile.risk_points), ""]
        )
    if len(lines) <= 10:
        lines.append("- 材料未提及")
    return "\n".join(lines) + "\n"


def render_timeline(manager: str, profiles: list[ProductProfileLike]) -> str:
    source_files = dedupe(
        source for profile in profiles for source in profile.source_files if source
    )
    lines = [
        "---",
        "profile_type: SourceTimeline",
        f'manager: "[[{manager}]]"',
        f'updated_at: "{today()}"',
        "tags: [Profile/Timeline]",
        "---",
        "",
        f"# {manager} Source Timeline",
        "",
        bullet_lines(sorted(source_files)) or "- 材料未提及",
        "",
    ]
    return "\n".join(lines)


def bullet_lines(values: Iterable[str]) -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    return "\n".join(f"- {item}" for item in items)


def first_non_empty(values: Iterable[str]) -> str:
    return next((str(value).strip() for value in values if str(value).strip()), "")


def list_attr(profile: ProductProfileLike, name: str) -> list[str]:
    value = getattr(profile, name, [])
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    return [str(value).strip()] if str(value).strip() else []


def dedupe(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def choose_preferred_manager_name(current: str, incoming: str) -> str:
    if not current:
        return incoming
    if not incoming:
        return current
    if manager_name_score(incoming) > manager_name_score(current):
        return incoming
    return current


def manager_name_score(value: str) -> tuple[int, int, str]:
    text = str(value).strip()
    suffix_keywords = (
        "私募基金管理有限责任公司",
        "基金管理有限责任公司",
        "资产管理有限责任公司",
        "投资管理有限责任公司",
        "资本管理有限责任公司",
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
        "基金管理有限公司",
        "有限责任公司",
        "有限公司",
    )
    has_company_suffix = int(any(text.endswith(keyword) for keyword in suffix_keywords))
    return (has_company_suffix, len(text), text)


def escape_cell(value: str) -> str:
    return str(value).replace("|", "｜").replace("\n", " ")


def safe_filename(name: str) -> str:
    for ch in '<>:"/\\|?*\n\r\t':
        name = name.replace(ch, "_")
    return name.strip(" .") or "untitled"


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")
