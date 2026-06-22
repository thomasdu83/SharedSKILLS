from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from fund_profile_wiki.cache.file_manifest import (
    ManifestRecord,
    append_manifest,
    manifest_path,
    now_iso,
)
from fund_profile_wiki.health.health_check import write_health_check
from fund_profile_wiki.index.profile_index import ProductProfileRecord
from fund_profile_wiki.index.relation_index import (
    build_relation_index,
    build_relation_records,
)
from fund_profile_wiki.wiki.governance import write_governance_docs


def test_relation_index_extracts_query_relevant_relations(tmp_path: Path) -> None:
    records = [sample_record()]

    relations = build_relation_records(records)
    triples = {(item.subject, item.predicate, item.object) for item in relations}

    assert ("上海阿尔法投资有限公司", "has_product", "Alpha中证1000指数增强1号") in triples
    assert ("Alpha中证1000指数增强1号", "has_product_line", "中证1000指增") in triples
    assert ("Alpha中证1000指数增强1号", "has_people_background", "WorldQuant背景") in triples
    assert ("Alpha中证1000指数增强1号", "has_exposure_constraint", "行业暴露3%以内") in triples
    assert ("Alpha中证1000指数增强1号", "has_exposure_constraint", "Barra风险约束") in triples

    jsonl_path, sqlite_path, count = build_relation_index(records, tmp_path / "indexes")

    assert count == len(relations)
    assert jsonl_path.exists()
    assert sqlite_path.exists()
    payloads = [
        json.loads(line)
        for line in jsonl_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(item["predicate"] == "has_people_background" for item in payloads)
    with sqlite3.connect(sqlite_path) as conn:
        sqlite_count = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    assert sqlite_count == count


def test_health_check_flags_source_notes_without_index_records(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    source_dir = docs_root / "source_notes" / "平方和"
    source_dir.mkdir(parents=True)
    (source_dir / "note.md").write_text("# 平方和尽调笔记\n", encoding="utf-8")

    report = write_health_check(
        docs_root,
        records=[],
        profile_root=docs_root / "product_profiles",
    )

    assert report.status == "error"
    assert report.high_count == 1
    assert report.issues[0].kind == "source_notes_without_index_records"
    assert (docs_root / "reports" / "health_check.json").exists()
    assert (docs_root / "reports" / "health_check.md").exists()
    assert (docs_root / "review_queue" / "open.jsonl").exists()


def test_governance_docs_create_global_navigation_and_append_log(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    records = [sample_record()]

    write_governance_docs(docs_root, records, relation_count=10, health_report=None)
    write_governance_docs(docs_root, records, relation_count=11, health_report=None)

    assert (docs_root / "fund_wiki_purpose.md").exists()
    assert (docs_root / "fund_wiki_schema.md").exists()
    assert (docs_root / "index.md").exists()
    assert (docs_root / "overview.md").exists()
    assert (docs_root / "log.md").exists()
    index_text = (docs_root / "index.md").read_text(encoding="utf-8")
    overview_text = (docs_root / "overview.md").read_text(encoding="utf-8")
    log_text = (docs_root / "log.md").read_text(encoding="utf-8")

    assert "上海阿尔法投资有限公司" in index_text
    assert "中证1000指增" in overview_text
    assert "| 1 | 1 | 11 |" in log_text
    assert "| 1 | 1 | 10 |" in log_text


def test_health_check_writes_source_lifecycle_review_queue_without_duplicates(
    tmp_path: Path,
) -> None:
    docs_root = tmp_path / "docs"
    retained_note = docs_root / "retained_note.md"
    retained_note.parent.mkdir(parents=True)
    retained_note.write_text("# retained historical note\n", encoding="utf-8")
    manifest_file = manifest_path(docs_root / "run_logs")
    append_manifest(
        manifest_file,
        [
            ManifestRecord(
                run_id="run-1",
                manager="Alpha",
                source_path=str(tmp_path / "raw" / "missing.pdf"),
                source_relpath="missing.pdf",
                sha256="hash-missing",
                size=123,
                mtime="2026-06-01T00:00:00",
                parsed_at=now_iso(),
                source_note_path=str(retained_note),
                status="source_missing",
                snapshot_mode="manifest",
                snapshot_path="",
                provider="",
                model="",
                parser_version="parser",
                prompt_version="prompt",
                schema_version="schema",
                error="source file no longer exists",
            ),
            ManifestRecord(
                run_id="run-1",
                manager="Alpha",
                source_path=str(tmp_path / "raw" / "encrypted.pdf"),
                source_relpath="encrypted.pdf",
                sha256="hash-failed",
                size=456,
                mtime="2026-06-01T00:00:00",
                parsed_at=now_iso(),
                source_note_path="",
                status="failed",
                snapshot_mode="manifest",
                snapshot_path="",
                provider="",
                model="",
                parser_version="parser",
                prompt_version="prompt",
                schema_version="schema",
                error="encrypted or OCR unavailable",
            ),
        ],
    )

    first_report = write_health_check(
        docs_root,
        records=[],
        profile_root=docs_root / "product_profiles",
    )
    second_report = write_health_check(
        docs_root,
        records=[],
        profile_root=docs_root / "product_profiles",
    )

    assert {issue.kind for issue in first_report.issues} >= {
        "source_missing",
        "source_parse_failed",
    }
    assert {issue.kind for issue in second_report.issues} >= {
        "source_missing",
        "source_parse_failed",
    }
    open_queue = docs_root / "review_queue" / "open.jsonl"
    rows = [
        json.loads(line)
        for line in open_queue.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 2
    assert len({row["item_id"] for row in rows}) == 2


def test_health_check_classifies_expected_strategy_guardrail_as_info(
    tmp_path: Path,
) -> None:
    docs_root = tmp_path / "docs"
    record = sample_record()
    record = ProductProfileRecord(
        **{
            **record.__dict__,
            "rejected_strategy_tags": ["基本面CTA"],
            "primary_strategy_tags": ["指数增强"],
            "secondary_strategy_tags": ["1000指增"],
            "product_line": ["中证1000指增"],
        }
    )

    report = write_health_check(
        docs_root,
        records=[record],
        profile_root=docs_root / "product_profiles",
    )

    kinds = {issue.kind: issue.severity for issue in report.issues}
    assert kinds["strategy_tag_rejected_expected"] == "info"
    assert report.warning_count == 0
    queue_rows = [
        json.loads(line)
        for line in (docs_root / "review_queue" / "open.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert queue_rows == []


def test_health_check_classifies_zm_cross_manager_candidates(
    tmp_path: Path,
) -> None:
    docs_root = tmp_path / "docs"
    normal = ProductProfileRecord(
        **{
            **sample_record().__dict__,
            "product_name": "半鞅CTA均衡1号",
            "manager": "海南半鞅私募基金管理合伙企业（有限合伙）",
            "zm_match_status": "cross_manager_candidates_only",
            "zm_rejected_candidates": [
                "fundID=944407 | fundName=半鞅CTA进取1号 | manager=上海半鞅私募基金管理合伙企业（有限合伙）"
            ],
        }
    )
    suspicious = ProductProfileRecord(
        **{
            **sample_record().__dict__,
            "product_name": "Alpha CTA 1号",
            "manager": "上海阿尔法投资有限公司",
            "path": str(tmp_path / "Alpha CTA 1号.md"),
            "zm_match_status": "cross_manager_candidates_only",
            "zm_rejected_candidates": [
                "fundID=1 | fundName=Alpha CTA 1号 | manager=深圳贝塔资产管理有限公司"
            ],
        }
    )

    report = write_health_check(
        docs_root,
        records=[normal, suspicious],
        profile_root=docs_root / "product_profiles",
    )

    issues = {(issue.product_name, issue.kind): issue.severity for issue in report.issues}
    assert issues[("半鞅CTA均衡1号", "zm_cross_manager_candidates_normal")] == "info"
    assert issues[("Alpha CTA 1号", "zm_cross_manager_candidates_suspicious")] == "warning"


def test_health_check_flags_low_tier_external_only_evidence(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    record = ProductProfileRecord(
        **{
            **sample_record().__dict__,
            "evidence_source_type": "search_discovery_only",
            "external_evidence_status": "external_only",
            "external_evidence": [
                {
                    "url": "https://example.com/fund",
                    "title": "third party fund page",
                    "source_tier": "third_party_public",
                    "claim": "Alpha CTA 1号 belongs to Alpha",
                }
            ],
        }
    )

    report = write_health_check(
        docs_root,
        records=[record],
        profile_root=docs_root / "product_profiles",
    )

    kinds = {issue.kind: issue.severity for issue in report.issues}
    assert kinds["external_evidence_only"] == "warning"
    assert kinds["external_evidence_low_tier"] == "warning"


def test_health_check_flags_source_note_product_schema_missing_fields(
    tmp_path: Path,
) -> None:
    docs_root = tmp_path / "docs"
    note_dir = docs_root / "source_notes" / "Alpha"
    note_dir.mkdir(parents=True)
    (note_dir / "note.md").write_text(
        """---
entity_type: "Manager"
primary_entity: "[[Alpha]]"
source_file: "alpha.pdf"
tags: [Source/Diligence]
---

<!-- system: mentioned_products_json (do not edit manually) -->
```json
[
  {"name": "[[Alpha Fund]]", "entity_type": "product"}
]
```
""",
        encoding="utf-8",
    )
    record = ProductProfileRecord(
        **{
            **sample_record().__dict__,
            "manager": "Alpha",
            "product_name": "Alpha Fund",
        }
    )

    report = write_health_check(
        docs_root,
        records=[record],
        profile_root=docs_root / "product_profiles",
    )

    kinds = {issue.kind: issue.severity for issue in report.issues}
    assert kinds["source_note_product_schema_missing_fields"] == "warning"
    queue_rows = [
        json.loads(line)
        for line in (docs_root / "review_queue" / "open.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert any(
        row["kind"] == "source_note_product_schema_missing_fields"
        for row in queue_rows
    )


def test_review_queue_overrides_suppress_confirmed_items(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    queue_dir = docs_root / "review_queue"
    queue_dir.mkdir(parents=True)
    record = ProductProfileRecord(
        **{
            **sample_record().__dict__,
            "profile_quality_status": "needs_review",
            "product_name_reason": "suspicious_short_name",
        }
    )
    (queue_dir / "overrides.yaml").write_text(
        """
overrides:
  - kind: profile_quality_short_name
    manager: 上海阿尔法投资有限公司
    product_name: Alpha中证1000指数增强1号
    status: confirmed
    note: 人工确认该短名产品有效
""",
        encoding="utf-8",
    )

    report = write_health_check(
        docs_root,
        records=[record],
        profile_root=docs_root / "product_profiles",
    )

    assert any(issue.kind == "profile_quality_short_name" for issue in report.issues)
    queue_rows = [
        json.loads(line)
        for line in (queue_dir / "open.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert queue_rows == []


def test_build_profile_index_script_writes_relation_health_and_governance_docs(
    tmp_path: Path,
) -> None:
    docs_root = tmp_path / "docs"
    profile_root = docs_root / "product_profiles"
    index_dir = docs_root / "indexes"
    profile_root.mkdir(parents=True)
    (profile_root / "alpha.md").write_text(product_profile_markdown(), encoding="utf-8")

    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "scripts" / "build_profile_index.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--profile-root",
            str(profile_root),
            "--index-dir",
            str(index_dir),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )

    assert "Indexed 1 product profiles" in completed.stdout
    assert "Relations:" in completed.stdout
    assert "Health:" in completed.stdout
    assert "Review queue:" in completed.stdout
    assert (index_dir / "product_profiles.jsonl").exists()
    assert (index_dir / "product_profiles.sqlite").exists()
    assert (index_dir / "relations.jsonl").exists()
    assert (index_dir / "relations.sqlite").exists()
    assert (docs_root / "reports" / "health_check.json").exists()
    assert (docs_root / "review_queue" / "open.jsonl").exists()
    assert (docs_root / "fund_wiki_schema.md").exists()
    assert (docs_root / "index.md").exists()


def sample_record() -> ProductProfileRecord:
    return ProductProfileRecord(
        product_name="Alpha中证1000指数增强1号",
        manager="上海阿尔法投资有限公司",
        strategy_links=["[[中证1000指数增强]]", "[[指数增强]]"],
        people_links=["[[张三]]"],
        source_notes=["Y:\\投顾管理人研究\\fund_profile_wiki_docs\\source_notes\\阿尔法\\alpha.md"],
        profile_text="Alpha中证1000指数增强1号是上海阿尔法投资有限公司旗下产品，投资经理曾任 WorldQuant。",
        evidence_text="策略定位: 中证1000指数增强，行业偏离≤±3%，组合使用 Barra 风险模型。",
        search_text="Alpha 中证1000 指数增强 WorldQuant 行业偏离≤±3% Barra",
        path="Y:\\投顾管理人研究\\fund_profile_wiki_docs\\product_profiles\\Alpha中证1000指数增强1号.md",
        updated_at="2026-06-03",
        manager_aliases=["阿尔法"],
        product_aliases=["Alpha 1000指增"],
        strategy_positioning="产品线：中证1000指增；代表证据：行业偏离≤±3%。",
        product_line=["中证1000指增", "指数增强"],
        risk_points=["行业偏离≤±3%，组合使用 Barra 风险模型。"],
        key_people_summary="投资经理曾任 WorldQuant，负责量化选股模型研发。",
        evidence_summary=[
            "策略定位: 中证1000指数增强，行业偏离≤±3%，组合使用 Barra 风险模型。",
            "投资经理曾任 WorldQuant。",
        ],
        source_files=["alpha.md"],
        canonical_product_name="Alpha中证1000指数增强1号",
        profile_quality_status="confirmed",
        product_name_reason="product_specific",
    )


def product_profile_markdown() -> str:
    return """---
profile_type: ProductProfile
product_name: "[[Alpha中证1000指数增强1号]]"
manager: "[[上海阿尔法投资有限公司]]"
strategy_links: ["[[中证1000指数增强]]", "[[指数增强]]"]
people_links: ["[[张三]]"]
source_notes: ["Y:\\\\投顾管理人研究\\\\fund_profile_wiki_docs\\\\source_notes\\\\阿尔法\\\\alpha.md"]
manager_aliases: ["阿尔法"]
product_aliases: ["Alpha 1000指增"]
strategy_positioning: "产品线：中证1000指增；代表证据：行业偏离≤±3%。"
product_line: ["中证1000指增", "指数增强"]
risk_points: ["行业偏离≤±3%，组合使用 Barra 风险模型。"]
key_people_summary: "投资经理曾任 WorldQuant，负责量化选股模型研发。"
evidence_summary: ["策略定位: 中证1000指数增强，行业偏离≤±3%，组合使用 Barra 风险模型。"]
source_files: ["alpha.md"]
canonical_product_name: "Alpha中证1000指数增强1号"
profile_quality_status: "confirmed"
product_name_reason: "product_specific"
updated_at: "2026-06-03"
tags: [Profile/Product]
---

# Alpha中证1000指数增强1号

## LLM Profile
Alpha中证1000指数增强1号是上海阿尔法投资有限公司旗下产品，投资经理曾任 WorldQuant。

## Evidence
- 策略定位: 中证1000指数增强，行业偏离≤±3%，组合使用 Barra 风险模型。
"""
