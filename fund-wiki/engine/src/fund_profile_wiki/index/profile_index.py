"""Index product profile markdown files into JSONL and SQLite."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from fund_profile_wiki.config import Settings
from fund_profile_wiki.notes.diligence_note_reader import (
    extract_wikilink,
    parse_frontmatter,
)
from fund_profile_wiki.profiles.product_name_normalizer import generate_manager_aliases


@dataclass(frozen=True)
class ProductProfileRecord:
    product_name: str
    manager: str
    strategy_links: list[str]
    people_links: list[str]
    source_notes: list[str]
    profile_text: str
    evidence_text: str
    search_text: str
    path: str
    updated_at: str
    entity_type: str = "product"
    entity_confidence: str = "high"
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
    profile_quality_status: str = ""
    product_name_reason: str = ""
    review_reasons: list[str] = field(default_factory=list)
    zm_match_status: str = ""
    zm_fund_ids: list[str] = field(default_factory=list)
    zm_fund_codes: list[str] = field(default_factory=list)
    zm_candidate_matches: list[str] = field(default_factory=list)
    zm_rejected_candidates: list[str] = field(default_factory=list)


def build_profile_index(
    profile_root: Path = Settings.product_profiles_dir,
    index_dir: Path = Settings.indexes_dir,
) -> tuple[Path, Path, int]:
    records = load_profile_records(profile_root)
    index_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = index_dir / Settings.product_profile_jsonl
    sqlite_path = index_dir / Settings.product_profile_sqlite
    write_jsonl(records, jsonl_path)
    write_sqlite(records, sqlite_path)
    return jsonl_path, sqlite_path, len(records)


def load_profile_records(profile_root: Path) -> list[ProductProfileRecord]:
    if not profile_root.exists():
        return []
    records = []
    for path in sorted(profile_root.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(raw)
        if frontmatter.get("profile_type") != "ProductProfile":
            continue
        product_name = extract_wikilink(frontmatter.get("product_name", path.stem))
        manager = extract_wikilink(frontmatter.get("manager", ""))
        strategy_links = normalize_string_list(frontmatter.get("strategy_links", []))
        people_links = normalize_string_list(frontmatter.get("people_links", []))
        source_notes = normalize_string_list(frontmatter.get("source_notes", []))
        entity_type = str(
            frontmatter.get("entity_type", "product") or "product"
        ).strip()
        entity_confidence = str(
            frontmatter.get("entity_confidence", "high") or "high"
        ).strip()
        manager_aliases = normalize_string_list(
            normalize_string_list(frontmatter.get("manager_aliases", []))
            + generate_manager_aliases(manager)
        )
        product_aliases = normalize_string_list(frontmatter.get("product_aliases", []))
        strategy_positioning = str(
            frontmatter.get("strategy_positioning", "") or ""
        ).strip()
        product_line = normalize_string_list(frontmatter.get("product_line", []))
        risk_points = normalize_string_list(frontmatter.get("risk_points", []))
        key_people_summary = str(
            frontmatter.get("key_people_summary", "") or ""
        ).strip()
        evidence_summary = normalize_string_list(
            frontmatter.get("evidence_summary", [])
        )
        source_files = normalize_string_list(frontmatter.get("source_files", []))
        evidence_source_type = str(
            frontmatter.get("evidence_source_type", "internal_due_diligence")
            or "internal_due_diligence"
        ).strip()
        external_evidence_status = str(
            frontmatter.get("external_evidence_status", "not_checked") or "not_checked"
        ).strip()
        evidence_conflict_status = str(
            frontmatter.get("evidence_conflict_status", "none") or "none"
        ).strip()
        source_priority = normalize_int(frontmatter.get("source_priority", 10), 10)
        external_evidence = normalize_dict_list(
            frontmatter.get("external_evidence", [])
        )
        strategy_raw_terms = normalize_string_list(
            frontmatter.get("strategy_raw_terms", [])
        )
        strategy_evidence = normalize_string_list(
            frontmatter.get("strategy_evidence", [])
        )
        primary_strategy_codes = normalize_string_list(
            frontmatter.get("primary_strategy_codes", [])
        )
        primary_strategy_tags = normalize_string_list(
            frontmatter.get("primary_strategy_tags", [])
        )
        secondary_strategy_codes = normalize_string_list(
            frontmatter.get("secondary_strategy_codes", [])
        )
        secondary_strategy_tags = normalize_string_list(
            frontmatter.get("secondary_strategy_tags", [])
        )
        direct_strategy_tags = normalize_string_list(
            frontmatter.get("direct_strategy_tags", [])
        )
        mentioned_strategy_tags = normalize_string_list(
            frontmatter.get("mentioned_strategy_tags", [])
        )
        rejected_strategy_tags = normalize_string_list(
            frontmatter.get("rejected_strategy_tags", [])
        )
        strategy_facets = normalize_facet_dict(frontmatter.get("strategy_facets", {}))
        candidate_strategy_tags = normalize_string_list(
            frontmatter.get("candidate_strategy_tags", [])
        )
        strategy_tag_confidence = str(
            frontmatter.get("strategy_tag_confidence", "") or ""
        ).strip()
        strategy_tag_source = str(
            frontmatter.get("strategy_tag_source", "") or ""
        ).strip()
        strategy_tag_review_status = str(
            frontmatter.get("strategy_tag_review_status", "") or ""
        ).strip()
        canonical_product_name = extract_wikilink(
            frontmatter.get("canonical_product_name", "")
        )
        profile_quality_status = str(
            frontmatter.get("profile_quality_status", "") or ""
        ).strip()
        product_name_reason = str(
            frontmatter.get("product_name_reason", "") or ""
        ).strip()
        review_reasons = normalize_string_list(frontmatter.get("review_reasons", []))
        zm_match_status = str(frontmatter.get("zm_match_status", "") or "").strip()
        zm_fund_ids = normalize_string_list(frontmatter.get("zm_fund_ids", []))
        zm_fund_codes = normalize_string_list(frontmatter.get("zm_fund_codes", []))
        zm_candidate_matches = normalize_string_list(
            frontmatter.get("zm_candidate_matches", [])
        )
        zm_rejected_candidates = normalize_string_list(
            frontmatter.get("zm_rejected_candidates", [])
        )
        profile_text = extract_section(body, "LLM Profile")
        evidence_text = extract_section(body, "Evidence")
        search_text = "\n".join(
            [
                product_name,
                manager,
                entity_type,
                entity_confidence,
                " ".join(strategy_links),
                " ".join(people_links),
                " ".join(manager_aliases),
                " ".join(product_aliases),
                strategy_positioning,
                " ".join(product_line),
                " ".join(risk_points),
                key_people_summary,
                " ".join(evidence_summary),
                " ".join(source_files),
                evidence_source_type,
                external_evidence_status,
                evidence_conflict_status,
                str(source_priority),
                json.dumps(external_evidence, ensure_ascii=False),
                " ".join(strategy_raw_terms),
                " ".join(strategy_evidence),
                " ".join(primary_strategy_codes),
                " ".join(primary_strategy_tags),
                " ".join(secondary_strategy_codes),
                " ".join(secondary_strategy_tags),
                " ".join(direct_strategy_tags),
                " ".join(mentioned_strategy_tags),
                " ".join(rejected_strategy_tags),
                json.dumps(strategy_facets, ensure_ascii=False),
                " ".join(candidate_strategy_tags),
                strategy_tag_confidence,
                strategy_tag_source,
                strategy_tag_review_status,
                canonical_product_name,
                profile_quality_status,
                product_name_reason,
                " ".join(review_reasons),
                zm_match_status,
                " ".join(zm_fund_ids),
                " ".join(zm_fund_codes),
                " ".join(zm_candidate_matches),
                profile_text,
                evidence_text,
            ]
        )
        records.append(
            ProductProfileRecord(
                product_name=product_name,
                manager=manager,
                strategy_links=strategy_links,
                people_links=people_links,
                source_notes=source_notes,
                profile_text=profile_text,
                evidence_text=evidence_text,
                search_text=search_text,
                path=str(path),
                updated_at=str(frontmatter.get("updated_at", "")),
                entity_type=entity_type,
                entity_confidence=entity_confidence,
                manager_aliases=manager_aliases,
                product_aliases=product_aliases,
                strategy_positioning=strategy_positioning,
                product_line=product_line,
                risk_points=risk_points,
                key_people_summary=key_people_summary,
                evidence_summary=evidence_summary,
                source_files=source_files,
                evidence_source_type=evidence_source_type,
                external_evidence_status=external_evidence_status,
                evidence_conflict_status=evidence_conflict_status,
                source_priority=source_priority,
                external_evidence=external_evidence,
                strategy_raw_terms=strategy_raw_terms,
                strategy_evidence=strategy_evidence,
                primary_strategy_codes=primary_strategy_codes,
                primary_strategy_tags=primary_strategy_tags,
                secondary_strategy_codes=secondary_strategy_codes,
                secondary_strategy_tags=secondary_strategy_tags,
                direct_strategy_tags=direct_strategy_tags,
                mentioned_strategy_tags=mentioned_strategy_tags,
                rejected_strategy_tags=rejected_strategy_tags,
                strategy_facets=strategy_facets,
                candidate_strategy_tags=candidate_strategy_tags,
                strategy_tag_confidence=strategy_tag_confidence,
                strategy_tag_source=strategy_tag_source,
                strategy_tag_review_status=strategy_tag_review_status,
                canonical_product_name=canonical_product_name,
                profile_quality_status=profile_quality_status,
                product_name_reason=product_name_reason,
                review_reasons=review_reasons,
                zm_match_status=zm_match_status,
                zm_fund_ids=zm_fund_ids,
                zm_fund_codes=zm_fund_codes,
                zm_candidate_matches=zm_candidate_matches,
                zm_rejected_candidates=zm_rejected_candidates,
            )
        )
    return records


def write_jsonl(records: Iterable[ProductProfileRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def read_jsonl(path: Path) -> list[ProductProfileRecord]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(record_from_payload(json.loads(line)))
    return records


def write_sqlite(records: Iterable[ProductProfileRecord], path: Path) -> None:
    rows = list(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        conn = sqlite3.connect(tmp_path)
        try:
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("DROP TABLE IF EXISTS profiles")
            conn.execute(
                """
                CREATE TABLE profiles (
                    product_name TEXT,
                    manager TEXT,
                    strategy_links TEXT,
                    people_links TEXT,
                    source_notes TEXT,
                    profile_text TEXT,
                    evidence_text TEXT,
                    search_text TEXT,
                    path TEXT PRIMARY KEY,
                    updated_at TEXT,
                    entity_type TEXT,
                    entity_confidence TEXT,
                    manager_aliases TEXT,
                    product_aliases TEXT,
                    strategy_positioning TEXT,
                    product_line TEXT,
                    risk_points TEXT,
                    key_people_summary TEXT,
                    evidence_summary TEXT,
                    source_files TEXT,
                    evidence_source_type TEXT,
                    external_evidence_status TEXT,
                    evidence_conflict_status TEXT,
                    source_priority INTEGER,
                    external_evidence TEXT,
                    strategy_raw_terms TEXT,
                    strategy_evidence TEXT,
                    primary_strategy_codes TEXT,
                    primary_strategy_tags TEXT,
                    secondary_strategy_codes TEXT,
                    secondary_strategy_tags TEXT,
                    direct_strategy_tags TEXT,
                    mentioned_strategy_tags TEXT,
                    rejected_strategy_tags TEXT,
                    strategy_facets TEXT,
                    candidate_strategy_tags TEXT,
                    strategy_tag_confidence TEXT,
                    strategy_tag_source TEXT,
                    strategy_tag_review_status TEXT,
                    canonical_product_name TEXT,
                    profile_quality_status TEXT,
                    product_name_reason TEXT,
                    review_reasons TEXT,
                    zm_match_status TEXT,
                    zm_fund_ids TEXT,
                    zm_fund_codes TEXT,
                    zm_candidate_matches TEXT,
                    zm_rejected_candidates TEXT
                )
                """
            )
            sqlite_rows = [sqlite_row_for_record(r) for r in rows]
            if sqlite_rows:
                placeholders = ", ".join("?" for _ in sqlite_rows[0])
                conn.executemany(
                    f"INSERT INTO profiles VALUES ({placeholders})",
                    sqlite_rows,
                )
            try:
                conn.execute("DROP TABLE IF EXISTS profile_fts")
                conn.execute(
                    "CREATE VIRTUAL TABLE profile_fts USING fts5(product_name, manager, search_text, path)"
                )
                conn.executemany(
                    "INSERT INTO profile_fts(product_name, manager, search_text, path) VALUES (?, ?, ?, ?)",
                    [(r.product_name, r.manager, r.search_text, r.path) for r in rows],
                )
            except sqlite3.OperationalError:
                pass
            conn.commit()
        finally:
            conn.close()
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def extract_section(body: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", body, re.MULTILINE)
    if not match:
        return ""
    rest = body[match.end() :]
    next_heading = re.search(r"^##\s+", rest, re.MULTILINE)
    return (rest[: next_heading.start()] if next_heading else rest).strip()


def sqlite_row_for_record(r: ProductProfileRecord) -> tuple:
    return (
        r.product_name,
        r.manager,
        json.dumps(r.strategy_links, ensure_ascii=False),
        json.dumps(r.people_links, ensure_ascii=False),
        json.dumps(r.source_notes, ensure_ascii=False),
        r.profile_text,
        r.evidence_text,
        r.search_text,
        r.path,
        r.updated_at,
        r.entity_type,
        r.entity_confidence,
        json.dumps(r.manager_aliases, ensure_ascii=False),
        json.dumps(r.product_aliases, ensure_ascii=False),
        r.strategy_positioning,
        json.dumps(r.product_line, ensure_ascii=False),
        json.dumps(r.risk_points, ensure_ascii=False),
        r.key_people_summary,
        json.dumps(r.evidence_summary, ensure_ascii=False),
        json.dumps(r.source_files, ensure_ascii=False),
        r.evidence_source_type,
        r.external_evidence_status,
        r.evidence_conflict_status,
        r.source_priority,
        json.dumps(r.external_evidence, ensure_ascii=False),
        json.dumps(r.strategy_raw_terms, ensure_ascii=False),
        json.dumps(r.strategy_evidence, ensure_ascii=False),
        json.dumps(r.primary_strategy_codes, ensure_ascii=False),
        json.dumps(r.primary_strategy_tags, ensure_ascii=False),
        json.dumps(r.secondary_strategy_codes, ensure_ascii=False),
        json.dumps(r.secondary_strategy_tags, ensure_ascii=False),
        json.dumps(r.direct_strategy_tags, ensure_ascii=False),
        json.dumps(r.mentioned_strategy_tags, ensure_ascii=False),
        json.dumps(r.rejected_strategy_tags, ensure_ascii=False),
        json.dumps(r.strategy_facets, ensure_ascii=False),
        json.dumps(r.candidate_strategy_tags, ensure_ascii=False),
        r.strategy_tag_confidence,
        r.strategy_tag_source,
        r.strategy_tag_review_status,
        r.canonical_product_name,
        r.profile_quality_status,
        r.product_name_reason,
        json.dumps(r.review_reasons, ensure_ascii=False),
        r.zm_match_status,
        json.dumps(r.zm_fund_ids, ensure_ascii=False),
        json.dumps(r.zm_fund_codes, ensure_ascii=False),
        json.dumps(r.zm_candidate_matches, ensure_ascii=False),
        json.dumps(r.zm_rejected_candidates, ensure_ascii=False),
    )


def normalize_string_list(values: object) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        values = [values]
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def normalize_facet_dict(values: object) -> dict[str, list[str]]:
    if not isinstance(values, dict):
        return {}
    return {
        str(key).strip(): normalize_string_list(value)
        for key, value in values.items()
        if str(key).strip()
    }


def normalize_dict_list(values: object) -> list[dict]:
    if values is None:
        return []
    if isinstance(values, dict):
        values = [values]
    if not isinstance(values, list):
        return []
    result: list[dict] = []
    for value in values:
        if isinstance(value, dict):
            result.append({str(key): value[key] for key in value if str(key).strip()})
    return result


def normalize_int(value: object, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def record_from_payload(payload: dict) -> ProductProfileRecord:
    defaults = {
        "manager_aliases": [],
        "product_aliases": [],
        "entity_type": "product",
        "entity_confidence": "high",
        "strategy_positioning": "",
        "product_line": [],
        "risk_points": [],
        "key_people_summary": "",
        "evidence_summary": [],
        "source_files": [],
        "evidence_source_type": "internal_due_diligence",
        "external_evidence_status": "not_checked",
        "evidence_conflict_status": "none",
        "source_priority": 10,
        "external_evidence": [],
        "strategy_raw_terms": [],
        "strategy_evidence": [],
        "primary_strategy_codes": [],
        "primary_strategy_tags": [],
        "secondary_strategy_codes": [],
        "secondary_strategy_tags": [],
        "direct_strategy_tags": [],
        "mentioned_strategy_tags": [],
        "rejected_strategy_tags": [],
        "strategy_facets": {},
        "candidate_strategy_tags": [],
        "strategy_tag_confidence": "",
        "strategy_tag_source": "",
        "strategy_tag_review_status": "",
        "canonical_product_name": "",
        "profile_quality_status": "",
        "product_name_reason": "",
        "review_reasons": [],
        "zm_match_status": "",
        "zm_fund_ids": [],
        "zm_fund_codes": [],
        "zm_candidate_matches": [],
        "zm_rejected_candidates": [],
    }
    return ProductProfileRecord(**{**defaults, **payload})
