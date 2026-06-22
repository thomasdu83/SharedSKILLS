#!/usr/bin/env python3
"""Extract text from PDF pages with range, keyword, and truncation controls.

Output goes to stdout only; no temporary files are ever written.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


def extract_pages_text(pdf_path: str, pages: Sequence[int], max_chars: int) -> None:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in pages:
            if page_num < 1 or page_num > len(pdf.pages):
                print(f"=== Page {page_num} (out of range, total {len(pdf.pages)}) ===")
                continue
            text = pdf.pages[page_num - 1].extract_text() or "(no text)"
            print(f"=== Page {page_num} ===")
            if max_chars and len(text) > max_chars:
                print(text[:max_chars])
            else:
                print(text)
            print()


def find_keyword_pages(pdf_path: str, keyword: str, context: int) -> list[int]:
    import pdfplumber

    matched: set[int] = set()
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if keyword in text:
                for offset in range(-context, context + 1):
                    page_num = i + 1 + offset
                    if 1 <= page_num <= len(pdf.pages):
                        matched.add(page_num)
    return sorted(matched)


def parse_pages(raw: str) -> list[int]:
    parts = raw.split("-", 1)
    if len(parts) == 1:
        return [int(parts[0])]
    start, end = int(parts[0]), int(parts[1])
    if start > end:
        raise ValueError(f"invalid page range: {start}-{end}")
    return list(range(start, end + 1))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract text from PDF pages to stdout."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--pages", help="Page range, e.g. 29-31 or single page 5")
    parser.add_argument("--first", type=int, help="Extract first N pages")
    parser.add_argument(
        "--keyword", help="Search for keyword and extract surrounding pages"
    )
    parser.add_argument(
        "--context-pages",
        type=int,
        default=0,
        help="Number of surrounding pages when using --keyword (default: 0)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=0,
        help="Truncate each page to at most N characters (0 = no limit)",
    )
    args = parser.parse_args()

    pdf_path = args.pdf_path
    if not Path(pdf_path).exists():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    try:
        if args.keyword:
            pages = find_keyword_pages(pdf_path, args.keyword, args.context_pages)
            if not pages:
                print(f"No pages found matching keyword: {args.keyword}")
                return 0
        elif args.pages:
            pages = parse_pages(args.pages)
        elif args.first:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                total = len(pdf.pages)
            pages = list(range(1, min(args.first, total) + 1))
        else:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                total = len(pdf.pages)
            pages = list(range(1, total + 1))

        extract_pages_text(pdf_path, pages, args.max_chars)
    except ValueError as exc:
        print(f"Invalid argument: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - depends on PDF parser internals
        print(
            "PDF extraction failed. The file may be encrypted, damaged, image-only, "
            f"or inaccessible: {exc}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
