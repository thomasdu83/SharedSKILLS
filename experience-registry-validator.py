#!/usr/bin/env python3
"""experience-registry.yaml 的只读校验器。

职责：校验经验登记文件的格式、字段、状态合法性与引用完整性。
本脚本只读，不修改任何文件，也不自动修改任何 Skill。

用法：
    python experience-registry-validator.py                   # 校验同目录 experience-registry.yaml
    python experience-registry-validator.py --registry <路径>  # 校验指定文件
    python experience-registry-validator.py --selftest        # 运行内置语义测试
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - exercised on minimal installations
    yaml = None


def _configure_output() -> None:
    """让 Windows 旧控制台也能稳定显示中文校验结果。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, OSError):
            pass

# ---- 固定取值与状态机 ----

VALID_TARGET_TYPES = {"skill", "template", "rule", "script", "model_card", "project_local"}

VALID_STATUS = {"observed", "proposed", "trial", "approved", "applied", "deprecated", "reverted"}

REQUIRED_FIELDS = ("experience_id", "title", "target_type", "status")

# 合法状态转换（有向边）。不允许的跳跃（如 observed->approved/applied、
# proposed->applied、reverted->applied）不在边集合内，会被判为非法。
ALLOWED_TRANSITIONS = {
    "observed": {"proposed", "deprecated"},
    "proposed": {"trial", "observed", "deprecated"},
    "trial": {"approved", "proposed", "deprecated", "reverted"},
    "approved": {"applied", "proposed", "deprecated"},
    "applied": {"deprecated", "reverted"},
    "reverted": {"proposed", "deprecated"},
    "deprecated": set(),
}

# 需要在 >= 2 个独立项目中重复出现的状态
MULTI_PROJECT_STATUS = {"trial", "approved", "applied"}

# 需要正反用例的状态
VALIDATION_REQUIRED_STATUS = {"trial", "approved", "applied"}

# project_local 经验不允许进入的“共享”状态
SHARED_STATUS = {"trial", "approved", "applied"}

# 项目特有绝对路径启发式：识别“项目特有路径”是否被误登记为共享经验
ABSOLUTE_PATH_RE = re.compile(r"[A-Za-z]:[\\/]|^/[a-zA-Z0-9_.-]+/|\\[a-zA-Z0-9_.-]+\\")


def validate_registry(data) -> list[str]:
    """校验登记数据，返回错误列表（空列表表示通过）。"""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["顶层必须是 YAML mapping（含 experiences 键）"]

    experiences = data.get("experiences")
    if not isinstance(experiences, list):
        return ["缺少 experiences 列表（或不是列表）"]

    ids: dict[str, str] = {}
    for i, exp in enumerate(experiences):
        prefix = f"experiences[{i}]"
        if not isinstance(exp, dict):
            errors.append(f"{prefix} 必须是 mapping")
            continue

        for field in REQUIRED_FIELDS:
            if not exp.get(field):
                errors.append(f"{prefix}.{field} 缺失或为空")

        eid = exp.get("experience_id")
        if eid:
            if eid in ids:
                errors.append(f"{prefix}.experience_id 重复：{eid}")
            else:
                ids[eid] = prefix

        target_type = exp.get("target_type")
        if target_type and target_type not in VALID_TARGET_TYPES:
            errors.append(f"{prefix}.target_type 非法：{target_type!r}（允许 {sorted(VALID_TARGET_TYPES)}）")

        status = exp.get("status")
        if status and status not in VALID_STATUS:
            errors.append(f"{prefix}.status 非法：{status!r}（允许 {sorted(VALID_STATUS)}）")

        target_path = exp.get("target_path")
        if target_type and target_type != "project_local" and not target_path:
            errors.append(f"{prefix}.target_path 缺失（target_type={target_type} 必须指向目标 Skill/模板/规则/脚本路径）")

        if target_type == "project_local" and status in SHARED_STATUS:
            errors.append(f"{prefix} target_type=project_local 不得进入共享状态 {status}")

        # 项目特有绝对路径被写成共享经验的启发式检查
        if target_type and target_type != "project_local":
            for field_name in ("generalized_rule", "description"):
                value = exp.get(field_name)
                if isinstance(value, str) and ABSOLUTE_PATH_RE.search(value):
                    errors.append(
                        f"{prefix}.{field_name} 含项目绝对路径，应抽象为角色/动作或转 target_type=project_local"
                    )

        # 多项目重复出现
        if status in MULTI_PROJECT_STATUS:
            source_retros = exp.get("source_retros") or []
            project_ids = {
                sr.get("project_id")
                for sr in source_retros
                if isinstance(sr, dict) and sr.get("project_id")
            }
            if len(project_ids) < 2:
                errors.append(f"{prefix} status={status} 需要 >=2 个独立项目来源（source_retros）")

        # 正反用例
        if status in VALIDATION_REQUIRED_STATUS:
            validation_cases = exp.get("validation_cases") or []
            kinds = {vc.get("kind") for vc in validation_cases if isinstance(vc, dict)}
            if "positive" not in kinds or "negative" not in kinds:
                errors.append(f"{prefix} status={status} 需要 validation_cases 同时含 positive 与 negative")

        # applied 需要实际变更 + 验证证据
        if status == "applied":
            if not exp.get("applied_at"):
                errors.append(f"{prefix} status=applied 缺少 applied_at")
            if not exp.get("applied_version"):
                errors.append(f"{prefix} status=applied 缺少 applied_version")
            if not exp.get("evidence_refs"):
                errors.append(f"{prefix} status=applied 缺少变更验证证据 evidence_refs")

        # deprecated / reverted 必须保留原因
        if status in {"deprecated", "reverted"}:
            if not exp.get("decision_log"):
                errors.append(f"{prefix} status={status} 缺少 decision_log 以保留原因/证据/关联版本")

        errors.extend(_validate_decision_log(prefix, exp))

    # 引用完整性（supersedes / superseded_by）
    for i, exp in enumerate(experiences):
        if not isinstance(exp, dict):
            continue
        prefix = f"experiences[{i}]"
        for ref in ("supersedes", "superseded_by"):
            value = exp.get(ref)
            if value and value not in ids:
                errors.append(f"{prefix}.{ref} 引用了不存在的 experience_id：{value!r}")

    return errors


