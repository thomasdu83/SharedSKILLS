"""Read structured diligence source notes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
FENCED_FRONTMATTER_RE = re.compile(
    r"^```(?:yaml|yml)\s*\n---\s*\n(.*?)\n---\s*\n```\s*\n?",
    re.DOTALL | re.IGNORECASE,
)
SYSTEM_PRODUCTS_RE = re.compile(
    r"<!--\s*system:\s*mentioned_products_json.*?-->\s*```json\s*(.*?)\s*```",
    re.DOTALL | re.IGNORECASE,
)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


@dataclass(frozen=True)
class MarkdownNote:
    path: Path
    frontmatter: dict[str, Any]
    body: str
    raw: str


def read_markdown_note(path: Path) -> MarkdownNote:
    raw = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw)
    return MarkdownNote(path=path, frontmatter=frontmatter, body=body, raw=raw)


def parse_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.search(markdown)
    if not match:
        match = FENCED_FRONTMATTER_RE.search(markdown)
    if not match:
        return {}, markdown
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data, markdown[match.end() :]


def extract_wikilink(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    match = WIKILINK_RE.search(text)
    return match.group(1).strip() if match else text.strip("'\" ")


def ensure_wikilink(name: str) -> str:
    clean = extract_wikilink(name)
    return f"[[{clean}]]" if clean else ""


def normalize_link_list(values: Any) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        values = [values]
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        link = ensure_wikilink(str(item))
        if link and link not in seen:
            result.append(link)
            seen.add(link)
    return result


def parse_system_mentioned_products(markdown_body: str) -> list[dict[str, Any]]:
    match = SYSTEM_PRODUCTS_RE.search(markdown_body)
    if not match:
        return []
    try:
        data = json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    products: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict) and item.get("name"):
            products.append(
                {
                    "name": ensure_wikilink(str(item.get("name"))),
                    "main_strategies": normalize_link_list(item.get("main_strategies", [])),
                    "sub_strategies": normalize_link_list(item.get("sub_strategies", [])),
                    "entity_type": str(item.get("entity_type", "") or "").strip(),
                    "confidence": str(item.get("confidence", "") or "").strip(),
                    "evidence_quote": str(item.get("evidence_quote", "") or "").strip(),
                    "evidence_section": str(item.get("evidence_section", "") or "").strip(),
                    "manager_name": ensure_wikilink(str(item.get("manager_name", "") or "")),
                    "is_series": bool(item.get("is_series", False)),
                }
            )
        elif isinstance(item, str):
            products.append(
                {
                    "name": ensure_wikilink(item),
                    "main_strategies": [],
                    "sub_strategies": [],
                    "entity_type": "",
                    "confidence": "",
                    "evidence_quote": "",
                    "evidence_section": "",
                    "manager_name": "",
                    "is_series": False,
                }
            )
    return products


def extract_products(note: MarkdownNote) -> list[dict[str, Any]]:
    products = parse_system_mentioned_products(note.body)
    if not products:
        simple = normalize_link_list(note.frontmatter.get("mentioned_products_simple", []))
        products = [{"name": item, "main_strategies": [], "sub_strategies": []} for item in simple]
    if str(note.frontmatter.get("entity_type", "")).strip() == "Fund" and note.frontmatter.get("primary_entity"):
        primary = ensure_wikilink(str(note.frontmatter["primary_entity"]))
        if primary and all(p.get("name") != primary for p in products):
            products.insert(
                0,
                {
                    "name": primary,
                    "main_strategies": normalize_link_list(note.frontmatter.get("main_strategies", [])),
                    "sub_strategies": normalize_link_list(note.frontmatter.get("sub_strategies", [])),
                },
            )
    return [p for p in products if p.get("name")]


def extract_heading_section(markdown_body: str, entity_name: str) -> str:
    if not entity_name:
        return ""
    heading = re.compile(rf"^###\s+\[\[\s*{re.escape(entity_name)}\s*\]\]\s*$", re.MULTILINE)
    match = heading.search(markdown_body)
    if not match:
        return ""
    rest = markdown_body[match.end() :]
    next_heading = re.search(r"^\s*(?:#{1,3})\s+", rest, re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(markdown_body)
    return markdown_body[match.start() : end].strip()


def extract_lines_containing(markdown_body: str, keywords: list[str], limit: int = 12) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for raw_line in markdown_body.splitlines():
        line = raw_line.strip()
        if not line or line in seen or "(未提及)" in line:
            continue
        if any(keyword.lower() in line.lower() for keyword in keywords):
            lines.append(line)
            seen.add(line)
            if len(lines) >= limit:
                break
    return lines
