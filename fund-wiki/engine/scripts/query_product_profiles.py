"""Query product profiles."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from fund_profile_wiki.config import Settings, ensure_output_dirs  # noqa: E402
from fund_profile_wiki.query.profile_query_engine import execute_profile_query  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Query product profiles.")
    parser.add_argument("query")
    parser.add_argument("--index-jsonl", default=str(Settings.indexes_dir / Settings.product_profile_jsonl))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--context-budget", type=int, default=8000)
    parser.add_argument("--per-result-chars", type=int, default=900)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    ensure_output_dirs()
    execution = execute_profile_query(
        Path(args.index_jsonl),
        args.query,
        limit=args.limit,
        context_budget_chars=args.context_budget,
        per_result_chars=args.per_result_chars,
    )
    output = render_results(args.query, execution)
    print(output)
    if args.write_report:
        report = Settings.reports_dir / f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report.write_text(output, encoding="utf-8")
        print(f"\nReport: {report}")


def render_results(query: str, execution) -> str:
    lines = [
        "# Query Result",
        "",
        f"Query: {query}",
        f"Mode: {execution.intent.mode}",
        f"Recognized manager: {execution.intent.recognized_manager or '未识别'}",
        f"Recognized product: {execution.intent.recognized_product or '未识别'}",
        f"Hard filters: {', '.join(item.label for item in execution.intent.hard_filters) or '无'}",
        f"Context budget: {execution.used_context_chars}/{execution.context_budget_chars} chars, truncated results: {execution.truncated_result_count}",
        "",
    ]
    if execution.grouped_results:
        lines.extend(["## 分组结果", ""])
        for group in execution.grouped_results:
            lines.extend(
                [
                    f"### {group.group_name}",
                    f"- 代表产品: {', '.join(group.representative_products) or '未提及'}",
                    f"- 证据片段: {' | '.join(group.evidence_snippets) or '未提及'}",
                    f"- Profile 文件: {', '.join(f'`{path}`' for path in group.paths) or '无'}",
                    "",
                ]
            )
    lines.extend(["## 候选产品", ""])
    if not execution.results:
        lines.append("No matching product profiles found.")
        return "\n".join(lines)
    for idx, result in enumerate(execution.results, start=1):
        if result.hard_filter_status == "satisfied":
            hard_filter_text = "满足"
        elif result.hard_filter_status == "unsatisfied":
            hard_filter_text = "缺失 " + ", ".join(result.missing_terms)
        else:
            hard_filter_text = "不适用"
        lines.extend(
            [
                f"### {idx}. {result.product_name}",
                f"- 管理人: {result.manager or '未提及'}",
                f"- 实体类型: {result.entity_type}; 置信度: {result.entity_confidence}",
                f"- 画像质量: {result.profile_quality_status or 'unknown'}; 复核原因: {', '.join(result.review_reasons) or '无'}",
                f"- 证据来源: {result.evidence_source_type}; 外部佐证: {result.external_evidence_status}; 冲突状态: {result.evidence_conflict_status}",
                f"- 分数: {result.score:.1f}",
                f"- 命中词: {', '.join(result.matched_terms)}",
                f"- 硬条件: {hard_filter_text}",
                f"- 直接策略标签: {', '.join(result.direct_strategy_tags) or '未提及'}",
                f"- 提及但未直接归属标签: {', '.join(result.mentioned_strategy_tags) or '无'}",
                f"- 被规则剔除标签: {', '.join(result.rejected_strategy_tags) or '无'}",
                f"- 关系命中: {', '.join(result.relation_matches) or '无'}",
                f"- 排序原因: {', '.join(result.ranking_reasons) or '无'}",
                f"- Profile: {result.packed_profile_text or result.profile_text}",
                f"- 证据片段: {result.packed_evidence or result.evidence_snippet}",
                f"- 上下文字符: {result.context_chars}",
                f"- Profile 文件: `{result.path}`",
                "",
            ]
        )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