def _validate_decision_log(prefix: str, exp: dict) -> list[str]:
    errors: list[str] = []
    decision_log = exp.get("decision_log")
    if decision_log is None:
        return errors
    if not isinstance(decision_log, list):
        return [f"{prefix}.decision_log 必须是列表"]

    last_to = None
    for j, step in enumerate(decision_log):
        if not isinstance(step, dict):
            errors.append(f"{prefix}.decision_log[{j}] 必须是 mapping")
            continue
        frm = step.get("from")
        to = step.get("to")
        if frm not in VALID_STATUS or to not in VALID_STATUS:
            errors.append(f"{prefix}.decision_log[{j}] 状态非法：{frm!r}->{to!r}")
            continue
        if to not in ALLOWED_TRANSITIONS.get(frm, set()):
            errors.append(f"{prefix}.decision_log[{j}] 非法转换：{frm}->{to}")
        last_to = to

    current = exp.get("status")
    if decision_log and last_to is not None and current and last_to != current:
        errors.append(f"{prefix} 当前 status={current} 与 decision_log 末态 {last_to} 不一致")

    return errors


# ---- 内置语义测试 ----

def _mk(**kwargs) -> dict:
    """构造一条最小合法经验的默认值，再按需覆盖。"""
    base = {
        "experience_id": "exp-001",
        "title": "测试经验",
        "description": "测试用经验描述",
        "source_retros": [],
        "target_type": "rule",
        "target_path": "F:/Thomas/SharedSKILLS/example.md",
        "generalized_rule": "把管理动作和分析动作分离",
        "status": "observed",
        "evidence_count": 0,
        "evidence_refs": [],
        "validation_cases": [],
        "conflicts": [],
        "owner": "tester",
        "proposed_at": None,
        "approved_at": None,
        "applied_at": None,
        "review_after": None,
        "applied_version": None,
        "supersedes": None,
        "superseded_by": None,
        "decision_log": [],
    }
    base.update(kwargs)
    return base


def _one_project() -> list[dict]:
    return [{"project_id": "p1", "location": "r1"}]


def _two_projects() -> list[dict]:
    return [{"project_id": "p1", "location": "r1"}, {"project_id": "p2", "location": "r2"}]


def _pos_neg() -> list[dict]:
    return [
        {"kind": "positive", "description": "正例"},
        {"kind": "negative", "description": "反例"},
    ]


