#!/usr/bin/env python
"""Validate a frozen research artifact or a delivery-input record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from skill_doctor import parse_yaml_simple
except ImportError:  # pragma: no cover
    from scripts.skill_doctor import parse_yaml_simple


DECISION_USES = {"research_only", "internal_decision", "portfolio_input", "live"}
REVIEW_STATUSES = {"draft", "reviewed", "approved"}
REQUIRED = {
    "artifact_id", "title", "audience", "decision_use", "as_of", "thesis",
    "facts", "claims", "inferences", "judgments", "actions", "risks",
    "falsifiers", "limitations", "source_manifest", "run_manifest",
    "review_status", "owner", "reviewer",
}


def _load(path: Path) -> dict:
    value = parse_yaml_simple(path.read_text(encoding="utf-8")) or {}
    return value if isinstance(value, dict) else {}


def validate(path: Path) -> dict:
    errors: list[str] = []
    if not path.is_file():
        return {"status": "fail", "errors": [f"artifact 文件不存在：{path}"]}
    try:
        raw = _load(path)
    except Exception as exc:
        return {"status": "fail", "errors": [f"artifact 解析失败：{exc}"]}
    artifact = raw.get("artifact", raw)
    if not isinstance(artifact, dict):
        return {"status": "fail", "errors": ["artifact 必须是 mapping"]}
    missing = sorted(REQUIRED - set(artifact))
    if missing:
        errors.append(f"artifact 缺少字段：{', '.join(missing)}")
    for field in ("artifact_id", "title", "audience", "as_of", "thesis", "run_manifest", "owner"):
        if field in artifact and not str(artifact.get(field) or "").strip():
            errors.append(f"artifact.{field} 不能为空")
    if artifact.get("decision_use") not in DECISION_USES:
        errors.append(f"artifact.decision_use 非法：{artifact.get('decision_use')}")
    if artifact.get("review_status") not in REVIEW_STATUSES:
        errors.append(f"artifact.review_status 非法：{artifact.get('review_status')}")
    for field in ("facts", "claims", "inferences", "judgments", "actions", "risks", "falsifiers", "limitations", "source_manifest"):
        if field in artifact and not isinstance(artifact.get(field), list):
            errors.append(f"artifact.{field} 必须是列表")
    if artifact.get("decision_use") != "research_only" and not artifact.get("judgments"):
        errors.append("非 research_only artifact 必须包含 judgments")
    if artifact.get("review_status") == "approved" and not str(artifact.get("reviewer") or "").strip():
        errors.append("approved artifact 必须有 reviewer")
    if not artifact.get("source_manifest"):
        errors.append("artifact.source_manifest 不能为空")
    status = "fail" if errors else "pass"
    return {"status": status, "artifact_id": artifact.get("artifact_id"), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(Path(args.artifact).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result)
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
