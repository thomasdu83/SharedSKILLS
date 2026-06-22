"""Build product profile indexes."""

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from fund_profile_wiki.config import Settings
from fund_profile_wiki.health.health_check import write_health_check
from fund_profile_wiki.index.profile_index import build_profile_index, load_profile_records
from fund_profile_wiki.index.relation_index import build_relation_index
from fund_profile_wiki.wiki.governance import write_governance_docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build JSONL/SQLite indexes for product profiles.")
    parser.add_argument("--profile-root", default=str(Settings.product_profiles_dir))
    parser.add_argument("--index-dir", default=str(Settings.indexes_dir))
    args = parser.parse_args()
    profile_root = Path(args.profile_root)
    index_dir = Path(args.index_dir)
    docs_root = infer_docs_root(profile_root, index_dir)
    jsonl, sqlite, count = build_profile_index(profile_root, index_dir)
    records = load_profile_records(profile_root)
    relation_jsonl, relation_sqlite, relation_count = build_relation_index(records, index_dir)
    health_report = write_health_check(docs_root, records=records, profile_root=profile_root)
    governance_docs = write_governance_docs(
        docs_root,
        records,
        relation_count=relation_count,
        health_report=health_report,
    )
    print(f"Indexed {count} product profiles")
    print(f"JSONL: {jsonl}")
    print(f"SQLite: {sqlite}")
    print(f"Relations: {relation_count}")
    print(f"Relation JSONL: {relation_jsonl}")
    print(f"Relation SQLite: {relation_sqlite}")
    print(f"Health: {health_report.status} ({health_report.issue_count} issues)")
    print(f"Health report: {docs_root / 'reports' / 'health_check.md'}")
    print(f"Review queue: {docs_root / 'review_queue' / 'open.md'}")
    print(f"Governance docs: {len(governance_docs)}")


def infer_docs_root(profile_root: Path, index_dir: Path) -> Path:
    """Infer the docs root from standard fund-wiki subfolder locations."""
    if index_dir.name == "indexes":
        return index_dir.parent
    if profile_root.name == "product_profiles":
        return profile_root.parent
    return Settings.docs_root


if __name__ == "__main__":
    main()
