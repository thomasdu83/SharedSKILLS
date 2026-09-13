#!/usr/bin/env python
"""Validate the release manifest against the current SharedSKILLS tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from skill_doctor import parse_yaml_simple
except ImportError:  # pragma: no cover
    from scripts.skill_doctor import parse_yaml_simple


def _load(path: Path) -> dict:
    data = parse_yaml_simple(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def validate(root: Path) -> dict:
    errors: list[str] = []
    manifest_path = root / "skill-release.yaml"
    if not manifest_path.exists():
        return {"status": "fail", "errors": ["缺少 skill-release.yaml"]}
    try:
        manifest = _load(manifest_path)
    except Exception as exc:
        return {"status": "fail", "errors": [f"skill-release.yaml 解析失败：{exc}"]}

    entries = manifest.get("skills", [])
    if not isinstance(entries, list):
        return {"status": "fail", "errors": ["skill-release.yaml 缺少 skills 列表"]}

    versions_path = root / "skill-versions.yaml"
    versions_by_key: dict[tuple[str, str], str] = {}
    if not versions_path.exists():
        errors.append("缺少 skill-versions.yaml（全库版本唯一来源）")
    else:
        try:
            versions = _load(versions_path)
            version_entries = versions.get("skills", [])
            if not isinstance(version_entries, list):
                errors.append("skill-versions.yaml 缺少 skills 列表")
            else:
                for item in version_entries:
                    if not isinstance(item, dict):
                        errors.append("skill-versions.yaml 存在非 mapping 条目")
                        continue
                    key = (
                        str(item.get("id", "")).strip(),
                        str(item.get("path", "")).replace("\\", "/").strip(),
                    )
                    version = str(item.get("version", "")).strip()
                    if not key[0] or not key[1] or not version:
                        errors.append("skill-versions.yaml 条目缺少 id、path 或 version")
                        continue
                    if key in versions_by_key:
                        errors.append(f"skill-versions.yaml 存在重复条目：{key[0]} / {key[1]}")
                    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
                        errors.append(f"{key[0]} version 不是语义版本：{version}")
                    versions_by_key[key] = version
        except Exception as exc:
            errors.append(f"skill-versions.yaml 解析失败：{exc}")

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    actual_paths: set[str] = set()
    for skill_file in root.rglob("SKILL.md"):
        if any(part in {".git", "__pycache__", "node_modules", ".venv"} for part in skill_file.parts):
            continue
        actual_paths.add(skill_file.parent.relative_to(root).as_posix())

    for item in entries:
        if not isinstance(item, dict):
            errors.append("发布清单存在非 mapping 条目")
            continue
        skill_id = str(item.get("id", "")).strip()
        rel = str(item.get("path", "")).replace("\\", "/").strip()
        if not skill_id or not rel:
            errors.append("发布清单条目缺少 id 或 path")
            continue
        if skill_id in seen_ids:
            errors.append(f"发布清单存在重复 id：{skill_id}")
        if rel in seen_paths:
            errors.append(f"发布清单存在重复 path：{rel}")
        seen_ids.add(skill_id)
        seen_paths.add(rel)
        skill_file = root / rel / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"发布清单 path 不存在 SKILL.md：{rel}")
            continue
        expected_hash = str(item.get("sha256", "")).strip().lower()
        actual_hash = hashlib.sha256(skill_file.read_bytes()).hexdigest()
        if expected_hash != actual_hash:
            errors.append(f"{rel} sha256 漂移（记录 {expected_hash or '<empty>'}，实际 {actual_hash}）")
        if not str(item.get("version", "")).strip() or str(item.get("version")) == "unversioned":
            errors.append(f"{rel} 仍为 unversioned，必须使用显式初始版本")
        governed_version = versions_by_key.get((skill_id, rel))
        if governed_version is None:
            errors.append(f"{rel} 未在 skill-versions.yaml 中登记")
        elif governed_version != str(item.get("version", "")).strip():
            errors.append(f"{rel} 的 release version 与 skill-versions.yaml 不一致")

    missing = sorted(actual_paths - seen_paths)
    stale = sorted(seen_paths - actual_paths)
    if missing:
        errors.append(f"发布清单缺少 Skill：{missing}")
    if stale:
        errors.append(f"发布清单包含不存在的 Skill：{stale}")
    version_paths = {path for (_skill_id, path) in versions_by_key}
    if versions_by_key and version_paths != actual_paths:
        errors.append(
            "skill-versions.yaml 与磁盘 Skill 集合漂移："
            f"missing={sorted(actual_paths - version_paths)} stale={sorted(version_paths - actual_paths)}"
        )

    registry_path = root / "skill-registry.yaml"
    if registry_path.exists():
        try:
            registry = _load(registry_path)
            manifest_by_id = {str(item.get("id")): item for item in entries if isinstance(item, dict)}
            for item in registry.get("skills", []) if isinstance(registry.get("skills"), list) else []:
                if not isinstance(item, dict):
                    continue
                skill_id = str(item.get("id", ""))
                release = manifest_by_id.get(skill_id)
                if release is None:
                    errors.append(f"核心注册表 Skill 未出现在发布清单：{skill_id}")
                    continue
                registry_version = str(item.get("version", "")).strip()
                if registry_version and registry_version != str(release.get("version", "")).strip():
                    errors.append(f"{skill_id} registry version 与 release version 不一致")
        except Exception as exc:
            errors.append(f"skill-registry.yaml 解析失败：{exc}")

    return {
        "status": "fail" if errors else "pass",
        "release_id": manifest.get("release_id"),
        "skill_count": len(entries),
        "errors": errors,
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
