#!/usr/bin/env python
"""Validate dependency manifest structure and registry references."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

try:
    from skill_doctor import parse_yaml_simple
except ImportError:  # pragma: no cover
    from scripts.skill_doctor import parse_yaml_simple


ALLOWED_KINDS = {"repository_path", "runtime_environment", "external_service"}
ALLOWED_POLICIES = {"blocked", "warning", "needs_review"}


def validate(root: Path) -> dict:
    errors: list[str] = []
    checks: list[dict] = []
    manifest_path = root / "skill-dependencies.yaml"
    if not manifest_path.exists():
        return {"status": "fail", "errors": ["缺少 skill-dependencies.yaml"]}
    try:
        data = parse_yaml_simple(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return {"status": "fail", "errors": [f"skill-dependencies.yaml 解析失败：{exc}"]}
    dependencies = data.get("dependencies", []) if isinstance(data, dict) else []
    if not isinstance(dependencies, list):
        return {"status": "fail", "errors": ["skill-dependencies.yaml 缺少 dependencies 列表"]}

    by_id: dict[str, dict] = {}
    covered: dict[str, set[str]] = {}
    for item in dependencies:
        if not isinstance(item, dict):
            errors.append("依赖清单存在非 mapping 条目")
            continue
        dep_id = str(item.get("id", "")).strip()
        if not dep_id:
            errors.append("依赖条目缺少 id")
            continue
        if dep_id in by_id:
            errors.append(f"依赖 id 重复：{dep_id}")
        by_id[dep_id] = item
        if item.get("kind") not in ALLOWED_KINDS:
            errors.append(f"依赖 {dep_id} 的 kind 非法：{item.get('kind')}")
        if not str(item.get("provider", "")).strip():
            errors.append(f"依赖 {dep_id} 缺少 provider")
        if not isinstance(item.get("paths"), list):
            errors.append(f"依赖 {dep_id} 的 paths 必须是列表")
        if item.get("missing_policy") not in ALLOWED_POLICIES:
            errors.append(f"依赖 {dep_id} 的 missing_policy 非法：{item.get('missing_policy')}")
        if not str(item.get("verification", "")).strip():
            errors.append(f"依赖 {dep_id} 缺少 verification")
        users = item.get("required_by")
        if not isinstance(users, list) or not users:
            errors.append(f"依赖 {dep_id} 必须声明 required_by")
            continue
        for skill_id in users:
            covered.setdefault(str(skill_id), set()).add(dep_id)

        # Only repository_path dependencies can be checked deterministically
        # from this workstation. Runtime services and network sources remain
        # explicit "not_checked" states rather than guessed as available.
        provider = str(item.get("provider", "")).strip()
        paths = item.get("paths") if isinstance(item.get("paths"), list) else []
        dep_check = {
            "id": dep_id,
            "kind": item.get("kind"),
            "missing_policy": item.get("missing_policy"),
            "status": "not_checked",
            "provider": provider,
            "missing_paths": [],
        }
        if item.get("kind") == "repository_path":
            provider_path = provider
            # A provider may be a literal Windows/UNC path or a repository
            # name. Do not invent a path for names such as "QuantSystem".
            is_path = bool(re.match(r"^[A-Za-z]:[\\/]", provider_path) or provider_path.startswith("\\\\"))
            base = Path(provider_path) if is_path else None
            if base is None:
                dep_check["status"] = "not_checked"
            else:
                targets = [base / str(rel) for rel in paths] if paths else [base]
                missing = [str(target) for target in targets if not target.exists()]
                dep_check["status"] = "available" if not missing else "missing"
                dep_check["missing_paths"] = missing
        checks.append(dep_check)

    registry_path = root / "skill-registry.yaml"
    if registry_path.exists():
        try:
            registry = parse_yaml_simple(registry_path.read_text(encoding="utf-8")) or {}
            registry_ids = {
                str(item.get("id"))
                for item in registry.get("skills", []) if isinstance(item, dict) and item.get("id")
            }
            for skill_id in covered:
                if skill_id not in registry_ids:
                    # Reference/meta Skills are valid dependency consumers even if
                    # they are intentionally outside the core route registry.
                    skill_path = next((root / str(item.get("path")) for item in registry.get("skills", []) if isinstance(item, dict) and str(item.get("id")) == skill_id), None)
                    if skill_path is None:
                        inventory_path = root / "skill-inventory.yaml"
                        if inventory_path.exists():
                            inventory = parse_yaml_simple(inventory_path.read_text(encoding="utf-8")) or {}
                            inventory_ids = {str(item.get("id")) for item in inventory.get("skills", []) if isinstance(item, dict) and item.get("id")}
                            if skill_id not in inventory_ids:
                                errors.append(f"依赖 {skill_id} 引用未知 Skill")
                        else:
                            errors.append(f"依赖 {skill_id} 引用未知 Skill")
            for item in registry.get("skills", []) if isinstance(registry.get("skills"), list) else []:
                if not isinstance(item, dict) or not item.get("id"):
                    continue
                skill_id = str(item["id"])
                # Dependency use is optional; when declared in this manifest it
                # must resolve to a known dependency id.
                declared = item.get("dependencies", []) or []
                if isinstance(declared, list):
                    for dep_id in declared:
                        if str(dep_id) not in by_id:
                            errors.append(f"Skill {skill_id} 引用未登记依赖：{dep_id}")
                        elif skill_id not in {
                            str(user) for user in (by_id[str(dep_id)].get("required_by") or [])
                        }:
                            errors.append(
                                f"依赖 {dep_id} 未反向登记 required_by={skill_id}"
                            )
        except Exception as exc:
            errors.append(f"skill-registry.yaml 解析失败：{exc}")

    return {
        "status": "fail" if errors else "pass",
        "dependency_count": len(dependencies),
        "errors": errors,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(Path(args.root).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result)
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
