#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""run_skill_evals.py — 评估用例格式检查器（只读，不调用 LLM）。

本工具只验证评估用例文件的格式与自洽性，不执行 LLM 行为、不产生路由或
报告结论。三个评估状态必须区分：

- case_validated        用例格式已通过校验（本工具只能产生这一项）
- llm_behavior_executed LLM 行为已实际执行（本工具不产生）
- human_reviewed        人工已复核（本工具不产生）

用法：
    python scripts\\run_skill_evals.py --root . --validate-only
    python scripts\\run_skill_evals.py --root . --case tests\\routing-cases.yaml --validate-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# 复用 skill_doctor 的最小 YAML 解析器（同目录）
try:
    from skill_doctor import parse_yaml_simple
except ImportError:  # 运行目录不是 scripts/ 时兜底
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from skill_doctor import parse_yaml_simple


# 引用 Skill 的字段：这些字段的值应当能在注册表 id/alias 中找到。
_SKILL_REF_FIELDS = (
    "expected_primary",
    "forbidden_primary",
    "expected_route",
    "expected_supports",
)
# 期望行为 / 失败条件的字段。
_EXPECTED_FIELDS = (
    "expected",
    "expected_behavior",
    "expected_action",
    "forbidden",
    "forbidden_action",
    "expected_primary",
)

EXECUTION_STATUSES = {"ready", "draft", "needs_review", "blocked", "failed"}


def load_registry_ids(root: str):
    """读取注册表，返回 (id 与 alias 集合, 错误信息)。"""
    p = os.path.join(root, "skill-registry.yaml")
    if not os.path.exists(p):
        return set(), "skill-registry.yaml 不存在"
    try:
        with open(p, "r", encoding="utf-8") as fh:
            reg = parse_yaml_simple(fh.read()) or {}
    except Exception as e:
        return set(), f"skill-registry.yaml 解析失败：{e}"
    skills = reg.get("skills", []) if isinstance(reg, dict) else []
    ids: set[str] = set()
    for s in skills:
        if isinstance(s, dict):
            if s.get("id"):
                ids.add(str(s["id"]))
            for a in s.get("aliases", []) or []:
                ids.add(str(a))
    return ids, None


