#!/usr/bin/env python3
"""Check the runtime environment for the standalone fund-wiki skill."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys
from dataclasses import dataclass

from _env import env_file_candidates, load_env_files
from _paths import (
    PathResolutionError,
    docs_root_candidates,
    raw_root_candidates,
    resolve_docs_root,
    resolve_project_root,
    resolve_raw_root,
)


@dataclass(frozen=True)
class Dependency:
    label: str
    module: str
    required: bool = True


DEPENDENCIES = (
    Dependency("OpenAI SDK", "openai"),
    Dependency("python-dotenv", "dotenv"),
    Dependency("PyYAML", "yaml"),
    Dependency("PyMuPDF", "fitz"),
    Dependency("python-pptx", "pptx"),
    Dependency("python-docx", "docx"),
    Dependency("Pillow", "PIL"),
    Dependency("pytesseract", "pytesseract", required=False),
)

DEFAULT_TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def print_check(label: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "MISSING"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")


def check_tesseract_runtime() -> tuple[bool, str]:
    if not module_available("pytesseract"):
        return False, "pytesseract Python package missing; OCR fallback will be skipped."
    import pytesseract  # pylint: disable=import-outside-toplevel

    command = os.environ.get("FPW_TESSERACT_CMD") or os.environ.get("TESSERACT_CMD") or DEFAULT_TESSERACT_CMD
    if os.path.exists(command):
        pytesseract.pytesseract.tesseract_cmd = command
    elif shutil.which("tesseract"):
        command = shutil.which("tesseract") or "tesseract"
        pytesseract.pytesseract.tesseract_cmd = command
    else:
        return False, f"Tesseract executable missing. Expected {command} or tesseract on PATH."
    try:
        langs = set(pytesseract.get_languages(config=""))
    except Exception as exc:  # pylint: disable=broad-except
        return False, f"Tesseract not usable: {exc}"
    required = {"chi_sim", "eng"}
    missing = sorted(required - langs)
    if missing:
        return False, f"Tesseract language data missing: {', '.join(missing)}"
    return True, command


def main() -> int:
    parser = argparse.ArgumentParser(description="Check standalone fund-wiki skill environment.")
    parser.add_argument("--raw-root")
    parser.add_argument("--docs-root")
    parser.add_argument("--project-root")
    parser.add_argument("--env-file", help="Explicit .env file to load before checks.")
    parser.add_argument("--allow-local-docs-fallback", action="store_true")
    args = parser.parse_args()

    loaded_env_files = load_env_files(args.env_file)

    failures = 0

    print("fund-wiki environment check")
    print(f"Python: {sys.executable}")
    if loaded_env_files:
        print("Loaded .env files:")
        for path in loaded_env_files:
            print(f"- {path}")
    else:
        print("Loaded .env files: none")
        print("Checked .env candidates:")
        for path in env_file_candidates(args.env_file):
            print(f"- {path}")
    print("")

    try:
        project_root = resolve_project_root(args.project_root)
        print_check("skill engine", True, str(project_root))
    except PathResolutionError as exc:
        failures += 1
        print_check("skill engine", False, str(exc).replace("\n", " | "))

    try:
        raw_root = resolve_raw_root(args.raw_root)
        print_check("raw material root", True, str(raw_root))
    except PathResolutionError:
        print_check(
            "raw material root",
            False,
            "候选: " + "; ".join(str(path) for path in raw_root_candidates(args.raw_root)),
        )

    try:
        docs_root = resolve_docs_root(
            args.docs_root,
            allow_local_fallback=args.allow_local_docs_fallback,
            create=False,
            accept_creatable=True,
        )
        print_check("fund_profile_wiki_docs root", True, str(docs_root))
    except PathResolutionError:
        print_check(
            "fund_profile_wiki_docs root",
            False,
            "候选: "
            + "; ".join(
                str(path)
                for path in docs_root_candidates(
                    args.docs_root,
                    allow_local_fallback=args.allow_local_docs_fallback,
                )
            ),
        )

    print("")
    for dep in DEPENDENCIES:
        ok = module_available(dep.module)
        print_check(dep.label, ok, dep.module)
        if dep.required and not ok:
            failures += 1

    ocr_ok, ocr_detail = check_tesseract_runtime()
    print_check("Tesseract OCR runtime", ocr_ok, ocr_detail)
    if not ocr_ok:
        print("Note: deposit can continue without OCR, but scanned PDFs will be recorded as parse warnings.")

    print("")
    llm_keys = {
        "KIMI_API_KEY": bool(os.environ.get("KIMI_API_KEY")),
        "DEEPSEEK_API_KEY": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "OPENAI_API_KEY/CHATGPT_API_KEY": bool(
            os.environ.get("OPENAI_API_KEY") or os.environ.get("CHATGPT_API_KEY")
        ),
    }
    for label, ok in llm_keys.items():
        print_check(label, ok)
    if not any(llm_keys.values()):
        print("Note: no LLM API key found. Query still works, but --use-llm ingest will fail.")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
