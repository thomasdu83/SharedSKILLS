"""Build lightweight relationship indexes from product profile records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import sqlite3
import uuid
from typing import Iterable

from fund_profile_wiki.index.profile_index import ProductProfileRecord
from fund_profile_wiki.notes.diligence_note_reader import extract_wikilink


RELATION_JSONL = "relations.jsonl"
RELATION_SQLITE = "relations.sqlite"


@dataclass(frozen=True)
class RelationRecord:
    subject: str
    predicate: str
    object: str
    manager: str = ""
    product_name: str = ""
    evidence: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: str = "confirmed"
    path: str = ""


def build_relation_index(
    records: Iterable[ProductProfileRecord], index_dir: Path
) -> tuple[Path, Path, int]:
    relation_records = build_relation_records(records)
    index_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = index_dir / RELATION_JSONL
    sqlite_path = index_dir / RELATION_SQLITE
    write_relation_jsonl(relation_records, jsonl_path)
    write_relation_sqlite(relation_records, sqlite_path)
    return jsonl_path, sqlite_path, len(relation_records)


def relation_jsonl_path_for(index_jsonl: Path) -> Path:
    return index_jsonl.with_name(RELATION_JSONL)


def relation_sqlite_path_for(index_jsonl: Path) -> Path:
    return index_jsonl.with_name(RELATION_SQLITE)


def read_relation_jsonl(path: Path) -> list[RelationRecord]:
    if not path.exists():
        return []
    rows: list[RelationRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(relation_from_payload(json.loads(line)))
    return rows


def read_relation_sqlite(
    path: Path,
    product_names: Iterable[str] | None = None,
    predicates: Iterable[str] | None = None,
) -> list[RelationRecord]:
    if not path.exists():
        return []
    product_filter = [str(item) for item in product_names or [] if str(item)]
    predicate_filter = [str(item) for item in predicates or [] if str(item)]
    rows: list[RelationRecord] = []
    with sqlite3.connect(path) as conn:
        if product_filter or predicate_filter:
            product_chunks = list(chunks(product_filter, 500)) if product_filter else [[]]
            predicate_chunks = (
                list(chunks(predicate_filter, 500)) if predicate_filter else [[]]
            )
            for product_chunk in product_chunks:
                for predicate_chunk in predicate_chunks:
                    clauses: list[str] = []
                    params: list[str] = []
                    if product_chunk:
                        placeholders = ", ".join("?" for _ in product_chunk)
                        clauses.append(f"product_name IN ({placeholders})")
                        params.extend(product_chunk)
                    if predicate_chunk:
                        placeholders = ", ".join("?" for _ in predicate_chunk)
                        clauses.append(f"predicate IN ({placeholders})")
                        params.extend(predicate_chunk)
                    where_clause = " AND ".join(clauses)
                    rows.extend(
                        relation_from_sqlite_row(row)
                        for row in conn.execute(
                            f"""
                            SELECT subject, predicate, object, manager, product_name,
                                   evidence, sources, confidence, path
                            FROM relations
                            WHERE {where_clause}
                            """,
                            params,
                        )
                    )
        else:
            rows.extend(
                relation_from_sqlite_row(row)
                for row in conn.execute(
                    """
                    SELECT subject, predicate, object, manager, product_name,
                           evidence, sources, confidence, path
                    FROM relations
                    """
                )
            )
    return rows


def relation_from_sqlite_row(row: tuple) -> RelationRecord:
    return RelationRecord(
        subject=str(row[0] or "").strip(),
        predicate=str(row[1] or "").strip(),
        object=str(row[2] or "").strip(),
        manager=str(row[3] or "").strip(),
        product_name=str(row[4] or "").strip(),
        evidence=json_list(row[5]),
        sources=json_list(row[6]),
        confidence=str(row[7] or "confirmed").strip(),
        path=str(row[8] or "").strip(),
    )


def relation_from_payload(payload: dict) -> RelationRecord:
    return RelationRecord(
        subject=str(payload.get("subject", "") or "").strip(),
        predicate=str(payload.get("predicate", "") or "").strip(),
        object=str(payload.get("object", "") or "").strip(),
        manager=str(payload.get("manager", "") or "").strip(),
        product_name=str(payload.get("product_name", "") or "").strip(),
        evidence=dedupe(payload.get("evidence", []) or []),
        sources=dedupe(payload.get("sources", []) or []),
        confidence=str(payload.get("confidence", "confirmed") or "confirmed").strip(),
        path=str(payload.get("path", "") or "").strip(),
    )


def json_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return dedupe(value)
    try:
        payload = json.loads(str(value))
    except json.JSONDecodeError:
        return dedupe([str(value)])
    if isinstance(payload, list):
        return dedupe(payload)
    return []


def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def build_relation_records(
    records: Iterable[ProductProfileRecord],
) -> list[RelationRecord]:
    relations: list[RelationRecord] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for record in records:
        def add(
            subject: str,
            predicate: str,
            obj: str,
            *,
            evidence: list[str] | None = None,
            confidence: str | None = None,
        ) -> None:
            subject = subject.strip()
            obj = obj.strip()
            if not subject or not obj:
                return
            key = (
                subject,
                predicate,
                obj,
                record.manager,
                record.product_name,
            )
            if key in seen:
                return
            seen.add(key)
            relations.append(
                RelationRecord(
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    manager=record.manager,
                    product_name=record.product_name,
                    evidence=dedupe(evidence or record.evidence_summary[:3]),
                    sources=dedupe(record.source_files + record.source_notes),
                    confidence=confidence or confidence_for(record),
                    path=record.path,
                )
            )

        add(record.manager, "has_product", record.product_name)
        add(record.product_name, "belongs_to_manager", record.manager)
        for alias in record.manager_aliases:
            add(record.manager, "has_manager_alias", alias)
        for alias in record.product_aliases:
            add(record.product_name, "has_product_alias", alias)
        if record.canonical_product_name:
            add(record.product_name, "has_canonical_product_name", record.canonical_product_name)
        for line in record.product_line:
            add(record.product_name, "has_product_line", line)
        for strategy in record.strategy_links:
            add(record.product_name, "has_strategy", extract_wikilink(strategy))
        for tag in record.primary_strategy_tags:
            add(
                record.product_name,
                "has_primary_strategy",
                tag,
                evidence=record.strategy_evidence[:3],
                confidence=record.strategy_tag_confidence or None,
            )
        for tag in record.secondary_strategy_tags:
            add(
                record.product_name,
                "has_secondary_strategy",
                tag,
                evidence=record.strategy_evidence[:3],
                confidence=record.strategy_tag_confidence or None,
            )
        for tag in record.direct_strategy_tags:
            add(
                record.product_name,
                "has_direct_strategy_tag",
                tag,
                evidence=record.strategy_evidence[:3],
                confidence=record.strategy_tag_confidence or "confirmed",
            )
        for tag in record.mentioned_strategy_tags:
            add(
                record.product_name,
                "mentions_strategy_tag",
                tag,
                evidence=record.strategy_evidence[:3],
                confidence="mentioned",
            )
        for tag in record.rejected_strategy_tags:
            add(
                record.product_name,
                "rejects_strategy_tag",
                tag,
                evidence=record.strategy_evidence[:3],
                confidence="rejected",
            )
        for axis, values in record.strategy_facets.items():
            for value in values:
                add(
                    record.product_name,
                    "has_strategy_facet",
                    f"{axis}={value}",
                    evidence=record.strategy_evidence[:3],
                    confidence=record.strategy_tag_confidence or None,
                )
        for tag in record.candidate_strategy_tags:
            add(
                record.product_name,
                "has_candidate_strategy",
                tag,
                evidence=record.strategy_evidence[:3],
                confidence="needs_review",
            )
        for risk in record.risk_points[:5]:
            add(record.product_name, "has_risk_point", risk, evidence=[risk])
        for source_file in record.source_files:
            add(record.product_name, "has_source_file", source_file, evidence=[])
        for source_note in record.source_notes:
            add(record.product_name, "has_source_note", source_note, evidence=[])
        for background in infer_background_tags(record):
            add(record.product_name, "has_people_background", background)
            if record.manager:
                add(record.manager, "has_people_background", background)
        for constraint in infer_exposure_constraints(record):
            add(record.product_name, "has_exposure_constraint", constraint)
    return sorted(
        relations,
        key=lambda item: (
            item.manager,
            item.product_name,
            item.subject,
            item.predicate,
            item.object,
        ),
    )


def write_relation_jsonl(records: Iterable[RelationRecord], path: Path) -> None:
    rows = list(records)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            for record in rows:
                handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_relation_sqlite(records: Iterable[RelationRecord], path: Path) -> None:
    rows = list(records)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        conn = sqlite3.connect(tmp_path)
        try:
            conn.execute(
                """
                CREATE TABLE relations (
                    subject TEXT,
                    predicate TEXT,
                    object TEXT,
                    manager TEXT,
                    product_name TEXT,
                    evidence TEXT,
                    sources TEXT,
                    confidence TEXT,
                    path TEXT
                )
                """
            )
            conn.executemany(
                "INSERT INTO relations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        item.subject,
                        item.predicate,
                        item.object,
                        item.manager,
                        item.product_name,
                        json.dumps(item.evidence, ensure_ascii=False),
                        json.dumps(item.sources, ensure_ascii=False),
                        item.confidence,
                        item.path,
                    )
                    for item in rows
                ],
            )
            conn.execute("CREATE INDEX idx_relations_predicate ON relations(predicate)")
            conn.execute("CREATE INDEX idx_relations_manager ON relations(manager)")
            conn.execute("CREATE INDEX idx_relations_product ON relations(product_name)")
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


def infer_background_tags(record: ProductProfileRecord) -> list[str]:
    text = "\n".join([record.key_people_summary, record.search_text, record.profile_text])
    tags = []
    if "worldquant" in text.lower() or "世坤" in text:
        tags.append("WorldQuant背景")
    if "千禧" in text or "millennium" in text.lower():
        tags.append("Millennium背景")
    if "gsa" in text.lower():
        tags.append("GSA背景")
    return tags


def infer_exposure_constraints(record: ProductProfileRecord) -> list[str]:
    text = "\n".join(
        [
            record.strategy_positioning,
            "\n".join(record.risk_points),
            "\n".join(record.evidence_summary),
            record.search_text,
        ]
    )
    constraints = []
    if "行业" in text and ("3%" in text or "3％" in text) and ("偏离" in text or "暴露" in text):
        constraints.append("行业暴露3%以内")
    if "barra" in text.lower():
        constraints.append("Barra风险约束")
    return constraints


def confidence_for(record: ProductProfileRecord) -> str:
    status = record.profile_quality_status or "confirmed"
    if status == "confirmed":
        return "confirmed"
    if status in {"generic", "inferred", "low_confidence"}:
        return "inferred"
    return status


def dedupe(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result