def discover_case_files(root: str, case_arg: str | None):
    """确定要检查的用例文件路径列表。"""
    if case_arg:
        candidates = [
            os.path.join(root, case_arg),
            case_arg,
            os.path.join(os.getcwd(), case_arg),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return [os.path.abspath(c)]
        return []
    tests_dir = os.path.join(root, "tests")
    if not os.path.isdir(tests_dir):
        return []
    return sorted(
        os.path.join(tests_dir, f)
        for f in os.listdir(tests_dir)
        if f.endswith((".yaml", ".yml"))
    )


def extract_cases(data):
    """从顶层结构提取用例列表：遍历所有 list 值，收集其中 dict 项。"""
    cases = []
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        cases.append(item)
    return cases


def check_case(case: dict, registry_ids: set[str]):
    """检查单个用例，返回 (用例 id, 问题列表)。"""
    problems: list[str] = []
    cid = case.get("id") or case.get("name")
    if not cid:
        problems.append("missing id/name")

    has_prompt = any(
        k in case for k in ("prompt", "input", "expected_behavior", "expected_route")
    )
    if not has_prompt:
        problems.append("missing prompt/input/expected_behavior")

    for f in _SKILL_REF_FIELDS:
        if f not in case:
            continue
        vals = case[f]
        if isinstance(vals, str):
            vals = [vals]
        elif not isinstance(vals, list):
            continue
        for v in vals:
            if v and registry_ids and v not in registry_ids:
                problems.append(f"unknown skill: {v}")

    has_expected = any(k in case for k in _EXPECTED_FIELDS)
    if not has_expected:
        problems.append("missing expected_behavior/failure condition")

    # Contract cases must be executable descriptions rather than prose-only
    # rules.  The validator intentionally checks shape, not whether an LLM
    # actually complied; execution/review are separate lifecycle states.
    if case.get("contract"):
        prompt = case.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            problems.append("missing non-empty prompt")
        if "input" not in case:
            problems.append("missing input")
        expected = case.get("expected_behavior")
        if not isinstance(expected, dict):
            problems.append("expected_behavior must be a mapping")
        else:
            if not expected.get("status"):
                problems.append("expected_behavior missing status")
            elif expected.get("status") not in EXECUTION_STATUSES:
                problems.append(
                    "expected_behavior.status must use execution.yaml status; "
                    "put domain/lifecycle state in a separate field"
                )
            if not isinstance(expected.get("required_fields"), list) or not expected.get("required_fields"):
                problems.append("expected_behavior missing required_fields")
        forbidden = case.get("forbidden_behavior")
        if not isinstance(forbidden, list) or not forbidden:
            problems.append("missing forbidden_behavior")
        output_fields = case.get("required_output_fields")
        if not isinstance(output_fields, list) or not output_fields:
            problems.append("missing required_output_fields")

    # 复盘用例：声明了经验相关输入时，必须声明经验状态。
    inp = case.get("input")
    if isinstance(inp, dict) and any(
        k in inp for k in ("independent_projects", "project_specific", "repeated_pattern")
    ):
        exp = case.get("expected")
        if isinstance(exp, dict) and not exp.get("status"):
            problems.append("missing experience status (expected.status)")

    return cid, problems


def run_evals(root: str, case_arg: str | None):
    errors: list[str] = []
    registry_ids, reg_err = load_registry_ids(root)
    if reg_err:
        errors.append(reg_err)

    files = discover_case_files(root, case_arg)
    if case_arg and not files:
        errors.append(f"未找到用例文件：{case_arg}")
        return {
            "status": "fail",
            "mode": "validate_only",
            "total_cases": 0,
            "case_validated": 0,
            "llm_behavior_executed": 0,
            "human_reviewed": 0,
            "errors": errors,
            "case_files": [],
            "missing_fields": [],
        }

    seen_ids: dict[str, str] = {}
    total = 0
    format_valid = 0
    missing_fields: list[str] = []
    case_file_results = []

    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                data = parse_yaml_simple(fh.read()) or {}
        except Exception as e:
            errors.append(f"{fp}：解析失败：{e}")
            continue
        cases = extract_cases(data)
        file_problems = 0
        for case in cases:
            total += 1
            cid, problems = check_case(case, registry_ids)
            if cid:
                if cid in seen_ids:
                    errors.append(f"{fp}：重复用例 ID：{cid}")
                seen_ids[cid] = fp
            for pr in problems:
                file_problems += 1
                label = cid or "<unnamed>"
                missing_fields.append(f"{os.path.basename(fp)}::{label} -> {pr}")
                if "unknown skill" in pr or "duplicate" in pr:
                    errors.append(f"{os.path.basename(fp)}::{label} -> {pr}")
            if not problems:
                format_valid += 1
        case_file_results.append({
            "file": os.path.relpath(fp, root),
            "case_count": len(cases),
            "problems": file_problems,
        })

    # 只有格式问题（缺失字段等）记为 warning 级，不判 fail；
    # 未知 Skill 引用、重复 ID、文件解析失败才判 fail。
    if errors:
        status = "fail"
    elif missing_fields:
        status = "warning"
    else:
        status = "pass"

    return {
        "status": status,
        "mode": "validate_only",
        "total_cases": total,
        "cases_discovered": total,
        "cases_format_valid": format_valid,
        "case_validated": format_valid,
        "cases_behavior_executed": 0,
        "cases_human_reviewed": 0,
        "llm_behavior_executed": 0,
        "human_reviewed": 0,
        "errors": errors,
        "case_files": case_file_results,
        "missing_fields": missing_fields,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="评估用例格式检查器（只读，不调用 LLM）")
    parser.add_argument("--root", default=".", help="SharedSKILLS 根目录")
    parser.add_argument("--case", default=None, help="指定单个用例文件（相对 root 或绝对）")
    parser.add_argument("--validate-only", action="store_true",
                        help="仅校验用例格式（本工具始终只做此项）")
    args = parser.parse_args(argv)

    result = run_evals(args.root, args.case)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["status"] == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
