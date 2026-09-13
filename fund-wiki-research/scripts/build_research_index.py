#!/usr/bin/env python3
"""Build the fund-wiki research index through an explicit backend.

The research index implementation belongs to the fund-wiki project.  This
wrapper keeps the SharedSKILLS entry point stable and refuses to guess a
missing backend instead of letting a weaker model run a non-existent path.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SHARED_ROOT = SKILL_ROOT.parent


def _unique(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).casefold()
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def backend_candidates(project_root: str | None) -> list[Path]:
    """Return backend candidates in explicit-to-conventional order."""
    candidates: list[Path] = []
    explicit_script = os.environ.get("FPW_RESEARCH_INDEX_SCRIPT")
    if explicit_script:
        candidates.append(Path(explicit_script))

    roots: list[Path] = []
    if project_root:
        roots.append(Path(project_root))
    for env_name in ("FPW_PROJECT_ROOT", "FUND_PROFILE_WIKI_PROJECT_ROOT"):
        value = os.environ.get(env_name)
        if value:
            roots.append(Path(value))

    # The usual standalone project layouts.
    for root in roots:
        # Prefer the implementation under engine/.  A project-level
        # scripts/build_research_index.py may itself be a convenience wrapper
        # with a different CLI, which would otherwise recurse into this
        # wrapper and reject --research-root/--index-dir.
        candidates.extend(
            [root / "engine" / "scripts" / "build_research_index.py",
             root / "scripts" / "build_research_index.py"]
        )

    # A sibling QuantSystem checkout is an optional external dependency.  It
    # is discovered only when present; it is never silently required.
    sibling_quant = SHARED_ROOT.parent / "QuantSystem"
    candidates.extend(
        [sibling_quant / ".trae" / "skills" / "fund-wiki" / "engine" / "scripts" / "build_research_index.py",
         sibling_quant / ".trae" / "skills" / "fund-wiki" / "scripts" / "build_research_index.py"]
    )

    # A future self-contained fund-wiki package may add the implementation.
    candidates.extend(
        [SHARED_ROOT / "fund-wiki" / "scripts" / "build_research_index.py",
         SHARED_ROOT / "fund-wiki" / "engine" / "scripts" / "build_research_index.py"]
    )
    return _unique(candidates)


def resolve_backend(project_root: str | None) -> tuple[Path | None, list[Path]]:
    candidates = backend_candidates(project_root)
    for candidate in candidates:
        try:
            if candidate.is_file() and candidate.resolve() != Path(__file__).resolve():
                return candidate, candidates
        except OSError:
            continue
    return None, candidates


def resolve_docs_root(explicit: str | None, allow_local_fallback: bool) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    for env_name in ("FPW_DOCS_ROOT", "FUND_PROFILE_WIKI_DOCS_ROOT"):
        value = os.environ.get(env_name)
        if value:
            candidates.append(Path(value))
    candidates.extend(
        [Path(r"Y:\投顾管理人研究\fund_profile_wiki_docs"),
         Path(r"\\10.168.20.10\资产-投资研究\投顾管理人研究\fund_profile_wiki_docs")]
    )
    if allow_local_fallback:
        local_appdata = os.environ.get("LOCALAPPDATA")
        candidates.append(
            Path(local_appdata) / "QuantSystem" / "fund-wiki" / "fund_profile_wiki_docs"
            if local_appdata
            else SKILL_ROOT / ".local" / "fund_profile_wiki_docs"
        )

    for candidate in _unique(candidates):
        try:
            if candidate.is_dir():
                return candidate
            if allow_local_fallback and candidate.parent.is_dir():
                candidate.mkdir(parents=True, exist_ok=True)
                return candidate
        except OSError:
            continue
    raise RuntimeError(
        "未找到 fund_profile_wiki_docs。请显式传入 --docs-root，或使用 "
        "--allow-local-docs-fallback；不会自动猜测输出目录。"
    )


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build fund-wiki research indexes through the configured backend.")
    parser.add_argument("--docs-root", help="fund_profile_wiki_docs root")
    parser.add_argument("--project-root", help="fund-wiki project root containing the backend")
    parser.add_argument("--env-file", help="Reserved for compatibility; load it before invoking this wrapper")
    parser.add_argument("--python", default=sys.executable or "python", help="Python executable used for the backend")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--allow-local-docs-fallback", action="store_true")
    args = parser.parse_args(argv)

    # Do not print or parse secrets.  Loading a dotenv file is intentionally
    # conservative and only supports simple KEY=VALUE lines.
    if args.env_file:
        env_file = Path(args.env_file)
        if not env_file.is_file():
            return emit_error(args.json_output, "env_file", f"env 文件不存在：{env_file}")
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

    backend, candidates = resolve_backend(args.project_root)
    if backend is None:
        return emit_error(
            args.json_output,
            "backend_resolve",
            "未找到 build_research_index.py 后端。请通过 --project-root 或 FPW_RESEARCH_INDEX_SCRIPT 显式指定。",
            candidates=[str(path) for path in candidates],
        )

    try:
        docs_root = resolve_docs_root(args.docs_root, args.allow_local_docs_fallback)
    except RuntimeError as exc:
        return emit_error(args.json_output, "path_resolve", str(exc))

    research_root = docs_root / "research"
    index_dir = docs_root / "indexes"
    env = os.environ.copy()
    env.update({"FPW_DOCS_ROOT": str(docs_root), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    command = [args.python, str(backend), "--research-root", str(research_root), "--index-dir", str(index_dir)]
    try:
        completed = subprocess.run(
            command,
            cwd=str(backend.parent.parent),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return emit_error(args.json_output, "backend_exec", str(exc), backend=str(backend))

    # Older fund-wiki engine snapshots expose the index function but omit the
    # Settings.research_* attributes expected by their CLI module.  Retry via
    # a small compatibility shim in the wrapper process; this keeps the
    # external project untouched while preserving one stable SharedSKILLS
    # entry point.  Other failures are returned unchanged.
    if completed.returncode != 0 and "has no attribute 'research_dir'" in completed.stderr:
        engine_src = backend.parent.parent / "src"
        shim = (
            "import sys; from pathlib import Path; "
            "sys.path.insert(0, sys.argv[1]); "
            "from fund_profile_wiki.config import Settings; "
            "Settings.research_dir=Path(sys.argv[2]); "
            "Settings.indexes_dir=Path(sys.argv[3]); "
            "Settings.research_notes_jsonl='research_notes.jsonl'; "
            "Settings.research_notes_sqlite='research_notes.sqlite'; "
            "from fund_profile_wiki.index.research_index import build_research_index; "
            "j,s,c=build_research_index(Path(sys.argv[2]), Path(sys.argv[3])); "
            "print(f'Indexed {c} research notes'); print(f'JSONL: {j}'); print(f'SQLite: {s}')"
        )
        try:
            completed = subprocess.run(
                [args.python, "-c", shim, str(engine_src), str(research_root), str(index_dir)],
                cwd=str(engine_src.parent),
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            return emit_error(args.json_output, "backend_compat_exec", str(exc), backend=str(backend))

    if completed.returncode != 0:
        return emit_error(
            args.json_output,
            "build_research_index",
            completed.stderr or completed.stdout or f"后端退出码 {completed.returncode}",
            backend=str(backend),
            returncode=completed.returncode,
        )

    payload = {
        "status": "success",
        "stage": "build_research_index",
        "backend": str(backend),
        "docs_root": str(docs_root),
        "research_root": str(research_root),
        "index_jsonl": str(index_dir / "research_notes.jsonl"),
        "index_sqlite": str(index_dir / "research_notes.sqlite"),
        "research_note_count": count_jsonl(index_dir / "research_notes.jsonl"),
        "stdout": completed.stdout,
    }
    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif completed.stdout:
        print(completed.stdout.rstrip())
    return 0


def emit_error(json_output: bool, stage: str, error: str, **extra: object) -> int:
    payload = {"status": "error", "stage": stage, "error": error, **extra}
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(error, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
