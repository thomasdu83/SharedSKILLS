#!/usr/bin/env python
"""Validate one route-decision JSON object against SharedSKILLS registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from skill_doctor import parse_yaml_simple
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from skill_doctor import parse_yaml_simple


def load_registry(root: Path) -> dict:
    return parse_yaml_simple((root / "skill-registry.yaml").read_text(encoding="utf-8-sig")) or {}


def validate(decision: dict, registry: dict) -> dict:
    errors: list[str] = []
    skills = registry.get("skills", [])
    by_id = {str(s.get("id")): s for s in skills if isinstance(s, dict)}
    declared_supports = {
        str(value).split("#", 1)[0].strip()
        for s in skills if isinstance(s, dict)
        for value in (s.get("supports", []) or [])
    }
    aliases = {}
    for s in skills:
        if isinstance(s, dict):
            for alias in s.get("aliases", []) or []:
                aliases[str(alias)] = str(s.get("id"))

    primary = str(decision.get("primary_skill", ""))
    primary_id = aliases.get(primary, primary)
    entry = by_id.get(primary_id)
    if not entry:
        errors.append("primary_skill 不在注册表")
    elif entry.get("status") != "active" or str(entry.get("routable")).lower() != "true":
        errors.append("primary_skill 必须是 active 且 routable=true")

    supports = decision.get("support_skills", [])
    if not isinstance(supports, list):
        errors.append("support_skills 必须是列表")
        supports = []
    if len(supports) > 2:
        errors.append("support_skills 实际输出最多两个")
    for support in supports:
        sid = aliases.get(str(support), str(support))
        declared_by_primary = {
            str(value).split("#", 1)[0].strip()
            for value in (entry.get("supports", []) or [])
        } if entry else set()
        if sid not in by_id and sid not in declared_supports:
            errors.append(f"support_skill 未注册或未被主入口声明：{support}")
        if entry and sid not in declared_by_primary:
            errors.append(f"support_skill 不在当前主入口 supports 中：{support}")
        if sid == primary_id:
            errors.append("support_skill 不能与 primary_skill 相同")
        excludes = {str(x).split("#", 1)[0].strip() for x in (entry.get("excludes", []) or [])} if entry else set()
        if entry and sid in excludes:
            errors.append(f"support_skill 命中主 Skill excludes：{support}")

    for field in ("task_class", "risk_level", "trigger_evidence", "excluded_skills", "unresolved"):
        if field not in decision:
            errors.append(f"缺少路由字段：{field}")
    if decision.get("risk_level") not in (1, 2, 3, 4, "1", "2", "3", "4"):
        errors.append("risk_level 必须为 1–4")

    return {"status": "pass" if not errors else "fail", "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", required=True, help="路由决策 JSON 文件或 JSON 字符串")
    args = parser.parse_args()
    try:
        source = Path(args.json)
        payload = json.loads(source.read_text(encoding="utf-8") if source.exists() else args.json)
        result = validate(payload, load_registry(Path(args.root).resolve()))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        result = {"status": "fail", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
