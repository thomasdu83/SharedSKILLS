#!/usr/bin/env python3
"""Plan multi-fund audit reuse vs fresh-audit work without creating reports."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable


@dataclass
class FundPlan:
    fund: str
    status: str
    audit_time: str
    report_path: str
    action: str


def _find_saved_report(query: str, shared_root: str | None) -> dict:
    cmd = [PYTHON, str(SCRIPT_DIR / "find_saved_report.py"), query, "--json"]
    if shared_root:
        cmd.extend(["--shared-root", shared_root])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode == 2:
        raise SystemExit(proc.stdout.strip() or proc.stderr.strip())
    if proc.returncode not in (0, 1):
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip() or "find report failed")
    return json.loads(proc.stdout or '{"matches":0,"reports":[]}')


def build_plan(
    funds: list[str],
    refresh_all: bool,
    refresh_funds: set[str],
    shared_root: str | None,
) -> list[FundPlan]:
    plans: list[FundPlan] = []
    for fund in funds:
        payload = _find_saved_report(fund, shared_root)
        reports = payload.get("reports", [])
        must_refresh = refresh_all or fund in refresh_funds
        if reports and not must_refresh:
            report = reports[0]
            plans.append(
                FundPlan(
                    fund=fund,
                    status="已有历史报告",
                    audit_time=report.get("audit_time", "-"),
                    report_path=report.get("path", "-"),
                    action="默认复用",
                )
            )
        elif reports and must_refresh:
            report = reports[0]
            plans.append(
                FundPlan(
                    fund=fund,
                    status="已有历史报告",
                    audit_time=report.get("audit_time", "-"),
                    report_path=report.get("path", "-"),
                    action="按用户要求重新审核",
                )
            )
        else:
            plans.append(
                FundPlan(
                    fund=fund,
                    status="未命中历史报告",
                    audit_time="-",
                    report_path="-",
                    action="需要新审核",
                )
            )
    return plans


def emit_markdown(plans: list[FundPlan]) -> None:
    print("## 多基金审核预检")
    print("")
    print("| 基金 | 历史报告状态 | 审核时间 | 建议动作 | 报告路径 |")
    print("|---|---|---|---|---|")
    for item in plans:
        print(
            f"| {item.fund} | {item.status} | {item.audit_time} | {item.action} | {item.report_path} |"
        )
    print("")
    has_history = any(item.status == "已有历史报告" for item in plans)
    has_new = any(item.status == "未命中历史报告" for item in plans)
    if has_history and has_new:
        print("建议默认复用已有历史报告，仅审核未覆盖基金。")
    elif has_history:
        print("所有基金均已有历史报告；如需重新审核，请明确说明。")
    else:
        print("未命中历史报告；需要逐只基金执行新审核。")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan multi-fund audit reuse vs fresh audit.")
    parser.add_argument("funds", nargs="+", help="Fund names to check")
    parser.add_argument("--refresh-all", action="store_true", help="Mark all funds for fresh audit")
    parser.add_argument(
        "--refresh",
        action="append",
        default=[],
        help="Fund name that should be freshly audited. Repeat as needed.",
    )
    parser.add_argument(
        "--shared-root",
        help="Shared report root. Defaults to Y:\\投顾管理人研究\\fund-track-tag-audit or env FUND_TRACK_TAG_AUDIT_ROOT.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    plans = build_plan(args.funds, args.refresh_all, set(args.refresh), args.shared_root)
    if args.json:
        print(json.dumps([item.__dict__ for item in plans], ensure_ascii=False, indent=2))
    else:
        emit_markdown(plans)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
