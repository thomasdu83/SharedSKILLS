#!/usr/bin/env python
"""Validate the behavior-eval registry without calling an LLM."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from skill_doctor import parse_yaml_simple
except ImportError:  # pragma: no cover
    from scripts.skill_doctor import parse_yaml_simple


STATUSES = {"pending", "executed", "reviewed", "failed"}
REQUIRED_RUN_FIELDS = {
    "run_id", "suite_id", "case_id", "model_id", "started_at", "input_ref",
    "output_ref", "automatic_checks", "human_review", "result",
}


def _load(path: Path) -> dict:
    value = parse_yaml_simple(path.read_text(encoding="utf-8")) or {}
    return value if isinstance(value, dict) else {}


def _case_ids(path: Path) -> set[str]:
    data = _load(path)
    ids: set[str] = set()
    if not isinstance(data, dict):
        return ids
    for value in data.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict):
                case_id = item.get("id") or item.get("name")
                if case_id:
                    ids.add(str(case_id))
    return ids


def _version(value: object) -> tuple[int, int] | None:
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.\d+)?", str(value or "").strip())
    return (int(match.group(1)), int(match.group(2))) if match else None


def validate(root: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    path = root / "behavior-eval-registry.yaml"
    if not path.exists():
        return {"status": "fail", "errors": ["缺少 behavior-eval-registry.yaml"]}
    try:
        registry = _load(path)
    except Exception as exc:
        return {"status": "fail", "errors": [f"行为回归登记册解析失败：{exc}"]}

    baseline = registry.get("baseline", {})
    if not isinstance(baseline, dict):
        errors.append("baseline 必须是 mapping")
        baseline = {}
    minimum = _version(baseline.get("minimum_version"))
    if minimum is None:
        errors.append("baseline.minimum_version 必须是 major.minor 版本")
    required_fields = set(baseline.get("required_run_fields", []) or [])
    if required_fields != REQUIRED_RUN_FIELDS:
        errors.append("baseline.required_run_fields 与登记规范不一致")
    template = str(baseline.get("run_template", "")).replace("\\", "/").strip()
    if not template or not (root / template).is_file():
        errors.append("baseline.run_template 不存在")

    suites = registry.get("suites", [])
    suite_cases: dict[str, set[str]] = {}
    if not isinstance(suites, list) or not suites:
        errors.append("suites 必须是非空列表")
        suites = []
    for suite in suites:
        if not isinstance(suite, dict):
            errors.append("suites 存在非 mapping 条目")
            continue
        suite_id = str(suite.get("id", "")).strip()
        case_file = str(suite.get("case_file", "")).replace("\\", "/").strip()
        if not suite_id or not case_file:
            errors.append("suite 缺少 id 或 case_file")
            continue
        case_path = root / case_file
        if not case_path.is_file():
            errors.append(f"suite {suite_id} 的 case_file 不存在：{case_file}")
            continue
        try:
            suite_cases[suite_id] = _case_ids(case_path)
        except Exception as exc:
            errors.append(f"suite {suite_id} 用例解析失败：{exc}")
    runs = registry.get("runs", [])
    if not isinstance(runs, list):
        errors.append("runs 必须是列表")
        runs = []
    seen_runs: set[str] = set()
    for run in runs:
        if not isinstance(run, dict):
            errors.append("runs 存在非 mapping 条目")
            continue
        run_id = str(run.get("run_id", "")).strip()
        if not run_id:
            errors.append("行为回归记录缺少 run_id")
        elif run_id in seen_runs:
            errors.append(f"行为回归记录重复 run_id：{run_id}")
        seen_runs.add(run_id)
        status = str(run.get("status", "")).strip()
        if status not in STATUSES:
            errors.append(f"行为回归 {run_id or '<unnamed>'} status 非法：{status}")
        suite_id = str(run.get("suite_id", "")).strip()
        case_id = str(run.get("case_id", "")).strip()
        if suite_id not in suite_cases:
            errors.append(f"行为回归 {run_id or '<unnamed>'} 引用未知 suite：{suite_id}")
        elif case_id not in suite_cases[suite_id]:
            errors.append(f"行为回归 {run_id or '<unnamed>'} 引用未知 case：{case_id}")
        model_version = _version(run.get("model_version"))
        if model_version is None:
            errors.append(f"行为回归 {run_id or '<unnamed>'} 缺少合法 model_version")
        elif minimum is not None and model_version < minimum:
            errors.append(f"行为回归 {run_id} 使用低于基线的模型：{run.get('model_version')}")
        missing = [field for field in REQUIRED_RUN_FIELDS if field not in run]
        if missing:
            errors.append(f"行为回归 {run_id or '<unnamed>'} 缺少字段：{', '.join(missing)}")
        for field in ("model_id", "input_ref", "output_ref"):
            if field in run and not str(run.get(field) or "").strip():
                errors.append(f"行为回归 {run_id or '<unnamed>'} 的 {field} 不能为空")
        if not isinstance(run.get("result"), dict):
            errors.append(f"行为回归 {run_id or '<unnamed>'} result 必须是 mapping")
        if status == "pending":
            warnings.append(f"行为回归 {run_id or '<unnamed>'} 尚未执行真实模型")
        elif status == "executed" and not isinstance(run.get("automatic_checks"), dict):
            errors.append(f"行为回归 {run_id} executed 时 automatic_checks 必须是 mapping")
        elif status == "reviewed" and not isinstance(run.get("human_review"), dict):
            errors.append(f"行为回归 {run_id} reviewed 时 human_review 必须是 mapping")
        elif status == "reviewed" and not str((run.get("human_review") or {}).get("reviewer", "")).strip():
            errors.append(f"行为回归 {run_id} reviewed 时必须填写 human_review.reviewer")
        if status == "failed" and not str((run.get("result") or {}).get("failure_classification", "")).strip():
            errors.append(f"行为回归 {run_id} failed 时必须填写 result.failure_classification")

    if not runs:
        warnings.append("尚未登记任何真实模型行为回归；格式通过不等于行为验收通过")
    return {
        "status": "fail" if errors else ("warning" if warnings else "pass"),
        "suite_count": len(suites),
        "run_count": len(runs),
        "executed_count": sum(str(r.get("status")) in {"executed", "reviewed", "failed"} for r in runs if isinstance(r, dict)),
        "reviewed_count": sum(str(r.get("status")) == "reviewed" for r in runs if isinstance(r, dict)),
        "errors": errors,
        "warnings": warnings,
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
