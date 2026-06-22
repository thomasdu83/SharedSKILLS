"""Parse raw diligence docs and write source notes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from fund_profile_wiki.config import ensure_output_dirs  # noqa: E402
from fund_profile_wiki.config import Settings  # noqa: E402
from fund_profile_wiki.extraction.source_note_builder import ingest_folder  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest raw diligence documents into source notes."
    )
    parser.add_argument(
        "--input",
        required=True,
        action="append",
        help="Input file/folder containing raw docs. Can be provided multiple times.",
    )
    parser.add_argument("--manager", required=True, help="Manager name hint.")
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM to extract structured source notes.",
    )
    parser.add_argument(
        "--provider", default="kimi", choices=["kimi", "deepseek", "openai"]
    )
    parser.add_argument(
        "--snapshot", default="manifest", choices=["manifest", "none"]
    )
    parser.add_argument("--changed-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--log-path")
    parser.add_argument(
        "--parse-workers", type=int, help="Max workers for parse-stage parallelism."
    )
    parser.add_argument(
        "--ingest-scope",
        default="all",
        choices=["all", "priority"],
        help="Whether to ingest all files or only top-priority files.",
    )
    parser.add_argument(
        "--parsed-cache-root",
        default=str(Settings.parsed_cache_root),
        help="Local parsed-text cache root. This is not a formal docs_root artifact.",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    ensure_output_dirs()
    roots = []
    for item in args.input:
        input_path = Path(item)
        roots.append(input_path.parent if input_path.is_file() else input_path)
    written, counts = ingest_folder(
        roots,
        manager=args.manager,
        use_llm=args.use_llm,
        provider=args.provider,
        snapshot_mode=args.snapshot,
        changed_only=args.changed_only,
        force=args.force,
        run_id=args.run_id,
        log_path=args.log_path,
        parse_workers=args.parse_workers,
        ingest_scope=args.ingest_scope,
        parsed_cache_root=Path(args.parsed_cache_root) if args.parsed_cache_root else None,
    )
    payload = {
        "status": "success" if counts["failed"] == 0 else "partial_success",
        "manager": args.manager,
        "input": str(roots[0]) if len(roots) == 1 else [str(root) for root in roots],
        "inputs": [str(root) for root in roots],
        "input_count": len(roots),
        "written": [str(path) for path in written],
        "parsed_cache_cleaned_by_ingest": False,
        "parsed_cache_cleanup_owner": "deposit_manager",
        "parsed_cache_cleanup_stage": "post_deposit",
        "parsed_cache_cleaned": False,
        **counts,
    }
    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"Ingested {len(written)} source notes")
        print(
            "Files: "
            f"total={counts['files_total']} "
            f"processed={counts['processed']} "
            f"skipped={counts['skipped']} "
            f"failed={counts['failed']} "
            f"source_missing={counts['source_missing']}"
        )
        for path in written:
            print(path)


if __name__ == "__main__":
    main()
