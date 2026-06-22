"""Persistent human-review queue for fund-wiki quality issues."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import uuid
from typing import Iterable

import yaml


OPEN_QUEUE_JSONL = "open.jsonl"
OPEN_QUEUE_MD = "open.md"
RESOLVED_QUEUE_JSONL = "resolved.jsonl"
OVERRIDES_YAML = "overrides.yaml"
SUPPRESSED_STATUSES = {"confirmed", "ignored", "resolved", "closed"}


@dataclass(frozen=True)
class ReviewItem:
    item_id: str
    status: str
    severity: str
    kind: str
    manager: str = ""
    product_name: str = ""
    detail: str = ""
    evidence: list[str] = field(default_factory=list)
    path: str = ""
    suggested_action: str = ""
    created_at: str = ""
    updated_at: str = ""


def write_review_queue(docs_root: Path, issues: Iterable[object]) -> tuple[Path, Path, int]:
    """Write/update open review items derived from health issues."""
    queue_dir = docs_root / "review_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = queue_dir / OPEN_QUEUE_JSONL
    md_path = queue_dir / OPEN_QUEUE_MD
    resolved_path = queue_dir / RESOLVED_QUEUE_JSONL
    if not resolved_path.exists():
        resolved_path.write_text("", encoding="utf-8")

    now = datetime.now().isoformat(timespec="seconds")
    existing = {item.item_id: item for item in read_review_items(jsonl_path)}
    overrides = read_review_overrides(queue_dir / OVERRIDES_YAML)
    next_items: dict[str, ReviewItem] = {}
    for issue in issues:
        if issue_severity(issue) not in {"high", "warning"}:
            continue
        candidate = item_from_issue(issue, now=now)
        previous = existing.get(candidate.item_id)
        if previous:
            item = ReviewItem(
                item_id=previous.item_id,
                status=previous.status or "open",
                severity=candidate.severity,
                kind=candidate.kind,
                manager=candidate.manager,
                product_name=candidate.product_name,
                detail=candidate.detail,
                evidence=candidate.evidence,
                path=candidate.path,
                suggested_action=candidate.suggested_action,
                created_at=previous.created_at or candidate.created_at,
                updated_at=now,
            )
        else:
            item = candidate
        item = apply_override(item, overrides, now=now)
        if item.status in SUPPRESSED_STATUSES:
            continue
        next_items[item.item_id] = item

    items = sorted(
        next_items.values(),
        key=lambda item: (severity_rank(item.severity), item.manager, item.product_name, item.kind),
    )
    write_jsonl(items, jsonl_path)
    md_path.write_text(render_review_queue(items), encoding="utf-8")
    return jsonl_path, md_path, len(items)


def item_from_issue(issue: object, *, now: str) -> ReviewItem:
    severity = issue_severity(issue)
    kind = str(getattr(issue, "kind", "") or "")
    manager = str(getattr(issue, "manager", "") or "")
    product_name = str(getattr(issue, "product_name", "") or "")
    detail = str(getattr(issue, "detail", "") or "")
    path = str(getattr(issue, "path", "") or "")
    evidence = dedupe(getattr(issue, "evidence", []) or [])
    return ReviewItem(
        item_id=stable_item_id(kind=kind, manager=manager, product_name=product_name, path=path),
        status="open",
        severity=severity,
        kind=kind,
        manager=manager,
        product_name=product_name,
        detail=detail,
        evidence=evidence,
        path=path,
        suggested_action=suggested_action(kind),
        created_at=now,
        updated_at=now,
    )


def read_review_overrides(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    if isinstance(payload, dict):
        raw_rows = payload.get("overrides", [])
    elif isinstance(payload, list):
        raw_rows = payload
    else:
        raw_rows = []
    rows: list[dict[str, str]] = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        normalized = {
            str(key): str(value).strip()
            for key, value in row.items()
            if value is not None and str(value).strip()
        }
        if normalized:
            rows.append(normalized)
    return rows


def apply_override(
    item: ReviewItem, overrides: list[dict[str, str]], *, now: str
) -> ReviewItem:
    override = matching_override(item, overrides)
    if not override:
        return item
    status = normalize_status(override.get("status", item.status))
    note = override.get("note", "")
    suggested_action = item.suggested_action
    if note and status not in SUPPRESSED_STATUSES:
        suggested_action = f"{suggested_action} Override note: {note}"
    return ReviewItem(
        item_id=item.item_id,
        status=status or item.status,
        severity=item.severity,
        kind=item.kind,
        manager=item.manager,
        product_name=item.product_name,
        detail=item.detail,
        evidence=item.evidence,
        path=item.path,
        suggested_action=suggested_action,
        created_at=item.created_at,
        updated_at=now,
    )


def matching_override(
    item: ReviewItem, overrides: list[dict[str, str]]
) -> dict[str, str] | None:
    for override in overrides:
        if override.get("item_id") and normalize_text(override["item_id"]) == normalize_text(item.item_id):
            return override
        fields = ["kind", "manager", "product_name", "path"]
        specified = [field for field in fields if override.get(field)]
        if not specified:
            continue
        if all(
            normalize_text(override[field]) == normalize_text(getattr(item, field))
            for field in specified
        ):
            return override
    return None


def normalize_status(status: str) -> str:
    return str(status or "").strip().lower()


def normalize_text(value: object) -> str:
    return str(value or "").strip().casefold()


def stable_item_id(*, kind: str, manager: str, product_name: str, path: str) -> str:
    text = "|".join([kind, manager, product_name, path]).casefold()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def read_review_items(path: Path) -> list[ReviewItem]:
    if not path.exists():
        return []
    rows: list[ReviewItem] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows.append(review_item_from_payload(payload))
    return rows


def review_item_from_payload(payload: dict) -> ReviewItem:
    return ReviewItem(
        item_id=str(payload.get("item_id", "") or ""),
        status=str(payload.get("status", "open") or "open"),
        severity=str(payload.get("severity", "") or ""),
        kind=str(payload.get("kind", "") or ""),
        manager=str(payload.get("manager", "") or ""),
        product_name=str(payload.get("product_name", "") or ""),
        detail=str(payload.get("detail", "") or ""),
        evidence=dedupe(payload.get("evidence", []) or []),
        path=str(payload.get("path", "") or ""),
        suggested_action=str(payload.get("suggested_action", "") or ""),
        created_at=str(payload.get("created_at", "") or ""),
        updated_at=str(payload.get("updated_at", "") or ""),
    )


def write_jsonl(items: Iterable[ReviewItem], path: Path) -> None:
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    rows = list(items)
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            for item in rows:
                handle.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def render_review_queue(items: list[ReviewItem]) -> str:
    lines = [
        "---",
        "profile_type: FundWikiReviewQueue",
        f'generated_at: "{datetime.now().isoformat(timespec="seconds")}"',
        f"open_items: {len(items)}",
        "---",
        "",
        "# Fund Wiki Review Queue",
        "",
    ]
    if not items:
        lines.append("- No open review items.")
        return "\n".join(lines) + "\n"
    for item in items:
        target = " / ".join(part for part in [item.manager, item.product_name] if part)
        title = f"## {item.item_id} | {item.severity} | {item.kind}"
        if target:
            title += f" | {target}"
        lines.extend(
            [
                title,
                "",
                f"- Status: {item.status}",
                f"- Detail: {item.detail or 'n/a'}",
                f"- Suggested action: {item.suggested_action or 'review manually'}",
            ]
        )
        if item.path:
            lines.append(f"- Path: `{item.path}`")
        if item.evidence:
            lines.append(f"- Evidence: {' | '.join(item.evidence[:5])}")
        lines.append("")
    return "\n".join(lines)


def suggested_action(kind: str) -> str:
    actions = {
        "profile_quality_warning": "Review product name, canonical alias, and whether this is a real product.",
        "profile_quality_short_name": "Verify whether the short product name is a real product, share class, or shorthand for a fuller registered fund name.",
        "profile_quality_entity_review": "Review whether this profile should remain queryable as a product or be treated as series/strategy context.",
        "strategy_tag_rejected_conflict": "Inspect rejected strategy tags and product-scope evidence for a possible strategy classification conflict.",
        "zm_cross_manager_candidates_suspicious": "Inspect ZM candidates and manager hard filter; add manager alias or confirm this is a true cross-manager product-name collision.",
        "source_notes_without_index_records": "Run profile build/index refresh or inspect why source notes did not compile into profiles.",
        "profile_index_record_mismatch": "Rebuild product profile index and verify all profile markdown pages are indexed.",
        "missing_strategy_positioning": "Inspect profile compiler output and add strategy positioning evidence if available.",
        "missing_evidence_summary": "Inspect extraction evidence and regenerate the profile if evidence was missed.",
        "missing_sources": "Attach source note/source file references before treating this profile as query-ready.",
        "external_evidence_only": "Find internal due-diligence evidence before treating this external/search-only claim as confirmed.",
        "external_evidence_low_tier": "Prefer official/regulatory/manager website evidence or keep the item as review-context only.",
        "external_evidence_conflict": "Compare external public evidence with internal due-diligence evidence and resolve the conflict manually.",
        "duplicate_canonical_product": "Merge or rename duplicate product profiles sharing the same canonical product.",
        "source_missing": "Verify whether the raw file was intentionally removed; keep derived notes visible until reviewed.",
        "source_parse_failed": "Inspect the failed file, OCR dependency, encryption, or permissions.",
        "source_note_missing": "Regenerate source notes or mark the derived profile stale.",
        "parse_warning_source_note": "Review parse warning note and decide whether OCR/manual extraction is needed.",
        "source_note_unreadable": "Inspect source note encoding or permissions and regenerate it if needed.",
        "source_note_missing_frontmatter": "Regenerate the source note with YAML frontmatter before compiling product profiles.",
        "source_note_frontmatter_missing_fields": "Add required source note frontmatter fields or regenerate extraction with the current prompt.",
        "source_note_products_json_invalid": "Fix mentioned_products_json or regenerate extraction; product profiles may miss structured entity evidence.",
        "source_note_products_json_not_list": "Regenerate mentioned_products_json as a JSON list of product evidence objects.",
        "source_note_product_schema_invalid": "Regenerate mentioned_products_json item as an object with product evidence fields.",
        "source_note_product_schema_missing_fields": "Regenerate extraction so each product candidate includes entity_type, confidence, manager_name, evidence_quote, and evidence_section.",
        "source_note_product_entity_type_invalid": "Use one of product, product_series, strategy_line, generic_bucket, or unknown for entity_type.",
    }
    return actions.get(kind, "Review the issue and update profile/source evidence if needed.")


def severity_rank(severity: str) -> int:
    return {"high": 0, "warning": 1, "info": 2}.get(severity, 9)


def issue_severity(issue: object) -> str:
    return str(getattr(issue, "severity", "") or "").strip().lower()


def dedupe(values: Iterable[object]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result
