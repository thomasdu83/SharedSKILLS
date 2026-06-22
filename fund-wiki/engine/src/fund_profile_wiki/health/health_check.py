"""Health check reports for fund-wiki docs."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Iterable

from fund_profile_wiki.cache.file_manifest import (
    ManifestRecord,
    latest_by_path,
    load_manifest,
    manifest_path,
)
from fund_profile_wiki.index.profile_index import (
    ProductProfileRecord,
    load_profile_records,
    read_jsonl,
)
from fund_profile_wiki.notes.diligence_note_reader import parse_frontmatter
from fund_profile_wiki.notes.source_note_validator import validate_source_note
from fund_profile_wiki.profiles.product_name_normalizer import manager_identity_key
from fund_profile_wiki.review.review_queue import write_review_queue


@dataclass(frozen=True)
class HealthIssue:
    severity: str
    kind: str
    manager: str = ""
    product_name: str = ""
    detail: str = ""
    path: str = ""
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HealthReport:
    status: str
    generated_at: str
    issue_count: int
    high_count: int
    warning_count: int
    info_count: int
    profile_count: int
    index_record_count: int
    source_note_count: int
    issues: list[HealthIssue]


def write_health_check(
    docs_root: Path,
    *,
    records: Iterable[ProductProfileRecord] | None = None,
    profile_root: Path | None = None,
) -> HealthReport:
    report = build_health_report(docs_root, records=records, profile_root=profile_root)
    reports_dir = docs_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "health_check.json").write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "health_check.md").write_text(
        render_health_report(report),
        encoding="utf-8",
    )
    write_review_queue(docs_root, report.issues)
    return report


def build_health_report(
    docs_root: Path,
    *,
    records: Iterable[ProductProfileRecord] | None = None,
    profile_root: Path | None = None,
) -> HealthReport:
    index_path = docs_root / "indexes" / "product_profiles.jsonl"
    product_profile_root = profile_root or docs_root / "product_profiles"
    source_notes_root = docs_root / "source_notes"
    rows = list(records) if records is not None else read_jsonl(index_path)
    profile_rows = load_profile_records(product_profile_root)
    if not profile_rows and records is not None:
        profile_rows = list(rows)
    issues: list[HealthIssue] = []

    if source_notes_root.exists():
        for manager_dir in sorted(path for path in source_notes_root.iterdir() if path.is_dir()):
            note_count = count_markdown(manager_dir)
            if note_count == 0:
                continue
            if not any(manager_matches(manager_dir.name, record) for record in rows):
                issues.append(
                    HealthIssue(
                        severity="high",
                        kind="source_notes_without_index_records",
                        manager=manager_dir.name,
                        detail=f"{manager_dir.name} has {note_count} source notes but no matching product profile index records.",
                        path=str(manager_dir),
                    )
                )

    if profile_rows and len(rows) < len(profile_rows):
        issues.append(
            HealthIssue(
                severity="high",
                kind="profile_index_record_mismatch",
                detail=f"product_profiles has {len(profile_rows)} records but JSONL index has {len(rows)} records.",
                path=str(index_path),
            )
        )

    canonical_groups: dict[tuple[str, str], list[ProductProfileRecord]] = defaultdict(list)
    for record in rows:
        canonical = record.canonical_product_name or record.product_name
        canonical_groups[(record.manager, canonical)].append(record)
        if not record.manager:
            issues.append(
                HealthIssue(
                    severity="high",
                    kind="missing_manager",
                    product_name=record.product_name,
                    detail="Product profile has no canonical manager.",
                    path=record.path,
                )
            )
        if record.entity_type and record.entity_type != "product":
            issues.append(
                HealthIssue(
                    severity="warning",
                    kind="non_product_entity_profile",
                    manager=record.manager,
                    product_name=record.product_name,
                    detail=f"Profile entity_type is {record.entity_type}; query answers should treat it as non-confirmed product knowledge.",
                    path=record.path,
                    evidence=record.review_reasons,
                )
            )
        if record.entity_confidence == "low":
            issues.append(
                HealthIssue(
                    severity="warning",
                    kind="low_entity_confidence",
                    manager=record.manager,
                    product_name=record.product_name,
                    detail="Product entity confidence is low.",
                    path=record.path,
                    evidence=record.review_reasons,
                )
            )
        if record.profile_quality_status and record.profile_quality_status != "confirmed":
            quality_kind = profile_quality_issue_kind(record)
            issues.append(
                HealthIssue(
                    severity="warning",
                    kind=quality_kind,
                    manager=record.manager,
                    product_name=record.product_name,
                    detail=f"Profile quality is {record.profile_quality_status}: {record.product_name_reason}",
                    path=record.path,
                )
            )
        if record.rejected_strategy_tags:
            kind, severity = classify_rejected_strategy_issue(record)
            issues.append(
                HealthIssue(
                    severity=severity,
                    kind=kind,
                    manager=record.manager,
                    product_name=record.product_name,
                    detail=rejected_strategy_detail(kind),
                    path=record.path,
                    evidence=record.rejected_strategy_tags,
                )
            )
        if record.zm_match_status == "cross_manager_candidates_only":
            kind, severity = classify_zm_cross_manager_issue(record)
            issues.append(
                HealthIssue(
                    severity=severity,
                    kind=kind,
                    manager=record.manager,
                    product_name=record.product_name,
                    detail=zm_cross_manager_detail(kind),
                    path=record.path,
                    evidence=record.zm_rejected_candidates,
                )
            )
        if not record.strategy_positioning or "材料未提及" in record.strategy_positioning:
            issues.append(
                HealthIssue(
                    severity="warning",
                    kind="missing_strategy_positioning",
                    manager=record.manager,
                    product_name=record.product_name,
                    detail="Strategy positioning is missing or weak.",
                    path=record.path,
                )
            )
        if not record.evidence_summary:
            issues.append(
                HealthIssue(
                    severity="warning",
                    kind="missing_evidence_summary",
                    manager=record.manager,
                    product_name=record.product_name,
                    detail="Evidence summary is missing.",
                    path=record.path,
                )
            )
        if not record.source_files and not record.source_notes:
            issues.append(
                HealthIssue(
                    severity="warning",
                    kind="missing_sources",
                    manager=record.manager,
                    product_name=record.product_name,
                    detail="No source files/source notes are attached.",
                    path=record.path,
                )
            )
        issues.extend(external_evidence_issues(record))
        if not record.risk_points:
            issues.append(
                HealthIssue(
                    severity="info",
                    kind="missing_risk_points",
                    manager=record.manager,
                    product_name=record.product_name,
                    detail="Risk points are not explicitly captured.",
                    path=record.path,
                )
            )

    for (manager, canonical), group in canonical_groups.items():
        names = sorted({record.product_name for record in group})
        if len(names) > 1:
            issues.append(
                HealthIssue(
                    severity="warning",
                    kind="duplicate_canonical_product",
                    manager=manager,
                    product_name=canonical,
                    detail=f"Multiple product profiles share the same canonical product: {', '.join(names[:8])}",
                    evidence=names,
                )
            )

    issues.extend(collect_source_lifecycle_issues(docs_root))

    counts = Counter(issue.severity for issue in issues)
    status = "ok"
    if counts["high"]:
        status = "error"
    elif counts["warning"]:
        status = "warning"
    return HealthReport(
        status=status,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        issue_count=len(issues),
        high_count=counts["high"],
        warning_count=counts["warning"],
        info_count=counts["info"],
        profile_count=len(profile_rows),
        index_record_count=len(rows),
        source_note_count=count_markdown(source_notes_root),
        issues=issues,
    )


def profile_quality_issue_kind(record: ProductProfileRecord) -> str:
    if "suspicious_short_name" in (record.product_name_reason or ""):
        return "profile_quality_short_name"
    if record.entity_type and record.entity_type != "product":
        return "profile_quality_entity_review"
    return "profile_quality_warning"


def classify_rejected_strategy_issue(
    record: ProductProfileRecord,
) -> tuple[str, str]:
    confirmed_strategy_fields = (
        record.direct_strategy_tags
        or record.primary_strategy_tags
        or record.secondary_strategy_tags
        or record.product_line
    )
    if (
        record.entity_type == "product"
        and record.entity_confidence != "low"
        and confirmed_strategy_fields
        and record.profile_quality_status in {"", "confirmed"}
    ):
        return "strategy_tag_rejected_expected", "info"
    return "strategy_tag_rejected_conflict", "warning"


def rejected_strategy_detail(kind: str) -> str:
    if kind == "strategy_tag_rejected_expected":
        return "Strategy tags were mentioned in the same material but were expectedly rejected by product-scope guardrails."
    return "Strategy tags were rejected by product-scope guardrails and need review for possible strategy conflict."


def classify_zm_cross_manager_issue(
    record: ProductProfileRecord,
) -> tuple[str, str]:
    record_key = manager_identity_key(record.manager)
    candidate_keys = {
        manager_identity_key(manager)
        for manager in extract_candidate_managers(record.zm_rejected_candidates)
        if manager_identity_key(manager)
    }
    if record_key and record_key in candidate_keys:
        return "zm_cross_manager_candidates_normal", "info"
    return "zm_cross_manager_candidates_suspicious", "warning"


def zm_cross_manager_detail(kind: str) -> str:
    if kind == "zm_cross_manager_candidates_normal":
        return "ZM candidates matched product aliases but appear to use a manager alias or historical/regional manager variant."
    return "ZM candidates matched product aliases but failed manager hard filter and may indicate a true cross-manager name collision."


def external_evidence_issues(record: ProductProfileRecord) -> list[HealthIssue]:
    """Classify external-public-evidence governance issues.

    External web/search material is intentionally a supporting evidence layer. It
    should never silently replace internal due-diligence evidence, so low-tier,
    external-only, and conflict statuses remain visible to the review queue.
    """

    issues: list[HealthIssue] = []
    source_type = normalize_evidence_status(
        getattr(record, "evidence_source_type", "")
    )
    external_status = normalize_evidence_status(
        getattr(record, "external_evidence_status", "")
    )
    conflict_status = normalize_evidence_status(
        getattr(record, "evidence_conflict_status", "")
    )
    evidence = external_evidence_lines(getattr(record, "external_evidence", []) or [])
    if external_status == "conflict" or conflict_status in {
        "conflict",
        "partial_conflict",
    }:
        issues.append(
            HealthIssue(
                severity="warning",
                kind="external_evidence_conflict",
                manager=record.manager,
                product_name=record.product_name,
                detail="External public evidence conflicts with internal fund-wiki evidence; do not overwrite profile facts automatically.",
                path=record.path,
                evidence=evidence,
            )
        )
    if source_type == "search_discovery_only" or external_status == "external_only":
        issues.append(
            HealthIssue(
                severity="warning",
                kind="external_evidence_only",
                manager=record.manager,
                product_name=record.product_name,
                detail="Profile claim is based only on external/search discovery and still needs internal due-diligence confirmation.",
                path=record.path,
                evidence=evidence,
            )
        )
    if has_low_tier_external_evidence(getattr(record, "external_evidence", []) or []):
        issues.append(
            HealthIssue(
                severity="warning",
                kind="external_evidence_low_tier",
                manager=record.manager,
                product_name=record.product_name,
                detail="External evidence includes third-party or search-only sources; use it as a clue unless corroborated by official/internal material.",
                path=record.path,
                evidence=evidence,
            )
        )
    return issues


def normalize_evidence_status(value: object) -> str:
    return str(value or "").strip().lower()


def has_low_tier_external_evidence(rows: Iterable[object]) -> bool:
    low_tiers = {"third_party_public", "search_discovery_only"}
    for row in rows:
        if not isinstance(row, dict):
            continue
        tier = str(row.get("source_tier", "") or "").strip().lower()
        if tier in low_tiers:
            return True
    return False


def external_evidence_lines(rows: Iterable[object]) -> list[str]:
    lines: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        tier = str(row.get("source_tier", "") or "").strip()
        title = str(row.get("title", "") or "").strip()
        url = str(row.get("url", "") or "").strip()
        claim = str(row.get("claim", "") or "").strip()
        line = " | ".join(part for part in [tier, title, claim, url] if part)
        if line:
            lines.append(line)
    return lines[:8]


def extract_candidate_managers(candidates: Iterable[str]) -> list[str]:
    managers: list[str] = []
    for candidate in candidates:
        match = re.search(r"manager=([^|]+)", str(candidate))
        if match:
            managers.append(match.group(1).strip())
    return managers


def render_health_report(report: HealthReport) -> str:
    lines = [
        "---",
        "profile_type: FundWikiHealthCheck",
        f'generated_at: "{report.generated_at}"',
        f'status: "{report.status}"',
        "---",
        "",
        "# Fund Wiki Health Check",
        "",
        f"- Status: {report.status}",
        f"- Issues: {report.issue_count} (high={report.high_count}, warning={report.warning_count}, info={report.info_count})",
        f"- Product profiles: {report.profile_count}",
        f"- Index records: {report.index_record_count}",
        f"- Source notes: {report.source_note_count}",
        "",
    ]
    if not report.issues:
        lines.extend(["## Issues", ""])
        lines.append("- No issues detected.")
        return "\n".join(lines) + "\n"
    kind_counts = Counter(issue.kind for issue in report.issues)
    lines.extend(["## Issue Summary", ""])
    for kind, count in sorted(kind_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {kind}: {count}")
    lines.extend(["", "## Issues", ""])
    for issue in report.issues[:200]:
        target = " / ".join(part for part in [issue.manager, issue.product_name] if part)
        title = f"[{issue.severity}] {issue.kind}"
        if target:
            title += f" - {target}"
        lines.append(f"- {title}: {issue.detail}")
        if issue.path:
            lines.append(f"  - Path: `{issue.path}`")
    return "\n".join(lines) + "\n"


def collect_source_lifecycle_issues(docs_root: Path) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    manifest_file = manifest_path(docs_root / "run_logs")
    latest_records = latest_by_path(load_manifest(manifest_file))
    for record in sorted(latest_records.values(), key=lambda item: (item.manager, item.source_relpath)):
        issues.extend(issues_from_manifest_record(record))
    issues.extend(collect_parse_warning_note_issues(docs_root / "source_notes"))
    issues.extend(collect_source_note_schema_issues(docs_root / "source_notes"))
    return issues


def issues_from_manifest_record(record: ManifestRecord) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    note_path = record.source_note_path or ""
    evidence = [item for item in [record.source_relpath, note_path, record.error] if item]
    if record.status == "source_missing":
        issues.append(
            HealthIssue(
                severity="warning",
                kind="source_missing",
                manager=record.manager,
                detail="Raw source file no longer exists; derived source notes/profiles are retained until reviewed.",
                path=record.source_path,
                evidence=evidence,
            )
        )
    elif record.status == "failed":
        issues.append(
            HealthIssue(
                severity="warning",
                kind="source_parse_failed",
                manager=record.manager,
                detail=f"Raw source failed parsing/OCR: {record.error or 'n/a'}",
                path=record.source_path,
                evidence=evidence,
            )
        )
    if note_path and not Path(note_path).exists():
        issues.append(
            HealthIssue(
                severity="warning",
                kind="source_note_missing",
                manager=record.manager,
                detail="Manifest references a source note that no longer exists.",
                path=note_path,
                evidence=[item for item in [record.source_path, record.source_relpath] if item],
            )
        )
    return issues


def collect_parse_warning_note_issues(source_notes_root: Path) -> list[HealthIssue]:
    if not source_notes_root.exists():
        return []
    issues: list[HealthIssue] = []
    for note_path in sorted(path for path in source_notes_root.rglob("*.md") if path.is_file()):
        try:
            frontmatter, _body = parse_frontmatter(note_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        tags = frontmatter.get("tags", [])
        if isinstance(tags, str):
            tag_text = tags
        else:
            tag_text = " ".join(str(tag) for tag in tags)
        if "Source/ParseWarning" not in tag_text:
            continue
        issues.append(
            HealthIssue(
                severity="warning",
                kind="parse_warning_source_note",
                manager=str(frontmatter.get("primary_entity", "") or "").strip("[]"),
                detail="Source note was generated as a parse warning; OCR/manual review may be needed.",
                path=str(note_path),
                evidence=[
                    str(frontmatter.get("source_file", "") or ""),
                    str(frontmatter.get("parse_status", "") or ""),
                    str(frontmatter.get("parse_quality_reason", "") or ""),
                ],
            )
        )
    return issues


def collect_source_note_schema_issues(source_notes_root: Path) -> list[HealthIssue]:
    if not source_notes_root.exists():
        return []
    issues: list[HealthIssue] = []
    for note_path in sorted(path for path in source_notes_root.rglob("*.md") if path.is_file()):
        for issue in validate_source_note(note_path):
            issues.append(
                HealthIssue(
                    severity=issue.severity,
                    kind=issue.kind,
                    manager=source_note_manager_name(note_path, source_notes_root),
                    detail=issue.detail,
                    path=issue.path,
                    evidence=issue.evidence,
                )
            )
    return issues


def source_note_manager_name(note_path: Path, source_notes_root: Path) -> str:
    try:
        relative = note_path.relative_to(source_notes_root)
    except ValueError:
        return ""
    return relative.parts[0] if relative.parts else ""


def manager_matches(manager_hint: str, record: ProductProfileRecord) -> bool:
    hint = normalize(manager_hint)
    candidates = [record.manager, *record.manager_aliases]
    for candidate in candidates:
        normalized = normalize(candidate)
        if hint and normalized and (hint in normalized or normalized in hint):
            return True
    return False


def count_markdown(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*.md") if path.is_file())


def normalize(value: str) -> str:
    keep = [ch for ch in str(value) if ch.isalnum() or "\u4e00" <= ch <= "\u9fff"]
    return "".join(keep).lower()
