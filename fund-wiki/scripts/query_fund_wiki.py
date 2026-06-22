#!/usr/bin/env python3
"""Query fund_profile_wiki from the Trae fund-wiki skill."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from _env import load_env_files
from _paths import PathResolutionError, default_python, resolve_docs_root, resolve_project_root


def run_command(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def ensure_index(project_root: Path, docs_root: Path, python_exe: str, env: dict[str, str]) -> Path:
    index_jsonl = docs_root / "indexes" / "product_profiles.jsonl"
    if index_jsonl.exists():
        return index_jsonl

    profile_root = docs_root / "product_profiles"
    if not profile_root.exists() or not any(profile_root.rglob("*.md")):
        raise RuntimeError(
            "未找到 product_profiles，无法查询。请先运行 deposit_manager.py 沉淀管理人尽调材料。"
        )

    command = [python_exe, "scripts\\build_profile_index.py"]
    completed = run_command(command, cwd=project_root, env=env)
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"索引重建失败，退出码 {completed.returncode}")
    if not index_jsonl.exists():
        raise RuntimeError(f"索引重建后仍未找到: {index_jsonl}")
    return index_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description="Query fund-wiki product profiles.")
    parser.add_argument("query", help="Natural-language query.")
    parser.add_argument("--docs-root", help="Explicit fund_profile_wiki_docs root.")
    parser.add_argument("--project-root", help="Explicit fund_profile_wiki project root.")
    parser.add_argument("--env-file", help="Explicit .env file to load before querying.")
    parser.add_argument("--python", default=default_python(), help="Python executable for fund_profile_wiki scripts.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--context-budget", type=int, default=8000)
    parser.add_argument("--per-result-chars", type=int, default=900)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--rebuild-index", action="store_true")
    parser.add_argument("--allow-local-docs-fallback", action="store_true")
    args = parser.parse_args()
    load_env_files(args.env_file)

    try:
        project_root = resolve_project_root(args.project_root)
        docs_root = resolve_docs_root(
            args.docs_root,
            allow_local_fallback=args.allow_local_docs_fallback,
            create=False,
        )
    except PathResolutionError as exc:
        if args.json_output:
            print(json.dumps({"status": "error", "stage": "path_resolve", "query": args.query, "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(str(exc), file=sys.stderr)
        return 2

    env = os.environ.copy()
    env["FPW_DOCS_ROOT"] = str(docs_root)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        index_jsonl = docs_root / "indexes" / "product_profiles.jsonl"
        if args.rebuild_index and (docs_root / "product_profiles").exists():
            completed = run_command([args.python, "scripts\\build_profile_index.py"], cwd=project_root, env=env)
            if completed.stdout:
                print(completed.stdout.rstrip())
            if completed.stderr:
                print(completed.stderr.rstrip(), file=sys.stderr)
            if completed.returncode != 0:
                raise RuntimeError(f"索引重建失败，退出码 {completed.returncode}")
        index_jsonl = ensure_index(project_root, docs_root, args.python, env)
    except RuntimeError as exc:
        if args.json_output:
            print(json.dumps({"status": "error", "stage": "index", "query": args.query, "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.json_output:
        sys.path.insert(0, str(project_root / "src"))
        from fund_profile_wiki.query.profile_query_engine import execute_profile_query

        execution = execute_profile_query(
            index_jsonl,
            args.query,
            limit=args.limit,
            context_budget_chars=args.context_budget,
            per_result_chars=args.per_result_chars,
        )
        payload = {
            "status": "success",
            "stage": "query",
            "query": args.query,
            "query_path": "query_fund_wiki.py",
            "docs_root": str(docs_root),
            "index_jsonl": str(index_jsonl),
            "relations_jsonl": str(index_jsonl.with_name("relations.jsonl")),
            "limit": args.limit,
            "context_budget_chars": execution.context_budget_chars,
            "used_context_chars": execution.used_context_chars,
            "truncated_result_count": execution.truncated_result_count,
            "intent_mode": execution.intent.mode,
            "recognized_manager": execution.intent.recognized_manager,
            "recognized_product": execution.intent.recognized_product,
            "normalized_conditions": execution.intent.normalized_conditions,
            "hard_filters": [item.label for item in execution.intent.hard_filters],
            "grouped_results": [
                {
                    "group_name": group.group_name,
                    "representative_products": group.representative_products,
                    "evidence_snippets": group.evidence_snippets,
                    "paths": group.paths,
                }
                for group in execution.grouped_results
            ],
            "manager_results": [
                {
                    "rank": idx,
                    "manager": result.manager,
                    "score": result.score,
                    "matched_products": result.matched_products,
                    "representative_products": result.representative_products,
                    "matched_strategy_tags": result.matched_strategy_tags,
                    "evidence_snippets": result.evidence_snippets,
                    "paths": result.paths,
                    "confidence": result.confidence,
                    "review_flags": result.review_flags,
                }
                for idx, result in enumerate(execution.manager_results, start=1)
            ],
            "results": [
                {
                    "rank": idx,
                    "product_name": result.product_name,
                    "manager": result.manager,
                    "score": result.score,
                    "matched_terms": result.matched_terms,
                    "missing_terms": result.missing_terms,
                    "hard_filter_satisfied": result.hard_filter_satisfied,
                    "hard_filter_status": result.hard_filter_status,
                    "profile_text": result.profile_text,
                    "evidence_snippet": result.evidence_snippet,
                    "relation_matches": result.relation_matches,
                    "ranking_reasons": result.ranking_reasons,
                    "packed_profile_text": result.packed_profile_text,
                    "packed_evidence": result.packed_evidence,
                    "context_chars": result.context_chars,
                    "path": result.path,
                    "entity_type": result.entity_type,
                    "entity_confidence": result.entity_confidence,
                    "canonical_product_name": result.canonical_product_name,
                    "profile_quality_status": result.profile_quality_status,
                    "review_reasons": result.review_reasons,
                    "evidence_source_type": result.evidence_source_type,
                    "external_evidence_status": result.external_evidence_status,
                    "evidence_conflict_status": result.evidence_conflict_status,
                    "source_priority": result.source_priority,
                    "external_evidence": result.external_evidence,
                    "primary_strategy_tags": result.primary_strategy_tags,
                    "secondary_strategy_tags": result.secondary_strategy_tags,
                    "direct_strategy_tags": result.direct_strategy_tags,
                    "mentioned_strategy_tags": result.mentioned_strategy_tags,
                    "rejected_strategy_tags": result.rejected_strategy_tags,
                    "strategy_facets": result.strategy_facets,
                    "strategy_tag_confidence": result.strategy_tag_confidence,
                    "strategy_tag_review_status": result.strategy_tag_review_status,
                }
                for idx, result in enumerate(execution.results, start=1)
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    command = [
        args.python,
        "scripts\\query_product_profiles.py",
        args.query,
        "--index-jsonl",
        str(index_jsonl),
        "--limit",
        str(args.limit),
    ]
    command.extend(["--context-budget", str(args.context_budget)])
    command.extend(["--per-result-chars", str(args.per_result_chars)])
    if args.write_report:
        command.append("--write-report")

    completed = run_command(command, cwd=project_root, env=env)
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
