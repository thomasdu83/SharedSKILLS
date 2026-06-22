"""Build product profiles from source notes."""

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from fund_profile_wiki.config import Settings, ensure_output_dirs
from fund_profile_wiki.profiles.product_profile_compiler import ProductProfileCompiler


def main() -> None:
    parser = argparse.ArgumentParser(description="Build product profile markdown files.")
    parser.add_argument("--source-root", action="append", help="Source note root. Can repeat.")
    parser.add_argument("--output-root", default=str(Settings.product_profiles_dir))
    args = parser.parse_args()
    ensure_output_dirs()
    roots = [Path(p) for p in args.source_root] if args.source_root else [Settings.source_notes_dir]
    written = ProductProfileCompiler().compile_from_roots(roots, Path(args.output_root))
    print(f"Built {len(written)} product profiles")
    print(f"Output: {args.output_root}")


if __name__ == "__main__":
    main()