def selftest() -> tuple[list[str], int]:
    """运行 7 组语义测试，返回 (失败信息列表, 用例总数)。"""
    failures: list[str] = []
    total = 0

    def check(name, data, expect_error_contains=None, expect_ok=False):
        nonlocal total
        total += 1
        errors = validate_registry(data)
        if expect_ok:
            if errors:
                failures.append(f"[FAIL] {name}: 期望通过，实际报错 {errors}")
            return
        if expect_error_contains:
            if not any(expect_error_contains in e for e in errors):
                failures.append(f"[FAIL] {name}: 期望包含 {expect_error_contains!r}，实际 {errors}")
        else:
            if not errors:
                failures.append(f"[FAIL] {name}: 期望报错，实际通过")

    # 1. 单次项目经验只能进入 observed 或 proposed
    check("1a 单项目 observed 通过",
          {"experiences": [_mk(status="observed", source_retros=_one_project())]}, expect_ok=True)
    check("1b 单项目 proposed 通过",
          {"experiences": [_mk(status="proposed", source_retros=_one_project())]}, expect_ok=True)
    check("1c 单项目 trial 应报错",
          {"experiences": [_mk(status="trial", source_retros=_one_project(), validation_cases=_pos_neg())]},
          expect_error_contains=">=2 个独立项目")

    # 2. 两个独立项目重复出现后可进入 trial
    check("2 两独立项目 trial 通过",
          {"experiences": [_mk(status="trial", source_retros=_two_projects(), validation_cases=_pos_neg())]},
          expect_ok=True)

    # 3. 没有正反用例时不能进入 approved
    check("3 approved 缺正反例应报错",
          {"experiences": [_mk(status="approved", source_retros=_two_projects())]},
          expect_error_contains="positive 与 negative")

    # 4. 没有实际变更和验证证据时不能进入 applied
    check("4 applied 缺变更证据应报错",
          {"experiences": [_mk(
              status="applied",
              source_retros=_two_projects(),
              validation_cases=_pos_neg(),
              decision_log=[{"from": "approved", "to": "applied", "at": "2026-01-01", "by": "x", "reason": "y"}],
          )]},
          expect_error_contains="applied_at")

    # 5. 项目特有路径和按钮名称只能登记为 project_local
    check("5a project_local 可登记项目路径",
          {"experiences": [_mk(
              experience_id="exp-local",
              target_type="project_local",
              target_path="F:/项目/按钮A",
              description="项目特有按钮 F:/项目/按钮A",
              status="observed",
          )]}, expect_ok=True)
    check("5b skill 含项目绝对路径应报错",
          {"experiences": [_mk(
              experience_id="exp-skill",
              target_type="skill",
              target_path="F:/Thomas/SharedSKILLS/x/SKILL.md",
              generalized_rule="按钮 F:/项目/按钮A 要拆分",
              status="observed",
          )]}, expect_error_contains="项目绝对路径")

    # 6. 应用后出现误路由可以进入 deprecated 或 reverted
    check("6 applied->deprecated 保留原因通过",
          {"experiences": [_mk(
              status="deprecated",
              decision_log=[{"from": "applied", "to": "deprecated", "at": "2026-01-01", "by": "x", "reason": "不再适用"}],
          )]}, expect_ok=True)

    # 7. 已回滚的经验不能被无记录地重新标记为 applied
    check("7 reverted->applied 非法",
          {"experiences": [_mk(
              status="applied",
              decision_log=[
                  {"from": "applied", "to": "reverted", "at": "1", "by": "x", "reason": "y"},
                  {"from": "reverted", "to": "applied", "at": "2", "by": "x", "reason": "z"},
              ],
          )]}, expect_error_contains="非法转换：reverted->applied")

    return failures, total


# ---- 主入口 ----

def main(argv=None) -> int:
    _configure_output()
    parser = argparse.ArgumentParser(description="experience-registry.yaml 只读校验器")
    parser.add_argument("--registry", default=None, help="登记文件路径（默认同目录 experience-registry.yaml）")
    parser.add_argument("--selftest", action="store_true", help="运行内置语义测试")
    args = parser.parse_args(argv)

    if args.selftest:
        failures, total = selftest()
        if failures:
            print(f"自测失败 {len(failures)} / {total} 项：")
            for f in failures:
                print("  " + f)
            return 1
        print(f"自测通过：{total} 个用例全部符合预期")
        return 0

    path = Path(args.registry) if args.registry else Path(__file__).resolve().parent / "experience-registry.yaml"
    if not path.exists():
        print(f"文件不存在：{path}")
        return 1
    try:
        text = path.read_text(encoding="utf-8")
        if yaml is not None:
            data = yaml.safe_load(text)
        else:
            # Keep the validator usable in a zero-dependency environment.
            # The repository registry is deliberately within skill_doctor's
            # supported YAML subset.
            sys.path.insert(0, str(path.parent / "scripts"))
            from skill_doctor import parse_yaml_simple  # type: ignore
            data = parse_yaml_simple(text)
    except Exception as exc:
        print(f"YAML 解析失败：{exc}")
        return 1
    except OSError as exc:
        print(f"读取失败：{exc}")
        return 1

    errors = validate_registry(data)
    if errors:
        print(f"校验失败，共 {len(errors)} 项：")
        for e in errors:
            print("  - " + e)
        return 1

    count = len(data.get("experiences", [])) if isinstance(data, dict) else 0
    print(f"校验通过：{path.name} 格式、字段、状态与引用均合法（{count} 条经验）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
