#!/usr/bin/env python3
"""Controlled CLI wrapper for documented zmdata APIs."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


API_TITLE_RE = re.compile(r"^##\s+.+\(([a-z][a-z0-9_]*)\)\s*$")
REQUIRED_ZMDATA_VERSION = "1.4.2"
SDK_WHEEL_PATH = Path(
    "/Users/lee/git/APIClientResearch/release/zmdata-1.4.2-py3-none-any.whl"
)
API_MIN_VERSION = {
    "fund_search_quick": "1.4.2",
    "risk_factor_returns": "1.4.1",
}
PM_API_NAMES = {
    "pm_info_list",
    "pm_analysis_config",
    "pm_base_info",
    "pm_strategy_tracks",
    "pm_strategy_benchmark",
    "pm_performance_trend",
    "pm_nav",
    "pm_performance_stats",
    "pm_subfunds",
    "pm_subfund_nav",
    "pm_asset_allocation",
    "pm_strategy_nav",
    "pm_strategy_period_performance",
    "pm_strategy_full_period_performance",
    "pm_strategy_cumulative_pnl",
    "pm_strategy_cumulative_return",
    "pm_strategy_pnl_by_period",
    "pm_brinson_attribution",
    "pm_strategy_correlation",
    "pm_strategy_benchmark_comparison",
    "pm_strategy_performance_list",
    "pm_strategy_track_allocation",
    "pm_strategy_track_cumulative_pnl",
    "pm_strategy_track_cumulative_return",
    "pm_strategy_track_contribution",
    "pm_track_allocation",
    "pm_track_revenue",
    "pm_risk_asset_exposure_trend",
    "pm_risk_asset_exposure_by_fund",
    "pm_risk_asset_exposure_by_track",
    "pm_risk_style_exposure_trend",
    "pm_risk_style_exposure_by_fund",
    "pm_risk_style_exposure_by_track",
    "pm_risk_industry_exposure_trend",
    "pm_risk_industry_exposure_by_fund",
    "pm_risk_industry_exposure_by_track",
    "pm_risk_credit_exposure_trend",
    "pm_risk_credit_exposure_by_fund",
    "pm_risk_credit_exposure_by_track",
    "pm_risk_factor_exposure",
    "pm_adviser_factor_sensitivity",
    "pm_holding_fund_navs",
    "pm_holding_fund_performance",
    "pm_holding_current_fund_stats",
    "pm_holding_historical_fund_stats",
    "pm_holding_yield_decomposition",
    "pm_holding_fund_correlation",
    "pm_holding_track_correlation",
    "pm_adviser_track_correlation",
    "pm_adviser_track_correlation_trend",
    "pm_adviser_correlation",
    "pm_holding_asset_exposure_by_fund",
    "pm_holding_style_exposure_by_fund",
}


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def reference_dir() -> Path:
    return skill_root() / "references"


def documented_apis() -> dict[str, dict[str, str]]:
    apis: dict[str, dict[str, str]] = {}
    for path in sorted(reference_dir().glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = API_TITLE_RE.match(line.strip())
            if match:
                name = match.group(1)
                apis[name] = {
                    "file": str(path.relative_to(skill_root())),
                    "title": line.strip().lstrip("#").strip(),
                }
    return apis


def parse_params(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--params must be valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("--params must be a JSON object")
    return value


def parse_key_value(value: str) -> tuple[str, Any]:
    if "=" not in value:
        raise SystemExit("--set values must use key=value")
    key, raw = value.split("=", 1)
    key = key.strip()
    if not key:
        raise SystemExit("--set key cannot be empty")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = raw
    return key, parsed


def build_params(args: argparse.Namespace) -> dict[str, Any]:
    params = parse_params(args.params)
    for item in args.set or []:
        key, value = parse_key_value(item)
        params[key] = value
    return params


def ensure_pm_key(api_name: str, api_module: Any) -> None:
    if api_name not in PM_API_NAMES:
        return
    env_key = os.getenv("ZM_PM_API_KEY")
    if env_key:
        setattr(api_module, "PM_API_KEY", env_key)
        return
    existing = getattr(api_module, "PM_API_KEY", None)
    if existing:
        return
    raise SystemExit(
        f"{api_name} is a 投后(组合) API and requires ZM_PM_API_KEY in the "
        "environment. Do not pass real API keys on the command line."
    )


def import_zmdata() -> Any:
    try:
        import zmdata as api  # type: ignore
    except Exception as exc:
        raise SystemExit(
            "Failed to import zmdata. Install/configure the zmdata package in "
            f"this Python environment first. Original error: {exc}"
        ) from exc
    return api


def version_parts(version: str | None) -> tuple[int, ...]:
    if not version:
        return (0,)
    parts = []
    for raw in str(version).split("."):
        match = re.match(r"^(\d+)", raw)
        if not match:
            break
        parts.append(int(match.group(1)))
    return tuple(parts) if parts else (0,)


def version_lt(installed: str | None, required: str) -> bool:
    left = version_parts(installed)
    right = version_parts(required)
    length = max(len(left), len(right))
    left += (0,) * (length - len(left))
    right += (0,) * (length - len(right))
    return left < right


def sdk_install_hint() -> str:
    return f"python -m pip install --upgrade {SDK_WHEEL_PATH}"


def ensure_sdk_min_version(api_name: str, api_module: Any) -> None:
    min_version = API_MIN_VERSION.get(api_name)
    if not min_version:
        return
    installed = getattr(api_module, "__version__", None)
    if version_lt(installed, min_version):
        raise SystemExit(
            f"{api_name} requires zmdata >= {min_version}; installed "
            f"version is {installed or 'unknown'}.\n"
            f"Upgrade from the local wheel:\n  {sdk_install_hint()}"
        )


def normalize_result(result: Any, head: int | None = None) -> Any:
    if head is not None and hasattr(result, "head"):
        return result.head(head)
    return result


def write_result(result: Any, output_format: str, out_path: str | None) -> None:
    if hasattr(result, "to_json") and output_format == "json":
        text = result.to_json(orient="records", date_format="iso", force_ascii=False)
    elif hasattr(result, "to_csv") and output_format == "csv":
        text = result.to_csv(index=False)
    elif hasattr(result, "to_markdown") and output_format == "markdown":
        text = result.to_markdown(index=False)
    else:
        text = json.dumps(result, ensure_ascii=False, default=str, indent=2)

    if out_path:
        Path(out_path).write_text(text, encoding="utf-8")
    else:
        print(text)


def cmd_list(args: argparse.Namespace) -> int:
    apis = documented_apis()
    keyword = args.keyword.lower() if args.keyword else None
    for name in sorted(apis):
        meta = apis[name]
        haystack = f"{name} {meta['title']} {meta['file']}".lower()
        if keyword and keyword not in haystack:
            ref_text = (skill_root() / meta["file"]).read_text(encoding="utf-8").lower()
            if keyword not in ref_text:
                continue
        print(f"{name}\t{meta['file']}\t{meta['title']}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    apis = documented_apis()
    meta = apis.get(args.api_name)
    if not meta:
        raise SystemExit(f"Undocumented API: {args.api_name}")
    print(f"{args.api_name}\t{meta['file']}\t{meta['title']}")
    ref = skill_root() / meta["file"]
    lines = ref.read_text(encoding="utf-8").splitlines()
    start = None
    for idx, line in enumerate(lines):
        if API_TITLE_RE.match(line.strip()) and args.api_name in line:
            start = idx
            break
    if start is None:
        return 0
    section = []
    for line in lines[start:]:
        if section and line.startswith("## "):
            break
        section.append(line)
    print("\n".join(section[: args.lines]))
    return 0


def cmd_call(args: argparse.Namespace) -> int:
    apis = documented_apis()
    if args.api_name not in apis:
        choices = ", ".join(sorted(apis))
        raise SystemExit(f"Undocumented API: {args.api_name}\nAllowed APIs: {choices}")

    api = import_zmdata()
    ensure_sdk_min_version(args.api_name, api)
    ensure_pm_key(args.api_name, api)
    func = getattr(api, args.api_name, None)
    if not callable(func):
        min_version = API_MIN_VERSION.get(args.api_name)
        version_hint = (
            f" This API requires zmdata >= {min_version}."
            if min_version else ""
        )
        raise SystemExit(
            f"zmdata has no callable API named {args.api_name}. "
            f"Check that the installed zmdata version matches the references.{version_hint}"
        )

    params = build_params(args)
    result = func(**params)
    result = normalize_result(result, args.head)
    write_result(result, args.format, args.out)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    try:
        api = import_zmdata()
        installed = getattr(api, "__version__", None)
        import_ok = True
    except SystemExit as exc:
        installed = None
        import_ok = False
        print(str(exc), file=sys.stderr)

    wheel_exists = SDK_WHEEL_PATH.exists()
    version_ok = import_ok and not version_lt(installed, REQUIRED_ZMDATA_VERSION)

    print(f"zmdata importable: {import_ok}")
    print(f"installed version: {installed or 'unknown'}")
    print(f"required version: {REQUIRED_ZMDATA_VERSION}")
    print(f"version ok: {version_ok}")
    print(f"local wheel: {SDK_WHEEL_PATH}")
    print(f"wheel exists: {wheel_exists}")
    if not version_ok:
        print(f"upgrade command: {sdk_install_hint()}")
    return 0 if import_ok and version_ok and wheel_exists else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Call documented zmdata APIs through a controlled CLI."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List documented API names")
    list_parser.add_argument("--keyword", help="Filter API list by keyword")
    list_parser.set_defaults(func=cmd_list)

    info_parser = sub.add_parser("info", help="Show reference section for an API")
    info_parser.add_argument("api_name")
    info_parser.add_argument("--lines", type=int, default=80)
    info_parser.set_defaults(func=cmd_info)

    doctor_parser = sub.add_parser("doctor", help="Check zmdata SDK version")
    doctor_parser.set_defaults(func=cmd_doctor)

    call_parser = sub.add_parser("call", help="Call a documented zmdata API")
    call_parser.add_argument("api_name")
    call_parser.add_argument(
        "--params",
        default="{}",
        help="JSON object passed as keyword arguments",
    )
    call_parser.add_argument(
        "--set",
        action="append",
        help="Add/override one parameter using key=value; value may be JSON",
    )
    call_parser.add_argument(
        "--format",
        choices=["json", "csv", "markdown"],
        default="json",
        help="Output format for pandas-like results",
    )
    call_parser.add_argument("--head", type=int, help="Return only first N rows")
    call_parser.add_argument("--out", help="Write output to a file")
    call_parser.set_defaults(func=cmd_call)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
