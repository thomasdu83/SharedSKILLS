#!/usr/bin/env python3
"""First-run initialization and environment self-check for the fund-wiki skill."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from _env import env_file_candidates, load_env_files
from _paths import (
    DOCS_ROOT_ENVS,
    RAW_ROOT_ENVS,
    SKILL_ROOT,
    PathResolutionError,
    default_python,
    resolve_docs_root,
    resolve_project_root,
    resolve_raw_root,
)
from check_environment import DEPENDENCIES, check_tesseract_runtime, module_available


SUPPORTED_PROVIDERS = ("deepseek", "openai", "kimi", "auto")
MANAGED_ENV_KEYS = (
    "FPW_DEFAULT_PROVIDER",
    "FPW_DOCS_ROOT",
    "FPW_RAW_ROOT",
    "FPW_TESSERACT_CMD",
    "FPW_ALLOW_LOCAL_DOCS_FALLBACK",
)


def _item(
    level: str,
    code: str,
    title: str,
    detail: str,
    *,
    affects: list[str] | None = None,
    suggested_action: str = "",
) -> dict[str, Any]:
    return {
        "level": level,
        "code": code,
        "title": title,
        "detail": detail,
        "affects": affects or [],
        "suggested_action": suggested_action,
    }


def provider_key_status() -> dict[str, bool]:
    return {
        "deepseek": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "openai": bool(
            os.environ.get("OPENAI_API_KEY") or os.environ.get("CHATGPT_API_KEY")
        ),
        "kimi": bool(os.environ.get("KIMI_API_KEY")),
    }


def recommended_provider() -> str:
    configured = os.environ.get("FPW_DEFAULT_PROVIDER", "").strip().lower()
    keys = provider_key_status()
    if configured in keys and keys[configured]:
        return configured
    for provider in ("deepseek", "openai", "kimi"):
        if keys[provider]:
            return provider
    if configured in SUPPORTED_PROVIDERS:
        return configured
    return "deepseek"


def env_candidates_payload(explicit: str | None = None) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    explicit_path = Path(explicit).resolve() if explicit else None
    for path in env_file_candidates(explicit):
        resolved = path.resolve()
        payload.append(
            {
                "path": str(resolved),
                "exists": resolved.exists() and resolved.is_file(),
                "selected_by_user": explicit_path is not None
                and resolved == explicit_path,
            }
        )
    return payload


def dependency_payload() -> list[dict[str, Any]]:
    return [
        {
            "label": dep.label,
            "module": dep.module,
            "required": dep.required,
            "ok": module_available(dep.module),
        }
        for dep in DEPENDENCIES
    ]


def path_status(
    resolver,
    *,
    explicit: str | None = None,
    allow_local_docs_fallback: bool = False,
    create: bool = False,
    accept_creatable: bool = False,
) -> dict[str, Any]:
    try:
        if resolver is resolve_docs_root:
            path = resolver(
                explicit,
                allow_local_fallback=allow_local_docs_fallback,
                create=create,
                accept_creatable=accept_creatable,
            )
        else:
            path = resolver(explicit)
        return {
            "ok": True,
            "path": str(path),
            "exists": path.exists(),
            "is_dir": path.is_dir(),
        }
    except PathResolutionError as exc:
        return {
            "ok": False,
            "path": "",
            "exists": False,
            "is_dir": False,
            "error": str(exc),
        }


def docs_content_status(docs_root: Path | None) -> dict[str, Any]:
    if docs_root is None:
        return {
            "source_notes_exists": False,
            "product_profiles_exists": False,
            "product_profile_count": 0,
            "index_jsonl_exists": False,
            "query_data_ready": False,
        }
    product_profiles_dir = docs_root / "product_profiles"
    profile_count = 0
    if product_profiles_dir.exists():
        try:
            profile_count = sum(1 for _ in product_profiles_dir.rglob("*.md"))
        except OSError:
            profile_count = 0
    index_jsonl = docs_root / "indexes" / "product_profiles.jsonl"
    source_notes_dir = docs_root / "source_notes"
    return {
        "source_notes_exists": source_notes_dir.exists(),
        "product_profiles_exists": product_profiles_dir.exists(),
        "product_profile_count": profile_count,
        "index_jsonl_exists": index_jsonl.exists(),
        "query_data_ready": index_jsonl.exists() or profile_count > 0,
    }


def build_report(args) -> dict[str, Any]:
    loaded_env_files = load_env_files(args.env_file)
    project = path_status(resolve_project_root, explicit=args.project_root)
    raw = path_status(resolve_raw_root, explicit=args.raw_root)
    docs = path_status(
        resolve_docs_root,
        explicit=args.docs_root,
        allow_local_docs_fallback=args.allow_local_docs_fallback,
        create=False,
        accept_creatable=True,
    )
    docs_root = Path(docs["path"]) if docs.get("ok") and docs.get("path") else None
    docs_content = docs_content_status(docs_root)
    dependencies = dependency_payload()
    missing_required_modules = [
        item["module"] for item in dependencies if item["required"] and not item["ok"]
    ]
    ocr_ok, ocr_detail = check_tesseract_runtime()
    provider_keys = provider_key_status()
    provider = recommended_provider()

    blocking_items: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    info_items: list[dict[str, Any]] = []
    actions_requiring_user_confirmation: list[dict[str, Any]] = []
    suggested_config_writes: list[dict[str, Any]] = []

    if not project["ok"]:
        blocking_items.append(
            _item(
                "blocking",
                "project_root_missing",
                "未找到 skill engine",
                project["error"],
                affects=["query", "deposit", "deposit_with_llm"],
                suggested_action="确认 skill 目录完整，或通过 --project-root / FPW_PROJECT_ROOT 指向 bundled engine。",
            )
        )
    else:
        info_items.append(
            _item(
                "info",
                "project_root_resolved",
                "已定位 skill engine",
                project["path"],
            )
        )

    if not raw["ok"]:
        blocking_items.append(
            _item(
                "blocking",
                "raw_root_missing",
                "未找到尽调材料根目录",
                raw["error"],
                affects=["deposit", "deposit_with_llm"],
                suggested_action="确认 W:/Z: 网盘或 UNC 路径可达，必要时通过 --raw-root 或 FPW_RAW_ROOT 指定。",
            )
        )
        actions_requiring_user_confirmation.append(
            _item(
                "confirm",
                "confirm_raw_root",
                "需要用户确认尽调材料根目录",
                "首次使用前需要确认当前机器能访问哪一个原始材料根目录。",
            )
        )
    else:
        info_items.append(
            _item("info", "raw_root_resolved", "已定位尽调材料根目录", raw["path"])
        )
        if RAW_ROOT_ENVS[0] not in os.environ:
            suggested_config_writes.append(
                _item(
                    "suggestion",
                    "write_raw_root",
                    "建议写入默认原始材料根目录",
                    raw["path"],
                )
            )

    if not docs["ok"]:
        blocking_items.append(
            _item(
                "blocking",
                "docs_root_missing",
                "未找到输出目录",
                docs["error"],
                affects=["query", "deposit", "deposit_with_llm"],
                suggested_action="确认 Y: 共享目录可达，或通过 --docs-root / FPW_DOCS_ROOT 指定。",
            )
        )
        actions_requiring_user_confirmation.append(
            _item(
                "confirm",
                "confirm_docs_root",
                "需要用户确认输出目录",
                "首次使用前需要确认是使用共享 docs root 还是启用本地 fallback。",
            )
        )
    else:
        info_items.append(
            _item("info", "docs_root_resolved", "已定位输出目录", docs["path"])
        )
        if not docs["exists"]:
            warnings.append(
                _item(
                    "warning",
                    "docs_root_creatable",
                    "输出目录尚未创建",
                    f"当前候选目录尚不存在，但其父目录可用，后续首次沉淀时可自动创建：{docs['path']}",
                    affects=["query", "deposit", "deposit_with_llm"],
                )
            )
        if DOCS_ROOT_ENVS[0] not in os.environ:
            suggested_config_writes.append(
                _item(
                    "suggestion",
                    "write_docs_root",
                    "建议写入默认输出目录",
                    docs["path"],
                )
            )

    if missing_required_modules:
        blocking_items.append(
            _item(
                "blocking",
                "python_dependencies_missing",
                "缺少 Python 依赖",
                ", ".join(missing_required_modules),
                affects=["deposit", "deposit_with_llm"],
                suggested_action="安装 requirements.txt 中的依赖后再进行首次沉淀。",
            )
        )

    if not ocr_ok:
        warnings.append(
            _item(
                "warning",
                "ocr_unavailable",
                "OCR 未就绪",
                ocr_detail,
                affects=["deposit", "deposit_with_llm"],
                suggested_action="若需要处理扫描版 PDF，再补充 pytesseract、Tesseract 和 chi_sim/eng 语言包。",
            )
        )
        actions_requiring_user_confirmation.append(
            _item(
                "confirm",
                "confirm_ocr_needed",
                "需要确认是否必须启用 OCR",
                "若只处理可直接抽取文本的材料，可先跳过 OCR 配置。",
            )
        )
    else:
        info_items.append(_item("info", "ocr_ready", "OCR 已就绪", ocr_detail))

    if not any(provider_keys.values()):
        warnings.append(
            _item(
                "warning",
                "llm_api_key_missing",
                "未发现 LLM API Key",
                "当前仍可完成环境检查和非 LLM 流程，但 `--use-llm` 沉淀不可用。",
                affects=["deposit_with_llm"],
                suggested_action="请用户选择 provider，并在 skill-local `.env` 或显式 `--env-file` 中配置对应 API Key。",
            )
        )
        actions_requiring_user_confirmation.append(
            _item(
                "confirm",
                "confirm_llm_provider",
                "需要确认默认 LLM provider",
                "若首次交付需要支持 `--use-llm` 沉淀，请确认默认 provider 并配置对应 API Key。",
            )
        )
    else:
        info_items.append(
            _item(
                "info",
                "llm_provider_ready",
                "已发现可用 LLM provider",
                ", ".join(provider for provider, ok in provider_keys.items() if ok),
            )
        )

    if os.environ.get("FPW_DEFAULT_PROVIDER", "").strip().lower() != provider:
        suggested_config_writes.append(
            _item(
                "suggestion",
                "write_default_provider",
                "建议写入默认 provider",
                provider,
            )
        )

    if not docs_content["query_data_ready"] and docs.get("ok"):
        warnings.append(
            _item(
                "warning",
                "query_data_missing",
                "尚未发现可查询的数据层",
                "当前输出目录下尚未发现 product_profiles 或索引文件。环境已可初始化，但首次查询前仍需先沉淀至少一个管理人。",
                affects=["query"],
            )
        )

    skill_env_path = SKILL_ROOT / ".env"
    if not skill_env_path.exists():
        suggested_config_writes.append(
            _item(
                "suggestion",
                "create_skill_env",
                "建议创建 skill-local `.env`",
                str(skill_env_path),
            )
        )
        actions_requiring_user_confirmation.append(
            _item(
                "confirm",
                "confirm_create_skill_env",
                "需要确认是否创建 skill-local `.env`",
                "首次迁移到新用户机器时，建议创建 skill-local `.env` 固化默认路径和 provider。",
            )
        )

    ready_for_deposit = bool(
        project["ok"] and raw["ok"] and docs["ok"] and not missing_required_modules
    )
    ready_for_deposit_with_llm = ready_for_deposit and any(provider_keys.values())
    ready_for_query = bool(
        project["ok"] and docs["ok"] and docs_content["query_data_ready"]
    )

    if ready_for_deposit_with_llm:
        overall_status = "ready"
    elif ready_for_deposit or (project["ok"] and docs["ok"]):
        overall_status = "partial"
    else:
        overall_status = "needs_setup"

    return {
        "status": overall_status,
        "skill": "fund-wiki",
        "stage": "init",
        "ready_for_query": ready_for_query,
        "ready_for_deposit": ready_for_deposit,
        "ready_for_deposit_with_llm": ready_for_deposit_with_llm,
        "recommended_provider": provider,
        "provider_key_status": provider_keys,
        "python_executable": default_python(),
        "loaded_env_files": [str(path) for path in loaded_env_files],
        "env_candidates": env_candidates_payload(args.env_file),
        "resolved_paths": {
            "project_root": project,
            "raw_root": raw,
            "docs_root": docs,
        },
        "docs_content": docs_content,
        "dependencies": dependencies,
        "ocr": {"ok": ocr_ok, "detail": ocr_detail},
        "blocking_items": blocking_items,
        "warnings": warnings,
        "info_items": info_items,
        "actions_requiring_user_confirmation": actions_requiring_user_confirmation,
        "suggested_config_writes": suggested_config_writes,
        "next_actions": build_next_actions(
            project_ok=project["ok"],
            docs_ok=docs["ok"],
            raw_ok=raw["ok"],
            ready_for_query=ready_for_query,
            ready_for_deposit=ready_for_deposit,
            ready_for_deposit_with_llm=ready_for_deposit_with_llm,
        ),
    }


def build_next_actions(
    *,
    project_ok: bool,
    docs_ok: bool,
    raw_ok: bool,
    ready_for_query: bool,
    ready_for_deposit: bool,
    ready_for_deposit_with_llm: bool,
) -> list[str]:
    actions: list[str] = []
    if not (project_ok and docs_ok):
        actions.append("先补齐 skill engine 与 docs root，再重新执行初始化检查。")
        return actions
    if not raw_ok:
        actions.append("确认尽调材料根目录可达，再重新执行初始化检查。")
    if ready_for_deposit_with_llm:
        actions.append("可以直接执行带 `--use-llm` 的管理人沉淀。")
    elif ready_for_deposit:
        actions.append(
            "可以先执行不依赖 LLM 的基础沉淀，或补充 API Key 后启用 `--use-llm`。"
        )
    if ready_for_query:
        actions.append("可以直接执行 fund-wiki 查询。")
    else:
        actions.append("先沉淀至少一个管理人，再执行标准 query 流程。")
    return actions


def update_env_text(existing_text: str, updates: dict[str, str]) -> str:
    lines = existing_text.splitlines()
    pending = dict(updates)
    rewritten: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            rewritten.append(line)
            continue
        key, _, _value = line.partition("=")
        normalized_key = key.strip()
        if normalized_key in pending:
            rewritten.append(f"{normalized_key}={pending.pop(normalized_key)}")
        else:
            rewritten.append(line)
    if pending:
        if rewritten and rewritten[-1].strip():
            rewritten.append("")
        for key, value in pending.items():
            rewritten.append(f"{key}={value}")
    return "\n".join(rewritten).rstrip() + "\n"


def new_env_template(updates: dict[str, str]) -> str:
    lines = [
        "# fund-wiki local configuration",
        "# Add one API key below if you want to enable --use-llm deposit.",
        "# DEEPSEEK_API_KEY=",
        "# KIMI_API_KEY=",
        "# OPENAI_API_KEY=",
        "# CHATGPT_API_KEY=",
        "",
    ]
    for key in MANAGED_ENV_KEYS:
        value = updates.get(key)
        if value:
            lines.append(f"{key}={value}")
    return "\n".join(lines).rstrip() + "\n"


def apply_skill_env(args, report: dict[str, Any]) -> dict[str, Any]:
    target = SKILL_ROOT / ".env"
    resolved_paths = report["resolved_paths"]
    updates: dict[str, str] = {}

    provider = (args.provider or report["recommended_provider"]).strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise RuntimeError(f"Unsupported provider: {provider}")
    updates["FPW_DEFAULT_PROVIDER"] = provider

    docs_path = args.docs_root or resolved_paths["docs_root"].get("path", "")
    raw_path = args.raw_root or resolved_paths["raw_root"].get("path", "")
    tesseract_cmd = args.tesseract_cmd or (
        report["ocr"]["detail"] if report["ocr"]["ok"] else ""
    )

    if docs_path:
        updates["FPW_DOCS_ROOT"] = docs_path
    if raw_path:
        updates["FPW_RAW_ROOT"] = raw_path
    if args.allow_local_docs_fallback:
        updates["FPW_ALLOW_LOCAL_DOCS_FALLBACK"] = "1"
    if tesseract_cmd and Path(tesseract_cmd).suffix.lower() == ".exe":
        updates["FPW_TESSERACT_CMD"] = tesseract_cmd

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing_text = target.read_text(encoding="utf-8")
        target.write_text(update_env_text(existing_text, updates), encoding="utf-8")
    else:
        target.write_text(new_env_template(updates), encoding="utf-8")
    os.environ.update(updates)
    return {"path": str(target), "updated_keys": sorted(updates)}


def render_human_report(report: dict[str, Any]) -> str:
    lines = [
        "fund-wiki 初始化检查",
        f"status: {report['status']}",
        f"ready_for_query: {report['ready_for_query']}",
        f"ready_for_deposit: {report['ready_for_deposit']}",
        f"ready_for_deposit_with_llm: {report['ready_for_deposit_with_llm']}",
        f"recommended_provider: {report['recommended_provider']}",
        "",
    ]
    for label, items in (
        ("Blocking", report["blocking_items"]),
        ("Warnings", report["warnings"]),
        ("Info", report["info_items"]),
    ):
        lines.append(label + ":")
        if not items:
            lines.append("- none")
        else:
            for item in items:
                lines.append(f"- {item['title']}: {item['detail']}")
        lines.append("")
    lines.append("Next Actions:")
    for item in report["next_actions"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize fund-wiki for first-time users."
    )
    parser.add_argument("--raw-root", help="Explicit raw material root.")
    parser.add_argument("--docs-root", help="Explicit docs root.")
    parser.add_argument("--project-root", help="Explicit project root.")
    parser.add_argument("--env-file", help="Explicit .env file to load before checks.")
    parser.add_argument("--provider", choices=SUPPORTED_PROVIDERS)
    parser.add_argument("--tesseract-cmd", help="Explicit Tesseract executable path.")
    parser.add_argument("--allow-local-docs-fallback", action="store_true")
    parser.add_argument(
        "--apply-skill-env",
        action="store_true",
        help="Write or update skill-local .env after the user has confirmed the chosen defaults.",
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    args = parser.parse_args()

    report = build_report(args)
    if args.apply_skill_env:
        applied_config = apply_skill_env(args, report)
        report = build_report(args)
        report["applied_config"] = applied_config

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_human_report(report))
    return 0 if not report["blocking_items"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
