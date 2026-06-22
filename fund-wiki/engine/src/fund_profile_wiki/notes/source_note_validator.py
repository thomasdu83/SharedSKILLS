"""Schema checks for generated diligence source notes."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Iterable

from fund_profile_wiki.notes.diligence_note_reader import parse_frontmatter


SYSTEM_PRODUCTS_RE = re.compile(
    r"<!--\s*system:\s*mentioned_products_json.*?-->\s*```json\s*(.*?)\s*```",
    re.DOTALL | re.IGNORECASE,
)
ALLOWED_PRODUCT_ENTITY_TYPES = {
    "product",
    "product_series",
    "strategy_line",
    "generic_bucket",
    "unknown",
}
REQUIRED_FRONTMATTER_FIELDS = ("entity_type", "primary_entity", "source_file")
REQUIRED_PRODUCT_FIELDS = (
    "name",
    "entity_type",
    "confidence",
    "manager_name",
    "evidence_quote",
    "evidence_section",
)
NEW_PRODUCT_SCHEMA_FIELDS = set(REQUIRED_PRODUCT_FIELDS[1:]) | {"is_series"}


@dataclass(frozen=True)
class SourceNoteValidationIssue:
    severity: str
    kind: str
    detail: str
    path: str = ""
    evidence: list[str] = field(default_factory=list)


def validate_source_note(path: Path) -> list[SourceNoteValidationIssue]:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [
            SourceNoteValidationIssue(
                severity="warning",
                kind="source_note_unreadable",
                detail=f"Source note cannot be read: {exc}",
                path=str(path),
            )
        ]
    frontmatter, body = parse_frontmatter(raw)
    issues: list[SourceNoteValidationIssue] = []
    if not frontmatter:
        issues.append(
            SourceNoteValidationIssue(
                severity="warning",
                kind="source_note_missing_frontmatter",
                detail="Source note has no YAML frontmatter.",
                path=str(path),
            )
        )
    else:
        missing = missing_fields(frontmatter, REQUIRED_FRONTMATTER_FIELDS)
        if missing:
            issues.append(
                SourceNoteValidationIssue(
                    severity="warning",
                    kind="source_note_frontmatter_missing_fields",
                    detail="Source note frontmatter is missing required fields.",
                    path=str(path),
                    evidence=missing,
                )
            )
    issues.extend(validate_system_products_json(body, path))
    return issues


def validate_system_products_json(
    markdown_body: str, path: Path
) -> list[SourceNoteValidationIssue]:
    match = SYSTEM_PRODUCTS_RE.search(markdown_body)
    if not match:
        return []
    try:
        payload = json.loads(match.group(1).strip())
    except json.JSONDecodeError as exc:
        return [
            SourceNoteValidationIssue(
                severity="warning",
                kind="source_note_products_json_invalid",
                detail=f"mentioned_products_json is not valid JSON: {exc.msg}",
                path=str(path),
            )
        ]
    if not isinstance(payload, list):
        return [
            SourceNoteValidationIssue(
                severity="warning",
                kind="source_note_products_json_not_list",
                detail="mentioned_products_json must be a JSON list.",
                path=str(path),
            )
        ]
    issues: list[SourceNoteValidationIssue] = []
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            issues.append(
                SourceNoteValidationIssue(
                    severity="warning",
                    kind="source_note_product_schema_invalid",
                    detail="mentioned_products_json item must be an object.",
                    path=str(path),
                    evidence=[f"index={idx}"],
                )
            )
            continue
        missing = missing_fields(item, REQUIRED_PRODUCT_FIELDS)
        if missing and uses_new_product_schema(item):
            issues.append(
                SourceNoteValidationIssue(
                    severity="warning",
                    kind="source_note_product_schema_missing_fields",
                    detail="mentioned_products_json item is missing required product evidence fields.",
                    path=str(path),
                    evidence=[f"index={idx}", *missing],
                )
            )
        entity_type = str(item.get("entity_type", "") or "").strip()
        if entity_type and entity_type not in ALLOWED_PRODUCT_ENTITY_TYPES:
            issues.append(
                SourceNoteValidationIssue(
                    severity="warning",
                    kind="source_note_product_entity_type_invalid",
                    detail=f"Unknown product entity_type: {entity_type}",
                    path=str(path),
                    evidence=[f"index={idx}", entity_type],
                )
            )
    return issues


def uses_new_product_schema(row: dict) -> bool:
    return any(field_name in row for field_name in NEW_PRODUCT_SCHEMA_FIELDS)


def missing_fields(row: dict, fields: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for field_name in fields:
        value = row.get(field_name)
        if value is None or str(value).strip() == "":
            missing.append(field_name)
    return missing
