"""Write lightweight global wiki navigation and governance documents."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from fund_profile_wiki.health.health_check import HealthReport
from fund_profile_wiki.index.profile_index import ProductProfileRecord


@dataclass(frozen=True)
class GovernanceSummary:
    manager_count: int
    product_count: int
    strategy_count: int
    product_line_count: int
    source_note_count: int
    relation_count: int
    health_status: str


def write_governance_docs(
    docs_root: Path,
    records: Iterable[ProductProfileRecord],
    *,
    relation_count: int = 0,
    health_report: HealthReport | None = None,
) -> list[Path]:
    """Write global docs that make the fund-wiki folder easier for LLMs to navigate."""
    rows = sorted(
        list(records), key=lambda item: (item.manager, item.product_name, item.path)
    )
    docs_root.mkdir(parents=True, exist_ok=True)
    summary = build_summary(
        docs_root,
        rows,
        relation_count=relation_count,
        health_report=health_report,
    )
    log_path = docs_root / "log.md"
    previous_log = read_text(log_path)
    payloads = {
        "fund_wiki_purpose.md": render_purpose(summary),
        "fund_wiki_schema.md": render_schema(summary),
        "index.md": render_index(summary, rows),
        "overview.md": render_overview(summary, rows),
        "log.md": render_log(summary, health_report, previous_log=previous_log),
    }
    written: list[Path] = []
    for filename, content in payloads.items():
        path = docs_root / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def build_summary(
    docs_root: Path,
    records: list[ProductProfileRecord],
    *,
    relation_count: int = 0,
    health_report: HealthReport | None = None,
) -> GovernanceSummary:
    managers = {record.manager for record in records if record.manager}
    strategies = {
        strip_wikilink(strategy)
        for record in records
        for strategy in record.strategy_links
        if strip_wikilink(strategy)
    }
    product_lines = {
        line for record in records for line in record.product_line if line
    }
    return GovernanceSummary(
        manager_count=len(managers),
        product_count=len(records),
        strategy_count=len(strategies),
        product_line_count=len(product_lines),
        source_note_count=count_markdown(docs_root / "source_notes"),
        relation_count=relation_count,
        health_status=health_report.status if health_report else "unknown",
    )


def render_purpose(summary: GovernanceSummary) -> str:
    return "\n".join(
        [
            "---",
            "profile_type: FundWikiPurpose",
            f'updated_at: "{today()}"',
            "tags: [FundWiki/Governance]",
            "---",
            "",
            "# Fund Wiki Purpose",
            "",
            "fund-wiki is an LLM-readable due-diligence knowledge base for fund managers and products.",
            "",
            "It is optimized for flexible questions such as index-enhancement exposure, CTA product lines, manager backgrounds, risk constraints, and evidence tracing.",
            "",
            "Raw due-diligence materials are read-only evidence. The generated wiki layer contains source notes, product profiles, manager-level summaries, relationship indexes, and health checks.",
            "",
            "## Current Scope",
            "",
            f"- Managers: {summary.manager_count}",
            f"- Product profiles: {summary.product_count}",
            f"- Strategy tags: {summary.strategy_count}",
            f"- Product lines: {summary.product_line_count}",
            f"- Source notes: {summary.source_note_count}",
            f"- Relation records: {summary.relation_count}",
            f"- Health status: {summary.health_status}",
            "",
        ]
    )


def render_schema(summary: GovernanceSummary) -> str:
    return "\n".join(
        [
            "---",
            "profile_type: FundWikiSchema",
            f'updated_at: "{today()}"',
            "tags: [FundWiki/Governance]",
            "---",
            "",
            "# Fund Wiki Schema",
            "",
            "## Core Folders",
            "",
            "| Folder | Meaning |",
            "|---|---|",
            "| `source_notes/` | Parsed evidence notes from raw diligence materials. |",
            "| `product_profiles/` | LLM-readable product-level profiles with structured frontmatter. |",
            "| `manager_profiles/` | Manager-level strategy and product summaries. |",
            "| `product_maps/` | Manager product maps for quick overview queries. |",
            "| `risk_flags/` | Risk and constraint summaries by manager/product. |",
            "| `timelines/` | Source-file timeline summaries. |",
            "| `indexes/` | JSONL, SQLite, and relationship indexes for fast retrieval. |",
            "| `reports/` | Build quality and health-check reports. |",
            "| `run_logs/` | Run manifests, source catalogs, locks, and process logs. |",
            "",
            "## ProductProfile Fields",
            "",
            "| Field | Purpose |",
            "|---|---|",
            "| `manager` | Canonical manager name. |",
            "| `product_name` | Canonical product/profile name. |",
            "| `entity_type` | Entity class: product, product_series, strategy_line, generic_bucket, or unknown. |",
            "| `entity_confidence` | Confidence that this page represents a real product entity. |",
            "| `manager_aliases` | Names used for manager matching. |",
            "| `product_aliases` | Names used for product matching. |",
            "| `strategy_positioning` | One-sentence strategy positioning for LLM retrieval. |",
            "| `product_line` | Normalized product-line labels such as 1000指增, CTA, market neutral. |",
            "| `direct_strategy_tags` | Strategy labels directly supported by product-level evidence. |",
            "| `mentioned_strategy_tags` | Strategy labels mentioned in the same material but not assigned as direct product tags. |",
            "| `rejected_strategy_tags` | Strategy labels removed by product-scope guardrails. |",
            "| `risk_points` | Risk constraints and concerns, including exposure controls. |",
            "| `key_people_summary` | Personnel background clues such as WorldQuant or Millennium. |",
            "| `evidence_summary` | Short evidence lines supporting the profile. |",
            "| `profile_quality_status` / `review_reasons` | Product-name and entity-quality status for review and query ranking. |",
            "| `zm_match_status` / `zm_rejected_candidates` | External identity match status and cross-manager rejected candidates. |",
            "| `source_files` / `source_notes` | Traceability back to evidence notes and raw-file names. |",
            "",
            "## Relationship Index",
            "",
            "`indexes/relations.jsonl` and `indexes/relations.sqlite` flatten important links into subject-predicate-object records, such as manager has product, product has strategy, product has risk point, and product has people background.",
            "",
            f"Current relation records: {summary.relation_count}",
            "",
        ]
    )


def render_index(
    summary: GovernanceSummary, records: list[ProductProfileRecord]
) -> str:
    managers = group_by_manager(records)
    lines = [
        "---",
        "profile_type: FundWikiIndex",
        f'updated_at: "{today()}"',
        "tags: [FundWiki/Index]",
        "---",
        "",
        "# Fund Wiki Index",
        "",
        "## Quick Links",
        "",
        "- [[fund_wiki_purpose]]",
        "- [[fund_wiki_schema]]",
        "- [[overview]]",
        "- `reports/health_check.md`",
        "- `reports/profile_quality.json`",
        "- `indexes/product_profiles.jsonl`",
        "- `indexes/product_profiles.sqlite`",
        "- `indexes/relations.jsonl`",
        "- `indexes/relations.sqlite`",
        "",
        "## Counts",
        "",
        f"- Managers: {summary.manager_count}",
        f"- Product profiles: {summary.product_count}",
        f"- Source notes: {summary.source_note_count}",
        f"- Health status: {summary.health_status}",
        "",
        "## Managers",
        "",
        "| Manager | Products | Main product lines |",
        "|---|---:|---|",
    ]
    for manager, items in sorted(managers.items()):
        product_lines = top_values(line for item in items for line in item.product_line)
        lines.append(
            f"| {escape_cell(manager)} | {len(items)} | {escape_cell('、'.join(product_lines) or '材料未提及')} |"
        )
    if not managers:
        lines.append("| No managers indexed | 0 |  |")
    return "\n".join(lines) + "\n"


def render_overview(
    summary: GovernanceSummary, records: list[ProductProfileRecord]
) -> str:
    product_line_counts = Counter(
        line for record in records for line in record.product_line if line
    )
    strategy_counts = Counter(
        strip_wikilink(strategy)
        for record in records
        for strategy in record.strategy_links
        if strip_wikilink(strategy)
    )
    quality_counts = Counter(
        record.profile_quality_status or "unknown" for record in records
    )
    entity_type_counts = Counter(
        record.entity_type or "unknown" for record in records
    )
    entity_confidence_counts = Counter(
        record.entity_confidence or "unknown" for record in records
    )
    lines = [
        "---",
        "profile_type: FundWikiOverview",
        f'updated_at: "{today()}"',
        "tags: [FundWiki/Overview]",
        "---",
        "",
        "# Fund Wiki Overview",
        "",
        "## Snapshot",
        "",
        f"- Managers: {summary.manager_count}",
        f"- Product profiles: {summary.product_count}",
        f"- Strategy tags: {summary.strategy_count}",
        f"- Product lines: {summary.product_line_count}",
        f"- Relation records: {summary.relation_count}",
        f"- Health status: {summary.health_status}",
        "",
        "## Product Lines",
        "",
    ]
    lines.extend(counter_lines(product_line_counts))
    lines.extend(["", "## Strategy Tags", ""])
    lines.extend(counter_lines(strategy_counts))
    lines.extend(["", "## Profile Quality", ""])
    lines.extend(counter_lines(quality_counts))
    lines.extend(["", "## Entity Types", ""])
    lines.extend(counter_lines(entity_type_counts))
    lines.extend(["", "## Entity Confidence", ""])
    lines.extend(counter_lines(entity_confidence_counts))
    lines.extend(["", "## Recent Product Profiles", ""])
    for record in sorted(records, key=lambda item: item.updated_at, reverse=True)[:20]:
        lines.append(
            f"- {record.updated_at or 'unknown'} | {record.manager} | {record.product_name}"
        )
    if not records:
        lines.append("- No product profiles indexed.")
    return "\n".join(lines) + "\n"


def render_log(
    summary: GovernanceSummary,
    health_report: HealthReport | None,
    *,
    previous_log: str = "",
) -> str:
    health_line = (
        f"{health_report.status}; issues={health_report.issue_count}"
        if health_report
        else "unknown"
    )
    updated_at = now()
    latest_row = (
        f"| {updated_at} | {summary.manager_count} | {summary.product_count} | "
        f"{summary.relation_count} | {health_line} |"
    )
    rows = [latest_row] + extract_log_rows(previous_log)
    return "\n".join(
        [
            "---",
            "profile_type: FundWikiBuildLog",
            f'updated_at: "{updated_at}"',
            "tags: [FundWiki/Log]",
            "---",
            "",
            "# Fund Wiki Build Log",
            "",
            "| Updated at | Managers | Products | Relations | Health |",
            "|---|---:|---:|---:|---|",
            *dedupe(rows)[:200],
            "",
            "Detailed per-run logs live under `run_logs/runs/`.",
            "",
        ]
    )


def group_by_manager(
    records: Iterable[ProductProfileRecord],
) -> dict[str, list[ProductProfileRecord]]:
    grouped: dict[str, list[ProductProfileRecord]] = defaultdict(list)
    for record in records:
        grouped[record.manager or "未知管理人"].append(record)
    return grouped


def top_values(values: Iterable[str], *, limit: int = 8) -> list[str]:
    counts = Counter(str(value).strip() for value in values if str(value).strip())
    return [value for value, _ in counts.most_common(limit)]


def counter_lines(counter: Counter[str], *, limit: int = 20) -> list[str]:
    if not counter:
        return ["- None"]
    return [f"- {key}: {value}" for key, value in counter.most_common(limit)]


def count_markdown(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*.md") if path.is_file())


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def extract_log_rows(markdown: str) -> list[str]:
    rows: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| "):
            continue
        if stripped.startswith("| Updated at ") or stripped.startswith("|---"):
            continue
        if stripped.count("|") >= 5:
            rows.append(stripped)
    return rows


def dedupe(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def strip_wikilink(value: str) -> str:
    text = str(value or "").strip()
    if text.startswith("[[") and text.endswith("]]"):
        text = text[2:-2]
    return text.strip()


def escape_cell(value: str) -> str:
    return str(value).replace("|", "｜").replace("\n", " ")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")
